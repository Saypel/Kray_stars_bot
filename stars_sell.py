from telebot import types

from bot_loader import bot
from config import MIN_SELL_STARS, ADMIN_ID
from db import create_sell_request, get_sell_request, update_sell_request_status
from keyboards import (
    main_menu,
    back_only_menu,
    contact_share_kb,
    confirm_cancel_inline,
    admin_sell_kb,
)
from states import user_states, reset_state
from subscription import is_user_subscribed, send_subscribe_message


@bot.message_handler(func=lambda m: m.text == "💸 Продати Stars")
def sell_stars_handler(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscribe_message(message.chat.id)
        return

    user_states[message.from_user.id] = {
        "action": "sell_amount"
    }

    text = (
        "<b>💫 Продаж Telegram Stars</b>\n\n"
        "💰 Курс викупу розраховується автоматично\n"
        f"💡 Мінімальна кількість: <b>{MIN_SELL_STARS} ⭐️</b>\n\n"
        "<b>Комісія на виплату:</b>\n"
        "— TON: без комісії\n"
        "— UAH на картку: 2.5%\n\n"
        "⚠️ Важливо:\n"
        "— Виплата розраховується з урахуванням сервісних умов\n"
        "— У разі підозрілих дій виплата може бути тимчасово призупинена\n\n"
        "Введіть кількість Stars для продажу:"
    )
    bot.send_message(message.chat.id, text, reply_markup=back_only_menu())


@bot.message_handler(func=lambda m: m.text == "💎 TON — без комісії")
def sell_choose_ton(message):
    state = user_states.get(message.from_user.id)
    if not state or state.get("action") != "sell_choose_method":
        return

    state["sell_method"] = "TON"
    state["action"] = "sell_ton_wallet"

    text = (
        "<b>💎 Введіть адресу TON-гаманця для виплати</b>\n\n"
        "📝 Адреса має починатися з <b>UQ</b> або <b>EQ</b>\n"
        "⚠️ Вкажіть гаманець, для якого <b>не потрібен MEMO / TAG / коментар</b>\n"
        "⚠️ Інакше кошти можуть бути втрачені"
    )
    bot.send_message(message.chat.id, text, reply_markup=back_only_menu())


@bot.message_handler(func=lambda m: m.text == "💳 UAH — на картку (2.5%)")
def sell_choose_card(message):
    state = user_states.get(message.from_user.id)
    if not state or state.get("action") != "sell_choose_method":
        return

    state["sell_method"] = "UAH"
    state["action"] = "sell_card_number"

    bot.send_message(
        message.chat.id,
        "<b>💳 Введіть номер картки для виплати</b>",
        reply_markup=back_only_menu()
    )


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("action") == "sell_ton_wallet")
def sell_wallet_input(message):
    wallet = message.text.strip()

    if not (wallet.startswith("UQ") or wallet.startswith("EQ")):
        bot.send_message(message.chat.id, "Введіть коректну адресу TON-гаманця.")
        return

    state = user_states[message.from_user.id]
    state["sell_payout_details"] = wallet
    state["action"] = "sell_contact"

    bot.send_message(
        message.chat.id,
        "🔒 Для захисту від шахрайства потрібно поділитися номером телефону.\n\nНатисніть кнопку нижче:",
        reply_markup=contact_share_kb()
    )


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id, {}).get("action") == "sell_card_number")
def sell_card_input(message):
    raw = message.text.strip().replace(" ", "")
    if not (raw.isdigit() and 13 <= len(raw) <= 19):
        bot.send_message(message.chat.id, "Введіть коректний номер картки.")
        return

    state = user_states[message.from_user.id]
    state["sell_payout_details"] = raw
    state["action"] = "sell_contact"

    bot.send_message(
        message.chat.id,
        "🔒 Для захисту від шахрайства потрібно поділитися номером телефону.\n\nНатисніть кнопку нижче:",
        reply_markup=contact_share_kb()
    )


