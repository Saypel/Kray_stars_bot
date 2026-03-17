from bot_loader import bot
from keyboards import topup_menu, confirm_cancel_inline, paid_inline, main_menu, admin_topup_kb
from states import user_states, reset_state
from utils import generate_memo, safe_username
from db import create_topup_request
from config import ADMIN_ID, CARD_NUMBER, TON_WALLET, TON_RATE_UAH, MIN_TOPUP_UAH, MIN_TOPUP_TON
from telebot import types


def back_only_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔙 Назад")
    return kb


@bot.message_handler(func=lambda m: m.text == "💳 Поповнити баланс")
def topup_handler(message):
    reset_state(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Виберіть спосіб оплати:",
        reply_markup=topup_menu()
    )


@bot.message_handler(func=lambda m: m.text == "💳 Карта (UA)")
def topup_card_handler(message):
    user_states[message.from_user.id] = {
        "action": "topup_amount_card",
        "method": "Карта (UA)"
    }
    bot.send_message(
        message.chat.id,
        f"💳 Введіть суму поповнення в грн\nМінімум: <b>{MIN_TOPUP_UAH} грн</b>",
        reply_markup=back_only_menu()
    )


@bot.message_handler(func=lambda m: m.text == "💎 Криптовалюта (TON)")
def topup_ton_handler(message):
    user_states[message.from_user.id] = {
        "action": "topup_amount_ton",
        "method": "Криптовалюта (TON)"
    }
    bot.send_message(
        message.chat.id,
        (
            f"💎 Введіть кількість TON для поповнення\n"
            f"Мінімум: <b>{MIN_TOPUP_TON} TON</b>\n"
            f"Курс: <b>1 TON = {TON_RATE_UAH:.2f} грн</b>"
        ),
        reply_markup=back_only_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("topup"))
def topup_callback_handler(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})

    if call.data == "topup:confirm":
        action = state.get("action")
        if action not in ["topup_confirm_card", "topup_confirm_ton"]:
            bot.answer_callback_query(call.id, "Дані застаріли.")
            return

        amount = state["amount"]
        amount_uah = state["amount_uah"]
        method = state["method"]
        memo = generate_memo()

        state["memo"] = memo
        state["action"] = "topup_waiting_payment"

        if method == "Карта (UA)":
            text = (
                "<b>💳 Реквізити для поповнення</b>\n\n"
                f"Сума до оплати: <b>{amount_uah:.2f} грн</b>\n\n"
                "⚠️ Оплатіть точно вказану суму.\n\n"
                f"Номер карти: <code>{CARD_NUMBER}</code>\n"
                f"Memo: <code>{memo}</code>\n\n"
                "Після оплати натисніть кнопку <b>Я оплатив</b>."
            )
        else:
            text = (
                "<b>💎 Реквізити для поповнення</b>\n\n"
                f"Сума до оплати: <b>{amount:.4f} TON</b>\n"
                f"За курсом: <b>{amount_uah:.2f} грн</b>\n\n"
                f"TON Wallet: <code>{TON_WALLET}</code>\n"
                f"Memo: <code>{memo}</code>\n\n"
                "Після оплати натисніть кнопку <b>Я оплатив</b>."
            )

        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=paid_inline()
        )
        bot.answer_callback_query(call.id)
        return

    if call.data == "topup:cancel":
        reset_state(user_id)
        bot.edit_message_text(
            "Поповнення скасовано.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    if call.data == "topup_paid":
        if state.get("action") != "topup_waiting_payment":
            bot.answer_callback_query(call.id, "Дані застаріли.")
            return

        amount = state["amount"]
        amount_uah = state["amount_uah"]
        method = state["method"]
        memo = state["memo"]

        request_id = create_topup_request(
            user_id=user_id,
            username=call.from_user.username or "",
            method=method,
            amount=amount,
            amount_uah=amount_uah,
            memo=memo
        )

        admin_text = (
            "<b>💳 Нова заявка на поповнення</b>\n\n"
            f"ID заявки: <code>{request_id}</code>\n"
            f"Користувач: {safe_username(call.from_user.username)}\n"
            f"User ID: <code>{user_id}</code>\n"
            f"Спосіб: <b>{method}</b>\n"
            f"Сума: <b>{amount}</b>\n"
            f"У грн: <b>{amount_uah:.2f}</b>\n"
            f"Memo: <code>{memo}</code>"
        )

        bot.send_message(
            ADMIN_ID,
            admin_text,
            reply_markup=admin_topup_kb(request_id, user_id)
        )

        bot.edit_message_text(
            (
                "<b>Вашу заявку відправлено адміну ✅</b>\n\n"
                "Очікуйте підтвердження поповнення."
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

        reset_state(user_id)
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    if call.data == "topup_paid_cancel":
        reset_state(user_id)
        bot.edit_message_text(
            "Поповнення скасовано.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(call.message.chat.id, "Головне меню.", reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return