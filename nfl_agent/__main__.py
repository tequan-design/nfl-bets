"""Command line for the NFL picks agent.  Run `python -m nfl_agent -h`."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta

from . import alerts, espn, ledger, markets, monitor, odds, weather
from .common import DATA, fmt_et, load_json, now_et, profile, save_json


def out(obj):
    print(json.dumps(obj, indent=1, default=str))


def cmd_status(a):
    season, week, state = espn.current_week()
    out({"now_et": now_et().strftime("%a %Y-%m-%d %H:%M"), "season": season, "espn_week": week,
         "week_state": state, "odds_api_remaining": odds.remaining(),
         "hint": "If week_state is 'complete', ingest/grade that week and preview week+1."})


def cmd_ingest(a):
    out(espn.ingest_week(a.season, a.week))


def cmd_slate(a):
    gs = espn.games(a.week)
    lines = {}
    if not a.no_lines:
        for l in odds.game_lines():
            lines[(l["home"].split()[-1], l["away"].split()[-1])] = l
    start = min(g["date"] for g in gs)[:10] + "T00:00:00Z"
    end = max(g["date"] for g in gs)[:10] + "T23:59:59Z"
    poly = {}
    try:
        for p in markets.polymarket_games(start, end):
            poly[p["title"]] = p
    except Exception as e:
        print(f"polymarket error: {e}", file=sys.stderr)
    kal = {}
    try:
        for k in markets.kalshi_games():
            kal.setdefault(k["event"], []).append(k)
    except Exception as e:
        print(f"kalshi error: {e}", file=sys.stderr)
    rows = []
    for g in gs:
        line = next((l for (h, aw), l in lines.items()
                     if g["home"] and h.lower() in g["name"].lower() and aw.lower() in g["name"].lower()), None)
        kal_rows = kal.get(kalshi_event_ticker(g), [])
        poly_row = next((p for t, p in poly.items()
                         if g["name"].split()[-1] in t and g["name"].split(" at ")[0].split()[-1] in t), None)
        w = weather.kickoff_weather(g) if a.weather and g["state"] == "pre" else None
        rows.append({
            "game": g["short"], "kick": fmt_et(g["date"]), "tnf": now_tnf(g), "venue": g["venue"],
            "indoor": g["indoor"], "records": f"{g['away']} {g['away_record']} / {g['home']} {g['home_record']}",
            "home_spread": line and line["home_spread"], "total": line and line["total"],
            "home_win_prob_books": line and line["home_win_prob"],
            "kalshi": {k["team"]: {"p": k["prob"], "vol": k["volume"], "vol24h": k["volume_24h"]} for k in kal_rows},
            "polymarket": poly_row and {"prices": poly_row["prices"], "volume": poly_row["volume"]},
            "weather": w and w["summary"], "state": g["detail"],
        })
    save_json(DATA / f"slate_week{a.week}.json", rows)
    out(rows)


KALSHI_CODE = {"WSH": "WAS", "JAX": "JAC"}


def kalshi_event_ticker(g):
    from .common import parse_time, ET
    d = parse_time(g["date"]).astimezone(ET).strftime("%y%b%d").upper()
    c = lambda t: KALSHI_CODE.get(t, t)
    return f"KXNFLGAME-{d}{c(g['away'])}{c(g['home'])}"


def now_tnf(g):
    from .common import parse_time, ET
    return parse_time(g["date"]).astimezone(ET).weekday() == 3


def cmd_props(a):
    cfg = profile()["odds_api"]
    rem = odds.remaining()
    mkts = a.markets.split(",") if a.markets else cfg["wednesday_prop_markets"]
    evs = odds.events()
    if a.only:
        wanted = [s.lower() for s in a.only.split(",")]
        evs = [e for e in evs if any(w in (e["home_team"] + " " + e["away_team"]).lower() for w in wanted)]
    if a.days:
        from datetime import datetime, timezone
        cutoff = datetime.now(timezone.utc) + timedelta(days=a.days)
        evs = [e for e in evs if datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00")) < cutoff]
    cost = len(evs) * len(mkts)
    rem = odds.remaining()
    if rem is not None and rem - cost < cfg["min_remaining_for_props"] and not a.force:
        out({"skipped": True, "reason": f"Odds API credits low ({rem} left, this pull costs ~{cost}). "
             "Use Kalshi ladders / Billy Bets props instead, or pass --force."})
        return
    results = []
    for e in evs:
        payload = odds.event_props(e["id"], mkts)
        for r in odds.analyze_props(payload):
            r["game"] = f"{e['away_team']} @ {e['home_team']}"
            r["kick"] = fmt_et(e["commence_time"])
            results.append(r)
    results.sort(key=lambda r: -r["est_hit"])
    save_json(DATA / f"props_{now_et():%Y%m%d_%H%M}.json", results)
    out({"credits_remaining": odds.remaining(), "count": len(results), "top": results[: a.top]})


def cmd_ladders(a):
    rows = markets.kalshi_prop_ladders(a.series.split(",") if a.series else None, min_prob=a.min)
    rows = [r for r in rows if r["prob"] <= a.max]
    rows.sort(key=lambda r: (-r["prob"], -(r["volume"] or 0)))
    save_json(DATA / "kalshi_ladders_latest.json", rows)
    out({"count": len(rows), "rows": rows[: a.top]})


def cmd_form(a):
    out(ledger.form(a.player, a.stat, a.line, a.last))


def cmd_defense(a):
    out(ledger.defense_table())


def cmd_injuries(a):
    inj = espn.injuries()
    if a.team:
        inj = [i for i in inj if i["team"] in a.team.upper().split(",")]
    out(inj)


def cmd_weather(a):
    out([weather.kickoff_weather(g) for g in espn.games(a.week) if g["state"] == "pre"])


def cmd_monitor(a):
    out(monitor.run(a.week, with_lines=not a.no_lines, label=a.label))


def cmd_grade(a):
    out(ledger.grade(a.season, a.week))


def cmd_scorecard(a):
    out(ledger.scorecard())


def cmd_add_picks(a):
    rows = json.load(open(a.file))
    out({"added": ledger.add_picks(rows)})


def cmd_text(a):
    out(alerts.send(a.message, urgent=a.urgent))


def main(argv=None):
    p = argparse.ArgumentParser(prog="nfl_agent")
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("status"); s.set_defaults(f=cmd_status)
    s = sp.add_parser("ingest"); s.add_argument("--season", type=int, required=True); s.add_argument("--week", type=int, required=True); s.set_defaults(f=cmd_ingest)
    s = sp.add_parser("slate"); s.add_argument("--week", type=int, required=True); s.add_argument("--no-lines", action="store_true"); s.add_argument("--weather", action="store_true"); s.set_defaults(f=cmd_slate)
    s = sp.add_parser("props"); s.add_argument("--markets"); s.add_argument("--only", help="comma list of team-name fragments"); s.add_argument("--days", type=float); s.add_argument("--top", type=int, default=40); s.add_argument("--force", action="store_true"); s.set_defaults(f=cmd_props)
    s = sp.add_parser("ladders"); s.add_argument("--series"); s.add_argument("--min", type=float, default=0.6); s.add_argument("--max", type=float, default=0.95); s.add_argument("--top", type=int, default=60); s.set_defaults(f=cmd_ladders)
    s = sp.add_parser("form"); s.add_argument("player"); s.add_argument("stat"); s.add_argument("line", type=float, nargs="?"); s.add_argument("--last", type=int, default=6); s.set_defaults(f=cmd_form)
    s = sp.add_parser("defense"); s.set_defaults(f=cmd_defense)
    s = sp.add_parser("injuries"); s.add_argument("--team"); s.set_defaults(f=cmd_injuries)
    s = sp.add_parser("weather"); s.add_argument("--week", type=int, required=True); s.set_defaults(f=cmd_weather)
    s = sp.add_parser("monitor"); s.add_argument("--week", type=int, required=True); s.add_argument("--no-lines", action="store_true"); s.add_argument("--label", default="check"); s.set_defaults(f=cmd_monitor)
    s = sp.add_parser("grade"); s.add_argument("--season", type=int, required=True); s.add_argument("--week", type=int, required=True); s.set_defaults(f=cmd_grade)
    s = sp.add_parser("scorecard"); s.set_defaults(f=cmd_scorecard)
    s = sp.add_parser("add-picks"); s.add_argument("file"); s.set_defaults(f=cmd_add_picks)
    s = sp.add_parser("text"); s.add_argument("message"); s.add_argument("--urgent", action="store_true"); s.set_defaults(f=cmd_text)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
