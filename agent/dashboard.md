# Dashboard data store

Dashboard: **Too HOT 4 TV War Room** — https://claude.ai/artifact/HgVezfLhTTWUxuH64SmtPj

The page draws live standings and matchup scores itself (from the Flaim Fantasy
connector). Everything the agent decides goes into **saved rows** in the store, written
with the `ArtifactData` tool (`url` = the dashboard link above). Only editors (Quan, and
runs acting as Quan) can write these.

Every row carries `league`: exactly `"Dirty South"` or `"End Zone Bound"` (or `"Both"`
where noted).

## Collections

### `data/agent/moves` — the "Do this now" list
One doc per action item. Replace the whole list on each preview/inactives/waiver run:
delete docs that are done or stale, then write the new ones.
```json
{"league": "End Zone Bound", "priority": 1, "kind": "Lineup",
 "title": "Start Chase Brown over Ollie Gordon II",
 "detail": "CIN implied 30 pts vs MIA 14; Gordon faces a 16.5-pt spread.",
 "deadline": "Sun 1:00 PM ET", "confidence": "High", "updated": "2026-11-21T22:00:00-05:00"}
```
`priority`: 1 = do now, 2 = do before kickoff, 3 = consider. `kind`: Lineup | Waiver |
Drop | Trade | Injury | Watch. Doc id: `<league-slug>-<short-slug>` e.g. `ezb-start-brown`.

### `data/agent/lineup` — recommended starting lineup per league
One doc per starting slot (9 per league). Doc id `dsl-01`…`dsl-09`, `ezb-01`…`ezb-09`.
```json
{"league": "Dirty South", "order": 1, "slot": "QB", "player": "Dak Prescott",
 "nfl": "DAL", "game": "vs TEN · Sun 1:00", "teamTotal": 31.0,
 "verdict": "Start", "note": "Highest total on the slate (54.5).", "week": 11}
```
`verdict`: Start | Swap in | Check status. Use "Swap in" when the recommended player is
not where Yahoo currently has him (the note then says who goes to the bench).

### `data/agent/waivers` — pickup targets
Doc id `<league-slug>-<rank>`. Replace all on the Tuesday run.
```json
{"league": "Dirty South", "rank": 1, "player": "…", "pos": "WR", "nfl": "MIA",
 "status": "Free agent", "drop": "DeMario Douglas", "why": "…"}
```

### `data/agent/alerts` — league activity worth knowing
Doc id: the transaction's time as `YYYYMMDD-HHMM-<league-slug>`. Keep the last ~40;
delete older ones.
```json
{"at": "2026-11-20T13:44:00-05:00", "league": "Dirty South", "team": "Big B Money",
 "summary": "Added Dalton Kincaid (TE, BUF), dropped Joe Milton",
 "impact": "Opponent next week; TE upgrade for him.", "level": "info"}
```
`level`: info | heads-up | act (act = Quan should do something now, e.g. a useful player
just hit free agency in Dirty South).

### `data/agent/runs` — run log
Doc id `YYYYMMDD-HHMM-<playbook>`.
```json
{"at": "2026-11-21T22:00:00-05:00", "playbook": "preview", "summary": "First line of the push"}
```

### `data/agent/state` — agent memory between runs (not shown on the page)
Doc `cursor`: `{"Dirty South": <last seen transaction timestamp ms>, "End Zone Bound": <ms>}`.
Doc `txhours`: `{"counts": {"0": n, … "23": n}, "since": "2026-10-27"}` running histogram
of transaction hours (ET) used to re-tune the monitor schedule.

## Writing tips
- Use one `batch` call per run where possible (max 50 writes).
- Pin writes to existing docs with `if_version` (read first with `list`).
- Timestamps in ISO 8601 with the ET offset.
