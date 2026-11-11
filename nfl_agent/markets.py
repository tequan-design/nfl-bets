"""Prediction markets: Kalshi (games + player prop ladders) and Polymarket (games, volume).
Both public read APIs need no key."""
from __future__ import annotations

import json
import re

from .common import get_json

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
POLY = "https://gamma-api.polymarket.com"

KALSHI_PROP_SERIES = {
    "KXNFLRECYDS": "rec_yds", "KXNFLRSHYDS": "rush_yds", "KXNFLREC": "rec",
    "KXNFLPASSYDS": "pass_yds", "KXNFLPASSTDS": "pass_td", "KXNFLANYTD": "anytime_td",
    "KXNFLPASSCOMP": "pass_comp", "KXNFLPASSATT": "pass_att",
}


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mid(m: dict) -> float | None:
    bid, ask = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
    if bid and ask and ask - bid <= 0.10:
        return round((bid + ask) / 2, 3)
    return _f(m.get("last_price_dollars")) or bid or ask


def kalshi_events(series: str) -> list[dict]:
    out, cursor = [], None
    for _ in range(10):
        params = {"series_ticker": series, "status": "open", "with_nested_markets": "true", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        d = get_json(f"{KALSHI}/events", params)
        out += d.get("events", [])
        cursor = d.get("cursor")
        if not cursor:
            break
    return out


def kalshi_games() -> list[dict]:
    """Win probabilities + volume for open NFL game markets."""
    rows = []
    for e in kalshi_events("KXNFLGAME"):
        for m in e.get("markets", []):
            rows.append({
                "event": e["event_ticker"], "title": e.get("title"), "team": m.get("yes_sub_title"),
                "prob": _mid(m), "prev": _f(m.get("previous_price_dollars")),
                "volume": _f(m.get("volume_fp")), "volume_24h": _f(m.get("volume_24h_fp")),
                "open_interest": _f(m.get("open_interest_fp")),
            })
    return rows


_THRESH = re.compile(r"^(?P<player>.+?):\s*(?P<n>[\d.]+)\+")


def kalshi_prop_ladders(series_list: list[str] | None = None, min_prob: float = 0.0) -> list[dict]:
    """Every player threshold Kalshi lists (e.g. 'Malachi Fields: 25+ receiving yards')."""
    rows = []
    for series in series_list or list(KALSHI_PROP_SERIES):
        stat = KALSHI_PROP_SERIES.get(series, series)
        for e in kalshi_events(series):
            for m in e.get("markets", []):
                sub = m.get("yes_sub_title") or m.get("title") or ""
                mt = _THRESH.match(sub)
                p = _mid(m)
                if p is None or p < min_prob:
                    continue
                rows.append({
                    "game": e.get("title", "").split(":")[0], "event": e["event_ticker"], "stat": stat,
                    "player": mt.group("player").strip() if mt else sub,
                    "threshold": _f(mt.group("n")) if mt else None,
                    "prob": p, "volume": _f(m.get("volume_fp")), "spread": (
                        round(_f(m.get("yes_ask_dollars")) - _f(m.get("yes_bid_dollars")), 2)
                        if _f(m.get("yes_ask_dollars")) is not None and _f(m.get("yes_bid_dollars")) is not None else None),
                })
    return rows


def polymarket_games(start_iso: str, end_iso: str) -> list[dict]:
    """Moneyline prices and dollar volume for NFL games in a date window."""
    d = get_json(f"{POLY}/events", {"tag_slug": "nfl", "closed": "false", "limit": 100,
                                    "end_date_min": start_iso, "end_date_max": end_iso})
    rows = []
    for e in d:
        for m in e.get("markets", []):
            if m.get("sportsMarketType") != "moneyline":
                continue
            outcomes = json.loads(m.get("outcomes") or "[]")
            prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
            rows.append({
                "slug": e.get("slug"), "title": e.get("title"), "kickoff": e.get("endDate"),
                "prices": dict(zip(outcomes, prices)), "volume": _f(m.get("volume")),
                "volume_24h": _f(m.get("volume24hr")), "event_volume": _f(e.get("volume")),
            })
    return rows
