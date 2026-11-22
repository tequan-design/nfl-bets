# Playbook: trade ideas

Runs as a step inside the Saturday preview and the Tuesday waivers run, until the trade
deadline in `agent/leagues.md`. Can also be run on its own when Quan asks.

**Deadline math.** Both leagues ratify trades by league vote (Dirty South: 1-day reject
window, End Zone Bound: 2 days). A trade has to be *accepted* that many days before the
deadline to clear. Past that point, stop suggesting trades and delete the
`data/agent/trades` rows.

## Steps (each league)
1. Quan's roster: list each position's starters, then **surplus** (bench players who'd
   start for other teams) and **need** (the weakest starting slot, judged with that
   league's scoring).
2. `get_roster` for every other team. For each, note its needs (too few startable players
   at a position, or a starter Out/IR) and surplus (good players stuck on its bench).
3. Pair them: a partner with surplus at Quan's need **and** need at Quan's surplus. Prefer:
   - teams that are out of the race or below .500 (more willing to deal),
   - 2-for-1 offers from Quan's bench depth (the partner fills a hole, Quan consolidates),
   - not this week's opponent and not a direct rival for a playoff seed, unless the deal is
     clearly better for Quan.
4. Price each idea with a current rest-of-season trade value chart (search "trade value
   chart week N <year>"; Roto Street Journal, FantasyPros, CBS, Yahoo). Use one chart for
   both sides and quote it. Aim for offers the other manager would accept: Quan may give
   slightly more raw value when he gets the best player in the deal.
5. Verify health and role on the web for every player in an offer. Mark anything you
   couldn't verify "unverified".
6. Write 2–4 ideas per league, best first. Include a fallback when two ideas use the
   same player of Quan's.

## Write to the dashboard
`data/agent/trades` (replace all rows). Doc id `<league-slug>-<rank>`.
```json
{"league": "End Zone Bound", "rank": 1, "partner": "Anonymous", "partnerNote": "5-5; only 2 RBs",
 "give": "Jonah Coleman", "get": "Drake London",
 "why": "…", "value": "Coleman 2002 vs London 1839 (Roto Street Journal, Week 11)",
 "confidence": "Medium", "sendBy": "Mon 11/24"}
```
Add one priority-2 `data/agent/moves` item per league pointing at the best idea.

## Push summary
One line per league: "Offer <give> to <partner> for <get>."
