import json

from ..core.logger import get_logger

logger = get_logger(__name__)


def send_notification(title, message, provider="", token="", user_key=""):
    if not provider or provider == "none":
        logger.info(f"Notification skipped (no provider): {title}")
        return False
    try:
        if provider == "pushover":
            return _send_pushover(title, message, token, user_key)
        elif provider == "serverchan":
            return _send_serverchan(title, message, token)
        elif provider == "bark":
            return _send_bark(title, message, token)
        else:
            logger.warning(f"Unknown notification provider: {provider}")
            return False
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def _send_pushover(title, message, token, user_key):
    import http.client
    import urllib.parse

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST",
        "/1/messages.json",
        urllib.parse.urlencode({"token": token, "user": user_key, "title": title[:250], "message": message[:1024]}),
        {"Content-type": "application/x-www-form-urlencoded"},
    )
    return conn.getresponse().status == 200


def _send_serverchan(title, message, token):
    import urllib.parse
    import urllib.request

    url = f"https://sctapi.ftqq.com/{token}.send"
    data = urllib.parse.urlencode({"title": title[:128], "desp": message[:20000]}).encode("utf-8")
    resp = urllib.request.urlopen(url, data=data, timeout=10)
    return json.loads(resp.read().decode("utf-8")).get("code") == 0


def _send_bark(title, message, token):
    import urllib.parse
    import urllib.request

    url = f"https://api.day.app/{token}/{urllib.parse.quote(title)}/{urllib.parse.quote(message)}"
    resp = urllib.request.urlopen(url, timeout=10)
    return json.loads(resp.read().decode("utf-8")).get("code") == 200
