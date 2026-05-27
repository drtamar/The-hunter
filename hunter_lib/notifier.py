"""Multi-channel notifier: Telegram / Discord / Slack / generic webhook.

Pattern from drtamar/claudeos. All channels read their secrets from env vars
so nothing sensitive lands in scope.yaml.
"""
from __future__ import annotations
import os
import json
import urllib.request
import urllib.parse


def _post(url: str, data: dict, headers: dict | None = None) -> str:
    h = {"Content-Type": "application/json", "User-Agent": "hunter-notifier/0.1"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method="POST")
    try:
        return urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
    except Exception as e:
        return f"error: {e}"


def telegram(text: str, token_env: str = "TELEGRAM_BOT_TOKEN", chat_env: str = "TELEGRAM_CHAT_ID") -> str:
    tok = os.environ.get(token_env, "")
    chat = os.environ.get(chat_env, "")
    if not tok or not chat:
        return "skipped: missing env"
    body = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=body)
    try:
        return urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
    except Exception as e:
        return f"error: {e}"


def discord(text: str, env: str = "DISCORD_WEBHOOK_URL") -> str:
    url = os.environ.get(env, "")
    if not url:
        return "skipped: missing env"
    return _post(url, {"content": text})


def slack(text: str, env: str = "SLACK_WEBHOOK_URL") -> str:
    url = os.environ.get(env, "")
    if not url:
        return "skipped: missing env"
    return _post(url, {"text": text})


def webhook(url: str, payload: dict) -> str:
    return _post(url, payload)


def fan_out(text: str, channels: list[dict]) -> dict:
    """Dispatch one message to multiple channels.

    channels = [
      {"kind": "telegram"},
      {"kind": "discord"},
      {"kind": "slack"},
      {"kind": "webhook", "url": "..."},
    ]
    """
    results: dict = {}
    for ch in channels or []:
        k = ch.get("kind")
        if k == "telegram":
            results[k] = telegram(text)
        elif k == "discord":
            results[k] = discord(text)
        elif k == "slack":
            results[k] = slack(text)
        elif k == "webhook":
            results[k] = webhook(ch.get("url", ""), {"text": text})
    return results
