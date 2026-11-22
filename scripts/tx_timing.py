#!/usr/bin/env python3
"""Histogram of league transaction times (ET) by hour and weekday.

Input: one or more JSON files, each the raw result of Flaim `get_transactions`
(either the whole response or just its `transactions` list). Waiver batches that
share a timestamp are counted once per player move, as Yahoo records them.

  python3 scripts/tx_timing.py dirty_south.json end_zone_bound.json
"""
import json
import sys
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def load(path):
    d = json.load(open(path))
    if isinstance(d, dict):
        d = d.get("data", d).get("transactions", [])
    return [t["timestamp"] / 1000 for t in d if t.get("timestamp")]


def report(name, ts):
    hours = Counter(datetime.fromtimestamp(t, ET).hour for t in ts)
    days = Counter(datetime.fromtimestamp(t, ET).strftime("%a") for t in ts)
    print(f"\n== {name}: {len(ts)} moves")
    for h in range(24):
        print(f"{h:02d}:00 {'#' * hours[h]} {hours[h]}")
    print({d: days[d] for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})
    top = [h for h, _ in hours.most_common(4)]
    print("Busiest hours:", ", ".join(f"{h:02d}:00" for h in sorted(top)))


if __name__ == "__main__":
    allts = []
    for p in sys.argv[1:]:
        ts = load(p)
        allts += ts
        report(p, ts)
    if len(sys.argv) > 2:
        report("combined", allts)
