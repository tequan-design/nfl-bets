"""Text alerts via Twilio, with a safe fallback.

Configuration lives in the cloud environment, never in the repo:
  TWILIO_ACCOUNT_SID   (environment variable)
  TWILIO_FROM          (environment variable, your Twilio number, e.g. +14045551234)
  ALERT_TO             (environment variable, your cell, e.g. +14045559876)
  Auth token           (network secret on api.twilio.com, Basic auth; injected by the proxy)

If anything is missing, the alert is written to data/outbox.jsonl and the
scheduled task's push notification carries it instead.
"""
from __future__ import annotations

import base64
import json
import os

from .common import DATA, HttpError, now_et, post_form, profile, utcnow_iso

MAX_LEN = 600  # ~4 SMS segments


def _quiet_now() -> bool:
    start, end = profile()["alerts"]["quiet_hours_et"]
    t = now_et().strftime("%H:%M")
    return t >= start or t < end


def send(body: str, urgent: bool = False) -> dict:
    body = body.strip()
    if len(body) > MAX_LEN:
        body = body[: MAX_LEN - 3] + "..."
    record = {"at": utcnow_iso(), "body": body, "urgent": urgent}
    sid, frm, to = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_FROM"), os.getenv("ALERT_TO")
    if _quiet_now() and not urgent:
        record["status"] = "held_quiet_hours"
    elif sid and frm and to:
        # Placeholder Basic credentials; the proxy replaces the Authorization header.
        dummy = base64.b64encode(b"proxy:injected").decode()
        try:
            r = post_form(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                          {"To": to, "From": frm, "Body": body},
                          headers={"Authorization": f"Basic {dummy}"})
            record.update(status="sent", sid=r.get("sid"))
        except HttpError as e:
            record.update(status="error", error=str(e)[:300])
    else:
        record["status"] = "no_sms_config"
    DATA.mkdir(exist_ok=True)
    with (DATA / "outbox.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record
