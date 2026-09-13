# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What's in this repo

Several independent projects share one repo, `Claude-Project` (renamed from `space-shooter`; the local folder is `Claude Project`).

| Path | What it is | Docs |
|------|-----------|------|
| `business-tracker/` | **Pulse** — business metrics tracker. Single-file web app, data in localStorage | `business-tracker/README.md` |
| `staff-scheduler/` | 班表 — restaurant scheduling, timesheets, payroll. Single-file web app | `staff-scheduler/README.md` |
| `restaurant-site/` | 拾山 SHISHAN restaurant landing page | — |
| root `*.py` | F&B lead pipeline: scraping (`scrap*.py`), ICP qualification with Gemini (`analyze_leads.py`), cold emails (`generate_emails.py`), `leads_app.py` | `scrap.md`, `pp.md`, `icp.md`, `coldemail.md` |

The web apps have no build step and no dependencies: open `index.html` in a browser, or serve with `py -m http.server`.

## Live site (GitHub Pages)

GitHub Pages serves the `master` branch from the repo root:

- https://yong0225.github.io/Claude-Project/business-tracker/ — Pulse. The owner uses this daily on their phone from the home screen.
- Other folders are reachable the same way (`/staff-scheduler/`, `/restaurant-site/`).

**Anything pushed to `master` is live within 1–2 minutes.** Never push broken work to `master`.

Pulse stores each user's data in their own browser's localStorage (key `pulse.v1`). Every code change must keep reading existing saved data: extend `normalize()` for new fields, and never rename or remove stored keys without a migration.

Pulse cloud sync uses the Supabase project `rlaeklherxdfrlbduqde` (shared with staff-scheduler's `bb_*` objects — never touch those). Pulse's tables and functions are prefixed `pulse_`; the schema is in `business-tracker/supabase.sql`. Devices running an older cached copy of the page keep calling these functions, so change them only in backward-compatible ways, and keep the sync fields (`u`, `su`, `setu`, `del`) and merge rules in `mergeDB()` compatible.

## Git workflow

Remote: https://github.com/Yong0225/Claude-Project
Main branch: `master` (this is what the live site serves)

**Every change must be committed, pushed, and reach `master` before the session ends. No exceptions.**

1. At the start of a session, `git fetch origin` and make sure you are working on top of the latest `origin/master` (`git pull` on master, or `git merge --ff-only origin/master` on a branch).
2. After each change: `git add <changed files>` → `git commit -m "type: description"` → `git push`.
3. If you are on a branch other than `master` (e.g. a `claude/...` worktree branch), merge into `master` once the change is verified — syntax-checked and opened in a browser with no console errors:
   ```
   git fetch origin
   git merge origin/master        # resolve any conflicts on the branch, re-verify
   git push                        # update the branch
   git push origin HEAD:master     # fast-forward master = deploy
   ```
   Never force-push `master`. If `HEAD:master` is rejected, fetch and merge again rather than forcing.
4. Do not merge half-finished work. If a task is only partly done when the session ends, commit and push the branch, and tell the owner it has not been merged yet.

Commit message convention: `type: short description` (e.g. `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`). Do not batch unrelated changes into one commit.

Files to never commit:
- `.env` (contains API keys)
- `.claude/` (Claude Code local settings)
