---
name: "speckit-upgrade"
description: "Upgrade Spec Kit in this repository to a specified version tag or the latest tagged release. Use when the user asks to upgrade Spec Kit, update specify-cli, refresh .specify files, or reinstall GitHub Spec Kit."
argument-hint: "Optional version tag such as v0.8.5, or latest"
compatibility: "Requires uv, specify-cli install access, pnpm, and a Spec Kit project with .specify/ directory"
user-invocable: true
disable-model-invocation: false
metadata:
  internal: true
---

# Spec Kit Upgrade

Upgrade the GitHub Spec Kit CLI and refresh this repository's generated Spec Kit files. Leave resulting changes as local WIP; do not stage, commit, or revert unrelated changes.

## Target Input

Infer the requested Spec Kit target from the user's message. It may be:

- A version tag, for example `v0.8.5`
- `latest`, meaning the latest tagged release
- Empty, meaning the user must choose a version tag or latest

## Workflow

1.  **Confirm target**
    - If user input is empty or ambiguous, prompt the user to choose:
      - Provide a specific version tag
      - Update to the latest tagged release
    - Do not proceed until the target is clear.

2.  **Record current WIP**
    - Run `git status --short`.
    - Note existing local changes so you do not confuse pre-existing WIP with Spec Kit upgrade output.

3.  **Resolve version**
    - For a specified tag, set `SPEC_KIT_VERSION` to the trimmed tag exactly:

      ```bash
      SPEC_KIT_VERSION="v0.8.5"
      ```

    - For `latest`, resolve the newest semver-like `v*` tag from `github/spec-kit`:

           ```bash
           SPEC_KIT_VERSION="$(
             git ls-remote --tags --refs https://github.com/github/spec-kit.git 'v*' |
               sed 's|.*/||' |
               sort -V |
               tail -1
           )"
           ```

4.  **Install the CLI from the selected tag**
    - Use the selected tag in the git source ref. Do not install from the default branch for a tagged upgrade.

      ```bash
      uv tool install specify-cli --force --from "git+https://github.com/github/spec-kit.git@${SPEC_KIT_VERSION}"
      ```

5.  **Reinitialize Spec Kit in place**

    ```bash
    specify init --here --force --integration claude --no-git --branch-number timestamp
    ```

6.  **Format generated changes**

    ```bash
    pnpm format:write
    ```

7.  **Report results**
    - Run `git status --short`.
    - Summarize the installed Spec Kit target and the files changed by the refresh.
    - State that any updates are local WIP.
    - Do not stage or commit unless the user explicitly asks.

## Command Notes

- The selected version ref belongs after `.git@`, for example:

  ```bash
  uv tool install specify-cli --force --from "git+https://github.com/github/spec-kit.git@v0.8.5"
  ```

- If the install, init, or format command fails, stop and report the failing command and key error output.
