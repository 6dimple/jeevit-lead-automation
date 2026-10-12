import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

NOTIFY_LOG = Path("output") / "notifications.log"


def notify_hot(lead, result, kind="new_hot_lead", note=""):
    """
    Always writes to output/notifications.log (so you can show it in the demo).
    If SLACK_WEBHOOK_URL is set, also posts to Slack.
    Returns a short string describing what happened. Never raises.
    """
    title = "🔥 HOT LEAD" if kind == "new_hot_lead" else "⬆️ EXISTING LEAD LOOKS HOT"
    text = (f"{title}: {lead['name']} ({lead['company'] or 'no company'})\n"
            f"Email: {lead['email']}\n"
            f"Why: {result['reason']}\n"
            f"{note}".strip())

    NOTIFY_LOG.parent.mkdir(exist_ok=True)
    with open(NOTIFY_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {text}\n---\n")

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return "logged to notifications.log (Slack not configured)"
    try:
        req = urllib.request.Request(webhook, data=json.dumps({"text": text}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)

        return "logged and sent to Slack"
    except Exception as e:
        return f"logged, but Slack FAILED: {type(e).__name__}: {e}"