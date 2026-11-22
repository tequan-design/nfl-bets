# Playbook: Thursday afternoon TNF check

Fires Thursday ~3:45pm ET, before the 8:15pm Thursday game. On weeks with earlier games
(Wednesday games, Thanksgiving 1:00/4:30pm slates, international games), a one-off run
is scheduled a few hours before the first of them, and the prompt says which games to
cover. If this run fires after some of this week's games have already kicked off, cover
only the games still to come and say so.

## Steps
1. `python3 scripts/odds.py --week` to find the Thursday game (and any international or
   Friday game this week).
2. Flaim: Quan's rosters in both leagues. List every player on the Thursday teams,
   started or benched.
3. Web search the Thursday game's injury report and any late news for those players.
4. Decide: should each Thursday player be started this week? Compare with the Sunday
   alternatives already on the roster using implied totals and league scoring.
   Remember Thursday players lock at 8:15pm.
5. Also check: a Thursday-team player available in either league who would beat a
   current starter (Dirty South: immediate add; End Zone Bound: free agents only;
   waiver players won't clear in time).
6. If Quan has no Thursday players and no action, summary is one line.

## Write to the dashboard
- `data/agent/moves`: priority-1 items for Thursday decisions (deadline "Thu 8:15 PM ET").
- `data/agent/runs`: one row.

## Push summary
Line 1: the Thursday decision ("Start X tonight over Y" / "No Thursday players").
