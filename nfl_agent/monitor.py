"""Snapshot the week's state and diff it against the last snapshot to find
abnormal changes worth a text: line moves, injury status changes, market swings, weather."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import espn, markets, odds, weather
from .common import DATA, load_json, norm_name, profile, save_json, utcnow_iso
from .ledger import read_picks, usage_relevant_players

SNAP_DIR = DATA / "snapshots"
STATE = DATA / "monitor_state.json"


def take_snapshot(week: int, with_lines: bool = True) -> dict:
    gs = espn.games(week)
    snap = {"at": utcnow_iso(), "week": week, "games": gs, "injuries": espn.injuries()}
    if with_lines:
        try:
            snap["lines"] = odds.game_lines()
        except Exception as e:  # keep monitoring even if the odds call fails
            snap["lines_error"] = str(e)[:200]
    try:
        snap["kalshi"] = markets.kalshi_games()
    except Exception as e:
        snap["kalshi_error"] = str(e)[:200]
    soon = datetime.now(timezone.utc) + timedelta(days=4)
    snap["weather"] = []
    for g in gs:
        if g["state"] == "pre" and datetime.fromisoformat(g["date"].replace("Z", "+00:00")) < soon:
            try:
                snap["weather"].append(weather.kickoff_weather(g))
            except Exception as e:
                snap["weather"].append({"game": g["short"], "summary": f"weather error {e}"})
    return snap


def diff(prev: dict, cur: dict) -> list[dict]:
    cfg = profile()["alerts"]
    changes = []
    # line moves
    pl = {(l["home"], l["away"]): l for l in prev.get("lines", [])}
    for l in cur.get("lines", []):
        p = pl.get((l["home"], l["away"]))
        if not p:
            continue
        game = f"{l['away']} @ {l['home']}"
        if p["home_spread"] is not None and l["home_spread"] is not None and \
                abs(l["home_spread"] - p["home_spread"]) >= cfg["spread_move_pts"]:
            changes.append({"type": "spread_move", "game": game, "from": p["home_spread"], "to": l["home_spread"],
                            "note": "home spread"})
        if p["total"] is not None and l["total"] is not None and abs(l["total"] - p["total"]) >= cfg["total_move_pts"]:
            changes.append({"type": "total_move", "game": game, "from": p["total"], "to": l["total"]})
        if p["home_win_prob"] and l["home_win_prob"] and \
                abs(l["home_win_prob"] - p["home_win_prob"]) >= cfg["moneyline_prob_move"]:
            changes.append({"type": "win_prob_move", "game": game, "from": p["home_win_prob"], "to": l["home_win_prob"]})
    # kalshi swings + big money
    pk = {(k["event"], k["team"]): k for k in prev.get("kalshi", [])}
    for k in cur.get("kalshi", []):
        p = pk.get((k["event"], k["team"]))
        if p and p["prob"] and k["prob"] and abs(k["prob"] - p["prob"]) >= cfg["moneyline_prob_move"]:
            vol = (k["volume"] or 0) - (p["volume"] or 0)
            changes.append({"type": "kalshi_swing", "game": k["title"], "team": k["team"],
                            "from": p["prob"], "to": k["prob"], "new_volume": round(vol)})
    # injuries: new or changed statuses for relevant players / players we picked
    relevant = usage_relevant_players()
    picked = {norm_name(r["player"]) for r in read_picks() if not r["result"]}
    prev_inj = {(i["team"], i["player"]): i["status"] for i in prev.get("injuries", [])}
    playing = {g["home"] for g in cur["games"] if g["state"] == "pre"} | \
              {g["away"] for g in cur["games"] if g["state"] == "pre"}
    for i in cur.get("injuries", []):
        old = prev_inj.get((i["team"], i["player"]))
        if old == i["status"] or i["team"] not in playing:
            continue
        n = norm_name(i["player"] or "")
        is_pick = n in picked
        if not (is_pick or n in relevant or i["pos"] == "QB"):
            continue
        if i["status"] not in cfg["injury_statuses"] and not is_pick:
            continue
        changes.append({"type": "injury", "team": i["team"], "player": i["player"], "pos": i["pos"],
                        "from": old or "healthy", "to": i["status"], "detail": i["detail"][:160],
                        "on_our_picks": is_pick})
    # weather flags newly appearing
    pw = {w["game"]: set(w.get("flags", [])) for w in prev.get("weather", [])}
    for w in cur.get("weather", []):
        new_flags = set(w.get("flags", [])) - pw.get(w["game"], set())
        if new_flags:
            changes.append({"type": "weather", "game": w["game"], "flags": sorted(new_flags), "summary": w["summary"]})
    return changes


def run(week: int, with_lines: bool = True, label: str = "check") -> dict:
    """Take a snapshot, diff against the previous one, persist, and return new changes."""
    state = load_json(STATE, {"alerted": []})
    prev = load_json(SNAP_DIR / f"week{week}_latest.json")
    cur = take_snapshot(week, with_lines=with_lines)
    if prev and "lines" not in cur and "lines" in prev:
        cur["lines"] = prev["lines"]  # carry forward so the next diff still has a baseline
    changes = diff(prev, cur) if prev else []
    fresh = []
    for c in changes:
        key = f"{c['type']}|{c.get('game') or c.get('player')}|{c.get('to')}"
        if key not in state["alerted"]:
            fresh.append(c)
            state["alerted"].append(key)
    state["alerted"] = state["alerted"][-500:]
    save_json(SNAP_DIR / f"week{week}_latest.json", cur)
    save_json(SNAP_DIR / f"week{week}_{label}_{cur['at'][:16].replace(':', '')}.json",
              {k: cur[k] for k in cur if k != "injuries"})  # slim archive copy
    save_json(STATE, state)
    return {"week": week, "baseline_existed": bool(prev), "changes": fresh}
