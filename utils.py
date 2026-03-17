import random
import string


def generate_memo(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def safe_username(username):
    if not username:
        return "Немає username"
    if username.startswith("@"):
        return username
    return f"@{username}"