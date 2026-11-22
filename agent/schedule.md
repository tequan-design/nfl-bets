# Run schedule (America/New_York)

| Run | When | Playbook | Why then |
|---|---|---|---|
| Waivers | Tue 9:13 PM | `waivers.md` | After MNF; before End Zone Bound waivers process Wed ~4:45am |
| TNF check | Thu 3:47 PM | `tnf.md` | Before the 8:15pm lock, after Thursday injury news |
| Week preview | Sat 1:23 PM | `preview.md` | After Friday's final injury reports |
| Inactives | Sun 11:45 AM | `inactives.md` | Inactives for 1pm games drop ~11:30am |
| Transaction monitor | Daily 9:37 AM, 2:37 PM, 8:37 PM | `transactions.md` | See analysis below |
| Early-game check (one-off) | Wed 11/25 3:47 PM | `tnf.md` | Thanksgiving week: GB @ LAR Wed 8pm, Thu 1:00/4:30/8:20pm games |

## Transaction timing analysis (Oct 27 – Nov 21, 2026; 202 moves)

Busiest hours (ET), both leagues combined:
- **4:00–5:00 AM**: 27 moves; End Zone Bound's weekly waiver run (Wed ~4:45am).
- **5:00–8:00 PM**: 59 moves, the main window (after-work activity, both leagues).
- **12:00–2:00 PM**: 19 moves (lunch).
- **8:00 AM**: 10 moves.

Busiest days: Tue (43), Wed (45), Thu (37). Dirty South peaks Tuesday (no waiver
delay, so managers react right after MNF); End Zone Bound peaks Wednesday (waiver run).

Check times sit 30–90 minutes after each cluster and while Quan is awake:
- 9:37 AM catches the overnight waiver run plus the 8am bump.
- 2:37 PM catches the lunch window.
- 8:37 PM catches the 5–8pm peak.

The monitor keeps a running hour histogram (`data/agent/state` → `txhours`) and suggests
new times monthly if the pattern shifts. Re-run the analysis by hand with
`scripts/tx_timing.py`.
