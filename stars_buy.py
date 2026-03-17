from bot_loader import bot
from db import get_user, create_buy_request, update_balance
from keyboards import buy_menu, main_menu, admin_buy_kb, back_only_menu
from states import user_states, reset_state
from utils import safe_username
from config import ADMIN_ID, MIN_STARS_AMOUNT
from subscription import is_user_subscribed, send_subscribe_message


@bot.message_handler(func=lambda m: m.text == "⭐ Купити Stars")
def buy_stars_handler(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    reset_state(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Виберіть, кому купуєте Stars:",
        reply_markup=buy_menu()
    )


@bot.message_handler(func=lambda m: m.text == "👤 Собі")
def buy_for_self_handler(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    user_states[message.from_user.id] = {
        "action": "buy_self_amount",
        "target_type": "self",
        "target_username": safe_username(message.from_user.username)
    }
    bot.send_message(
        message.chat.id,
        f"✨ Вкажіть потрібну кількість Telegram Stars:\nМінімум: <b>{MIN_STARS_AMOUNT}</b>",
        reply_markup=back_only_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🎁 Другові")
def buy_for_friend_handler(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    user_states[message.from_user.id] = {
        "action": "buy_friend_username"
    }
    bot.send_message(
        message.chat.id,
        "Введіть username отримувача у форматі @username:",
        reply_markup=back_only_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def buy_callback_handler(call):
    user_id = call.from_user.id

    if not is_user_subscribed(user_id):
        bot.answer_callback_query(call.id, "Спочатку підпишіться на канал.")
        send_subscribe_message(call.message.chat.id)
        return

    state = user_states.get(user_id, {})

    if call.data == "buy:confirm":
        if state.get("action") != "buy_confirm":
            bot.answer_callback_query(call.id, "Дані застаріли.")
            return

        amount = state["amount"]
        price = state["price"]
        target_type = state["target_type"]
        target_username = state["target_username"]

        user = get_user(user_id)
        balance = float(user["balance"])

        if balance < price:
            not_enough = round(price - balance, 2)

            bot.edit_message_text(
                (
                    "<b>Недостатньо коштів на балансі</b>\n\n"
                    f"Ваш баланс: <b>{balance:.2f} грн</b>\n"
                    f"Не вистачає: <b>{not_enough:.2f} грн</b>"
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

            bot.send_message(
                call.message.chat.id,
                "Поповніть баланс та спробуйте ще раз.",
                reply_markup=main_menu()
            )

            reset_state(user_id)
            bot.answer_callback_query(call.id)
            return

        update_balance(user_id, -price)

        request_id = create_buy_request(
            user_id=user_id,
            username=call.from_user.username or "",
            target_type=target_type,
            target_username=target_username,
            stars_amount=amount,
            price=price
        )

        admin_text = (
            "<b>🛒 Нова заявка на покупку Stars</b>\n\n"
            f"ID заявки: <code>{request_id}</code>\n"
            f"Користувач: {safe_username(call.from_user.username)}\n"
            f"User ID: <code>{user_id}</code>\n"
            f"Отримувач: <b>{'собі' if target_type == 'self' else target_username}</b>\n"
            f"Кількість: <b>{amount} ⭐️</b>\n"
            f"Сума: <b>{price:.2f} грн</b>"
        )

        bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=admin_buy_kb(request_id, user_id)
        )

        bot.edit_message_text(
            (
                "<b>Заявку створено ✅</b>\n\n"
                f"З балансу списано <b>{price:.2f} грн</b>.\n"
                "Очікуйте підтвердження від адміністратора."
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        reset_state(user_id)
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    if call.data == "buy:cancel":
        reset_state(user_id)
        bot.edit_message_text(
            "Покупку скасовано.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return