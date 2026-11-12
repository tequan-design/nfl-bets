"""Text alerts.

Primary channel: the user's own Google Apps Script web app (ALERT_WEBHOOK_URL). It sends a
plain-text Gmail to the phone's carrier gateway (MetroPCS accepts Gmail; it blocks Brevo's
bulk-mail servers with "452 AUP#MXRT"). The phone address is written in the script, not here.
Fallbacks: Brevo email API, then Twilio SMS.

Configuration lives in the cloud environment, never in the repo:
  ALERT_WEBHOOK_URL    env var: Apps Script web-app URL (doPost reads form field `body`)
  ALERT_SMS_EMAIL      env var: the phone's gateway address, e.g. 4045551234@mymetropcs.com
  ALERT_FROM_EMAIL     env var: the Brevo-verified sender address
  Brevo API key        network secret on api.brevo.com (header api-key), injected by the proxy
  -- or Twilio --
  TWILIO_ACCOUNT_SID, TWILIO_FROM, ALERT_TO env vars + Basic-auth secret on api.twilio.com

If nothing is configured, the alert is written to data/outbox.jsonl and shown in the session.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .common import DATA, HttpError, UA, now_et, post_form, profile, utcnow_iso

MAX_LEN = 450  # gateway texts get split/truncated past a few segments


def _quiet_now() -> bool:
    start, end = profile()["alerts"]["quiet_hours_et"]
    t = now_et().strftime("%H:%M")
    return t >= start or t < end


def _send_brevo(to_addr: str, from_addr: str, body: str) -> dict:
    payload = {
        "sender": {"email": from_addr, "name": "NFL Picks"},
        "to": [{"email": to_addr}],
        "subject": "NFL",
        "textContent": body,  # plain text only: HTML shows up as raw tags on the phone
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode(), method="POST",
        headers={"User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json",
                 "api-key": "proxy-injected"})  # the proxy replaces this with the real key
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read().decode(errors="replace"), req.full_url)


def _send_webhook(url: str, body: str) -> str:
    data = urllib.parse.urlencode({"body": body}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"})
    try:
        # Apps Script answers with a 302 to script.googleusercontent.com; urllib follows it.
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode(errors="replace").strip()[:200]
    except urllib.error.HTTPError as e:
        raise HttpError(e.code, e.read().decode(errors="replace"), url)


def send(body: str, urgent: bool = False) -> dict:
    body = " ".join(body.split())  # one plain line; no HTML, no stray newlines
    if len(body) > MAX_LEN:
        body = body[: MAX_LEN - 3] + "..."
    record = {"at": utcnow_iso(), "body": body, "urgent": urgent}
    hook = os.getenv("ALERT_WEBHOOK_URL")
    gw, frm = os.getenv("ALERT_SMS_EMAIL"), os.getenv("ALERT_FROM_EMAIL")
    sid, tw_from, tw_to = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_FROM"), os.getenv("ALERT_TO")
    try:
        if _quiet_now() and not urgent:
            record["status"] = "held_quiet_hours"
        elif hook:
            reply = _send_webhook(hook, body)
            ok = reply == "ok"
            record.update(status="sent" if ok else "error", channel="gmail-script", reply=reply)
        elif gw and frm:
            r = _send_brevo(gw, frm, body)
            record.update(status="sent", channel="email-to-text", id=r.get("messageId"))
        elif sid and tw_from and tw_to:
            dummy = base64.b64encode(b"proxy:injected").decode()
            r = post_form(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                          {"To": tw_to, "From": tw_from, "Body": body},
                          headers={"Authorization": f"Basic {dummy}"})
            record.update(status="sent", channel="twilio", id=r.get("sid"))
        else:
            record["status"] = "no_sms_config"
    except (HttpError, urllib.error.URLError) as e:
        record.update(status="error", error=str(e)[:300])
    DATA.mkdir(exist_ok=True)
    with (DATA / "outbox.jsonl").open("a") as f:
        f.write(json.dumps(record) + "\n")
    return record
