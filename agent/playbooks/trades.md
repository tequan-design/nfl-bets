# Playbook: trade ideas

Runs as a step inside the Saturday preview and the Tuesday waivers run, until the trade
deadline in `agent/leagues.md`. Can also be run on its own when Quan asks.

**Deadline math.** Both leagues ratify trades by league vote (Dirty South: 1-day reject
window, End Zone Bound: 2 days). A trade has to be *accepted* that many days before the
deadline to clear. Past that point, stop suggesting trades and delete the
`data/agent/trades` rows.

## The bar every idea must clear (non-negotiable)

Quan's rule: **he has to get the better value, and the player he gets must be producing.**
Value charts and name recognition are not enough. Get each player's points from Yahoo's
weekly rosters (`get_roster` with `week=N`; see `research.md` §1a), and usage and schedule
from `python3 scripts/player_stats.py`.

A player Quan **receives** must have, in that league's scoring:
1. **Production:** points per game at least 3 higher than the starter he replaces, and
   recent form (last 3 games) that isn't collapsing. Reject anyone who rarely reaches
   10 points.
2. **Usage:** a real, stable role, e.g. WR 6+ targets/game, RB 12+ touches/game.
   Low-volume players whose points come from rare long TDs don't count.
3. **Schedule:** check the remaining opponents, especially fantasy playoff weeks 15–17.
   Flag any playoff week against a top-5 defense.
4. **Health:** verify on the web that he's active and not on a short-term injury.
5. **Not already a free agent.** Check `get_free_agents` first. Never trade for someone
   Quan could pick up for free.

The trade as a whole must leave Quan's **weekly starting lineup better**. Add up the
points-per-game gained where he upgrades, minus what he loses where the outgoing player's
replacement (bench player or best free agent) starts instead. Only suggest trades with a
clearly positive net, and state that net in the idea ("+6.8 pts/week").

## Steps (each league)
1. Quan's roster with `player_stats.py`: each starter's PPG, plus **surplus** (bench players
   who'd start elsewhere) and **need** (the weakest starting slot by PPG).
2. `get_roster` for every other team. For each, note needs (a weak starter, or a starter
   who is Out/on IR) and surplus (productive players stuck on its bench).
3. Pair them: a partner with surplus at Quan's need **and** need at Quan's surplus. Prefer
   partners where the deal also helps them on paper (more likely to be accepted), teams
   below .500, and 2-for-1s from Quan's depth. Avoid this week's opponent and direct seed
   rivals unless the deal is clearly better for Quan.
4. Run `player_stats.py` on every candidate and apply the bar above. Use a trade value
   chart (FantasyPros, CBS, Yahoo) only as a cross-check on how the other manager will see it.
5. Write 2–4 ideas per league, best first, with a fallback when two ideas use the same
   player of Quan's.

## Write to the dashboard
`data/agent/trades` (replace all rows). Doc id `<league-slug>-<rank>`.
```json
{"league": "End Zone Bound", "rank": 1, "partner": "A-TOWN JAGS", "partnerNote": "5-5 · Kenneth Walker III out",
 "give": "Chase Brown (RB, CIN) — 11.8 ppg", "get": "Tee Higgins (WR, CIN) — 17.1 ppg",
 "why": "…usage, recent form, playoff schedule, why they'd accept…",
 "value": "Net +5.3 pts/week for your lineup (league scoring, ESPN game logs)",
 "confidence": "Medium", "sendBy": "Mon 11/24"}
```
Add one priority-2 `data/agent/moves` item per league pointing at the best idea.

## Push summary
One line per league: "Offer <give> to <partner> for <get> (+N pts/week)."
