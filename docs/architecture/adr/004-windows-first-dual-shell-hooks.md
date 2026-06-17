# ADR 004: Windows-first, with dual PowerShell and Bash hook implementations

**Status:** Accepted

## Context

Claude Code hooks run shell commands. Most agentic tooling assumes a Unix shell, which leaves Windows developers patching scripts before anything works. The kit's author works on Windows, and the kit explicitly aims to be "Windows-first, cross-platform."

A hook is registered in `settings.json` with a concrete command. PowerShell and Bash differ enough — invocation, stdin handling, exit semantics — that one script cannot serve both cleanly.

## Decision

Ship every hook twice: a `.ps1` PowerShell version and a `.sh` Bash version, plus two settings files:

- `settings.json` (default) invokes `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <hook>.ps1`.
- `settings.unix.json` invokes the `.sh` scripts directly.

The default is the Windows configuration; macOS/Linux users copy `settings.unix.json` over `settings.json` during install.

## Alternatives considered

### Option A: Bash-only (assume WSL/Git Bash on Windows)
Pros: one implementation; matches most tooling.
Cons: forces Windows users into WSL/Git Bash; brittle path translation; contradicts the Windows-first goal.

### Option B: Pure-Python hooks, no shell scripts
Pros: one cross-platform implementation.
Cons: still need a shell to *invoke* Python with the right interpreter (`python` vs `python3`) and stdin piping; doesn't remove the platform branch, just moves it; loses the thin, readable shell wrappers.

### Option C: Dual `.ps1` + `.sh` with two settings files (chosen)
Pros: native experience on every platform; each script is idiomatic and thin; the Python tools stay the single source of truth (the shells just call them).
Cons: two copies of each hook to keep in sync; an install step (pick the settings file) that's easy to skip.

## Rationale

The shell scripts are deliberately tiny — they resolve the repo root and pipe stdin into a Python tool. Duplicating ten-line wrappers is cheap; the real logic lives once, in Python. That keeps the duplication burden low while giving every developer a native, no-surprises setup. Windows-first is a real constraint for this author and an underserved case generally.

## Trade-offs

Two risks come with the duplication:

1. **Drift.** The danger-pattern lists in `block-danger.ps1` and `block-danger.sh` have already diverged — the PowerShell version blocks Windows-specific patterns (`format`, `del /s /q`, `rd /s /q`, `Remove-Item -Recurse -Force $HOME`) the Bash version lacks. This is documented in [hooks & settings](../../reference/hooks-and-settings.md#pretooluse--block-danger) and must be reconciled by hand when edited.
2. **A skipped install step.** Forgetting to swap in `settings.unix.json` on macOS/Linux leaves hooks calling `powershell.exe`, which silently does nothing. The [install guide](../../guides/install-into-a-repo.md) calls this out explicitly.

## Consequences

- Every hook change is two edits; keep the pair in sync.
- The install flow has an OS-dependent step (choosing the settings file).
- The Python tools remain the single source of truth, so logic bugs are fixed once. See [tools](../../reference/tools.md).
