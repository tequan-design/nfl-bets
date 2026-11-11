# NFL Picks Agent

A scheduled Claude agent that studies the NFL every week and recommends pick'em entries for
PrizePicks, Underdog and Betr, plus Kalshi/Polymarket plays, for a Georgia-based player with a
small bankroll. Then it texts when something changes.

- **Wednesday ~8:40am ET**: grades last week's picks, adds the box scores to memory, reads lines,
  prediction-market money, injuries and weather, prices every prop, and publishes the week's picks
  to Google Drive (Sports bets folder) and `reports/`, then texts a summary.
- **Tue/Thu/Fri/Sat ~5:47pm ET**: checks for injury, trade, line, market and weather changes, and texts
  only when a pick or edge changes.
- **Game days** (Thu/Mon ~6:47pm, Sun ~11:47am / 2:47pm / 6:47pm ET): inactives check before kickoff.

How it works: `CLAUDE.md` (playbook), `prompts/` (each scheduled routine), `config/profile.json`
(bankroll and alert thresholds), `nfl_agent/` (data tools: `python3 -m nfl_agent -h`), `memory/`
(picks ledger + lessons), `data/` (season stats, snapshots).

Data sources: ESPN (schedule, box scores, injuries), The Odds API (sportsbook lines + PrizePicks/
Underdog/Betr prop lines), Kalshi and Polymarket (prices, volume, Kalshi player-prop ladders),
Open-Meteo (weather), Billy Bets (connector), Flaim (Yahoo fantasy leagues), web search (news).

No pick is guaranteed. Lines move; confirm in-app.
