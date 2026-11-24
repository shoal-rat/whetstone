---
name: whetstone
description: Claude directs and reviews while a GPT agent (OpenAI Codex CLI) does the building, for very long tasks such as "make a whole game from one sentence", a large app, or a complex system. Claude writes the contract, makes GPT study top tutorials and design docs before any craft work (maps, faces, hair, 3D models, lighting, VFX, UI, animation), checks every claim against evidence, catches corner-cutting, and gives GPT concrete aesthetic direction. Use whenever the user wants Claude to supervise, drive, pair with, or review Codex/GPT, hand a long build to GPT, stop GPT from slacking off or "building behind closed doors", or get Claude's taste applied to GPT's output, even if they don't name this skill.
---

# Whetstone

> *Fungar vice cotis, acutum reddere quae ferrum valet, exsors ipsa secandi.*
> "I'll play the whetstone, which makes steel sharp though it does not cut." (Horace, *Ars Poetica*)

GPT holds the keyboard. You hold the bar. GPT in Codex is fast, tireless at typing, and good at code, but on long tasks it drifts in predictable ways: it shrinks the scope, leaves stubs, reports work it has not checked, ends turns with plans instead of results, and builds art and level design from defaults instead of from how the best people in the field do it. Your job is the part it skips: deciding what "done" means, checking the evidence, and judging whether the result is beautiful and complete.

## Roles

**GPT builds.** It writes the code and assets, runs the builds, tests and captures. It does the heavy reading of the codebase. Every fix goes back to GPT with a brief.

**Claude directs.** You own the contract, the milestone plan, verification, the aesthetic verdict, and the decision that something is done. You do not quietly patch GPT's work. If you fix things yourself, GPT never sees the bar and the next milestone regresses to its old level, and your own context fills with code you did not need to read. Two exceptions: small verification scripts of your own, and the escalation step below.

**The user** sets the goal and reserves some calls: taste decisions they named, credentials, payments, anything outward-facing (publishing, pushing, posting). Everything else you settle from the contract, including the questions GPT asks.

## Setup

`SKILL_DIR` below means the folder that holds this SKILL.md. The scripts need Python 3.9+ and the Codex CLI; only `look.py` needs a package (Pillow).

1. Pick the workspace. A git repo is best: diffs are your cheapest evidence. Codex must already be logged in; never handle the user's credentials.
2. Run `python3 SKILL_DIR/scripts/setup.py DIR`. It finds the Codex CLI, creates `.whetstone/` with the contract and ledger templates, adds `.whetstone/` to `.gitignore`, and installs a marked block at the top of the workspace's `AGENTS.md`.
3. The ledger (`.whetstone/LEDGER.md`) is how a long task survives your context limits and usage limits: after any interruption, read `CONTRACT.md` and the ledger, then continue GPT's saved thread.

**The AGENTS.md block is GPT's half of the arrangement.** Codex reads it at the start of every session, so it holds across fresh threads and restarts without you repeating it in briefs. It tells GPT that a supervisor holds the contract, sets the build agreements (full scope, research before craft, evidence from this turn, keep going until the milestone passes), and carries the goal-and-writing principles from [fishtrap](https://github.com/shoal-rat/fishtrap): work out who will judge the result and hold every instruction against that outcome, apply each rule as far as its reason reaches, carry the task through instead of asking, and report plainly without hedging. In fishtrap's evaluation (240 Codex runs on job-application tasks) those principles raised the share of runs that met every check from 63% to 85%, without making GPT more timid. If the user's global Codex `AGENTS.md` already has fishtrap, setup leaves the principles out of the project block so GPT does not read them twice. Read the block: [templates/AGENTS.whetstone.md](templates/AGENTS.whetstone.md). When the task ends, `setup.py DIR --remove` takes the block out unless the user wants it kept.

All GPT turns go through [scripts/gpt_turn.py](scripts/gpt_turn.py), which runs `codex exec`, keeps the thread id, saves every turn under `.whetstone/turns/NNN/`, and prints a compact digest (final report, commands with exit codes, files changed, web searches, tokens). Read the digest, not the raw event log.

```bash
python3 SKILL_DIR/scripts/gpt_turn.py --workspace DIR --brief kickoff.md --new           # first turn, new thread
python3 SKILL_DIR/scripts/gpt_turn.py --workspace DIR --brief research.md --search       # research turn with live web search
python3 SKILL_DIR/scripts/gpt_turn.py --workspace DIR --brief fix.md --image shot.png    # continue the thread, captures attached
python3 SKILL_DIR/scripts/gpt_turn.py --workspace DIR --digest 007                       # re-read a saved turn's digest
```

