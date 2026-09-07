#!/usr/bin/env bash
# PreToolUse hook — deny Write/Edit/MultiEdit on files synced from agent-layer.
#
# Synced files are layer-owned: byte-identical in every subscribed repo, updated only
# by `layer sync-project`. Editing the copy here would drift this repo from the layer
# (and fail the vendored agent-layer check in CI), so this hook stops the write in
# real time and points the agent at the canonical path in ~/development/agent-layer.
# Reads the PreToolUse JSON on stdin; consults .agent-layer.json at the project root.
# Fails open: a missing/unparsable record must never block normal work — CI still
# catches real drift. Uses node (present in these repos) — no jq needed.
# shellcheck disable=SC2016  # the node -e program is single-quoted on purpose (no shell expansion)
exec node -e '
  const fs = require("fs");
  const path = require("path");
  let raw = "";
  process.stdin.on("data", (c) => (raw += c));
  process.stdin.on("end", () => {
    try {
      const fp = (JSON.parse(raw).tool_input || {}).file_path || "";
      const root = process.env.CLAUDE_PROJECT_DIR || process.cwd();
      if (!fp) return;
      const rel = path.relative(root, path.resolve(root, fp));
      if (rel.startsWith("..")) return; // outside this project
      const record = JSON.parse(fs.readFileSync(path.join(root, ".agent-layer.json"), "utf8"));
      const hit = (record.files || []).find((f) => f.mode === "synced" && f.path === rel);
      if (!hit) return;
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason:
            rel + " is synced from agent-layer (module \"" + hit.module + "\") and is " +
            "layer-owned — local edits drift this repo and fail the agent-layer CI check. " +
            "Edit the canonical file instead: ~/development/agent-layer/" + hit.source +
            " — then run `layer sync-project` here to fan the change out.",
        },
      }));
    } catch { /* fail open */ }
  });
'
