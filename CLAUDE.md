# Fantasy Football Agent — "Too HOT 4 TV"

This repo is a fantasy football **monitoring and advice agent** for Quan, who owns the
team "Too HOT 4 TV" in two Yahoo leagues. Scheduled cloud sessions open this repo and
run one of the playbooks in `agent/playbooks/`. A person may also open a session and
just ask questions; the same rules apply.

## What every run does

1. Read `agent/leagues.md` (league IDs, team IDs, scoring quirks, roster rules).
2. Read the playbook named in the prompt (`agent/playbooks/<name>.md`) and follow it.
3. Pull **live** data. Never reuse rosters, scores or injury news from memory or from a
   previous run's notes.
4. Write results to the dashboard (`agent/dashboard.md` explains the data store).
5. End with a short plain-text summary. It becomes the phone push notification, so the
   first line must say the single most important thing (e.g. "Start Chase Brown over
   Ollie Gordon in End Zone Bound"). If nothing needs action, say so in one line.

## Data sources, in priority order

| Need | Source |
|---|---|
| Rosters, lineups, matchups, standings, free agents, transactions | **Flaim Fantasy** connector (`mcp__Flaim_Fantasy__*`), Yahoo, season 2026 |
| Injury status, depth charts, role changes, beat-writer news | `WebSearch` (prefer team sites, NFL.com, ESPN, CBS, Rotowire, FantasyPros) |
| Game spreads/totals → implied team totals; player props | `python3 scripts/odds.py` (The Odds API; credentials are injected by the proxy) |
| Prediction-market signals and NFL player props | **Billy Bets** connector (optional; show its attribution and disclosure lines if used) |

Flaim session context: call `get_user_session` once, then `get_league_info` once per
league, before other Flaim calls (the connector requires this order). IDs are in
`agent/leagues.md`.

## Hard rules

- **Never state a player's team, role or health from memory.** Verify with a current web
  source or the connector. If you couldn't verify, say "unverified" next to the claim.
- Flaim is read-only. The agent **cannot** set lineups, add/drop or trade. It tells Quan
  exactly what to tap in the Yahoo app.
- Refer to teams and players by name. Never show internal IDs, team keys or player keys
  to the user.
- Score every recommendation **with the league's own scoring** (the two leagues differ a
  lot; see `agent/leagues.md`).
- Yahoo locks each player at his own kickoff. A Monday-night player who might be ruled
  out late is a risk: name a Sunday pivot before Sunday games lock if he is questionable.
- Be decisive: one recommendation per decision, with a one-line reason, plus the
  confidence (High / Medium / Coin flip). No essays.
- Don't spam. A push is only worth sending when there is something to do or to know.
  The transaction monitor in particular stays quiet when nothing relevant happened.

## Dashboard

"Too HOT 4 TV War Room": https://claude.ai/artifact/HgVezfLhTTWUxuH64SmtPj
Write with the `ArtifactData` tool (load via ToolSearch). Schemas: `agent/dashboard.md`.

## Repo layout

- `agent/leagues.md` — league facts and scoring digest
- `agent/playbooks/*.md` — one file per scheduled run
- `agent/dashboard.md` — dashboard store collections and row shapes
- `agent/schedule.md` — when each run fires and why (incl. transaction-timing analysis)
- `scripts/odds.py` — NFL lines → implied team totals, optional player props
- `scripts/tx_timing.py` — re-run the transaction-timing analysis from a JSON dump
