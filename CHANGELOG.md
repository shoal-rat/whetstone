# Changelog

## 1.0.0 (2026-11-24)

First release.

- `SKILL.md`: the supervision loop (contract, research first, milestones, build turn, verify, aesthetic review, fix brief, final acceptance), roles, how to write to GPT, escalation and budget.
- References: briefs, 13 corner-cutting patterns, research sources for 10 craft and engineering domains, aesthetic rubrics.
- `setup.py`: prepares a workspace and installs an `AGENTS.md` block with build agreements and fishtrap's principles (left out when fishtrap is already installed globally).
- `gpt_turn.py`: runs one Codex turn (new or resumed, sandbox kept on resume, optional live web search), enforces a JSON report, and prints a digest with red flags, including files written by shell commands and deleted tests.
- `lazy_scan.py`: scans a tree or a diff for stubs, placeholders, skipped or hollow tests, swallowed errors and scope-shrinking phrases.
- `look.py`: contact sheets (colour, value, squint, thumbnail) and image statistics, with before/after, reference and lit-to-shadow patch ratios.
- Claude Code plugin and marketplace manifests.
