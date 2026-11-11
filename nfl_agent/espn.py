"""ESPN public site API: schedule, box scores, injuries, team results."""
from __future__ import annotations

import csv
from pathlib import Path

from .common import DATA, get_json, norm_name

SITE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"


def scoreboard(week: int | None = None, seasontype: int = 2, year: int | None = None) -> dict:
    params = {}
    if week:
        params.update(week=week, seasontype=seasontype)
    if year:
        params["dates"] = year
    return get_json(f"{SITE}/scoreboard", params)


def current_week() -> tuple[int, int, str]:
    """(season year, week number, state) for ESPN's current week.
    state is 'complete' if every game is final, else 'in_progress'/'upcoming'."""
    sb = scoreboard()
    states = {e["competitions"][0]["status"]["type"]["state"] for e in sb["events"]}
    state = "complete" if states == {"post"} else ("upcoming" if states == {"pre"} else "in_progress")
    return sb["season"]["year"], sb["week"]["number"], state


def games(week: int) -> list[dict]:
    """Flattened game list for a regular-season week."""
    sb = scoreboard(week)
    out = []
    for e in sb["events"]:
        c = e["competitions"][0]
        teams = {t["homeAway"]: t for t in c["competitors"]}
        venue = c.get("venue", {})
        out.append({
            "id": e["id"],
            "name": e["name"],
            "short": e["shortName"],
            "date": e["date"],
            "state": c["status"]["type"]["state"],
            "detail": c["status"]["type"]["shortDetail"],
            "home": teams["home"]["team"]["abbreviation"],
            "away": teams["away"]["team"]["abbreviation"],
            "home_score": teams["home"].get("score"),
            "away_score": teams["away"].get("score"),
            "home_record": (teams["home"].get("records") or [{}])[0].get("summary"),
            "away_record": (teams["away"].get("records") or [{}])[0].get("summary"),
            "venue": venue.get("fullName"),
            "city": (venue.get("address") or {}).get("city"),
            "indoor": venue.get("indoor"),
            "neutral": c.get("neutralSite", False),
            "broadcast": c.get("broadcast"),
        })
    return out


def summary(event_id: str) -> dict:
    return get_json(f"{SITE}/summary", {"event": event_id})


def injuries() -> list[dict]:
    d = get_json(f"{SITE}/injuries")
    out = []
    for team in d.get("injuries", []):
        for i in team.get("injuries", []):
            a = i.get("athlete", {})
            status = i.get("status")
            if status == "Active":
                continue
            out.append({
                "team": (a.get("team") or {}).get("abbreviation") or team.get("displayName"),
                "player": a.get("displayName"),
                "pos": (a.get("position") or {}).get("abbreviation"),
                "status": status,
                "detail": i.get("shortComment") or "",
                "date": i.get("date"),
            })
    return out


# ---------- box scores -> memory ----------
STAT_MAP = {
    "passing": {"C/ATT": ("pass_comp", "pass_att"), "YDS": "pass_yds", "TD": "pass_td", "INT": "pass_int"},
    "rushing": {"CAR": "rush_att", "YDS": "rush_yds", "TD": "rush_td", "LONG": "rush_long"},
    "receiving": {"REC": "rec", "YDS": "rec_yds", "TD": "rec_td", "TGTS": "targets", "LONG": "rec_long"},
}
PLAYER_FIELDS = ["season", "week", "game_id", "date", "team", "opp", "home", "player", "player_id",
                 "pass_comp", "pass_att", "pass_yds", "pass_td", "pass_int",
                 "rush_att", "rush_yds", "rush_td", "rush_long",
                 "rec", "rec_yds", "rec_td", "targets", "rec_long", "tnf"]
