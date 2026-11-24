# Briefs to send GPT

Each brief is a file you pass to `gpt_turn.py --brief`. The script appends a short footer asking for the JSON report, so the brief itself can stay about the work. Fill in the angle brackets; delete lines that don't apply.

## Contents
- How to write to GPT
- Kickoff (first turn of a project)
- Research brief
- Milestone brief
- Fix brief (after your review)
- Re-research brief (craft gap that effort alone won't close)
- Final acceptance brief

## How to write to GPT

What tends to work with GPT-family agents in Codex:

- **Goal first, then who judges it, then the reason for each requirement.** GPT applies a rule far more sensibly when it knows why the rule exists.
- **A named bar.** "Lighting comparable to a modern stylized open world, lit:shadow about 3:1 in daylight" beats "make it look good".
- **Ownership and specific encouragement.** "You own the terrain system. The river banks in turn 12 are the best work so far: the wet edge and the reeds read at flight height. Bring the lake shore up to that." Specific praise tells it what to repeat.
- **Evidence requests.** "Prove each item with the command and its result or a capture path."
- **A few literal hard rules** (scope lock, safety, licences), stated once with their reasons.

What tends to backfire:

- Long stacks of MUST / NEVER / CRITICAL. GPT turns defensive: it hedges, adds disclaimers, refuses borderline steps, and asks permission it already has.
- Audit or threat framing ("I will check everything you do", "you were lazy"). It answers with caution, not quality. Name the gap and the target instead.
- Vague taste words with no target ("more polished", "prettier", "more epic").
- Asking for a plan when you want work. Ask for the work and a report.

## Kickoff (first turn of a project)

```markdown
You are the lead builder on <project>. I'm Claude, the director and reviewer: the user gave us the goal
below, I keep the contract and review each milestone for completeness and look. You own the craft and the code.

## Goal
<one sentence> Judged by: <who>.

## The contract
Read `.whetstone/CONTRACT.md` in full. It is the definition of done: acceptance items, the quality bar,
the scope lock and the craft domains that need research first.

## How we work
- Build the real thing at the contract's quality bar. When something is hard, that is the part worth doing;
  if it truly cannot be done in this environment, say what blocks it and move to the next most valuable item.
- Before craft work (characters, faces, hair, 3D models, materials, lighting, level design, VFX, animation,
  UI, audio), study how the best practitioners do it: official manuals, studio talks, art breakdowns,
  canonical books. Keep what you learn, with sources and numbers, in `.whetstone/research/<domain>.md`.
  Learn methods; don't copy others' assets, characters or music.
- Prove each acceptance item with a command and its output, a test, or a capture.
- Keep working inside a turn until the milestone passes your own checks.
- Settle questions from the contract when you can. Put the rest in the report and carry on with other items.

## This turn
Propose the milestone plan in `.whetstone/PLAN.md`: 5–12 milestones ordered by risk (core loop first,
art pipeline early), each ending in something demonstrable and listing the acceptance items it closes.
Then set up the project skeleton so it builds and runs, and prove it with the command.
```

## Research brief

Run with `--search`. One domain per brief when the domain is big (characters, lighting); several small ones may share a brief.

```markdown
## Research: <domain> for <project>
Why: <what in the contract depends on it, e.g. "the heroine's face and hair are the first thing players see;
the current model reads as a plastic helmet">.

Study how the best people do this before building it. Search the web and open the sources:
official manuals and docs, GDC / CEDEC / SIGGRAPH talks, studio postmortems and art breakdowns, canonical
books, respected educators. Prefer primary sources and specific techniques over listicles.

Write `.whetstone/research/<domain>.md` with:
1. Sources: title, author or studio, URL, and why it is authoritative (5–10 good ones beat 30 weak ones).
2. Techniques: each as a rule you could implement here, with its numbers (proportions, densities, ratios,
   timings, budgets) and which source it came from.
3. Application: how each technique maps onto this codebase and pipeline, and which acceptance items it serves.
4. A small proof: apply the single most important technique now and capture before/after.

Questions to answer specifically: <list 2–5, e.g. "how do anime-style 3D faces stay attractive from 3/4 view?",
"how are hair clumps built and shaded so they don't read as one shell?">
```

## Milestone brief

```markdown
## Milestone <M#>: <name>
Goal: <what this milestone makes possible and for whom>.
Acceptance items: <A3, A7, A12 with their text, copied from the contract>.
Bar: <the relevant part of the quality bar, plus numbers from research where they exist>.
Apply: `.whetstone/research/<domain>.md` sections <…>.
Keep: <things that already work and must keep working, decisions from the ledger>.
Scope lock for this milestone: <the parts most likely to be cut, named explicitly, with the reason>.
Evidence I need: <commands to run, captures to take (camera, resolution, time of day), clips>.
Last turn's best work: <one specific thing and why it works>. Bring <area> up to that level.
```

## Fix brief (after your review)

```markdown
## Review of turn <NNN>: <milestone>
Verdict: <n> of <m> items pass. <one sentence on overall state>.

What's working (keep it): <specific, with why>.

Failures (fix first):
1. <A#>: <what I observed, where, how I checked>. Expected: <…>. Likely cause: <if known>.
2. …

Look and quality (ranked by impact; captures attached):
1. <Area>: <observation> → <principle it breaks> → target: <measurable> → study/try: <technique, source>.
2. …
3. …

Re-shoot for before/after: <cameras, settings>. Prove each fix with the same capture.
```

Attach your captures and contact sheets with `--image`. Keep the list to what matters most this round; a 30-item list gets a shallow pass over everything.

## Re-research brief (craft gap that effort alone won't close)

Use when the same visual gap survives two rounds. Run with `--search` and attach captures.

```markdown
## Back to the sources: <specific technique>
Two rounds of tuning haven't closed this gap: <observation, with captures attached>. This is a knowledge gap,
not an effort gap, so let's learn how it's done before touching it again.
Find how <studios/artists> solve <the specific problem> (search for talks, breakdowns, manual pages).
Add what you learn to `.whetstone/research/<domain>.md`, then rebuild <the piece> using it and capture
before/after from the same camera.
```

## Final acceptance brief

```markdown
## Final acceptance
From a clean state (fresh clone or `git clean -xdf` on a copy), build and run everything. Walk every acceptance
item in `.whetstone/CONTRACT.md` and prove each one. Update README/run instructions so a stranger can run it.
List anything still short of the bar plainly: I'd rather report a known gap than discover it later.
```
