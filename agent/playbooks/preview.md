# Playbook: Saturday preview (full week)

Fires Saturday early afternoon ET, after Friday's final injury reports.

## Steps (do both leagues)
1. Flaim: session → league info → `get_matchups` (current week), `get_roster` for Quan's
   team, `get_standings`. Also `get_roster` for this week's **opponent** (team id from the
   matchup).
2. `python3 scripts/odds.py --week` → spread, total and implied team total per game.
   Teams missing from the list are on bye or already played (check Thursday result).
3. Web research (batch the searches, standard mode first):
   - Byes and the Thursday result for this week.
   - Final injury designations (Out / Doubtful / Questionable) for every player on both
     of Quan's rosters who might start. Search by team ("<team> final injury report week N").
   - Role news for any RB/WR in a committee or a changed depth chart.
   - Weather for outdoor games with wind > 15 mph or heavy rain/snow.
4. For each league decide every starting slot. Inputs, in order: availability → role/volume
   → implied team total and game script → that league's scoring (see `agent/leagues.md`)
   → matchup. Note bench players who outscore a starter.
5. Free-agent check (top 25 overall, plus position-filtered where Quan is thin). In
   **Dirty South** anyone available can be added immediately; in **End Zone Bound** check
   `acquisitionState` (waivers vs free agent). Recommend an add only if it improves this
   week's lineup or covers a bye/injury.
6. Opponent read: their projected points, their questionable starters, and whether Quan
   is an underdog (if so, lean upside plays; if a big favorite, lean safe floors).
7. Trade note (only until the trade deadline in `agent/leagues.md`): one idea per league
   if a clear surplus/need pairing exists with a specific team.

## Write to the dashboard
- `data/agent/lineup`: all 18 slot rows (9 per league).
- `data/agent/moves`: replace with this run's action items.
- `data/agent/runs`: one row.

## Push summary (final message)
Line 1: the most important move. Then at most 6 short lines: one per league with
record/projection/opponent and the swaps to make, any add/drop, and a reminder of
Monday-night players to monitor.
