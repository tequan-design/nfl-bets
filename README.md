# nfl-bets — fantasy football agent

A Claude agent that watches Quan's two Yahoo fantasy leagues (Dirty South League 1 and
End Zone Bound) and tells him what to do: start/sit, waiver pickups, inactives
emergencies and other managers' moves that matter.

- **How it runs:** scheduled Claude cloud sessions open this repo and follow a playbook
  in `agent/playbooks/`. Each run sends a push to the Claude app and updates the
  dashboard.
- **Dashboard:** [Too HOT 4 TV War Room](https://claude.ai/artifact/HgVezfLhTTWUxuH64SmtPj)
- **Schedule:** `agent/schedule.md`
- **Rules for the agent:** `CLAUDE.md`

Data: Flaim Fantasy connector (Yahoo league data), web search (injuries, roles), The Odds
API (Vegas lines → implied team totals), optionally Billy Bets (prediction-market signals).

The agent can't change Yahoo lineups or rosters; it tells you what to tap.