Turns run in Codex's `workspace-write` sandbox; add `--network` when GPT must install packages, and `--effort` to set reasoning effort for a turn. Turns can run for an hour or more: run them in the background and wait for completion instead of polling. Exit code 3 means a usage limit: note it in the ledger and resume later with the same command. The digest also lists files written by shell commands and any files deleted, so GPT cannot slip a change past it by writing through `cat > file`.

## The loop

### 1. Contract

Before GPT writes anything, write `.whetstone/CONTRACT.md` from [templates/CONTRACT.md](templates/CONTRACT.md). Long tasks are won or lost here. A one-sentence request ("make a witch game where you fly on a broom") hides a hundred expectations, and GPT will satisfy the sentence, not the expectations. Expand it into what the person will actually judge:

- **Outcome** in one sentence, and **who judges it** (a player, a customer, a reviewer, the user).
- **Acceptance items**: each one observable and paired with how it will be checked ("A new player reaches the first boss in 10–15 min; checked by a scripted playthrough plus a timed manual run"). Aim for 15–40 items on a big task.
- **Quality bar**: named reference works or a level ("lighting and foliage density comparable to a modern stylized open-world game; not low-poly flat colour"). Taste words alone ("polished", "beautiful") are not a bar.
- **Scope lock**: what GPT may not shrink, simplify, or swap for a placeholder. Name the things it is most likely to cut: content volume, playtime, art fidelity, error handling, the hard feature.
- **Craft domains** that need research first (see step 2).
- Constraints and non-goals: platform, licences, budget, what the user said not to do.

Show the user the contract only if they asked to approve plans; otherwise proceed and mention it in your report.

### 2. Research first ("take the highest as your model")

An old Chinese saying: aim at the best and you reach the middle; aim at the middle and you reach the bottom. For every craft domain in the contract, GPT studies how the best practitioners do it **before** building, then writes `.whetstone/research/<domain>.md`. Craft domains include characters, faces and hair; 3D modelling and sculpting; materials and shaders; lighting and colour grading; level and map design; environment density and foliage; VFX and particles; animation and game feel; UI and typography; music and sound. Engineering domains with established practice (netcode, physics, rendering pipelines, compilers, databases) count too.

Send the research brief from [references/briefs.md](references/briefs.md) with `--search` so GPT has live web search. Each research note must contain: the sources (official manuals, GDC/CEDEC/SIGGRAPH talks, studio postmortems and art breakdowns, canonical books, respected educators), the concrete techniques taken from each, the **numbers** (proportions, densities, ratios, timings, budgets), and how each applies to this project.

Check it before accepting it:
- The digest's web-search list shows the searches really happened and the cited pages were opened. Spot-check one source yourself.
- Techniques are specific enough to act on. "Use good lighting" fails. "Key light from 30–45° above the horizon, sky fill at about a third of the key, rim light on characters" passes.
- Methods are learned, not assets copied. No ripped models, textures, characters, logos or music; the user's private references stay private.

Where to look, per domain: [references/research-first.md](references/research-first.md).

### 3. Milestones

Have GPT propose a milestone plan against the contract; then edit it yourself. Order by risk: the core loop first, and the art pipeline early, because art is where GPT is weakest and where late surprises cost most. Each milestone ends in something demonstrable (a build, a capture, a passing test set) and lists the acceptance items it closes. Record the plan in the ledger.

### 4. Build turn

Send one milestone per turn using the milestone brief in [references/briefs.md](references/briefs.md). How you write to GPT matters as much as what you ask:

- **Goal and reason first.** Say what the milestone is for and who will judge it; give the reason behind each requirement so GPT applies it as far as the reason reaches and no further.
- **High bar, ownership, encouragement.** "You own this milestone; here is the bar; I've seen you do this well in X." Name the best thing in its last turn and why it works, so it repeats it. Praise that is specific works; generic praise is noise.
- **Few hard rules, stated literally.** GPT turns defensive and hedging under long lists of MUST/NEVER and audit-style threats. Keep the scope lock and safety constraints literal and short; frame everything else as the goal.
- **Ask for evidence, not reassurance.** The turn ends with the structured report (gpt_turn.py enforces a schema): acceptance items touched, the command or capture proving each, and an honest shortfall list.
- **Keep going inside the turn.** Tell GPT to continue until the milestone passes its own checks. A turn that ends with "Next I will…" has not done the work.

### 5. Verify

GPT's report is a claim, not evidence. Check independently, cheapest first:

