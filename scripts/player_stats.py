#!/usr/bin/env python3
"""Player production, usage and rest-of-season schedule from ESPN's public API,
scored with BOTH leagues' rules.

  python3 scripts/player_stats.py "Brian Thomas Jr." "Drake London" ...
  python3 scripts/player_stats.py --json "George Pickens"
  python3 scripts/player_stats.py --defense          # points allowed per game, all teams

For each player: team, position, games played, fantasy points per game in Dirty South
(full PPR + yardage bonuses) and End Zone Bound (half PPR, QB completions/sacks),
last-3-game average, usage (targets / carries / pass attempts per game), weekly lines,
and remaining opponents with how many points each defense allows (fantasy playoffs are
weeks 15-17).

Approximations: 2-pt conversions, return yards and End Zone Bound's 40+ yard TD bonus
aren't in ESPN's game logs, so they're left out. Treat numbers as within ~1-2 points.
"""
import json
import sys
import urllib.parse
import urllib.request
from functools import lru_cache

WEB = "https://site.web.api.espn.com/apis/common/v3"
SITE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
PLAYOFF_WEEKS = {15, 16, 17}
TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB",
         "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA", "MIN", "NE", "NO", "NYG",
         "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WSH"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return 0.0


def find_player(name):
    q = urllib.parse.quote(name)
    items = get(f"{WEB}/search?query={q}&limit=10&type=player").get("items", [])
    items = [i for i in items if i.get("league") == "nfl"]
    if not items:
        return None
    exact = [i for i in items if i.get("displayName", "").lower() == name.lower()]
    return (exact or items)[0]["id"]


def score(s):
    """s: dict of ESPN stat name -> float for one game. Returns (dirty_south, end_zone_bound)."""
    rec, ry, rtd = s.get("receptions", 0), s.get("receivingYards", 0), s.get("receivingTouchdowns", 0)
    ru, rtd2 = s.get("rushingYards", 0), s.get("rushingTouchdowns", 0)
    py, ptd, ints = s.get("passingYards", 0), s.get("passingTouchdowns", 0), s.get("interceptions", 0)
    cmp_, att, sacks = s.get("completions", 0), s.get("passingAttempts", 0), s.get("sacks", 0)
    fl = s.get("fumblesLost", 0)
    base = 0.1 * (ry + ru) + 6 * (rtd + rtd2) + 0.04 * py + 6 * ptd - 2 * ints - 2 * fl
    dsl = base + rec
    dsl += (5 if ru >= 125 else 0) + (2 if ru >= 150 else 0) + (5 if ru >= 175 else 0)
    dsl += (5 if ry >= 125 else 0) + (2 if ry >= 150 else 0) + (5 if ry >= 200 else 0)
    dsl += (3 if py >= 350 else 0) + (5 if py >= 400 else 0)
    ezb = base + 0.5 * rec + 0.5 * cmp_ - 0.5 * (att - cmp_) - sacks
    ezb += (3 if py >= 300 else 0) + (3 if ru >= 100 else 0) + (3 if ry >= 100 else 0)
    return round(dsl, 1), round(ezb, 1)


@lru_cache(maxsize=None)
def schedule(team):
    return get(f"{SITE}/teams/{team.lower()}/schedule").get("events", [])


@lru_cache(maxsize=None)
def defense_table():
    """Points allowed per game by each defense, from completed regular-season games."""
    out = {}
    for t in TEAMS:
        pa, g = 0, 0
        for e in schedule(t):
            comp = e["competitions"][0]
            scores = {}
            for c in comp["competitors"]:
                sc = c.get("score")
                val = sc.get("value") if isinstance(sc, dict) else sc
                scores[c["team"]["abbreviation"]] = val
            if None in scores.values() or len(scores) != 2:
                continue
            opp = [k for k in scores if k != t]
            if opp:
                pa += num(scores[opp[0]])
                g += 1
        out[t] = round(pa / g, 1) if g else None
    ranked = sorted((v, k) for k, v in out.items() if v is not None)
    rank = {k: i + 1 for i, (v, k) in enumerate(ranked)}  # 1 = stingiest
    return out, rank


