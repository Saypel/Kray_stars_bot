from bot_loader import bot
from db import add_user, get_user
from keyboards import main_menu, cancel_back_menu, confirm_cancel_inline, buy_menu, topup_menu
from states import user_states, reset_state
from config import MIN_STARS_AMOUNT, MIN_TOPUP_UAH, MIN_TOPUP_TON, STAR_PRICE_UAH, TON_RATE_UAH


@bot.message_handler(commands=["start"])
def start_command(message):
    add_user(message.from_user.id, message.from_user.username)

    text = (
        "Ласкаво просимо до <b>StarShop</b> ✨\n\n"
        "Оберіть потрібний розділ нижче."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back_handler(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state:
        bot.send_message(message.chat.id, "Головне меню.", reply_markup=main_menu())
        return

    action = state.get("action")

    if action in ["buy_self_amount", "buy_friend_username"]:
        reset_state(user_id)
        bot.send_message(message.chat.id, "Виберіть, кому купуєте Stars:", reply_markup=buy_menu())
        return

    if action == "buy_friend_amount":
        state["action"] = "buy_friend_username"
        bot.send_message(
            message.chat.id,
            "Введіть username отримувача у форматі @username:",
            reply_markup=cancel_back_menu()
        )
        return

    if action in ["topup_amount_card", "topup_amount_ton"]:
        reset_state(user_id)
        bot.send_message(message.chat.id, "Виберіть спосіб оплати:", reply_markup=topup_menu())
        return

    reset_state(user_id)
    bot.send_message(message.chat.id, "Головне меню.", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "❌ Скасувати")
def cancel_handler(message):
    reset_state(message.from_user.id)
    bot.send_message(message.chat.id, "Дію скасовано.", reply_markup=main_menu())


@bot.message_handler(content_types=["text"])
def text_router(message):
    user_id = message.from_user.id
    text = message.text.strip()

    ignore_buttons = [
        "⭐ Купити Stars",
        "👤 Профіль",
        "💳 Поповнити баланс",
        "👤 Собі",
        "🎁 Другові",
        "💳 Карта (UA)",
        "💎 Криптовалюта (TON)",
        "🔙 Назад",
        "❌ Скасувати",
    ]
    if text in ignore_buttons:
        return

    state = user_states.get(user_id)
    if not state:
        bot.send_message(message.chat.id, "Оберіть дію з меню нижче.", reply_markup=main_menu())
        return

    action = state.get("action")

    if action == "buy_friend_username":
        if not text.startswith("@") or len(text) < 5:
            bot.send_message(message.chat.id, "Введіть коректний username у форматі @username")
            return

        state["target_type"] = "friend"
        state["target_username"] = text
        state["action"] = "buy_friend_amount"

        bot.send_message(
            message.chat.id,
            f"✅ Отримувача збережено!\n\n✨ Вкажіть потрібну кількість Telegram Stars:\nМінімум: <b>{MIN_STARS_AMOUNT}</b>",
            reply_markup=cancel_back_menu()
        )
        return

    if action in ["buy_self_amount", "buy_friend_amount"]:
        if not text.isdigit():
            bot.send_message(message.chat.id, "Введіть кількість Stars числом.")
            return

        stars_amount = int(text)
        if stars_amount < MIN_STARS_AMOUNT:
            bot.send_message(message.chat.id, f"Мінімальна кількість для покупки — {MIN_STARS_AMOUNT} Stars.")
            return

        price = round(stars_amount * STAR_PRICE_UAH, 2)
        state["amount"] = stars_amount
        state["price"] = price
        state["action"] = "buy_confirm"

        user = get_user(user_id)
        balance = float(user["balance"])

        target_label = "Ви" if state["target_type"] == "self" else state["target_username"]

        msg = (
            "<b>Підтвердження покупки</b>\n\n"
            f"Отримувач: <b>{target_label}</b>\n"
            f"Кількість: <b>{stars_amount} ⭐️</b>\n"
            f"Сума: <b>{price:.2f} грн</b>\n"
            f"Ваш баланс: <b>{balance:.2f} грн</b>"
        )
        bot.send_message(message.chat.id, msg, reply_markup=confirm_cancel_inline("buy"))
        return

    if action == "topup_amount_card":
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            bot.send_message(message.chat.id, "Введіть коректну суму в грн.")
            return

        if amount < MIN_TOPUP_UAH:
            bot.send_message(message.chat.id, f"Мінімальне поповнення — {MIN_TOPUP_UAH} грн.")
            return

        state["amount"] = round(amount, 2)
        state["amount_uah"] = round(amount, 2)
        state["action"] = "topup_confirm_card"

        msg = (
            "<b>💳 Підтвердження поповнення</b>\n\n"
            f"Спосіб: <b>Карта (UA)</b>\n"
            f"Сума: <b>{amount:.2f} грн</b>\n\n"
            "Після підтвердження ви отримаєте реквізити для оплати."
        )
        bot.send_message(message.chat.id, msg, reply_markup=confirm_cancel_inline("topup"))
        return

    if action == "topup_amount_ton":
        try:
            amount_ton = float(text.replace(",", "."))
        except ValueError:
            bot.send_message(message.chat.id, "Введіть коректну кількість TON.")
            return

        if amount_ton < MIN_TOPUP_TON:
            bot.send_message(message.chat.id, f"Мінімальне поповнення — {MIN_TOPUP_TON} TON.")
            return

        amount_uah = round(amount_ton * TON_RATE_UAH, 2)

        state["amount"] = round(amount_ton, 4)
        state["amount_uah"] = amount_uah
        state["action"] = "topup_confirm_ton"

        msg = (
            "<b>💎 Підтвердження поповнення</b>\n\n"
            f"Спосіб: <b>Криптовалюта (TON)</b>\n"
            f"Сума: <b>{amount_ton:.4f} TON</b>\n"
            f"За курсом: <b>{amount_uah:.2f} грн</b>\n"
            f"Курс: <b>1 TON = {TON_RATE_UAH:.2f} грн</b>\n\n"
            "Після підтвердження ви отримаєте реквізити для оплати."
        )
        bot.send_message(message.chat.id, msg, reply_markup=confirm_cancel_inline("topup"))
        return