1. Read the digest: did the commands it cites actually run, with exit code 0? Were the files it describes actually changed?
2. `git diff --stat` for the turn; skim diffs only where the report and the stat disagree.
3. `python3 SKILL_DIR/scripts/lazy_scan.py DIR --since <rev>` for stubs, placeholders, skipped or weakened tests, swallowed errors and scope-shrinking phrases in the lines this turn added.
4. Run the build and tests yourself (or have GPT run them in the next turn while you read the output).
5. For anything visual or interactive: capture it yourself at the size and distance the user will see it, from a fixed camera you can repeat. Run `scripts/look.py` on the captures (step 6).
6. Tick each acceptance item in the ledger as pass / fail / unverified, with the proof.

The catalogue of corner-cutting patterns, with how to spot each and what to send back: [references/laziness.md](references/laziness.md). The ones seen most in long sessions: promise endings, silent scope cuts, stubs dressed as features, tests bent to pass, "verified" with no output, and craft built from defaults.

### 6. Aesthetic review

This is where you add the most. GPT can generate endlessly but rarely judges its own output against a bar. Look at real captures, never at GPT's description of them. Then:

- **Diagnose in order of impact**: lighting and values → colour → shape and silhouette → density and composition → materials → fine detail → motion. Lighting fixes rescue mediocre assets; detail never rescues bad lighting.
- **Use numbers where you can.** `python3 SKILL_DIR/scripts/look.py shot.png --ref ref.png -o sheet.png` makes a contact sheet (colour, value, squint, thumbnail) and reports luminance spread, contrast, clipping, saturation and edge density; `--patch lit=x,y,w,h --patch shadow=x,y,w,h` measures a light-to-shadow ratio. Feedback such as "the lit:shadow ratio on the gate is 1.7:1; take it to about 3:1" gets fixed. "The lighting feels flat" gets a cosmetic tweak.
- **Write feedback GPT can act on**: (1) what works and why, (2) the top three gaps ranked by visual impact, each as *observation → the principle it breaks → a measurable target → a technique or reference to study*, (3) the capture conditions to re-shoot for the before/after.
- When the gap is about craft knowledge rather than effort (faces, hair, foliage, VFX), send GPT back to research that specific technique before it tries again.

Rubrics for scenes, characters, UI and motion, plus the feedback template: [references/aesthetics.md](references/aesthetics.md).

### 7. Fix brief and repeat

Send findings with the fix brief: failures first, then aesthetic direction, then what to keep. Attach your captures with `--image` so GPT sees what you saw. Log the turn in the ledger. Repeat steps 4–7 until every acceptance item passes with evidence and the result meets the quality bar.

### 8. Final acceptance

From a clean checkout (or a fresh clone), build and run everything once more yourself. Walk the full acceptance list with proof. Report to the user plainly: what is done, what still falls short of the bar, and anything that needs their decision. Do not round up.

## Escalation

When the same acceptance item fails three rounds in a row, change the approach rather than repeating the request:
1. Split it into smaller items with their own checks.
2. Send GPT back to research that one technique, with your captures attached.
3. Give a worked example: a reference image, a tiny exemplar, or the exact numbers to hit.
4. Raise GPT's reasoning effort for that turn (`--effort xhigh`) or start a fresh thread with a clean brief if the old thread is full of failed attempts.
5. Only then write the piece yourself, and tell GPT what you changed and why, so the next milestone builds on it.

## Budget

Let GPT do the reading and writing; keep your own context for judgment. Read the digest, `git diff --stat`, scan output and captures, and open source files only where they disagree. Keep briefs short and specific: exact paths, the acceptance items in play, the numbers to hit. Keep the ledger current after every turn so any interruption costs one turn at most.

## Files

- [templates/CONTRACT.md](templates/CONTRACT.md), [templates/LEDGER.md](templates/LEDGER.md): copied into `.whetstone/` by setup.
- [templates/AGENTS.whetstone.md](templates/AGENTS.whetstone.md): the block GPT reads every session (supervisor arrangement, build agreements, fishtrap principles).
- [scripts/setup.py](scripts/setup.py): prepare a workspace, check it, or remove the block afterwards.
- [references/briefs.md](references/briefs.md): kickoff, research, milestone, fix and final briefs to send GPT.
- [references/laziness.md](references/laziness.md): corner-cutting patterns, detection, responses.
- [references/research-first.md](references/research-first.md): where the best sources live per domain, and how to check research.
- [references/aesthetics.md](references/aesthetics.md): review method, rubrics, feedback template.
- [scripts/gpt_turn.py](scripts/gpt_turn.py): run one Codex turn and digest it.
- [scripts/lazy_scan.py](scripts/lazy_scan.py): scan a tree or a diff for corner-cutting.
- [scripts/look.py](scripts/look.py): contact sheet and image statistics for aesthetic review (needs Pillow).
- [scripts/report.schema.json](scripts/report.schema.json): the report shape GPT must return each turn.