def remaining(team, from_week):
    pa, rank = defense_table()
    rows = []
    for e in schedule(team):
        wk = e.get("week", {}).get("number")
        if wk is None or wk < from_week or wk > 17:
            continue
        comp = e["competitions"][0]
        opp = [c["team"]["abbreviation"] for c in comp["competitors"] if c["team"]["abbreviation"] != team]
        home = any(c["team"]["abbreviation"] == team and c.get("homeAway") == "home" for c in comp["competitors"])
        o = opp[0] if opp else "?"
        rows.append({"week": wk, "opp": ("vs " if home else "@ ") + o,
                     "oppPtsAllowed": pa.get(o), "oppRank": rank.get(o)})
    return rows


def player(name, current_week):
    pid = find_player(name)
    if not pid:
        return {"name": name, "error": "not found on ESPN"}
    info = get(f"{WEB}/sports/football/nfl/athletes/{pid}")["athlete"]
    team = info.get("team", {}).get("abbreviation", "")
    pos = info.get("position", {}).get("abbreviation", "")
    gl = get(f"{WEB}/sports/football/nfl/athletes/{pid}/gamelog")
    names, events = gl.get("names", []), gl.get("events", {})
    games = []
    for st in gl.get("seasonTypes", []):
        if "Regular" not in st.get("displayName", ""):
            continue
        for cat in st.get("categories", []):
            for ev in cat.get("events", []):
                s = {n: num(v) for n, v in zip(names, ev.get("stats", []))}
                meta = events.get(ev.get("eventId"), {})
                d, z = score(s)
                games.append({"week": meta.get("week"), "opp": meta.get("opponent", {}).get("abbreviation"),
                              "dsl": d, "ezb": z, "tgt": s.get("receivingTargets", 0),
                              "rec": s.get("receptions", 0), "car": s.get("rushingAttempts", 0),
                              "att": s.get("passingAttempts", 0),
                              "yds": s.get("receivingYards", 0) + s.get("rushingYards", 0) + s.get("passingYards", 0)})
    games.sort(key=lambda g: g["week"] or 0)
    n = len(games) or 1
    avg = lambda k, gs: round(sum(g[k] for g in gs) / (len(gs) or 1), 1)
    last3 = games[-3:]
    inj = info.get("injuries") or []
    return {
        "name": info.get("displayName", name), "team": team, "pos": pos, "games": len(games),
        "injury": inj[0].get("status") if inj else None,
        "dsl_ppg": avg("dsl", games), "ezb_ppg": avg("ezb", games),
        "dsl_last3": avg("dsl", last3), "ezb_last3": avg("ezb", last3),
        "tgt_pg": avg("tgt", games), "car_pg": avg("car", games), "att_pg": avg("att", games),
        "dsl_10plus_games": sum(1 for g in games if g["dsl"] >= 10),
        "weekly": games,
        "remaining": remaining(team, current_week) if team else [],
    }


def current_week():
    try:
        return get(f"{SITE}/scoreboard")["week"]["number"]
    except Exception:
        return 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    wk = current_week()
    if "--defense" in sys.argv:
        pa, rank = defense_table()
        for t, r in sorted(rank.items(), key=lambda x: x[1]):
            print(f"{r:2d}. {t:4s} {pa[t]} pts allowed/game")
        return
    out = [player(a, wk) for a in args]
    if "--json" in sys.argv:
        print(json.dumps(out, indent=1))
        return
    for p in out:
        if "error" in p:
            print(f"\n{p['name']}: {p['error']}")
            continue
        print(f"\n{p['name']} ({p['pos']}, {p['team']}){'  injury: ' + p['injury'] if p['injury'] else ''}")
        print(f"  {p['games']} games | PPG Dirty South {p['dsl_ppg']} (last 3: {p['dsl_last3']}) | "
              f"End Zone Bound {p['ezb_ppg']} (last 3: {p['ezb_last3']})")
        print(f"  usage/game: {p['tgt_pg']} targets, {p['car_pg']} carries, {p['att_pg']} pass att | "
              f"10+ pt games (DS scoring): {p['dsl_10plus_games']}")
        print("  weekly DS/EZB: " + ", ".join(f"W{g['week']} {g['dsl']}/{g['ezb']}" for g in p["weekly"]))
        rem = p["remaining"]
        if rem:
            print("  rest of season (opp pts allowed/gm, rank 1=toughest): " + ", ".join(
                f"W{r['week']}{'*' if r['week'] in PLAYOFF_WEEKS else ''} {r['opp']} ({r['oppPtsAllowed']}, #{r['oppRank']})"
                for r in rem))
    print("\n* = fantasy playoff week")


if __name__ == "__main__":
    main()