@bot.message_handler(content_types=["contact"])
def sell_contact_handler(message):
    state = user_states.get(message.from_user.id)
    if not state or state.get("action") != "sell_contact":
        return

    phone = message.contact.phone_number
    state["sell_phone"] = phone
    state["action"] = "sell_confirm"

    stars_amount = state["sell_stars_amount"]
    method = state["sell_method"]
    payout_details = state["sell_payout_details"]

    if method == "TON":
        payout_amount = state["sell_payout_ton"]
        payout_text = f"{str(round(payout_amount, 4)).rstrip('0').rstrip('.')} TON"
    else:
        payout_amount = state["sell_payout_uah"]
        payout_text = f"{payout_amount:.2f} грн"

    text = (
        "<b>✅ Номер телефону отримано</b>\n\n"
        "<b>⭐ Підтвердження заявки</b>\n\n"
        f"Кількість Stars: <b>{stars_amount} ⭐️</b>\n"
        f"Спосіб виплати: <b>{method}</b>\n"
        f"Сума до отримання: <b>{payout_text}</b>\n"
        f"Реквізити: <code>{payout_details}</code>\n\n"
        "🛡 Останній крок — перевірка безпеки\n"
        "Після підтвердження бот надішле інвойс у Telegram Stars."
    )
    bot.send_message(message.chat.id, text, reply_markup=confirm_cancel_inline("sell"))


@bot.callback_query_handler(func=lambda call: call.data.startswith("sell:"))
def sell_callback_handler(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})

    if call.data == "sell:confirm":
        if state.get("action") != "sell_confirm":
            bot.answer_callback_query(call.id, "Дані застаріли.")
            return

        stars_amount = state["sell_stars_amount"]
        method = state["sell_method"]
        payout_details = state["sell_payout_details"]
        phone = state["sell_phone"]

        if method == "TON":
            payout_amount = state["sell_payout_ton"]
            payout_currency = "TON"
        else:
            payout_amount = state["sell_payout_uah"]
            payout_currency = "UAH"

        request_id = create_sell_request(
            user_id=user_id,
            username=call.from_user.username or "",
            stars_amount=stars_amount,
            payout_method=method,
            payout_details=payout_details,
            contact_phone=phone,
            payout_amount=payout_amount,
            payout_currency=payout_currency,
            status="waiting_payment"
        )

        prices = [types.LabeledPrice(label="Telegram Stars", amount=stars_amount)]

        bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Продаж Telegram Stars",
            description=f"Оплата заявки на продаж {stars_amount} Stars",
            invoice_payload=f"sell:{request_id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter=f"sellstars{request_id}"
        )

        bot.answer_callback_query(call.id, "Інвойс відправлено.")
        reset_state(user_id)
        return

    if call.data == "sell:cancel":
        reset_state(user_id)
        bot.edit_message_text(
            "Продаж Stars скасовано.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return


@bot.pre_checkout_query_handler(func=lambda query: query.invoice_payload.startswith("sell:"))
def process_sell_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_sell_payment(message):
    payment = message.successful_payment

    if payment.currency != "XTR":
        return

    if not payment.invoice_payload.startswith("sell:"):
        return

    request_id = int(payment.invoice_payload.split(":")[1])
    req = get_sell_request(request_id)
    if not req:
        return

    update_sell_request_status(request_id, "waiting_admin_payout")

    if req["payout_currency"] == "TON":
        payout_text = f"{str(round(req['payout_amount'], 4)).rstrip('0').rstrip('.')} TON"
    else:
        payout_text = f"{req['payout_amount']:.2f} грн"

    username = req["username"] if req["username"] else "no_username"

    admin_text = (
        "<b>💸 Нова заявка на виплату за продаж Stars</b>\n\n"
        f"ID заявки: <code>{request_id}</code>\n"
        f"Користувач: @{username}\n"
        f"User ID: <code>{req['user_id']}</code>\n"
        f"Телефон: <code>{req['contact_phone']}</code>\n"
        f"Кількість Stars: <b>{req['stars_amount']} ⭐️</b>\n"
        f"Спосіб виплати: <b>{req['payout_method']}</b>\n"
        f"Сума до виплати: <b>{payout_text}</b>\n"
        f"Реквізити: <code>{req['payout_details']}</code>"
    )

    bot.send_message(
        ADMIN_ID,
        admin_text,
        reply_markup=admin_sell_kb(request_id, req["user_id"])
    )

    bot.send_message(
        message.chat.id,
        "<b>✅ Оплату в Stars отримано</b>\n\nВаша заявка передана адміністратору на виплату.",
        reply_markup=main_menu()
    )