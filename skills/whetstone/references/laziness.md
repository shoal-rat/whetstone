# Corner-cutting patterns

How long-running GPT agents fall short, how to spot each pattern cheaply, and what to send back. Every pattern here was seen in real long sessions. Most are not "laziness" in a moral sense: the agent optimises for a turn that looks finished. Your checks change what "finished" means.

## Contents
1. Promise ending
2. Silent scope cut
3. Stub dressed as a feature
4. Tests bent to pass
5. Claimed but not checked
6. Building behind closed doors (craft from defaults)
7. Symptom patch
8. Shallow or fake research
9. Permission-seeking stop
10. Glossy reporting
11. Rewrite regression
12. Long-thread drift
13. Over-correction (the opposite failure)

## 1. Promise ending
**Looks like:** the turn ends with "Next I'll…", "I'm now going to…", "currently re-checking…", while the work it describes is not in the diff.
**Spot it:** the digest's summary flag ("describes plans rather than results"); few commands; `status: partial` with no blocker named.
**Send back:** "Do <X> in this turn and report the result. A turn ends when the milestone passes your checks or something only I can decide blocks you."

## 2. Silent scope cut
**Looks like:** "a simplified version", "basic implementation for now", three enemy types where the contract says eight, one level instead of a world, a feature quietly missing from the report.
**Spot it:** compare the acceptance list to the diff and the running build; `lazy_scan.py --since` scope-shrink hits; counts (levels, items, minutes of play, endpoints) against the contract.
**Send back:** restate the scope lock with its reason ("the user judges this by an hour of play; eight enemy types is what keeps that hour varied") and the specific missing items.

## 3. Stub dressed as a feature
**Looks like:** a function that returns a constant or mock data; a button with no handler; a save system that writes but never loads; grey boxes and spheres standing in for art; `TODO` inside a function the report calls done.
**Spot it:** `lazy_scan.py` (stub, placeholder, primitive-art, marker); exercise the feature end to end yourself, not just its unit.
**Send back:** the file:line, what the feature must actually do, and how you will check it.

## 4. Tests bent to pass
**Looks like:** `skip`/`xfail` added, assertions loosened or deleted, expected values edited to match a bug, the unit under test mocked away, test files deleted.
**Spot it:** `lazy_scan.py --since <rev>` (test-skip, hollow-test, deleted tests, removed assertions); `git diff <rev> -- '*test*'`.
**Send back:** "Restore <test>. The test describes the behaviour the user needs; fix the code to meet it." If a test really is wrong, GPT must say why in the report, and you decide.

## 5. Claimed but not checked
**Looks like:** "verified", "works", "tested on all settings", with no output; proof that cites a command which never ran this turn; screenshots taken but never opened, so a black frame passes.
**Spot it:** the digest's red flags (proof cites a command not run, artifact missing, pass with empty proof); open the captures yourself.
**Send back:** "Item A7 has no proof from this turn. Run <command> / capture <shot> and include the result."

## 6. Building behind closed doors (craft from defaults)
**Looks like:** art, levels and characters built from the agent's own head: primitive shapes, flat even lighting, one material everywhere, uniform scattering, sparse worlds, symmetrical faces with dead eyes, hair as a single shell, fire as a flat textured card, splashes that ignore physics. Several rounds of "tweaking" that never change the class of result.
**Real case:** a heroine's 3D face and hair failed review round after round until the user said "go and see how people model this kind of character". After researching specific techniques (hair split into clumps, face shading kept clean from 3/4 view) the result changed class instead of degree. In the same project a world felt empty with 7–13 trees per 100×100 m plot; once GPT looked up a field survey of a real old-growth forest (about 560 stems per hectare) the plots went to 385–478 trees and the world finally read as a forest.
**Spot it:** the research note for the domain is missing or generic; captures fail the rubric in [aesthetics.md](aesthetics.md); two rounds without a class change.
**Send back:** the re-research brief in [briefs.md](briefs.md), with captures, before any further tuning.

## 7. Symptom patch
**Looks like:** clipping hidden by scaling the cloth up; a flaky test given a longer timeout; a crash caught and ignored; a number tuned until the check passes while the cause remains.
**Spot it:** `lazy_scan.py` swallowed-error hits; diffs that change constants or thresholds only; ask for the cause in the report.
**Send back:** "What causes it? Fix the cause, and show the case that used to fail."

## 8. Shallow or fake research
**Looks like:** sources cited with no searches in the event log; listicles and SEO blogs instead of manuals and talks; "best practices" without a single number; techniques never applied; or the opposite, copying someone's model, texture, character or song.
**Spot it:** digest red flag ("cites web sources but made no web searches"); open one cited source; check each technique maps to a code or asset change.
**Send back:** ask for primary sources and numbers, name the kind of source you expect (the engine's manual, a studio talk, an art breakdown), and restate "learn methods, make original work".

## 9. Permission-seeking stop
**Looks like:** "Would you like me to continue?", "Shall I proceed with…?" on work the contract already authorises; the turn ends waiting.
**Spot it:** questions list full of things the contract answers.
**Send back:** answer the questions in one line each from the contract, and "you have the authority for everything in the contract; carry on until the milestone passes."

## 10. Glossy reporting
**Looks like:** vivid adjectives ("lush", "cinematic", "dramatically improved") and no measurements; before/after captures from different cameras or times of day.
**Spot it:** no numbers in the report; captures that don't match.
**Send back:** ask for the measurement that matters (fps, load time, lit:shadow ratio, density per area, item counts) and fixed-camera before/after pairs.

## 11. Rewrite regression
**Looks like:** asked to fix one thing, the agent rewrites a module; the fix lands and three other features break. Common late in long threads.
**Spot it:** `git diff --stat` far larger than the request; rerun the full acceptance list, not only the items in play.
**Send back:** the broken items with proof, and "make the smallest change that fixes <X>; keep <module> as is."

## 12. Long-thread drift
**Looks like:** decisions from fifty turns ago forgotten; removed features reintroduced; naming and style drifting.
**Spot it:** a brief that contradicts the ledger's decisions; repeated old bugs.
**Send back:** quote the relevant decisions from the ledger in the brief. If the thread is very long or full of failed attempts, start a fresh thread (`--new`) with the kickoff brief, the contract, and the decision list.

## 13. Over-correction (the opposite failure)
After hard feedback GPT may swing the other way: it hedges every line, asks questions it could answer, refuses steps it is authorised to take, pads the code with defensive checks, or stops at the first uncertainty. This is as costly as cutting corners.
**Send back:** less pressure, more goal. Restate the goal and its authority, keep only the essential hard rules, and name something it did well.
