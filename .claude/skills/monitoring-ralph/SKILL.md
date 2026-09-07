---
name: monitoring-ralph
description: Monitor a running Ralph autonomous loop (ralph-wiggum-plugin). Checks loop status, watches for stuck states, and reports completion metrics. Invoke manually with an optional worktree fragment (a run slug like `sse-fixes`, or any substring of the worktree path) to identify the target worktree.
disable-model-invocation: true
argument-hint: "[worktree-fragment]"
---

# Ralph Loop Monitor

You are a read-only loop observer. Your job is to watch an autonomous Ralph loop — tracking its progress, flagging problems to the user, and reporting results when it finishes.

**You do not make changes.** Never edit files in the worktree, never modify the task file or run plan, never patch the plugin, never kill or restart the loop. If something looks wrong, tell the user what you see and let them decide what to do.

## Where things live

| What                                                                                      | Path                                                                                     |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Shell functions (`ralph-status`, `wt-ralphlinear`, …)                                     | `scripts/dev/shell-helpers.sh` (sourced into the operator's shell)                       |
| Devbox commands (`devbox-list`, `devbox-ralph-status`) — repos with a devbox surface only | `scripts/dev/remote/devbox-helpers.sh` (sourced by shell-helpers)                        |
| Ralph status script (`ralph-status.sh`), run supervisor (`ralph-supervise.sh`)            | Installed plugin at `~/.claude/plugins/cache/...ralph-wiggum-plugin/.../shared-scripts/` |
| Gate policy                                                                               | `.ralph/command-policy` `[gates]` — the tier commands the run is frozen to               |
| Linear eval templates                                                                     | `scripts/dev/ralph/` (`linear-eval-framing.md`, `linear-ledger-template.md`)             |
| Run plans (a linear run's task checklist)                                                 | `linear-specs/<stamp>-<slug>/plan.md`                                                    |

> **Bash tool caveat:** The Bash tool does not have `shell-helpers.sh` sourced, so `ralph-status [fragment]` is not available as a bare command. Use the direct invocation pattern instead (see below).

## Resolving the target workspace

The user may pass a **worktree fragment** as an argument (e.g., `172552`, `sse-fixes`, `trust-ui`). Use it to locate the worktree — worktrees are named from the branch with `/` → `-` normalization (`linear/sse-fixes` → `…-linear-sse-fixes`):

```bash
# Fragment resolution — matches against git worktree list paths
_resolve_worktree() {
  local frag="${1:-}"
  if [[ -z "$frag" ]]; then
    echo "$PWD"
    return 0
  fi
  local search="${frag//\//-}"
  local matches=()
  while IFS= read -r line; do
    local wt_path="${line%% *}"
    [[ "$wt_path" == *"$frag"* || "$wt_path" == *"$search"* ]] && matches+=("$wt_path")
  done < <(git worktree list 2>/dev/null)
  if (( ${#matches[@]} == 1 )); then
    echo "${matches[0]}"
  elif (( ${#matches[@]} == 0 )); then
    echo ""; return 1
  else
    printf '%s\n' "${matches[@]}"; return 2
  fi
}
```

If no argument is given, use the current working directory. Check for `.ralph/activity.log` at the resolved path to confirm it's a ralph workspace.

## Phase 1: Detect loop state

Check for a running loop in **local tmux**, and — only if this repo has a devbox surface (`scripts/dev/remote/devbox-helpers.sh` exists) — in **devbox**.

### Local (tmux)

Ralph sessions use the naming convention `ralph-${branch//[\/.:]/-}` (e.g. `linear/sse-fixes` → `ralph-linear-sse-fixes`). List them:

```bash
tmux list-sessions 2>/dev/null | grep "^ralph-"
```

Resolution logic:

- **No ralph sessions** → not running locally; check devbox if this repo has one, else see "If not running".
- **Single ralph session, no frag provided** → assume that's the one.
- **Single ralph session, frag provided** → confirm frag matches the session name. If not, move on.
- **Multiple ralph sessions, frag provided** → match frag against session names. If exactly one matches, use it.
- **Multiple ralph sessions, no frag** → ask the user which one to monitor.

Once a session is identified, derive the workspace path from the branch name (worktrees live at sibling paths to the main repo, named with the branch after `/` → `-` normalization). Confirm with:

```bash
pgrep -f "ralph-setup.sh.*$WORKSPACE" || pgrep -f "stream-parser.sh $WORKSPACE" || pgrep -f "ralph-supervise.sh $WORKSPACE"
```

(Runs launched via `wt-ralphlinear` — and, since plugin 0.21.0, Spec Kit runs via `ralph`/`ralph-resume` too — are wrapped by the plugin's `ralph-supervise.sh`, which observes the run's exit, notifies the operator, and may auto-resume once for a mechanically-recoverable halt — so a live supervisor process with no driver can mean a resume is in flight.)

### Devbox (repos with a devbox surface)

If no local tmux session matches and `scripts/dev/remote/devbox-helpers.sh` exists, check for remote devbox instances:

```bash
devbox-list 2>/dev/null
```

This outputs columns: `NAME  BRANCH  STATUS  ENDPOINT`. Devbox names use a different convention than tmux sessions — they're prefixed with the repository directory name (not `ralph-`) plus the branch slug lowercased: `<repo>-feat-172552`.

Resolution logic (same shape as tmux, different naming):

- **No devboxes** → not running anywhere. See "If not running".
- **Single devbox, no frag** → assume that's the one.
- **Single devbox, frag provided** → match frag as substring of NAME or BRANCH columns. If no match, not running.
- **Multiple devboxes, frag provided** → substring match against NAME or BRANCH. Exactly one match → use it.
- **Multiple devboxes, no frag** → ask the user which one.

For devbox instances, use `devbox-ralph-status [fragment]` to get status.

### If not running

Before declaring a loop dead, tail the last lines of `activity.log` for `🔔 SUPERVISOR:` breadcrumbs — the supervisor logs every terminal outcome (complete, stopped, guttered, resumed) and its verdict tells you whether the run finished or halted.

Then tell the user the loop isn't running and give them the command to start it:

- Spec run, new worktree: `wt-ralphspec feat/[fragment]` (or `devbox-ralphspec feat/[fragment]` where a devbox surface exists)
- Linear run, new: `/linear-plan` writes the plan, then `wt-ralphlinear linear/<slug>` launches it
- Existing worktree: `ralph-resume` (auto-detects a linear plan from the `.ralph/task-file-path` breadcrumb; `ralph-resume <plan>` forces one)
- Verify phase only: `ralph-linear-verify`

Wait for them to confirm it's running before entering Phase 2.

## Phase 2: Active monitoring

Once a running loop is confirmed, enter a monitoring cycle using `ScheduleWakeup`. The goal is to surface meaningful events — task commits, gate results, stuck patterns — without generating noise between them.

### Primary signal: ralph-status.sh

Every cycle, run `ralph-status.sh` to get structured facts. This is your **only required tool call per cycle**:

```bash
WORKSPACE=/path/to/worktree
RALPH_STATUS_SH=$(find ~/.claude/plugins/cache -path "*/ralph-wiggum-plugin/*/shared-scripts/ralph-status.sh" | sort -V | tail -1)
bash "$RALPH_STATUS_SH" "$WORKSPACE"
```

Use its output to populate every field in the cycle report: task count, tokens, driver state, gate history, git tip. If `ralph-status.sh` cannot be found, fall back to tailing `activity.log` for all fields and note the fallback.

**Do not tail `activity.log` every cycle.** It emits a high volume of low-signal entries (TOKENS heartbeats, READ calls, SHELL invocations) that create the illusion of activity even when nothing meaningful has changed. Reading it every cycle generates excessive check-ins and wastes context.

### When to read activity.log

Tail `activity.log` (last ~40 lines) only when ralph-status reveals something worth investigating:

- A gate just failed — read to get the error detail and gate log path
- The driver stopped unexpectedly — read to find the last known state (and any `SUPERVISOR:` breadcrumb)
- The task counter hasn't advanced for 4+ consecutive cycles — read to assess whether the loop is truly stuck or just on a long task
- A `GUTTER` or `HEARTBEAT TIMEOUT` appears in ralph-status's recent events — read for context
- Generating the completion report — read the full log then

### Adaptive wakeup intervals

Base your `ScheduleWakeup` delay on what ralph-status shows, not on log chatter:

| ralph-status signal                       | Delay                                                      |
| ----------------------------------------- | ---------------------------------------------------------- |
| Gate currently running                    | `gate_start_time + expected_duration + 60s` (minimum 120s) |
| Task count just increased (new commit)    | 240s — let the next task's exploration settle              |
| Same task, no gate running, tokens < 70%  | 270s — mid-task generation, nothing to see                 |
| Same task, no gate running, tokens 70–85% | 180s — approaching rotation                                |
| Same task, tokens > 85%                   | 120s — imminent rotation                                   |
| Same task, 4+ "no progress" cycles        | Flag to user, then 180s                                    |
| Driver not running                        | Report immediately, stop scheduling                        |

For a running gate, estimate `expected_duration` from the most recent `duration=Ns` entries in ralph-status's gate history — gate runtimes are project- and tier-specific (seconds for lint-only tiers, many minutes for tiers that run integration/e2e or enforce a strict coverage bar), and the first gate in a fresh worktree runs cold (dependency install + cold build caches) and takes noticeably longer than warm ones. Schedule past the estimate rather than polling while it runs.

### Reporting each cycle

Print a subtle horizontal rule (`---`) before each update.

Only report when ralph-status shows something worth saying. If the task count is unchanged, no gate has completed or failed, and tokens are in the expected range for the current wakeup interval, a one-liner is fine. Save the full structured report for meaningful events: a new task commit, a gate result, a stuck flag, or approaching rotation.

**Full structured report** (use when something changed):

```
---

**Cycle check — HH:MM**

[One-line status: what changed since last check, e.g. "T005 committed", "full gate failed", "rotation imminent"]

Tasks: XX/YY ([completed TXXX at HH:MM | unchanged since TXXX at HH:MM])
Tokens: XX,XXX / XXX,XXX (XX%)
Gate in progress: [label @ HH:MM | none]
Prior gate: [label exit=N, Xs @ HH:MM | none]
[Flagging note — only if something warrants it]
```

**Short check-in** (use when nothing changed):

```
---
Cycle check — HH:MM — no change. T00X in progress, tokens XX% ([X/Y] tasks). Next check in Xs.
```

The short form is appropriate whenever: same task as last check, no new gate result, tokens within expected range for current wakeup. Reserve the full format for when there's actually something to report.

Key signals from ralph-status:

| Signal                                         | Meaning                            |
| ---------------------------------------------- | ---------------------------------- |
| `driver: ● RUNNING`                            | Loop is alive                      |
| `driver: ○ not running`                        | Loop crashed or completed          |
| Task count increased                           | New commit — loop progressing      |
| Same task for 4+ cycles                        | Possibly stuck — read activity.log |
| Gate failures in recent history                | Loop may be spinning               |
| `NATURAL END` or `RALPH STOP` in recent events | Loop completed                     |
| Token usage >85%                               | Imminent context rotation          |

### Tracking progress between checks

Keep a mental model of:

- Task count and git tip from the previous cycle
- Gate history changes (new pass or fail since last check)
- How many consecutive "no progress" cycles have elapsed
- Number of loop rotations observed

A cycle is "no progress" when the task count, git tip, and gate history are all identical to the previous check. Four consecutive no-progress cycles on the same task warrants reading `activity.log` to assess whether the loop is stuck.

## Phase 3: Stuck detection (observe and report only)

A loop may be **stuck** when it has made no meaningful progress across multiple checks despite the driver still running. Symptoms:

- Same current task for 4+ consecutive checks (~10-15 minutes)
- Gate failures repeating with the same exit pattern
- No new commits despite active processing
- `HEARTBEAT TIMEOUT` or `RECOVER_ATTEMPT` in recent events
- The handoff note is unchanged across rotations

**Do not intervene.** When you observe stuck symptoms, report what you see to the user with enough detail for them to act — the current task, how long it's been stuck, relevant gate log paths, and what the handoff says. Then continue monitoring unless the user tells you to stop.

Note that loops often self-correct via their own gutter detection and context rotation. A single check showing no progress is not stuck — wait for a pattern across multiple checks before flagging it. And when the repo's gate enforces a strict coverage bar, a task can legitimately spend several gate rounds closing coverage before it commits — repeated fails with _shrinking_ uncovered counts is progress, not spinning.

## Phase 4: Completion report

When the work loop finishes (`LOOP N END — ✅ COMPLETE` in the activity log), **do not generate the report yet**. A follow-on phase often starts within 1–3 minutes of the final work loop ending:

- **Linear runs** (`wt-ralphlinear`): the **verify phase** is chained automatically — the `linear-verify-loop` orchestrator runs linear-accept per verify group, rework for needs-work tickets, and gate-fix for a red final gate. Its working state is the ticket ledger at `.ralph/acceptance-report.md`.
- **Spec Kit runs**: the **eval phase** is a single-task loop (`All acceptance criteria met and verified`).

**Follow-on phase detection (same rules for both):**

- Look for a new `LOOP 1 START` after the work loop's `SESSION END` — that signals the follow-on phase has begun.
- If the log shows `SESSION END` but no new `LOOP 1 START`, schedule a check in 90s and look again. Do this at least twice (i.e., wait up to ~3 minutes) before concluding no follow-on phase is coming.
- Do **not** declare the session complete and begin the final report until either: (a) the follow-on phase has concluded, or (b) at least 3 minutes have elapsed since the final loop's `SESSION END` with no new start entry — and check for a `SUPERVISOR:` breadcrumb, since the supervisor may auto-resume a mechanically-halted run once.

Once the follow-on phase starts, wait for its `SESSION END` or `COMPLETE` signal before generating the report.

Generate the report only after reading the full activity log directly — not from memory of prior checks.

### Metrics to extract from activity.log

Parse the log to compute:

- **Total tasks**: count of checkbox items in the task file (for linear runs, the run plan at `linear-specs/<stamp>-<slug>/plan.md`)
- **Tasks completed**: count of `[x]` checkboxes
- **Total loops (context rotations)**: count of `LOOP N START` markers
- **Average tasks per loop**: completed_tasks / total_loops
- **Average time per task**: first timestamp to last timestamp before the follow-on phase / total_tasks
- **Gate runs**: total count, pass count, fail count, pass rate
- **Average gate duration**: parse `duration=Ns` from gate end events
- **Total wall-clock time**: first timestamp to last timestamp in activity.log
- **Token usage**: last `TOKENS:` line shows final consumption
- **Gutter events**: count of `GUTTER` lines (self-detected stuck states)
- **Verify/eval phase**: did it run? If so, how many loops — and for linear runs, the per-ticket verdicts from `.ralph/acceptance-report.md`: the pinned passed state, needs-work → reworked (how many rework cycles; cap is 2 per ticket), or terminal FAILED/UNSURE
- **Supervisor events**: any `SUPERVISOR:` breadcrumbs (notify-only vs auto-resume)

### Report format

```
## Ralph Loop Report: [branch-name]

**Outcome**: [completed all tasks | completed N/M tasks | stopped — reason]
**Duration**: [wall clock time]
**Loops**: [N context rotations]

### Progress
- Tasks: [done]/[total] ([pct]%)
- Avg tasks/loop: [N]
- Avg time/task: [N]
- Commits: [count from git log on that branch]

### Quality Gates
- Runs: [total] ([pass] pass, [fail] fail) — [pass_rate]% pass rate
- Avg duration: [N]s
- Gutter detections: [N]

### Token Efficiency
- Final usage: [tokens used] / [tokens available] ([pct]%)
- Avg context at rotation: [estimate from TOKENS lines before each LOOP START]

### Verify / Eval Phase
- [Ran / Did not run]
- [If ran: loops, outcome — for linear runs the per-ticket verdicts (KEY-N → passed | needs-work ×N → … | FAILED | UNSURE) and rework cycles used]

### Notes
[Any observations about patterns — e.g., "loop got stuck on T005 for 3 rotations before self-correcting via gutter", "gate pass rate dropped in final tasks suggesting increasing complexity", "supervisor auto-resumed once after a concurrent-writer halt"]
```

## Hard rules

- **Read-only.** Never edit files, modify task lists or plan checklists or the ticket ledger, patch plugins, kill processes, or restart loops unless expressly directed by the user to do so. You observe and report.
- **No speculation.** Only report facts visible in tool output. Do not infer intent, explain behavior, or describe what the loop is "trying to do" unless the log entry makes it explicit.
- **Hard math only.** All numbers (token counts, percentages, durations, gate counts, task counts, wall-clock times) must come directly from tool output — parse the actual values, do not estimate or round loosely. If you cannot compute an exact figure, say so rather than approximating.
- **ralph-status.sh is your pulse.** Run it every cycle. Derive all cycle report fields from its structured output. Do not tail `activity.log` every cycle — the high-frequency log entries (TOKENS heartbeats, READs, SHELLs) are noise, not signal, and checking them on every wakeup generates excessive, low-value updates.
- **activity.log is on-demand.** Read it only when ralph-status reveals a gate failure, unexpected driver stop, multi-cycle stuck pattern, or gutter event — and always when generating the completion report. Read the full log for the completion report; tail the last ~40 lines for diagnostics.
- **Trust the loop.** Ralph has its own gutter detection and context rotation, and supervised runs additionally have the supervisor watching for terminal halts. Most apparent "stuck" states resolve within 1-2 rotations. Flag to the user only when the pattern persists across 4+ consecutive no-progress cycles.
