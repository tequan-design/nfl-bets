# Playbook: Tuesday night waivers

Fires Tuesday ~9pm ET, after Monday night's game and before End Zone Bound's waivers
process (Wednesday ~4:45am ET). Dirty South has no waiver delay, so its adds can be made
the moment this summary arrives.

## Steps (both leagues)
1. Flaim: matchups for the week just finished (result, both scores) and standings.
   Next week's opponent (current week matchups after rollover).
2. Quan's rosters. Identify: injured players (verify on the web), bye weeks for next
   week (`scripts/odds.py --week` once next week's lines are posted, else web search),
   and the weakest bench spots (drop candidates).
2b. Opportunity scan (`agent/playbooks/research.md` §3): which NFL starters got hurt or
   benched this week, and is the next man up available in either league?
3. `get_free_agents` for each league: count 40 overall plus position-filtered for
   needs. Note `acquisitionState` in End Zone Bound.
4. `scripts/player_stats.py` on every candidate and on Quan's drop candidates; read the
   week's waiver-wire articles (NFL.com, Yahoo, CBS). Web research for top candidates: role change (injury to a starter, depth chart),
   snap share/targets/carries last week, next opponent's defense.
5. Rank up to 5 targets per league with the exact drop for each. End Zone Bound has
   rolling waiver priority (Quan's spot is in `get_standings` → `waiverPriority`): only
   recommend spending priority on a true difference-maker, otherwise target free agents.
6. Playoff angle: from week 12 on, weigh playoff-week schedules (weeks 15–17) and
   handcuffs for Quan's top RBs.
7. Early games: run `python3 scripts/odds.py --week --next`. If any of next week's games
   kick off before Thursday 3:45pm ET (Wednesday games, Thanksgiving, international), list
   Quan's players in them in the summary, and check `list_triggers` for a one-off early-game
   run; if there is none, say "No early-game check is scheduled. Ask me to add one."
8. Trades (until the deadline in `agent/leagues.md`): follow `agent/playbooks/trades.md`.
9. Recap last week in one line per league (win/loss, best and worst starter vs projection,
   and whether the agent's advice helped or hurt). Be honest.

## Write to the dashboard
- `data/agent/waivers`: replace all rows.
- `data/agent/moves`: replace with waiver/drop items (deadline "Wed 4:45 AM ET" for End
  Zone Bound claims, "Now" for Dirty South adds).
- `data/agent/runs`: one row.

## Push summary
Line 1: the best pickup and the drop. Then one line per league: last week's result and
the claims to put in.
