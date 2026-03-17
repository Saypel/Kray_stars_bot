from telebot import types


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("⭐ Купити Stars", "💸 Продати Stars")
    kb.row("👤 Профіль", "💳 Поповнити баланс")
    return kb


def buy_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👤 Собі", "🎁 Другові")
    kb.row("🔙 Назад")
    return kb


def topup_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 Карта (UA)", "💎 Криптовалюта (TON)")
    kb.row("🔙 Назад")
    return kb


def back_only_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Назад")
    return kb


def cancel_back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("❌ Скасувати", "🔙 Назад")
    return kb


def sell_payout_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💎 TON — без комісії")
    kb.row("💳 UAH — на картку (2.5%)")
    kb.row("🔙 Назад")
    return kb


def contact_share_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 Поділитися контактом", request_contact=True)
    kb.row(btn)
    kb.row("🔙 Назад")
    return kb


def confirm_cancel_inline(prefix):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Підтвердити", callback_data=f"{prefix}:confirm"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data=f"{prefix}:cancel")
    )
    return kb


def paid_inline():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Я оплатив", callback_data="topup_paid"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data="topup_paid_cancel")
    )
    return kb


def admin_topup_kb(request_id, user_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Підтвердити", callback_data=f"admin_topup_confirm:{request_id}"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data=f"admin_topup_cancel:{request_id}")
    )
    kb.row(types.InlineKeyboardButton("💬 Зв'язатися", url=f"tg://user?id={user_id}"))
    return kb


def admin_buy_kb(request_id, user_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Підтвердити", callback_data=f"admin_buy_confirm:{request_id}"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data=f"admin_buy_cancel:{request_id}")
    )
    kb.row(types.InlineKeyboardButton("💬 Зв'язатися", url=f"tg://user?id={user_id}"))
    return kb


def admin_sell_kb(request_id, user_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Підтвердити", callback_data=f"admin_sell_confirm:{request_id}"),
        types.InlineKeyboardButton("❌ Скасувати", callback_data=f"admin_sell_cancel:{request_id}")
    )
    kb.row(types.InlineKeyboardButton("💬 Зв'язатися", url=f"tg://user?id={user_id}"))
    return kb