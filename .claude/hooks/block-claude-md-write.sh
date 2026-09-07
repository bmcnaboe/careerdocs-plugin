#!/usr/bin/env bash
# PreToolUse hook — block Write/Edit/MultiEdit on CLAUDE.md.
#
# This repo keeps its conventions in AGENTS.md (the cross-tool standard); CLAUDE.md is only an
# `@AGENTS.md` import. The `claude-md-pointer` conformance guard enforces that at gate time;
# this hook stops the write in real time and redirects the agent to AGENTS.md, so it never
# wastes an edit. Reads the PreToolUse JSON on stdin and emits a "deny" decision when the
# target file's basename is CLAUDE.md. Uses node (always present in this repo) — no jq needed.
# shellcheck disable=SC2016  # the node -e program is single-quoted on purpose (no shell expansion)
exec node -e '
  let raw = "";
  process.stdin.on("data", (c) => (raw += c));
  process.stdin.on("end", () => {
    let fp = "";
    try { fp = (JSON.parse(raw).tool_input || {}).file_path || ""; } catch {}
    if (fp.split(/[\\/]/).pop() === "CLAUDE.md") {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason:
            "CLAUDE.md is a pointer to AGENTS.md (its only content is `@AGENTS.md`). " +
            "Edit AGENTS.md instead — this repo keeps its conventions there, and the " +
            "claude-md-pointer conformance check fails the build if CLAUDE.md grows content of its own."
        }
      }));
    }
  });
'
