"""Kickoff weather from Open-Meteo for outdoor games."""
from __future__ import annotations

from .common import get_json, parse_time

# Home stadium coordinates (lat, lon). Roofed stadiums are skipped via ESPN's `indoor` flag.
STADIUMS = {
    "ARI": (33.5276, -112.2626), "ATL": (33.7554, -84.4008), "BAL": (39.2780, -76.6227),
    "BUF": (42.7738, -78.7870), "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167),
    "CIN": (39.0955, -84.5161), "CLE": (41.5061, -81.6995), "DAL": (32.7473, -97.0945),
    "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
    "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3239, -81.6373),
    "KC": (39.0489, -94.4839), "LV": (36.0909, -115.1833), "LAC": (33.9535, -118.3392),
    "LAR": (33.9535, -118.3392), "MIA": (25.9580, -80.2389), "MIN": (44.9737, -93.2575),
    "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8135, -74.0745),
    "NYJ": (40.8135, -74.0745), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158),
    "SF": (37.4030, -121.9700), "SEA": (47.5952, -122.3316), "TB": (27.9759, -82.5033),
    "TEN": (36.1665, -86.7713), "WSH": (38.9078, -76.8645),
}

WMO_SNOW = {71, 73, 75, 77, 85, 86}
WMO_RAIN = {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}


def kickoff_weather(game: dict) -> dict:
    """Never raises: a forecast failure (e.g. Open-Meteo's daily limit) returns a summary instead."""
    try:
        return _kickoff_weather(game)
    except Exception as e:  # noqa: BLE001 - weather must never break a run
        return {"game": game["short"], "indoor": game.get("indoor"),
                "summary": f"Forecast unavailable ({str(e)[:60]}); check a weather app or news"}


def _kickoff_weather(game: dict) -> dict:
    if game.get("indoor"):
        return {"game": game["short"], "indoor": True, "summary": "Indoors/roof - weather not a factor"}
    if game.get("neutral") or game["home"] not in STADIUMS:
        return {"game": game["short"], "indoor": None,
                "summary": f"Neutral site ({game.get('venue')}, {game.get('city')}) - check weather manually"}
    lat, lon = STADIUMS[game["home"]]
    kick = parse_time(game["date"])
    d = get_json("https://api.open-meteo.com/v1/forecast", {
        "latitude": lat, "longitude": lon, "timezone": "UTC",
        "hourly": "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation_probability,precipitation,weather_code",
        "wind_speed_unit": "mph", "temperature_unit": "fahrenheit", "precipitation_unit": "inch",
        "start_date": kick.strftime("%Y-%m-%d"), "end_date": kick.strftime("%Y-%m-%d"),
    })
    h = d.get("hourly", {})
    times = h.get("time", [])
    target = kick.strftime("%Y-%m-%dT%H:00")
    if target not in times:
        return {"game": game["short"], "indoor": False, "summary": "Forecast not available yet (more than ~2 weeks out)"}
    i = times.index(target)
    idx = [j for j in (i, i + 1, i + 2, i + 3) if j < len(times)]  # game window
    wind = max(h["wind_speed_10m"][j] for j in idx)
    gust = max(h["wind_gusts_10m"][j] for j in idx)
    pop = max((h["precipitation_probability"][j] or 0) for j in idx) / 100
    temp = h["temperature_2m"][i]
    codes = {h["weather_code"][j] for j in idx}
    snow = bool(codes & WMO_SNOW)
    rain = bool(codes & WMO_RAIN)
    flags = []
    if wind >= 15 or gust >= 25:
        flags.append(f"WIND {wind:.0f} mph (gusts {gust:.0f})")
    if snow:
        flags.append("SNOW")
    elif rain and pop >= 0.5:
        flags.append(f"RAIN {pop:.0%}")
    if temp <= 25:
        flags.append(f"COLD {temp:.0f}F")
    return {
        "game": game["short"], "indoor": False, "temp_f": round(temp), "wind_mph": round(wind),
        "gust_mph": round(gust), "precip_prob": round(pop, 2), "snow": snow, "flags": flags,
        "summary": f"{temp:.0f}F, wind {wind:.0f} mph (gusts {gust:.0f}), precip {pop:.0%}"
                   + (f" -> {', '.join(flags)}" if flags else ""),
    }
