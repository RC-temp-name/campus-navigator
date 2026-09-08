# Contributing to MiniMap

Thanks for contributing. This guide is the source of truth for how we propose work, open pull requests, and verify changes before merging. If something is ambiguous or missing, ask and then update this guide.

## How we work, in one line

**Issue → focused branch → pull request → `just check` + CI → review → squash merge.**

```
Idea still uncertain?
  → discuss it in GitHub Discussions (Ideas category)
  → turn it into an actionable issue (bug / feature / engineering task)
  → create a focused branch off an up-to-date `main`
  → open a draft or ready pull request linked to that issue
  → run `just check` and wait for green CI
  → get it reviewed
  → squash-merge it
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager and version manager
- [just](https://github.com/casey/just) - command runner (defines the commands below)
- [Docker](https://www.docker.com/) - only needed for the `just docker` dev environment and the `docker-config` check step
- Node.js - used by the frontend tests (`just test-frontend`)

The GitHub Actions CI workflow runs the exact same commands, so what passes locally should pass in CI.

## Common commands

Run `just` with no arguments to list every recipe.

| Command | What it does |
| --- | --- |
| `just install` | Install dependencies (`uv sync`) - run once after cloning |
| `just run` | Start the app at <http://localhost:5000> |
| `just check` | **Full pre-push gate.** Lint, formatting, tests, compile, data validation, and Docker config |
| `just docker` | Build and run the Docker development environment |

`just check` runs, in order: `lint`, `format-check`, `test`, `test-frontend`, `compile`, `validate-data`, `docker-config`. CI runs the same seven steps on every pull request to `main`, so a green `just check` is a good proxy for a green build.

For faster iteration while developing, use the focused commands: `just lint`, `just format`, `just format-check`, `just test`, `just test-frontend`, `just validate-data`, `just coverage`. Run the full `just check` before pushing.

## Where ideas start

- **Concrete bug, feature, or task?** Open an issue using the right template:
  - **Bug report** - something is broken
  - **Feature request** - new or changed product behavior
  - **Engineering task** - refactors, documentation, data, infrastructure, maintenance
- Add an ownership label (`backend`, `frontend`, `data`, `documentation`, `integration`) so the right people notice it.

## Making a change

### 1. Start from an up-to-date `main`

Never commit directly to `main`. `main` must always stay stable and green.

```bash
git checkout main
git pull origin main          # make sure main is current
git checkout -b feat/short-description
```

Use a descriptive, prefixed branch name:

- `feat/room-to-room-routing`
- `fix/missing-node-route`
- `docs/contribution-workflow`
- `refactor/pathfinding-module`
- `chore/update-dependencies`

### 2. Keep the change small and focused

**One issue, one focused pull request.** If a change grows, split it into smaller PRs. They're easier to review, test, and merge. Keep commits small and focused on a single idea. Merge `main` into your branch often to catch conflicts early.

### 3. Open a pull request

Push your branch and open a PR into `main`. The pull request template will remind you to:

- link the issue with a closing keyword: `Closes #…`, `Fixes #…`, or `Resolves #…`
- explain what changed and why
- show how you tested it
- attach screenshots/recordings for UI changes
- note data/schema impact and run data validation for graph-data changes

**Open a draft PR early** for feedback if you want input before the work is finished.

### 4. Verify before merging

- Update tests whenever behavior changes, and add tests for new behavior.
- For changes to graph data (`data/`), run `just validate-data` (also part of `just check`).
- For UI changes, include screenshots or a screen recording.
- Run `just check` and make sure CI is green before requesting review.

### 5. Review and merge

- Request a review; a maintainer must approve before merging.
- Address feedback in follow-up commits and re-run `just check`.
- When approved, **squash-merge**, which is the default. Squashing keeps `main` history clean and gives one clear commit per PR.

**Title your PR in Conventional Commit style** so the squashed commit reads well:

| Type | Use for | Example |
| --- | --- | --- |
| `feat` | new feature | `feat: add room-to-room shortest path` |
| `fix` | bug fix | `fix: handle missing node in route lookup` |
| `docs` | documentation | `docs: add contribution workflow` |
| `refactor` | code change with no behavior change | `refactor: simplify pathfinding module` |
| `test` | tests only | `test: cover empty-route edge case` |
| `chore` | tooling, deps, maintenance | `chore: pin ruff version` |

### Handling merge conflicts

Conflicts are normal. Update your branch with `main`, resolve the conflicting files, run `just check`, and commit the resolution.

```bash
git merge main
# resolve conflicts in your editor
just check
git add .
git commit -m "Resolve merge conflicts with main"
```

## Definition of done

Before a PR can merge, all of these must be true:

- [ ] Linked to one issue with a closing keyword
- [ ] Scope is focused on that one issue
- [ ] Tests updated (and added) for behavior changes; all tests pass
- [ ] `just check` passes locally and CI is green
- [ ] Screenshots/recordings included for UI changes
- [ ] `just validate-data` run for graph-data changes
- [ ] Reviewed and approved by a maintainer
- [ ] Squash-merged with a clear Conventional Commit title

## AI-assisted contributions

AI-assisted code is welcome but treated exactly like any other contribution: **the author is responsible for it.** Before merging, make sure you understand every change, have tested it, and can explain it in review. An AI tool doesn't change the bar. Checks must still pass and reviewers must still be able to follow the code. If you can't explain a piece of generated code, rewrite it until you can.

## Keeping `main` protected

Rely on the rules above. We have branch protection enabled on `main`: require pull requests (no direct pushes). Keep branches up to date and require status checks to pass before merging.
