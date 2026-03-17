import random
import string
import requests


def generate_memo(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def safe_username(username):
    if not username:
        return "Немає username"
    if username.startswith("@"):
        return username
    return f"@{username}"


def get_ton_rate_uah():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "the-open-network",
            "vs_currencies": "uah"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data["the-open-network"]["uah"])
    except Exception:
        return 210.0