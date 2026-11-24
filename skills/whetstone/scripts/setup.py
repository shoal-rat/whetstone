#!/usr/bin/env python3
"""Prepare a workspace for a whetstone session, or tidy it up afterwards.

  python3 setup.py DIR            # create .whetstone/, copy templates, install the AGENTS.md block
  python3 setup.py DIR --check    # show what is installed
  python3 setup.py DIR --remove   # take the AGENTS.md block out again (keeps .whetstone/)

The AGENTS.md block is what GPT reads at the start of every Codex session in DIR:
the supervisor arrangement, the build agreements, and fishtrap's goal-and-writing
principles (github.com/shoal-rat/fishtrap) adapted for long builds. If the user's
global Codex AGENTS.md already carries fishtrap, those principles are left out of
the project block so GPT does not read them twice (override with --principles).

Standard library only. Safe to run again: it replaces its own block and leaves
the rest of AGENTS.md alone. A backup of any existing AGENTS.md goes to
.whetstone/backups/ first.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "templates"
BLOCK_SRC = TEMPLATES / "AGENTS.whetstone.md"
BEGIN_PREFIX = "<!-- whetstone:begin"
BEGIN = f"<!-- whetstone:begin v{VERSION} -->"
END = "<!-- whetstone:end -->"
FISHTRAP_RE = re.compile(r"<!-- fishtrap -->\n?(.*?)<!-- /fishtrap -->\n?", re.S)
MAC_CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()


def global_has_fishtrap() -> bool:
    p = codex_home() / "AGENTS.md"
    try:
        return "<!-- fishtrap:begin" in p.read_text(errors="replace")
    except OSError:
        return False


def build_block(with_principles: bool) -> str:
    text = BLOCK_SRC.read_text()
    text = FISHTRAP_RE.sub(lambda m: m.group(1) if with_principles else "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return f"{BEGIN}\n{text}\n{END}\n"


def strip_block(text: str) -> tuple[str, bool]:
    start = text.find(BEGIN_PREFIX)
    if start < 0:
        return text, False
    end = text.find(END, start)
    if end < 0:
        return text, False
    end += len(END)
    rest = (text[:start] + text[end:]).lstrip("\n")
    return rest, True


def find_codex() -> str | None:
    for cand in (os.environ.get("CODEX_BIN"), shutil.which("codex"), MAC_CODEX):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def in_git(ws: Path) -> bool:
    r = subprocess.run(["git", "-C", str(ws), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def ensure_gitignore(ws: Path) -> bool:
    gi = ws / ".gitignore"
    lines = gi.read_text().splitlines() if gi.exists() else []
    if any(l.strip() in (".whetstone", ".whetstone/", "/.whetstone/", "/.whetstone") for l in lines):
        return False
    with gi.open("a") as f:
        if lines and lines[-1].strip():
            f.write("\n")
        f.write(".whetstone/\n")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?", default=".")
    ap.add_argument("--check", action="store_true", help="report the current state and exit")
    ap.add_argument("--remove", action="store_true", help="remove the AGENTS.md block")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--principles", action="store_true", help="include fishtrap principles even if installed globally")
    g.add_argument("--no-principles", action="store_true", help="leave fishtrap principles out")
    ap.add_argument("--no-agents", action="store_true", help="do not touch AGENTS.md")
    ap.add_argument("--track", action="store_true", help="do not add .whetstone/ to .gitignore")
    a = ap.parse_args()

    ws = Path(a.workspace).expanduser().resolve()
    if not ws.is_dir():
        print(f"workspace not found: {ws}", file=sys.stderr)
        return 2
    state = ws / ".whetstone"
    agents = ws / "AGENTS.md"
    meta_path = state / "setup.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    if a.check:
        text = agents.read_text(errors="replace") if agents.exists() else ""
        m = re.search(r"<!-- whetstone:begin v([\d.]+) -->", text)
        print(f"workspace       {ws}")
        print(f"codex           {find_codex() or 'NOT FOUND'}")
        print(f"AGENTS.md block {'v' + m.group(1) if m else 'not installed'}"
              f"{' (with fishtrap principles)' if m and 'Understanding the task' in text else ''}")
        print(f"global fishtrap {'yes' if global_has_fishtrap() else 'no'} ({codex_home() / 'AGENTS.md'})")
        for name in ("CONTRACT.md", "LEDGER.md", "thread_id"):
            print(f"{name:<15} {'present' if (state / name).exists() else '-'}")
        return 0

    if a.remove:
        if not agents.exists():
            print("no AGENTS.md; nothing to remove")
            return 0
        text, found = strip_block(agents.read_text())
        if not found:
            print("no whetstone block in AGENTS.md")
            return 0
        if not text.strip() and meta.get("created_agents"):
            agents.unlink()
            print("removed AGENTS.md (whetstone had created it)")
        else:
            agents.write_text(text)
            print("removed the whetstone block from AGENTS.md")
        return 0

    state.mkdir(exist_ok=True)
    (state / "research").mkdir(exist_ok=True)
    for name in ("CONTRACT.md", "LEDGER.md"):
        dst = state / name
        if not dst.exists():
            shutil.copy2(TEMPLATES / name, dst)
            print(f"created .whetstone/{name}")

    if not a.track and in_git(ws) and ensure_gitignore(ws):
        print("added .whetstone/ to .gitignore")

    if not a.no_agents:
        if a.principles:
            with_p = True
        elif a.no_principles:
            with_p = False
        else:
            with_p = not global_has_fishtrap()
        block = build_block(with_p)
        existing = agents.read_text() if agents.exists() else ""
        if existing:
            (state / "backups").mkdir(exist_ok=True)
            bk = state / "backups" / f"AGENTS.md.{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(agents, bk)
        else:
            meta.setdefault("created_agents", True)
        rest, replaced = strip_block(existing)
        agents.write_text(block + ("\n" + rest if rest.strip() else ""))
        what = "updated" if replaced else "installed"
        note = ("with fishtrap principles" if with_p else
                "without fishtrap principles (already in the global Codex AGENTS.md)" if global_has_fishtrap()
                else "without fishtrap principles")
        print(f"{what} the whetstone block at the top of AGENTS.md, {note}")

    meta.update({"version": VERSION, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")})
    meta_path.write_text(json.dumps(meta, indent=2))
    codex = find_codex()
    print(f"codex: {codex or 'NOT FOUND - install Codex or set CODEX_BIN'}")
    print("next: write .whetstone/CONTRACT.md, then send the kickoff brief with gpt_turn.py --new")
    return 0


if __name__ == "__main__":
    sys.exit(main())
