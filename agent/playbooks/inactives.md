# Playbook: Sunday 11:45am ET inactives check

Fires Sunday 11:45am ET. Inactive lists for the 1:00pm games come out ~11:30am.

## Steps (both leagues)
1. Flaim: current roster for Quan's team in each league (lineup can have changed since Saturday).
2. Read last Saturday's `data/agent/moves` and `data/agent/lineup` to know what was advised.
3. Web search the inactive lists / late news for every **started** player and every
   Questionable player on either roster ("<team> inactives week N", "<player> active").
   Also check late-game (4pm) and Sunday/Monday night players for new downgrades.
4. Flag, in order of urgency:
   - A starter who is **Out/inactive** → name the best bench replacement (or free agent in
     Dirty South) and the exact swap.
   - A starter still listed Questionable and playing at 4pm or later, with a safe pivot.
   - A Monday-night starter at risk → recommend whether to pivot to a Sunday player now,
     because Sunday players lock at kickoff.
   - Advice from Saturday that the lineup still hasn't applied.
5. If everything is fine, the summary is one line: "All starters active in both leagues."

## Write to the dashboard
- Update affected `data/agent/lineup` rows (verdict "Swap in" / "Check status").
- Add priority-1 `data/agent/moves` items for every swap; mark stale ones done by deleting them.
- `data/agent/runs`: one row.

## Push summary
Line 1: the swap to make before 1:00pm, or "All starters active".
