# Wednesday weekly run (Wednesday ~8:40am ET)

Follow `CLAUDE.md`. Work from the repo root. Goal: learn from last week, then deliver this week's
picks report (Google Drive + repo) and a short text.

1. **Sync.** `git pull --rebase`. `python3 -m nfl_agent status` -> season Y, last completed week L,
   upcoming week W = L+1 (if ESPN still shows week L in progress because of MNF, wait/ingest what is final
   and note it).
2. **Build memory from last week.**
   - `python3 -m nfl_agent ingest --season Y --week L`
   - `python3 -m nfl_agent grade --season Y --week L`; for any "ungraded" leg check if the player was
     inactive (mark result `void`) by editing `memory/picks.csv`.
   - `python3 -m nfl_agent scorecard`. Write 3-6 new bullet lessons in `memory/lessons.md`: what hit,
     what missed and *why* (role change, game script, weather, TNF weirdness, line was a coin flip).
     Note any TNF anomalies explicitly. Prune lessons that no longer hold.
3. **Read the week.**
   - `python3 -m nfl_agent slate --week W --weather` (spreads, totals, Kalshi/Polymarket money + volume).
   - `mcp__Billy_Bets__slate` with sport `nfl`, then `mcp__Billy_Bets__game` for the TNF game and any game
     with an Alpha read or a big prop board.
   - `python3 -m nfl_agent injuries`, plus WebSearch for: trades, IR moves, QB changes, suspensions,
     coaching changes, and Wednesday practice reports.
   - `python3 -m nfl_agent defense` for matchup ranks.
   - WebSearch current PrizePicks and Underdog NFL promos/discounted lines that are not new-user offers.
4. **Price the props.**
   - `python3 -m nfl_agent props --top 60` (all games, Wednesday markets; respects the credit budget).
     If skipped for credits, rely on step 4b and Billy Bets props.
   - 4b. `python3 -m nfl_agent ladders --min 0.62 --max 0.92 --top 80` for Kalshi rungs.
   - For each candidate leg run `form` with the DFS line. Drop legs whose recent floor is far below the
     line unless the market price is strong.
5. **Build entries** per "Entry building" in `CLAUDE.md` (core, flex, longshot, prediction-market plays,
   TNF section with halved stakes). Respect bankroll rules. Show combined hit chance and payout per entry.
6. **Fantasy side notes.** Flaim: `get_user_session`, then for each Yahoo league get the user's roster.
   Flag any starter ruled out / on bye, and at most one standout waiver pickup per league
   (`get_free_agents`). One line each, only if real.
7. **Publish.**
   - Write `reports/{Y}-week{W:02d}.md` with: headline picks table, entries, TNF section, "where the money
     is" (Kalshi/Polymarket volume + line moves), key injuries/weather, last week's scorecard, fantasy
     notes, and the Billy Bets attribution/disclosure if used. End with "Lines move; confirm in-app.
     No pick is guaranteed."
   - Create a Google Doc in the Sports bets folder (parentId `1kB--GSqigM1ag_1WEkh1cTyC9tHBfbbi`) titled
     `NFL Week {W} Picks ({Mon D})` with the same markdown (`textContent`, `contentMimeType`
     `text/markdown`). Keep its link.
   - Save every recommended leg to the ledger: write a JSON list (fields as in `nfl_agent/ledger.py`
     FIELDS; `entry` = entry name, `entry_type` = power/flex/longshot/kalshi/polymarket, `tnf` = 1/0,
     `est_hit` = your probability) and run `python3 -m nfl_agent add-picks <file>`.
8. **Baseline for alerts.** `python3 -m nfl_agent monitor --week W --no-lines --label wed`
   (lines were already pulled by `slate`; this stores injuries/markets/weather as the baseline).
9. **Text the user** (`python3 -m nfl_agent text "..."`): about 400 chars max, e.g.
   `NFL Wk10 picks ready. CORE $10: A o4.5 rec + B o54.5 rush (est 44%, 3x). FLEX $5: ... TNF: ... Full report: <drive link>`.
   If the result status is not `sent`, put the same text in your final message so the scheduled-task
   push notification carries it.
10. **Commit + push** data/, memory/, reports/: `git add -A && git commit -m "Week W picks + Week L grading" && git push origin HEAD`.
