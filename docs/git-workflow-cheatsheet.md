# Git Workflow Cheat Sheet

Git commands can be run from any subfolder inside the repository. Git searches
upward until it finds the repository's `.git` directory.

## Find the Repository Root

| Command | Purpose |
|---|---|
| `git rev-parse --show-toplevel` | Show the repository root directory. |
| `git status --short` | Show modified, staged, deleted, and untracked files. |
| `git branch --show-current` | Show the current branch. |
| `git remote -v` | Show configured remote repositories. |

## Start a New Feature

```bash
git switch Main

git status
→ switch Main
→ pull --ff-only
→ create feature branch
→ edit code
→ run lint and tests
→ git diff --check
→ stage exact files
→ git diff --staged --check
→ commit
→ switch Main
→ merge --ff-only
→ delete feature branch
→ push Main