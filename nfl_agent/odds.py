"""The Odds API (v4). The key is injected by the environment's network proxy
(x-api-key header), so no key lives in code or env vars.

Credit cost: odds endpoint = markets x regions. When `bookmakers` is passed,
every 10 bookmakers count as one region, so we always pass an explicit list.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median

from .common import DATA, devig_pair, get_json, load_json, norm_name, profile, save_json, utcnow_iso

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
USAGE_FILE = DATA / "odds_api_usage.json"


def _hdr():
    # Placeholder; the proxy overwrites it with the real key.
    return {"x-api-key": "proxy-injected"}


def _record_usage(headers: dict, what: str):
    h = {k.lower(): v for k, v in headers.items()}
    usage = load_json(USAGE_FILE, {"log": []})
    usage["remaining"] = int(h.get("x-requests-remaining", usage.get("remaining", 0) or 0))
    usage["used"] = int(h.get("x-requests-used", usage.get("used", 0) or 0))
    usage["log"] = (usage["log"] + [{"at": utcnow_iso(), "what": what, "cost": h.get("x-requests-last")}])[-200:]
    save_json(USAGE_FILE, usage)
    return usage


def remaining() -> int | None:
    return load_json(USAGE_FILE, {}).get("remaining")


def events() -> list[dict]:
    """Free call: upcoming NFL events with ids."""
    body, headers = get_json(f"{BASE}/events", headers=_hdr(), want_headers=True)
    _record_usage(headers, "events")
    return body


def game_lines() -> list[dict]:
    """Moneyline, spread, total for every upcoming game. Cost: 3 credits."""
    cfg = profile()["odds_api"]
    books = cfg["sharp_books"] + ["bovada", "betonlineag", "lowvig"]
    body, headers = get_json(f"{BASE}/odds", {
        "markets": "h2h,spreads,totals", "oddsFormat": "american", "bookmakers": ",".join(books[:10]),
    }, headers=_hdr(), want_headers=True)
    _record_usage(headers, "game_lines")
    return [summarize_game(g) for g in body]


def summarize_game(g: dict) -> dict:
    """Consensus (median) line across books plus de-vigged win/over probability."""
    home, away = g["home_team"], g["away_team"]
    spreads, totals, ml_home_p = [], [], []
    for b in g.get("bookmakers", []):
        for m in b.get("markets", []):
            o = {x["name"]: x for x in m["outcomes"]}
            if m["key"] == "spreads" and home in o:
                spreads.append(o[home]["point"])
            elif m["key"] == "totals" and "Over" in o:
                totals.append(o["Over"]["point"])
            elif m["key"] == "h2h" and home in o and away in o:
                ph, _ = devig_pair(o[home]["price"], o[away]["price"])
                ml_home_p.append(ph)
    return {
        "id": g["id"], "commence": g["commence_time"], "home": home, "away": away,
        "home_spread": median(spreads) if spreads else None,
        "total": median(totals) if totals else None,
        "home_win_prob": round(median(ml_home_p), 3) if ml_home_p else None,
        "books": len(g.get("bookmakers", [])),
    }


def event_props(event_id: str, markets: list[str]) -> dict:
    """Player props for one event across sportsbooks and DFS apps. Cost: len(markets) credits
    (one region-equivalent because <=10 bookmakers are named)."""
    cfg = profile()["odds_api"]
    books = (cfg["dfs_books"] + cfg["sharp_books"])[:10]
    body, headers = get_json(f"{BASE}/events/{event_id}/odds", {
        "markets": ",".join(markets), "oddsFormat": "american", "bookmakers": ",".join(books),
    }, headers=_hdr(), want_headers=True)
    _record_usage(headers, f"props {event_id} {','.join(markets)}")
    return body


DFS = {"prizepicks", "underdog", "betr_us_dfs", "pick6", "parlayplay"}

# Rough change in hit probability per 1 unit of line difference near the median.
GAP_SCALE = {
    "player_receptions": 0.10, "player_reception_yds": 0.015, "player_rush_yds": 0.015,
    "player_pass_yds": 0.006, "player_rush_reception_yds": 0.012, "player_pass_completions": 0.04,
    "player_pass_attempts": 0.035, "player_rush_attempts": 0.05, "player_pass_tds": 0.15,
}


def analyze_props(event_payload: dict) -> list[dict]:
    """For each player/market, compare DFS app lines to the sportsbook consensus.

    Output rows: player, market, dfs lines per app, book line, fair P(over at book line),
    and an estimated hit probability for the better side of each DFS line.
    """
    # collect: (player, market) -> {"books": [(point, over, under)], "dfs": {app: point}}
    agg: dict[tuple, dict] = defaultdict(lambda: {"books": [], "dfs": {}})
    for b in event_payload.get("bookmakers", []):
        for m in b.get("markets", []):
            pairs: dict[tuple, dict] = defaultdict(dict)
            for o in m["outcomes"]:
                pairs[(o.get("description", ""), o.get("point"))][o["name"]] = o["price"]
            for (player, point), sides in pairs.items():
                key = (player, m["key"])
                if b["key"] in DFS:
                    agg[key]["dfs"][b["key"]] = point
                elif "Over" in sides and "Under" in sides and point is not None:
                    agg[key]["books"].append((point, sides["Over"], sides["Under"]))
    rows = []
    for (player, market), d in agg.items():
        if not d["books"] or not d["dfs"]:
            continue
        pts = [p for p, _, _ in d["books"]]
        book_line = median(pts)
        fair_over = median([devig_pair(o, u)[0] for p, o, u in d["books"] if p == book_line] or
                           [devig_pair(o, u)[0] for p, o, u in d["books"]])
        for app, dfs_line in d["dfs"].items():
            if dfs_line is None:
                continue
            gap = book_line - dfs_line  # >0 means DFS line is lower than books -> over value
            # Approximate probability shift per unit of line gap (density near the median).
            p_over = min(0.97, max(0.03, fair_over + gap * GAP_SCALE.get(market, 0.012)))
            side = "Over" if p_over >= 0.5 else "Under"
            rows.append({
                "player": player, "market": market, "app": app, "dfs_line": dfs_line,
                "book_line": book_line, "book_fair_over": round(fair_over, 3),
                "pick": side, "est_hit": round(max(p_over, 1 - p_over), 3), "line_gap": round(gap, 1),
                "n_books": len(d["books"]),
            })
    rows.sort(key=lambda r: -r["est_hit"])
    return rows


def norm_market(m: str) -> str:
    return {
        "player_receptions": "rec", "player_reception_yds": "rec_yds", "player_rush_yds": "rush_yds",
        "player_pass_yds": "pass_yds", "player_pass_tds": "pass_td", "player_rush_attempts": "rush_att",
        "player_pass_completions": "pass_comp", "player_pass_attempts": "pass_att",
        "player_rush_reception_yds": "rush_rec_yds",
    }.get(m, m)


def player_key(name: str) -> str:
    return norm_name(name)