TEAM_FIELDS = ["season", "week", "game_id", "date", "team", "opp", "home", "points", "opp_points",
               "total_yds", "pass_yds", "rush_yds", "turnovers", "tnf", "closing_spread", "closing_total", "result"]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def box_score_rows(game: dict, season: int, week: int) -> tuple[list[dict], list[dict]]:
    s = summary(game["id"])
    from .common import parse_time, ET
    kick = parse_time(game["date"]).astimezone(ET)
    tnf = kick.weekday() == 3
    players: dict[tuple, dict] = {}
    for team_block in s.get("boxscore", {}).get("players", []):
        abbr = team_block["team"]["abbreviation"]
        opp = game["away"] if abbr == game["home"] else game["home"]
        for cat in team_block.get("statistics", []):
            mapping = STAT_MAP.get(cat["name"])
            if not mapping:
                continue
            labels = cat.get("labels", [])
            for a in cat.get("athletes", []):
                key = (abbr, a["athlete"]["id"])
                row = players.setdefault(key, {
                    "season": season, "week": week, "game_id": game["id"], "date": game["date"][:10],
                    "team": abbr, "opp": opp, "home": int(abbr == game["home"]),
                    "player": a["athlete"]["displayName"], "player_id": a["athlete"]["id"], "tnf": int(tnf)})
                for label, val in zip(labels, a.get("stats", [])):
                    dest = mapping.get(label)
                    if dest is None:
                        continue
                    if isinstance(dest, tuple):
                        parts = str(val).split("/")
                        if len(parts) == 2:
                            row[dest[0]], row[dest[1]] = _num(parts[0]), _num(parts[1])
                    else:
                        row[dest] = _num(val)
    # team rows
    pc = (s.get("pickcenter") or [{}])[0]
    team_rows = []
    tstats = {t["team"]["abbreviation"]: {x["name"]: x.get("displayValue") for x in t.get("statistics", [])}
              for t in s.get("boxscore", {}).get("teams", [])}
    for abbr, opp in ((game["home"], game["away"]), (game["away"], game["home"])):
        pts = _num(game["home_score"] if abbr == game["home"] else game["away_score"])
        opp_pts = _num(game["away_score"] if abbr == game["home"] else game["home_score"])
        st = tstats.get(abbr, {})
        team_rows.append({
            "season": season, "week": week, "game_id": game["id"], "date": game["date"][:10],
            "team": abbr, "opp": opp, "home": int(abbr == game["home"]),
            "points": pts, "opp_points": opp_pts,
            "total_yds": _num(st.get("totalYards")), "pass_yds": _num(st.get("netPassingYards")),
            "rush_yds": _num(st.get("rushingYards")), "turnovers": _num(st.get("turnovers")),
            "tnf": int(tnf), "closing_spread": pc.get("details"), "closing_total": pc.get("overUnder"),
            "result": ("W" if pts > opp_pts else "L" if pts < opp_pts else "T") if pts is not None and opp_pts is not None else "",
        })
    return list(players.values()), team_rows


def _append_csv(path: Path, fields: list[str], rows: list[dict], key_fields: tuple) -> int:
    existing = set()
    if path.exists():
        with path.open() as f:
            for r in csv.DictReader(f):
                existing.add(tuple(r[k] for k in key_fields))
    new = [r for r in rows if tuple(str(r.get(k, "")) for k in key_fields) not in existing]
    write_header = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            w.writeheader()
        for r in new:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return len(new)


def ingest_week(season: int, week: int) -> dict:
    """Pull every final game of a week into data/player_games.csv and data/team_games.csv."""
    added_p = added_t = skipped = 0
    for g in games(week):
        if g["state"] != "post":
            skipped += 1
            continue
        prow, trow = box_score_rows(g, season, week)
        added_p += _append_csv(DATA / "player_games.csv", PLAYER_FIELDS, prow, ("game_id", "player_id"))
        added_t += _append_csv(DATA / "team_games.csv", TEAM_FIELDS, trow, ("game_id", "team"))
    return {"week": week, "player_rows_added": added_p, "team_rows_added": added_t, "games_not_final": skipped}


def load_player_games() -> list[dict]:
    p = DATA / "player_games.csv"
    if not p.exists():
        return []
    with p.open() as f:
        return list(csv.DictReader(f))


def player_log(name: str, rows: list[dict] | None = None) -> list[dict]:
    rows = rows if rows is not None else load_player_games()
    n = norm_name(name)
    return sorted([r for r in rows if norm_name(r["player"]) == n], key=lambda r: (int(r["season"]), int(r["week"])))
