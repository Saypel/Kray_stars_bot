from bot_loader import bot
from config import REQUIRED_CHANNEL
from telebot import types


def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def subscription_kb():
    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "📢 Підписатися",
            url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "✅ Перевірити підписку",
            callback_data="check_sub"
        )
    )

    return kb


def send_subscribe_message(chat_id):
    text = (
        "🔒 <b>Доступ обмежено</b>\n\n"
        "Щоб користуватися ботом — підпишіться на наш канал 👇\n\n"
        f"{REQUIRED_CHANNEL}\n\n"
        "Після підписки натисніть <b>Перевірити підписку</b>."
    )

    bot.send_message(chat_id, text, reply_markup=subscription_kb())