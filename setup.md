# Setup: two separate git repos

This folder holds two independent git repositories:

| Path | Contents | Remote |
|---|---|---|
| `./` (outer) | scripts, notes, analysis | GitHub |
| `report/` (inner) | LaTeX report (`main.tex`, sections, `bib/`) | TeXPage |

`report/` is **not** a submodule. It is a separate repo that the outer repo ignores.

## How the separation works

1. The outer `.gitignore` lists `report/` (and `data/`), so the outer repo never tracks anything under it.
2. Git uses the nearest `.git` directory. Commands run inside `report/` act on `report/.git`, and commands run anywhere else act on `./.git`.
3. Each repo keeps its own remotes in its own `.git/config`, so both can have a remote called `origin` without conflict.

Check which repo you are in with:

```bash
git rev-parse --show-toplevel
```

## Fresh setup on a new machine

```bash
# 1. Clone the outer repo
git clone <github-url> failure-attribution-datasets
cd failure-attribution-datasets

# 2. Clone the report into report/ (already ignored by the outer repo)
git clone https://git.texpage.com/<project-id>.git report

# 3. data/ is not in either repo; restore it separately
```

## Day-to-day

```bash
# Outer repo (from the top folder)
git add <files> && git commit -m "..." && git push

# Report (TeXPage)
cd report
git pull                       # get edits made in the TeXPage web editor
git add <files> && git commit -m "..." && git push
```

Or, without changing directory: `git -C report status`, `git -C report pull`, and so on.

## Rules

- **Keep `report/` in the outer `.gitignore`.** If you remove it, `git add .` stages `report/` as an embedded-repo pointer with no contents, which is almost never what you want.
- **Don't put credentials in remote URLs.** Use a URL without the token and a credential helper:
  ```bash
  git -C report remote set-url origin https://git.texpage.com/<project-id>.git
  git -C report config credential.helper store   # or: cache
  ```
- **The two histories are not linked.** Outer commits don't record which report version they go with. If you need that, convert `report/` to a submodule (`git submodule add <texpage-url> report`) and accept the extra submodule steps.
- **To also back up the report on GitHub**, add a second remote inside `report/` only:
  ```bash
  git -C report remote add github <github-url-for-report>
  git -C report push github main
  ```
