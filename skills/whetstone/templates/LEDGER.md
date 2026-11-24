# Ledger: <project name>

The supervisor's running record. After any interruption, read CONTRACT.md and this file, then resume GPT's thread (`.whetstone/thread_id`). Update it after every turn.

## Now
- Milestone: <M#> <name>
- Acceptance: <n>/<total> pass
- Waiting on: <GPT turn NNN running | my review | the user: …>

## Milestones
| id | goal | closes items | state |
|---|---|---|---|
| M1 | <…> | A1, A2 | planned / in progress / accepted |

## Acceptance status
| id | state | proof | turn |
|---|---|---|---|
| A1 | pass / fail / unverified | <command and result, capture path> | 004 |

## Decisions (quote the relevant ones in briefs)
- <date> <decision>: <reason> (from: user / supervisor)

## Turn log
| turn | milestone | GPT says | red flags | my verdict | next |
|---|---|---|---|---|---|
| 001 | kickoff | <status> | <n> | <accepted / sent back: why> | <…> |

## Research notes
| domain | file | accepted? | what changed because of it |
|---|---|---|---|

## Escalations
- <item>: failed <n> rounds; approach changed to <…>

## For the user
- <decisions only they can make, outward actions waiting for their go-ahead, honest gaps>
