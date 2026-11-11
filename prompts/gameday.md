# Game-day check (about 75-90 min before kickoffs: Thu/Mon ~6:47pm, Sun ~11:47am, ~2:47pm, ~6:47pm ET)

Follow `CLAUDE.md`. Goal: inactives and last-minute changes for games starting in the next ~2 hours.

1. `git pull --rebase`; `python3 -m nfl_agent status` -> week W.
2. `python3 -m nfl_agent monitor --week W --no-lines --label gameday` (free; injuries, Kalshi, weather).
   Add lines (drop `--no-lines`) only on Sunday 11:47am.
3. WebSearch "<team> inactives" for each game kicking off in the next ~2.5 hours, plus weather updates
   for those outdoor games.
4. Compare with this week's open picks in `memory/picks.csv`:
   - Pick player inactive or limited -> **urgent** text with a replacement leg.
   - Inactive star creates a clear edge for the games about to start -> text "NEW EDGE" with 1-2 legs.
   - Sunday 11:47am only: Flaim check of both Yahoo lineups. If a starter is inactive/out, add one line
     to the text ("Fantasy: bench X in End Zone Bound").
5. Thursday/Sunday-night/Monday-night: if the user's picks include this game, a short "good luck" isn't
   needed; text only on changes.
6. If nothing changed, do not text. Commit + push snapshots:
   `git add -A && git commit -m "Gameday check W" && git push origin HEAD`.
