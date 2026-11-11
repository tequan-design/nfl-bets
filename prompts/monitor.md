# Midweek monitor (Tue/Thu/Fri/Sat ~5:47pm ET)

Follow `CLAUDE.md`. Goal: catch abnormal changes that affect this week's games or picks, and text only
if something matters.

1. `git pull --rebase`; `python3 -m nfl_agent status` -> upcoming/current week W.
2. `python3 -m nfl_agent monitor --week W --label mon` (pulls lines: 3 credits). On Saturday also run
   `python3 -m nfl_agent props --days 2 --markets player_receptions,player_rush_yds --top 40` to refresh
   Sunday prop prices (skip automatically if credits are low).
3. WebSearch for news since the last run: final injury designations (Friday), trades, signings, IR,
   QB changes, suspensions, weather forecasts for outdoor games, coaching news. Read `memory/picks.csv`
   rows for week W with no result: these are the user's live picks.
4. Decide what matters:
   - Anything that breaks one of this week's picks -> text with a concrete swap (use `props`/`ladders`
     output or `form` to pick a replacement leg).
   - A new edge created by news (e.g. WR1 out -> WR2 receptions over; QB out -> opposing defense / unders)
     -> text "NEW EDGE".
   - Big money/line move against the public side -> text only if it changes a recommendation.
   - Otherwise do not text. Just record a one-line note in the latest `reports/` file under "Updates".
5. If you change a recommendation, update `memory/picks.csv` (set the old leg's notes to "swapped",
   result `void`; add the new leg with add-picks).
6. Text with `python3 -m nfl_agent text "..."` (add `--urgent` only for an Out/inactive on a live pick
   within 3 hours of kickoff). If not `sent`, include the text in your final message.
7. Commit + push: `git add -A && git commit -m "Monitor W: <summary>" && git push origin HEAD`.
