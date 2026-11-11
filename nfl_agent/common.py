"""Shared helpers: HTTP, paths, names, odds math. Standard library only."""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MEMORY = ROOT / "memory"
REPORTS = ROOT / "reports"
CONFIG = ROOT / "config" / "profile.json"
ET = ZoneInfo("America/New_York")

UA = "nfl-picks-agent/1.0"


def profile() -> dict:
    return json.loads(CONFIG.read_text())


def now_et() -> datetime:
    return datetime.now(ET)


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fmt_et(s: str | datetime) -> str:
    dt = parse_time(s) if isinstance(s, str) else s
    return dt.astimezone(ET).strftime("%a %-m/%-d %-I:%M%p ET")


class HttpError(Exception):
    def __init__(self, status, body, url):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status
        self.body = body


def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             retries: int = 3, want_headers: bool = False):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read().decode())
                return (body, dict(r.headers)) if want_headers else body
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                last = HttpError(e.code, body, url)
                continue
            raise HttpError(e.code, body, url)
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 ** attempt * 2)
    raise last  # type: ignore[misc]


def post_form(url: str, form: dict, headers: dict | None = None) -> dict:
    data = urllib.parse.urlencode(form).encode()
    h = {"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read().decode(errors="replace"), url)


# ---------- names ----------
_SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b\.?", re.I)


def norm_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    s = _SUFFIX.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------- odds math ----------
def american_to_prob(price: float) -> float:
    price = float(price)
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def prob_to_american(p: float) -> str:
    if p <= 0 or p >= 1:
        return "n/a"
    v = -100 * p / (1 - p) if p >= 0.5 else 100 * (1 - p) / p
    return f"{v:+.0f}"


def devig_pair(over_price: float, under_price: float) -> tuple[float, float]:
    """Multiplicative de-vig of a two-way market. Returns (p_over, p_under)."""
    po, pu = american_to_prob(over_price), american_to_prob(under_price)
    t = po + pu
    return po / t, pu / t


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=str))


def load_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
