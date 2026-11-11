"""Picks ledger (memory/picks.csv), grading against box scores, and player form."""
from __future__ import annotations

import csv
from collections import defaultdict
from statistics import mean, median

from .common import DATA, MEMORY, norm_name
from .espn import load_player_games

PICKS = MEMORY / "picks.csv"
FIELDS = ["season", "week", "made_at", "platform", "entry", "entry_type", "player", "team", "game", "stat",
          "line", "side", "est_hit", "stake", "multiplier", "tnf", "result", "actual", "notes"]

STATS = ["rec", "rec_yds", "rush_yds", "pass_yds", "pass_td", "pass_comp", "pass_att", "rush_att",
         "rush_rec_yds", "anytime_td", "targets", "pass_int"]


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def stat_value(row: dict, stat: str) -> float | None:
    if stat == "rush_rec_yds":
        a, b = _f(row.get("rush_yds")) or 0, _f(row.get("rec_yds")) or 0
        return a + b
    if stat == "anytime_td":
        return (_f(row.get("rush_td")) or 0) + (_f(row.get("rec_td")) or 0)
    v = _f(row.get(stat))
    if v is None and stat in STATS:
        return 0.0  # player appeared in box score but not in this category
    return v


def read_picks() -> list[dict]:
    if not PICKS.exists():
        return []
    with PICKS.open() as f:
        return list(csv.DictReader(f))


def write_picks(rows: list[dict]) -> None:
    with PICKS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def add_picks(new_rows: list[dict]) -> int:
    rows = read_picks()
    rows += [{k: r.get(k, "") for k in FIELDS} for r in new_rows]
    write_picks(rows)
    return len(new_rows)


def grade(season: int, week: int) -> dict:
    """Fill result/actual for ungraded player picks in a week using data/player_games.csv,
    and moneyline picks (stat == 'ml', player == team abbreviation) using team_games.csv."""
    games = [g for g in load_player_games() if int(g["season"]) == season and int(g["week"]) == week]
    by_name = {norm_name(g["player"]): g for g in games}
    teams = {}
    tpath = DATA / "team_games.csv"
    if tpath.exists():
        with tpath.open() as f:
            for r in csv.DictReader(f):
                if int(r["season"]) == season and int(r["week"]) == week:
                    teams[r["team"]] = r
    rows = read_picks()
    graded = 0
    for r in rows:
        if r["result"] or str(r["season"]) != str(season) or str(r["week"]) != str(week):
            continue
        if r["stat"] == "ml":
            t = teams.get(r["player"].upper())
            if t:
                r["actual"], r["result"] = t["result"], {"W": "hit", "L": "miss"}.get(t["result"], "push")
                graded += 1
            continue
        g = by_name.get(norm_name(r["player"]))
        if not g:
            continue  # player did not appear: leave for manual review (likely inactive = void)
        val = stat_value(g, r["stat"])
        line = _f(r["line"])
        if val is None or line is None:
            continue
        r["actual"] = val
        if val == line:
            r["result"] = "push"
        elif (val > line) == (r["side"].lower() in ("over", "more", "yes")):
            r["result"] = "hit"
        else:
            r["result"] = "miss"
        graded += 1
    write_picks(rows)
    return {"graded": graded, "ungraded": [r["player"] for r in rows if str(r["week"]) == str(week)
                                           and str(r["season"]) == str(season) and not r["result"]]}


def scorecard() -> dict:
    """Hit rates by stat, side, platform, TNF, and confidence band - feeds memory/lessons.md."""
    rows = [r for r in read_picks() if r["result"] in ("hit", "miss")]
    out = {}
    for key in ("stat", "side", "platform", "tnf", "entry_type"):
        agg = defaultdict(lambda: [0, 0])
        for r in rows:
            agg[r[key] or "-"][0] += r["result"] == "hit"
            agg[r[key] or "-"][1] += 1
        out[key] = {k: f"{h}/{n} ({h / n:.0%})" for k, (h, n) in sorted(agg.items())}
    bands = defaultdict(lambda: [0, 0])
    for r in rows:
        p = _f(r["est_hit"])
        if p is None:
            continue
        b = "70%+" if p >= 0.70 else "62-70%" if p >= 0.62 else "55-62%" if p >= 0.55 else "<55%"
        bands[b][0] += r["result"] == "hit"
        bands[b][1] += 1
    out["confidence_band"] = {k: f"{h}/{n} ({h / n:.0%})" for k, (h, n) in sorted(bands.items())}
    out["total"] = f"{sum(r['result'] == 'hit' for r in rows)}/{len(rows)}"
    return out


def form(player: str, stat: str, line: float | None = None, last: int = 6) -> dict:
    log = [g for g in load_player_games() if norm_name(g["player"]) == norm_name(player)]
    log.sort(key=lambda g: (int(g["season"]), int(g["week"])))
    vals = [(int(g["week"]), g["opp"], stat_value(g, stat)) for g in log]
    vals = [v for v in vals if v[2] is not None]
    recent = vals[-last:]
    res = {"player": player, "stat": stat, "games": len(vals),
           "recent": [f"W{w} vs {o}: {v:g}" for w, o, v in recent]}
    if recent:
        nums = [v for _, _, v in recent]
        res.update(avg=round(mean(nums), 1), median=median(nums), low=min(nums), high=max(nums))
        if line is not None:
            res["over_rate_recent"] = f"{sum(v > line for v in nums)}/{len(nums)}"
            allv = [v for _, _, v in vals]
            res["over_rate_season"] = f"{sum(v > line for v in allv)}/{len(allv)}"
    return res


def defense_table() -> list[dict]:
    """Yards allowed per game by each defense (from team_games.csv), with ranks (1 = stingiest)."""
    path = DATA / "team_games.csv"
    if not path.exists():
        return []
    allowed = defaultdict(lambda: {"pass": [], "rush": [], "pts": []})
    with path.open() as f:
        for r in csv.DictReader(f):
            d = allowed[r["opp"]]
            for k, col in (("pass", "pass_yds"), ("rush", "rush_yds"), ("pts", "points")):
                v = _f(r[col])
                if v is not None:
                    d[k].append(v)
    table = [{"team": t, "pass_allowed": round(mean(d["pass"]), 1) if d["pass"] else None,
              "rush_allowed": round(mean(d["rush"]), 1) if d["rush"] else None,
              "pts_allowed": round(mean(d["pts"]), 1) if d["pts"] else None, "games": len(d["pts"])}
             for t, d in allowed.items()]
    for k in ("pass_allowed", "rush_allowed", "pts_allowed"):
        for i, row in enumerate(sorted([t for t in table if t[k] is not None], key=lambda x: x[k]), 1):
            row[k + "_rank"] = i
    return sorted(table, key=lambda x: x["team"])


def usage_relevant_players(min_games: int = 2) -> set[str]:
    """Players worth alerting on: QBs with volume, RBs/WRs/TEs with real usage."""
    agg = defaultdict(list)
    for g in load_player_games():
        agg[(g["player"], g["team"])].append(g)
    keep = set()
    for (name, _), gs in agg.items():
        if len(gs) < min_games:
            continue
        att = mean(_f(g.get("pass_att")) or 0 for g in gs)
        ru = mean(_f(g.get("rush_att")) or 0 for g in gs)
        tg = mean(_f(g.get("targets")) or 0 for g in gs)
        if att >= 15 or ru >= 8 or tg >= 4.5:
            keep.add(norm_name(name))
    return keep
