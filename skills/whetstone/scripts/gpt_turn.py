#!/usr/bin/env python3
"""Run one GPT turn through the Codex CLI for a whetstone session, then print a digest.

The digest is what the supervising agent reads: GPT's structured report, the
commands it actually ran (with exit codes), the files it changed, the web
searches it made, token use, and red flags where the report and the event log
disagree. Everything is saved under <workspace>/.whetstone/turns/NNN/.

Exit codes: 0 turn finished, 1 Codex failed, 2 bad arguments, 3 usage limit
(resume later with the same command), 4 timeout.
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
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "report.schema.json"
MAC_CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
LIMIT_RE = re.compile(r"usage limit|hit your usage limit|rate limit|quota", re.I)
TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|[._-](test|spec)\.[a-z]+$|^test_.*\.py$", re.I)

FOOTER = """

---
Work until this brief's acceptance items pass by your own checks, or until you hit something only the
supervisor can decide. Then end the turn with the JSON report (the response schema is enforced):
for each acceptance item give pass/fail/not_checked and its proof from this turn (the exact command in
backticks and its result, a test name, or a capture path). List every shortfall plainly."""


def find_codex(explicit: str | None) -> str:
    for cand in (explicit, os.environ.get("CODEX_BIN"), shutil.which("codex"), MAC_CODEX):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    sys.exit("whetstone: Codex CLI not found. Install it, or set CODEX_BIN to its path.")


def next_turn_dir(turns: Path) -> Path:
    turns.mkdir(parents=True, exist_ok=True)
    nums = [int(p.name) for p in turns.iterdir() if p.is_dir() and p.name.isdigit()]
    d = turns / f"{(max(nums) + 1 if nums else 1):03d}"
    d.mkdir()
    return d


def toml_str(s: str) -> str:
    return json.dumps(s)  # a JSON string literal is a valid TOML basic string


def build_cmd(a, codex: str, ws: Path, tdir: Path, thread: str | None) -> list[str]:
    cmd = [codex, "exec"]
    if thread:
        cmd += ["resume"]
    cmd += ["--json", "--skip-git-repo-check", "-o", str(tdir / "last.md")]
    if not a.no_schema:
        cmd += ["--output-schema", str(SCHEMA)]
    if thread:
        # `codex exec resume` has no --sandbox/--cd flags and otherwise falls back to read-only.
        cmd += ["-c", f"sandbox_mode={toml_str(a.sandbox)}"]
    else:
        cmd += ["-C", str(ws), "-s", a.sandbox]
    if a.network and a.sandbox == "workspace-write":
        cmd += ["-c", "sandbox_workspace_write.network_access=true"]
    if a.search:
        cmd += ["-c", 'web_search="live"']
    if a.effort:
        cmd += ["-c", f"model_reasoning_effort={toml_str(a.effort)}"]
    if a.model:
        cmd += ["-m", a.model]
    for kv in a.config:
        cmd += ["-c", kv]
    for img in a.image:
        cmd += ["-i", str(Path(img).resolve())]
    if thread:
        cmd += [thread]
    cmd += ["-"]
    return cmd


def short(s: str, n: int = 110) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def unwrap_shell(cmd: str) -> str:
    m = re.match(r"^\S*(?:ba|z)?sh -lc\s+(.*)$", cmd, re.S)
    if not m:
        return cmd
    body = m.group(1).strip()
    if len(body) >= 2 and body[0] in "'\"" and body[-1] == body[0]:
        body = body[1:-1]
    elif body[:1] in "'\"":
        body = body[1:]
    return body


def parse_events(path: Path) -> dict:
    info = {"thread_id": None, "commands": [], "files": [], "searches": [], "messages": [],
            "usage": {}, "errors": [], "todos": None, "turn_completed": False}
    if not path.exists():
        return info
    for line in path.open(errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "thread.started":
            info["thread_id"] = ev.get("thread_id")
        elif t == "turn.completed":
            info["turn_completed"] = True
            for k, v in (ev.get("usage") or {}).items():
                if isinstance(v, (int, float)):
                    info["usage"][k] = info["usage"].get(k, 0) + v
        elif t in ("turn.failed", "error"):
            info["errors"].append(short(json.dumps(ev.get("error") or ev.get("message") or ev), 300))
        elif t == "item.completed":
            it = ev.get("item") or {}
            kind = it.get("type")
            if kind == "command_execution":
                out = it.get("aggregated_output") or ""
                info["commands"].append({"command": unwrap_shell(it.get("command", "")),
                                         "exit_code": it.get("exit_code"),
                                         "tail": out.strip().splitlines()[-1:] if out.strip() else []})
            elif kind == "file_change":
                for ch in it.get("changes") or []:
                    info["files"].append({"path": ch.get("path", ""), "kind": ch.get("kind", "")})
            elif kind == "web_search":
                act = it.get("action") or {}
                q = it.get("query") or act.get("query") or act.get("url") or ""
                doms = []
                for r in it.get("results") or []:
                    d = r.get("domain") or r.get("url")
                    if d and d not in doms:
                        doms.append(d)
                info["searches"].append({"query": q, "action": act.get("type", ""), "domains": doms[:5]})
            elif kind == "agent_message":
                info["messages"].append(it.get("text", ""))
            elif kind == "todo_list":
                info["todos"] = it.get("items")
            elif kind == "error":
                info["errors"].append(short(it.get("message", ""), 300))
    return info


WALK_SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "target", "DerivedData", ".gradle",
             ".next", ".cache", ".parcel-cache", ".turbo", "Pods", "site-packages"}


def git_deleted(ws: Path) -> set[str]:
    r = subprocess.run(["git", "-C", str(ws), "status", "--porcelain=v1", "-uno"], capture_output=True, text=True)
    if r.returncode != 0:
        return set()
    return {line[3:] for line in r.stdout.splitlines() if line[:2].strip() == "D" or line[1:2] == "D"}


def written_since(ws: Path, since: float, limit: int = 30000) -> list[str]:
    """Files modified after `since`, so writes made through shell commands show up too."""
    out, seen = [], 0
    for dirpath, dirnames, filenames in os.walk(ws):
        dirnames[:] = [d for d in dirnames if d not in WALK_SKIP]
        if Path(dirpath) == ws / ".whetstone":
            dirnames[:] = [d for d in dirnames if d != "turns"]
        for name in filenames:
            seen += 1
            if seen > limit:
                return sorted(out)
            p = Path(dirpath) / name
            try:
                if p.stat().st_mtime >= since:
                    out.append(str(p.relative_to(ws)))
            except OSError:
                continue
    return sorted(out)


def rel(p: str, ws: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(ws))
    except (ValueError, OSError):
        return p


def red_flags(report: dict | None, info: dict, ws: Path, a) -> list[str]:
    flags = []
    cmds = info["commands"]
    ran = "\n".join(c["command"] for c in cmds)
    if report is None:
        if not getattr(a, "no_schema", False):
            flags.append("final message is not the JSON report (schema bypassed or turn cut short)")
        return flags
    acc = report.get("acceptance") or []
    not_pass = [x.get("id", "?") for x in acc if x.get("status") != "pass"]
    if report.get("status") == "complete" and not_pass:
        flags.append(f"status is 'complete' but items are not passing: {', '.join(not_pass)}")
    if report.get("status") == "complete" and report.get("shortfalls"):
        flags.append("status is 'complete' while shortfalls are listed")
    if not cmds and any(x.get("status") == "pass" for x in acc):
        flags.append("items marked pass but no command ran this turn")
    for x in acc:
        if x.get("status") != "pass":
            continue
        proof = x.get("proof") or ""
        if not proof.strip():
            flags.append(f"{x.get('id')}: pass with empty proof")
            continue
        for span in re.findall(r"`([^`]{3,})`", proof):
            head = span.strip().split("\n")[0]
            looks_cmd = bool(re.match(r"^(\./|npm|npx|pnpm|yarn|node|python|pytest|cargo|go |make|uv |bun|deno|"
                                      r"swift|xcodebuild|gradle|mvn|dotnet|bash|sh |ctest|cmake)", head))
            if looks_cmd and head not in ran and head.split()[0] not in ran:
                flags.append(f"{x.get('id')}: proof cites `{short(head, 60)}` but no such command ran this turn")
    for art in report.get("artifacts") or []:
        p = Path(art) if os.path.isabs(art) else ws / art
        if not p.exists():
            flags.append(f"artifact listed but missing on disk: {art}")
    deleted = {rel(f["path"], ws) for f in info["files"] if f["kind"] == "delete"} | set(info.get("fs_deleted", []))
    deleted_tests = sorted(p for p in deleted if TEST_PATH_RE.search(p))
    if deleted_tests:
        flags.append("test files deleted: " + ", ".join(deleted_tests[:6]))
    if a.search and not info["searches"]:
        flags.append("web search was enabled for research but GPT made no searches")
    srcs = [s for s in report.get("sources") or [] if s.get("url", "").startswith("http")]
    if srcs and not info["searches"]:
        flags.append(f"cites {len(srcs)} web source(s) but made no web searches this turn: from memory?")
    text = (report.get("summary") or "") + " " + (report.get("next") or "")
    if re.search(r"\b(I will|I'll|next I|going to|will now)\b", report.get("summary") or "", re.I):
        flags.append("summary describes plans rather than results")
    if re.search(r"\b(simplif|placeholder|stub|for now|mock(ed)?|temporary|basic version)\w*", text, re.I):
        flags.append("report mentions simplification/placeholder/temporary work: read it closely")
    return flags


def fmt_tokens(u: dict) -> str:
    def k(n):
        return f"{n/1e6:.2f}M" if n >= 1e6 else f"{n/1e3:.0f}k"
    if not u:
        return "n/a"
    return (f"in {k(u.get('input_tokens', 0))} (cached {k(u.get('cached_input_tokens', 0))}), "
            f"out {k(u.get('output_tokens', 0))}, reasoning {k(u.get('reasoning_output_tokens', 0))}")


def digest(tdir: Path, ws: Path, a) -> tuple[str, dict]:
    meta = json.loads((tdir / "meta.json").read_text()) if (tdir / "meta.json").exists() else {}
    info = parse_events(tdir / "events.jsonl")
    info["fs_deleted"] = (meta.get("fs_changes") or {}).get("deleted", [])
    last = (tdir / "last.md").read_text(errors="replace") if (tdir / "last.md").exists() else ""
    if not last and info["messages"]:
        last = info["messages"][-1]
    report = None
    try:
        report = json.loads(last) if last.strip().startswith("{") else None
    except json.JSONDecodeError:
        report = None
    flags = red_flags(report, info, ws, a)
    out = []
    dur = meta.get("seconds", 0)
    out.append(f"whetstone turn {tdir.name}  thread {info['thread_id'] or meta.get('thread') or '?'}  "
               f"{int(dur // 3600)}h{int(dur % 3600 // 60):02d}m{int(dur % 60):02d}s  codex exit {meta.get('returncode', '?')}")
    if report:
        out.append(f"REPORT status={report.get('status')}")
        out.append("  " + short(report.get("summary", ""), 400))
        for x in report.get("acceptance") or []:
            out.append(f"  [{x.get('status')}] {x.get('id')}: {short(x.get('proof', ''), 140)}")
        for s in report.get("shortfalls") or []:
            out.append(f"  shortfall: {short(s, 160)}")
        for q in report.get("questions") or []:
            out.append(f"  question: {short(q, 160)}")
        for s in report.get("sources") or []:
            out.append(f"  source: {short(s.get('url', ''), 70)} → {short(s.get('takeaway', ''), 90)}")
        if report.get("artifacts"):
            out.append("  artifacts: " + ", ".join(report["artifacts"][:12]))
        if report.get("next"):
            out.append("  next: " + short(report["next"], 160))
    else:
        out.append("FINAL MESSAGE (not a JSON report):")
        out.append("  " + short(last, 1200))
    cmds = info["commands"]
    failed = [c for c in cmds if c["exit_code"] not in (0, None)]
    out.append(f"COMMANDS {len(cmds)} run, {len(failed)} non-zero exit")
    for c in failed[-8:]:
        tail = short(c["tail"][0], 70) if c["tail"] else ""
        out.append(f"  ✗ {c['exit_code']}: {short(c['command'], 90)}  → {tail}")
    for c in cmds[-6:]:
        out.append(f"  · {c['exit_code']}: {short(c['command'], 110)}")
    files = info["files"]
    kinds = Counter(f["kind"] for f in files)
    fs = meta.get("fs_changes") or {}
    via_edit = {rel(f["path"], ws) for f in files}
    via_shell = sorted(set(fs.get("written", [])) - via_edit)
    uniq = sorted(via_edit | set(via_shell))
    kind_txt = ", ".join(f"{k} {v}" for k, v in kinds.items()) or "none"
    out.append(f"FILES {len(uniq)} touched (edits: {kind_txt}; written by commands: {len(via_shell)})")
    tops = Counter(str(Path(p).parent) for p in uniq).most_common(6)
    if tops:
        out.append("  " + ", ".join(f"{d} ({n})" for d, n in tops))
    if via_shell:
        out.append("  by commands: " + ", ".join(via_shell[:12]) + (" …" if len(via_shell) > 12 else ""))
    dels = sorted({rel(f["path"], ws) for f in files if f["kind"] == "delete"} | set(fs.get("deleted", [])))
    if dels:
        out.append("  deleted: " + ", ".join(dels[:20]))
    if info["searches"]:
        out.append(f"WEB SEARCHES {len(info['searches'])}")
        for s in info["searches"][:12]:
            out.append(f"  - {short(s['query'], 80)}  → {', '.join(s['domains'][:3])}")
    out.append(f"TOKENS {fmt_tokens(info['usage'])}")
    if info["errors"]:
        out.append("ERRORS")
        out += [f"  {e}" for e in info["errors"][-5:]]
    if flags:
        out.append("RED FLAGS (check before accepting)")
        out += [f"  ! {f}" for f in flags]
    out.append(f"saved: {rel(str(tdir), ws)}/")
    summary = {"turn": tdir.name, "thread_id": info["thread_id"], "meta": meta, "report": report,
               "commands": len(cmds), "failed_commands": len(failed), "files": uniq, "deleted": dels,
               "searches": info["searches"], "usage": info["usage"], "errors": info["errors"], "red_flags": flags}
    return "\n".join(out), summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-w", "--workspace", default=".", help="project directory GPT works in (default: .)")
    ap.add_argument("-b", "--brief", help="brief file to send, or - for stdin")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--new", action="store_true", help="start a new GPT thread")
    g.add_argument("--thread", help="resume this thread id (default: the saved one)")
    ap.add_argument("--search", action="store_true", help="give GPT live web search (research turns)")
    ap.add_argument("--network", action="store_true", help="allow network in the workspace-write sandbox (package installs)")
    ap.add_argument("--effort", choices=["minimal", "low", "medium", "high", "xhigh"], help="reasoning effort")
    ap.add_argument("--model", help="model id for Codex")
    ap.add_argument("--sandbox", default="workspace-write", choices=["read-only", "workspace-write", "danger-full-access"])
    ap.add_argument("-i", "--image", action="append", default=[], help="attach an image (repeatable)")
    ap.add_argument("-c", "--config", action="append", default=[], help="extra Codex -c key=value (repeatable)")
    ap.add_argument("--no-schema", action="store_true", help="do not enforce the JSON report")
    ap.add_argument("--no-footer", action="store_true", help="send the brief without the standard report footer")
    ap.add_argument("--timeout", type=int, default=4 * 3600, help="seconds before the turn is stopped (default 4h)")
    ap.add_argument("--codex", help="path to the codex binary")
    ap.add_argument("--digest", metavar="TURN", help="re-print the digest of a saved turn (e.g. 007) and exit")
    a = ap.parse_args()

    ws = Path(a.workspace).resolve()
    state = ws / ".whetstone"
    turns = state / "turns"

    if a.digest:
        tdir = turns / a.digest.zfill(3)
        if not tdir.is_dir():
            print(f"no saved turn {tdir}", file=sys.stderr)
            return 2
        text, _ = digest(tdir, ws, a)
        print(text)
        return 0

    if not a.brief:
        ap.error("--brief is required")
    if not ws.is_dir():
        ap.error(f"workspace not found: {ws}")
    brief = sys.stdin.read() if a.brief == "-" else Path(a.brief).read_text()
    if not brief.strip():
        ap.error("brief is empty")
    if not a.no_footer and not a.no_schema:
        brief = brief.rstrip() + FOOTER

    codex = find_codex(a.codex)
    state.mkdir(exist_ok=True)
    thread = None
    if a.thread:
        thread = a.thread
    elif not a.new and (state / "thread_id").exists():
        thread = (state / "thread_id").read_text().strip() or None

    tdir = next_turn_dir(turns)
    (tdir / "brief.md").write_text(brief)
    cmd = build_cmd(a, codex, ws, tdir, thread)
    deleted_before = git_deleted(ws)
    started = time.time()
    meta = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "thread": thread, "resumed": bool(thread),
            "cmd": [c if c != codex else "codex" for c in cmd]}
    rc = None
    timed_out = False
    with (tdir / "events.jsonl").open("w") as evf, (tdir / "stderr.log").open("w") as errf:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=evf, stderr=errf, cwd=ws, text=True)
        try:
            proc.stdin.write(brief)
            proc.stdin.close()
            rc = proc.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                rc = proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            rc = proc.wait()
    meta.update({"seconds": round(time.time() - started, 1), "returncode": rc, "timed_out": timed_out,
                 "fs_changes": {"written": written_since(ws, started),
                                "deleted": sorted(git_deleted(ws) - deleted_before)}})
    (tdir / "meta.json").write_text(json.dumps(meta, indent=2))

    info = parse_events(tdir / "events.jsonl")
    if info["thread_id"]:
        (state / "thread_id").write_text(info["thread_id"] + "\n")
    text, summary = digest(tdir, ws, a)
    (tdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    report = summary.get("report") or {}
    with (state / "turns.tsv").open("a") as log:
        log.write("\t".join([tdir.name, meta["started"], info["thread_id"] or "", str(rc),
                             str(report.get("status", "")), str(meta["seconds"]),
                             str(info["usage"].get("output_tokens", "")), str(len(summary["red_flags"]))]) + "\n")
    print(text)

    stderr = (tdir / "stderr.log").read_text(errors="replace")
    if timed_out:
        print(f"\nturn stopped after {a.timeout}s; resume with the same thread to continue", file=sys.stderr)
        return 4
    if rc != 0:
        tail = "\n".join(stderr.strip().splitlines()[-6:])
        if LIMIT_RE.search(stderr) or any(LIMIT_RE.search(e) for e in info["errors"]):
            print(f"\nCodex usage limit reached. Note it in the ledger and rerun this command later.\n{tail}", file=sys.stderr)
            return 3
        print(f"\nCodex exited with {rc}:\n{tail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
