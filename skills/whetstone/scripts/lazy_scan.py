#!/usr/bin/env python3
"""Scan a project, or the lines added since a git revision, for signs of corner-cutting.

Looks for stubs, placeholders, TODO markers, skipped or hollow tests, swallowed
errors, and the phrases agents use when they quietly shrink the scope
("simplified version", "for now", "in a real implementation"). With --since it
also reports deleted test files and removed assertions.

A hit is a lead, not a verdict: read each one in context before sending it back.

  python3 lazy_scan.py DIR                 # whole tree
  python3 lazy_scan.py DIR --since HEAD~3  # only what changed since that revision (plus untracked files)
  python3 lazy_scan.py DIR --since HEAD --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SELF = Path(__file__).resolve()

# (category, severity, pattern). Severity: high = almost always a real gap, med = check it, low = context.
RULES = [
    ("stub", "high", r"\bNotImplemented(Error)?\b|\bunimplemented!\(|\btodo!\(|not (yet )?implemented|"
                     r"throw new Error\(\s*['\"`](TODO|not implemented|unimplemented)|"
                     r"^\s*pass\s*#|\bdef \w+\([^)]*\)\s*(->\s*[^:]+)?:\s*(pass|\.\.\.)\s*$|"
                     r"//\s*(stub|implement (this|me|later))\b|#\s*(stub|implement (this|me|later))\b"),
    ("test-skip", "high", r"\b(it|test|describe|context)\.(skip|todo)\(|\b(x|f)(it|describe|test)\(\s*['\"`]|"
                          r"@pytest\.mark\.(skip|xfail)\b|@unittest\.skip|\bpytest\.skip\(|\bt\.Skip(Now)?\(|"
                          r"#\[ignore\]|\b(it|test|describe)\.only\("),
    ("hollow-test", "high", r"\bassert\s+True\b|\bassertTrue\(\s*True\s*\)|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)|"
                            r"\bassert\s+1\s*==\s*1\b|expect\(\s*1\s*\)\.toBe\(\s*1\s*\)|assert!\(\s*true\s*\)"),
    ("swallowed-error", "high", r"except(\s+[\w.]+(\s+as\s+\w+)?)?\s*:\s*(pass|\.\.\.)\s*$|"
                                r"catch\s*(\([^)]*\))?\s*\{\s*\}|\.catch\(\s*\(\s*\w*\s*\)\s*=>\s*(\{\s*\}|null|undefined)\s*\)"),
    ("marker", "med", r"\b(TODO|FIXME|XXX|HACK)\b"),
    ("placeholder", "med", r"\bplaceholder\b|lorem ipsum|\bdummy (data|value|response|asset|texture|model)\b|"
                           r"\bfake (data|response|result|value)s?\b|\bmock(ed)? (data|response|result)s?\b|"
                           r"\bhard-?coded (for now|value|result|response)|\bstand-?in\b|"
                           r"\b(temp|temporary) (art|asset|model|texture|mesh|sprite|sound|music|ui)\b|programmer art"),
    ("scope-shrink", "low", r"\bfor now\b|\bsimplified (version|implementation|model|approach|logic)\b|"
                            r"\bin a real (implementation|app|application|game|system|project)\b|"
                            r"\bin production,? (you|we) (would|should)\b|left as an exercise|"
                            r"\b(basic|minimal|simple) (version|implementation) (for now|only)\b|"
                            r"\bfor brevity\b|\bomitted for\b|\bcoming soon\b|"
                            r"\bwould (normally|ideally) (be|use|do)\b|\bnot (supported|handled) yet\b|"
                            r"\bout of scope for (now|this)\b"),
    ("primitive-art", "low", r"\b(Box|Sphere|Cylinder|Capsule|Cone|Plane|Torus)(Buffer)?Geometry\(|"
                             r"\bMeshBasicMaterial\(|CreatePrimitive\(|PrimitiveType\.(Cube|Sphere|Capsule|Cylinder)|"
                             r"primitive_(cube|uv_sphere|cylinder|cone|plane)_add\(|\bfillRect\(.*#(f0f|ff00ff)"),
]
COMPILED = [(c, s, re.compile(p, re.I if c not in ("marker",) else 0)) for c, s, p in RULES]

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", "target", "vendor", ".venv", "venv", "env",
             "__pycache__", ".whetstone", ".next", ".nuxt", "coverage", "third_party", "third-party",
             ".cache", ".parcel-cache", ".turbo", "Pods", "DerivedData", ".gradle", ".idea", ".vscode",
             "site-packages", "bower_components", ".tmp", "tmp"}
TEXT_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte", ".go", ".rs", ".java", ".kt",
            ".kts", ".swift", ".m", ".mm", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".rb", ".php", ".lua",
            ".gd", ".gdshader", ".glsl", ".wgsl", ".hlsl", ".shader", ".frag", ".vert", ".sh", ".zsh", ".bash",
            ".sql", ".html", ".css", ".scss", ".md", ".mdx", ".txt", ".rst", ".toml", ".yaml", ".yml", ".json",
            ".ex", ".exs", ".scala", ".dart", ".zig", ".nim", ".r", ".jl", ".ps1"}
SKIP_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock", "go.sum"}
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|[._-](test|spec)\.[a-z]+$|(^|/)test_[^/]*\.py$", re.I)
ASSERT_LINE = re.compile(r"\bassert|\bexpect\(|\bshould\b|\bt\.(Error|Fatal)|\bXCTAssert|\bcheck\(", re.I)
MAX_BYTES = 1_000_000


def wanted(path: Path) -> bool:
    if path.name in SKIP_NAMES or path.name.endswith((".min.js", ".min.css", ".map")):
        return False
    return path.suffix.lower() in TEXT_EXT or path.name in {"Makefile", "Dockerfile", "CMakeLists.txt"}


def is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return b"\0" in f.read(4096)
    except OSError:
        return True


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".tmp")]
        for name in filenames:
            p = Path(dirpath) / name
            if p.resolve() == SELF or not wanted(p):
                continue
            try:
                if p.stat().st_size > MAX_BYTES or is_binary(p):
                    continue
            except OSError:
                continue
            yield p


def scan_line(text: str):
    for cat, sev, rx in COMPILED:
        if rx.search(text):
            yield cat, sev


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


def added_lines(root: Path, rev: str):
    """Yield (path, lineno, text) for lines added since rev, plus every line of untracked files."""
    diff = git(root, "diff", "--unified=0", "--no-color", "--no-ext-diff", rev, "--")
    path, lineno = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = None if line[4:] == "/dev/null" else line[4:].removeprefix("b/")
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and path:
            if wanted(Path(path)) and (root / path).resolve() != SELF:
                yield path, lineno, line[1:]
            lineno += 1
    for rel in git(root, "ls-files", "--others", "--exclude-standard").splitlines():
        p = root / rel
        if any(part in SKIP_DIRS for part in Path(rel).parts) or not wanted(p) or p.resolve() == SELF:
            continue
        try:
            if p.stat().st_size > MAX_BYTES or is_binary(p):
                continue
            for i, text in enumerate(p.read_text(errors="replace").splitlines(), 1):
                yield rel, i, text
        except OSError:
            continue


def removed_info(root: Path, rev: str) -> dict:
    deleted_tests, removed_asserts = [], 0
    for line in git(root, "diff", "--name-status", "--no-color", rev, "--").splitlines():
        parts = line.split("\t")
        if parts and parts[0] == "D" and len(parts) > 1 and TEST_PATH.search(parts[1]):
            deleted_tests.append(parts[1])
    diff = git(root, "diff", "--unified=0", "--no-color", "--no-ext-diff", rev, "--")
    path = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            path = line[4:].removeprefix("a/")
        elif line.startswith("-") and not line.startswith("---") and path and TEST_PATH.search(path):
            if ASSERT_LINE.search(line):
                removed_asserts += 1
    return {"deleted_tests": deleted_tests, "removed_assertions": removed_asserts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--since", metavar="REV", help="only scan lines added since this git revision")
    ap.add_argument("--max", type=int, default=8, help="examples shown per category (default 8)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any high-severity hit is found")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    hits: dict[str, list] = {}
    sev_of = {c: s for c, s, _ in RULES}
    removed = {}
    if a.since:
        try:
            lines = list(added_lines(root, a.since))
            removed = removed_info(root, a.since)
        except subprocess.CalledProcessError as e:
            print(f"git failed: {e.stderr.strip()}", file=sys.stderr)
            return 2
    else:
        lines = []
        for p in walk(root):
            try:
                for i, text in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    lines.append((str(p.relative_to(root)), i, text))
            except OSError:
                continue
    for path, i, text in lines:
        if len(text) > 400:
            text = text[:400]
        for cat, _ in scan_line(text):
            hits.setdefault(cat, []).append({"path": path, "line": i, "text": text.strip()[:160]})

    order = {"high": 0, "med": 1, "low": 2}
    cats = sorted(hits, key=lambda c: (order[sev_of[c]], -len(hits[c])))
    high = sum(len(hits[c]) for c in cats if sev_of[c] == "high") + len(removed.get("deleted_tests", []))

    if a.json:
        print(json.dumps({"root": str(root), "since": a.since, "lines_scanned": len(lines),
                          "counts": {c: len(hits[c]) for c in cats}, "hits": hits, **removed}, indent=2))
    else:
        scope = f"lines added since {a.since}" if a.since else "whole tree"
        print(f"lazy_scan: {root.name} ({scope}, {len(lines)} lines)")
        if removed.get("deleted_tests"):
            print(f"[high] deleted test files: {', '.join(removed['deleted_tests'])}")
        if removed.get("removed_assertions"):
            print(f"[med]  assertions removed from test files: {removed['removed_assertions']}")
        if not cats and not removed.get("deleted_tests"):
            print("no hits")
        for c in cats:
            print(f"[{sev_of[c]}] {c}: {len(hits[c])}")
            for h in hits[c][: a.max]:
                print(f"    {h['path']}:{h['line']}: {h['text']}")
            if len(hits[c]) > a.max:
                print(f"    … {len(hits[c]) - a.max} more")
        print("Hits are leads: read each in context. 'low' items matter when they touch contract items.")
    return 1 if a.strict and high else 0


if __name__ == "__main__":
    sys.exit(main())
