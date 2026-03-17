from bot_loader import bot
from db import add_user, get_user
from keyboards import (
    main_menu,
    confirm_cancel_inline,
    buy_menu,
    topup_menu,
    back_only_menu,
    sell_payout_menu,
)
from states import user_states, reset_state
from config import (
    MIN_STARS_AMOUNT,
    MAX_BUY_STARS,
    MIN_TOPUP_UAH,
    MIN_TOPUP_TON,
    MAX_TOPUP_UAH,
    MAX_TOPUP_TON,
    STAR_PRICE_UAH,
    STAR_SELL_RATE_UAH,
    CARD_PAYOUT_FEE,
    MIN_SELL_STARS,
)
from subscription import is_user_subscribed, send_subscribe_message
from utils import get_ton_rate_uah


@bot.message_handler(commands=["start"])
def start_command(message):
    add_user(message.from_user.id, message.from_user.username)

    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    text = (
        "Ласкаво просимо до <b>StarShop</b> ✨\n\n"
        "Оберіть потрібний розділ нижче."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if is_user_subscribed(call.from_user.id):
        bot.edit_message_text(
            "✅ Підписку підтверджено! Тепер можете користуватись ботом.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(
            call.message.chat.id,
            "Оберіть потрібний розділ нижче.",
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id, "Ви ще не підписані на канал.")


@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back_handler(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state:
        if not is_user_subscribed(user_id):
            send_subscribe_message(message.chat.id)
            return

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
            reply_markup=back_only_menu()
        )
        return

    if action in ["topup_amount_card", "topup_amount_ton"]:
        reset_state(user_id)
        bot.send_message(message.chat.id, "Виберіть спосіб оплати:", reply_markup=topup_menu())
        return

    if action in ["sell_amount", "sell_ton_wallet", "sell_card_number", "sell_contact"]:
        reset_state(user_id)
        bot.send_message(message.chat.id, "Головне меню.", reply_markup=main_menu())
        return

    reset_state(user_id)

    if not is_user_subscribed(user_id):
        send_subscribe_message(message.chat.id)
        return

    bot.send_message(message.chat.id, "Головне меню.", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "❌ Скасувати")
def cancel_handler(message):
    reset_state(message.from_user.id)

    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    bot.send_message(message.chat.id, "Дію скасовано.", reply_markup=main_menu())


@bot.message_handler(content_types=["text"])
def text_router(message):
    user_id = message.from_user.id
    text = message.text.strip()

    ignore_buttons = [
        "⭐ Купити Stars",
        "💸 Продати Stars",
        "👤 Профіль",
        "💳 Поповнити баланс",
        "👤 Собі",
        "🎁 Другові",
        "💳 Карта (UA)",
        "💎 Криптовалюта (TON)",
        "💎 TON — без комісії",
        "💳 UAH — на картку (2.5%)",
        "🔙 Назад",
        "❌ Скасувати",
        "📱 Поділитися контактом",
    ]
    if text in ignore_buttons:
        return

    state = user_states.get(user_id)
    if not state:
        if not is_user_subscribed(user_id):
            send_subscribe_message(message.chat.id)
            return

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

        buy_text = (
            "<b>✨ Вкажіть потрібну кількість Telegram Stars</b>\n\n"
            f"Мінімальна покупка: <b>від {MIN_STARS_AMOUNT} зірок</b>\n"
            f"Ціна за 1 Star: <b>{STAR_PRICE_UAH:.2f} грн</b>"
        )

        bot.send_message(
            message.chat.id,
            buy_text,
            reply_markup=back_only_menu()
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

        if stars_amount > MAX_BUY_STARS:
            bot.send_message(message.chat.id, "Введіть меншу кількість Stars.")
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

        if amount > MAX_TOPUP_UAH:
            bot.send_message(message.chat.id, f"Максимальне поповнення — {MAX_TOPUP_UAH} грн.")
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

        if amount_ton > MAX_TOPUP_TON:
            bot.send_message(message.chat.id, f"Максимальне поповнення — {MAX_TOPUP_TON} TON.")
            return

        ton_rate = state.get("ton_rate")
        if ton_rate is None:
            ton_rate = get_ton_rate_uah()
            state["ton_rate"] = ton_rate

        amount_uah = round(amount_ton * ton_rate, 2)

        state["amount"] = round(amount_ton, 4)
        state["amount_uah"] = amount_uah
        state["action"] = "topup_confirm_ton"

        pretty_ton = f"{amount_ton:.4f}".rstrip("0").rstrip(".")

        msg = (
            "<b>💎 Підтвердження поповнення</b>\n\n"
            f"Спосіб: <b>Криптовалюта (TON)</b>\n"
            f"Сума: <b>{pretty_ton} TON</b>\n"
            f"До зарахування: <b>{amount_uah:.2f} грн</b>\n\n"
            "Після підтвердження ви отримаєте реквізити для оплати."
        )
        bot.send_message(message.chat.id, msg, reply_markup=confirm_cancel_inline("topup"))
        return

    if action == "sell_amount":
        if not text.isdigit():
            bot.send_message(message.chat.id, "Введіть кількість Stars числом.")
            return

        stars_amount = int(text)
        if stars_amount < MIN_SELL_STARS:
            bot.send_message(message.chat.id, f"Мінімальна кількість для продажу — {MIN_SELL_STARS} Stars.")
            return

        ton_rate = get_ton_rate_uah()
        payout_uah = round(stars_amount * STAR_SELL_RATE_UAH, 2)
        payout_card = round(payout_uah * (1 - CARD_PAYOUT_FEE), 2)
        payout_ton = round(payout_uah / ton_rate, 4)

        state["sell_stars_amount"] = stars_amount
        state["sell_payout_uah"] = payout_card
        state["sell_payout_ton"] = payout_ton
        state["ton_rate"] = ton_rate
        state["action"] = "sell_choose_method"

        pretty_ton = f"{payout_ton:.4f}".rstrip("0").rstrip(".")

        msg = (
            f"<b>✅ Ви продаєте: {stars_amount} ⭐️</b>\n\n"
            "<b>Орієнтовна виплата:</b>\n"
            f"💎 TON: <b>{pretty_ton} TON</b>\n"
            f"💳 UAH на картку: <b>{payout_card:.2f} грн</b>\n\n"
            "Оберіть спосіб отримання коштів:"
        )
        bot.send_message(message.chat.id, msg, reply_markup=sell_payout_menu())
        return