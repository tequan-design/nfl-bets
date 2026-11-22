#!/usr/bin/env python3
"""NFL lines -> implied team totals, via The Odds API.

The cloud proxy injects the API key, so no key is needed here.

Usage:
  python3 scripts/odds.py --week          # remaining games this NFL week (to Tue 6am ET)
  python3 scripts/odds.py --week --next   # next NFL week's games (for the Tuesday run)
  python3 scripts/odds.py --json          # same, as JSON
  python3 scripts/odds.py --props EVENT_ID [--markets player_reception_yds,...]
  python3 scripts/odds.py --byes [--next] # teams with no remaining game that week

Each /odds call costs 2 credits (2 markets x 1 region); props cost more per event.
The remaining quota is printed to stderr.
"""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
ET = ZoneInfo("America/New_York")
ALL_TEAMS = [
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders",
]


def get(path, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    with urllib.request.urlopen(f"{BASE}/{path}?{q}", timeout=30) as r:
        left = r.headers.get("x-requests-remaining")
        print(f"[odds-api] credits remaining: {left}", file=sys.stderr)
        return json.load(r)


def consensus(game, key):
    """Median line across bookmakers for spreads/totals."""
    vals = {}
    for b in game.get("bookmakers", []):
        for m in b["markets"]:
            if m["key"] != key:
                continue
            for o in m["outcomes"]:
                vals.setdefault(o["name"], []).append(o.get("point"))
    def med(xs):
        xs = sorted(x for x in xs if x is not None)
        return xs[len(xs) // 2] if xs else None
    return {k: med(v) for k, v in vals.items()}


def week_end(now):
    """NFL week boundary: the next Tuesday 6:00am ET (today counts if before 6am Tue)."""
    local = now.astimezone(ET)
    days = (1 - local.weekday()) % 7  # Tuesday = 1
    end = (local + timedelta(days=days)).replace(hour=6, minute=0, second=0, microsecond=0)
    if end <= local:
        end += timedelta(days=7)
    return end


def week_games(next_week=False):
    data = get("odds", regions="us", markets="spreads,totals", oddsFormat="american")
    now = datetime.now(timezone.utc)
    end = week_end(now)
    start = now
    if next_week:
        start, end = end, end + timedelta(days=7)
    out = []
    for g in sorted(data, key=lambda g: g["commence_time"]):
        t = datetime.fromisoformat(g["commence_time"].replace("Z", "+00:00"))
        if t > end or (next_week and t < start):
            continue
        h, a = g["home_team"], g["away_team"]
        sp, tot = consensus(g, "spreads"), consensus(g, "totals").get("Over")
        row = {"id": g["id"], "kickoff_et": t.astimezone(ET).strftime("%a %m/%d %I:%M%p"),
               "away": a, "home": h, "total": tot,
               "home_spread": sp.get(h), "started": t < now}
        if tot is not None and sp.get(h) is not None:
            row["home_implied"] = round(tot / 2 - sp[h] / 2, 1)
            row["away_implied"] = round(tot / 2 + sp[h] / 2, 1)
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--byes", action="store_true")
    ap.add_argument("--next", action="store_true", help="next NFL week instead of the current one")
    ap.add_argument("--props")
    ap.add_argument("--markets", default="player_pass_yds,player_rush_yds,player_reception_yds,player_receptions,player_anytime_td")
    a = ap.parse_args()

    if a.props:
        ev = get(f"events/{a.props}/odds", regions="us", markets=a.markets, oddsFormat="american")
        for b in ev.get("bookmakers", [])[:1]:
            for m in b["markets"]:
                print(f"\n{m['key']} ({b['title']})")
                for o in m["outcomes"]:
                    print(f"  {o.get('description','')} {o['name']} {o.get('point','')} {o['price']}")
        return

    games = week_games(next_week=a.next)
    if a.json:
        print(json.dumps(games, indent=1))
        return
    if a.byes:
        playing = {g["away"] for g in games} | {g["home"] for g in games}
        print("No remaining game this NFL week (bye, or already played):")
        print(", ".join(t for t in ALL_TEAMS if t not in playing))
        return
    for g in games:
        if "home_implied" in g:
            print(f"{g['kickoff_et']}  {g['away']} ({g['away_implied']}) @ {g['home']} ({g['home_implied']})"
                  f"  spread {g['home_spread']:+}  total {g['total']}  id={g['id']}")
        else:
            print(f"{g['kickoff_et']}  {g['away']} @ {g['home']}  (no lines yet)  id={g['id']}")


if __name__ == "__main__":
    main()
