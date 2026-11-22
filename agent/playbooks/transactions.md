# Playbook: league transaction monitor

Fires 3× daily (see `agent/schedule.md`). Its job: notice what other managers did since
the last check and tell Quan only when it matters. **Stay quiet otherwise.**

## Steps
1. Read `data/agent/state` doc `cursor` (last seen transaction timestamp per league).
   If missing, use "24 hours ago".
2. Flaim `get_transactions` for each league (default recent window, count 50). Keep rows
   with `timestamp` > cursor.
   Flaim's `date` field is the **UTC** date. Convert `timestamp` (ms) to Eastern time with
   `python3 -c "from datetime import datetime;from zoneinfo import ZoneInfo;print(datetime.fromtimestamp(MS/1000,ZoneInfo('America/New_York')))"`
   and never guess times by hand.
3. For each new move, classify:
   - **act** — a player who would start for Quan, or is a top-36 RB/WR / top-12 QB/TE
     rest of season, was **dropped** in Dirty South (instant free agent: tell Quan to grab
     him now and name the drop), or dropped in End Zone Bound (on waivers until it
     processes: tell Quan to put in a claim).
   - **heads-up** — this week's opponent changed their lineup/roster in a way that shifts
     the matchup; a rival in the playoff race made a big add; a trade involving players
     on Quan's teams' schedule; a handcuff to one of Quan's RBs was picked up.
   - **info** — everything else.
   Verify on the web before calling something act (why was he dropped? injured?).
4. Update the hour histogram in `data/agent/state` doc `txhours` with each new
   transaction's hour in America/New_York.
5. Save the newest timestamp per league to `cursor`.

## Write to the dashboard
- `data/agent/alerts`: one row per **act** or **heads-up** move (skip plain info unless
  fewer than 3 alerts were written today; then include info rows so the feed isn't empty).
  Delete alerts beyond the newest 40.
- `data/agent/moves`: add a priority-1 item for each **act**.
- `data/agent/runs`: one row only if something act/heads-up happened.

## Re-tuning the schedule (first run of each month)
Look at `txhours`. If the busiest windows have moved by 2+ hours from the ones in
`agent/schedule.md`, say so in the summary and propose new check times 30–60 minutes
after each busy window, all between 8am and 11pm ET. Don't change the schedule yourself;
Quan approves it.

## Push summary
- Something act-level: line 1 = "Grab <player> in <league> now (dropped by <team>)" or
  "Claim <player> in End Zone Bound".
- Only heads-up: one line per item, max 3.
- Nothing relevant: exactly "No league moves that affect you." (no detail).
