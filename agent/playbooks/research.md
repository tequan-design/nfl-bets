# Research toolkit (used by every playbook)

## 1. Production and usage: `scripts/player_stats.py`
ESPN game logs scored with **both** leagues' rules: points per game, last-3 average,
targets/carries per game, weekly lines and remaining schedule (playoff weeks 15–17
starred, each opponent's points allowed and rank). Use it for every start/sit coin flip,
pickup and trade. A player's name, draft pedigree or value-chart rank never outweighs
what he is actually scoring.

## 2. Expert consensus: weekly start/sit articles
These sites are reachable from the cloud environment; fetch the current week's pieces
(the `web-fetch` agent, `curl -L -A "Mozilla/5.0"`, or `WebSearch` to find the URL):
- NFL.com fantasy: https://www.nfl.com/news/series/fantasy (start 'em/sit 'em, waiver wire)
- Yahoo fantasy: https://sports.yahoo.com/fantasy/ (start/sit, injury tracker, waiver wire)
- CBS fantasy: https://www.cbssports.com/fantasy/football/ (rankings, trade value chart)
- Rotowire: https://www.rotowire.com/football/ (injury news, depth charts)
- Fantasy Life: https://www.fantasylife.com/ (upgrades/downgrades, utilization)
- ESPN: https://www.espn.com/fantasy/football/
- FantasyPros (consensus rankings, trade chart) and 4for4 when a page is public.

For each of Quan's close calls, note what 2+ sources say. If the agent's pick goes
against consensus, say so and why (scoring settings, matchup, usage data).

## 3. Opportunity scan: injuries create pickups
Every preview, waivers and monitor run:
1. List NFL starters (RB1, WR1/WR2, TE1, QB) who are **Out, on IR, or newly benched**
   this week (Yahoo injury tracker, NFL.com injury reports, Rotowire).
2. For each, identify the **next man up** from beat reporters / depth charts.
3. Check his availability in each league (`get_free_agents` with the position, or
   `get_players` by name).
4. Check how he produced when he got the role before (`player_stats.py` weekly lines:
   the weeks the starter missed).
5. Recommend the add when the opportunity is real (projected 12+ touches or 6+ targets),
   naming the drop. In **Dirty South** this is first-come-first-served, so it's an
   immediate push. In **End Zone Bound** it's a waiver claim (process Wed ~4:45am) unless
   the player is a free agent.

## 4. Vegas: `scripts/odds.py`
Implied team totals for game environment; `--next` for next week (Tuesday run).

## What we can't use
Yahoo Plus features (Yahoo's own projections, matchup ratings, trade grades) live inside
Yahoo's app behind Quan's login. The Flaim connector only reads league data (rosters,
matchups with Yahoo's projections and win probability, standings, free agents,
transactions). If Quan shares a screenshot of a Yahoo Plus screen, treat it as an
extra input.
