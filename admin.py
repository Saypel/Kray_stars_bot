from bot_loader import bot
from config import ADMIN_ID
from db import (
    get_topup_request,
    update_topup_request_status,
    update_balance,
    get_buy_request,
    update_buy_request_status
)
from keyboards import main_menu


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Немає доступу.")
        return

    if call.data.startswith("admin_topup_confirm:"):
        request_id = int(call.data.split(":")[1])
        req = get_topup_request(request_id)

        if not req or req["status"] != "waiting_admin_confirm":
            bot.answer_callback_query(call.id, "Заявка вже оброблена.")
            return

        update_balance(req["user_id"], req["amount_uah"])
        update_topup_request_status(request_id, "confirmed")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.answer_callback_query(call.id, "Поповнення підтверджено.")

        bot.send_message(
            req["user_id"],
            (
                "<b>✅ Баланс успішно поповнено!</b>\n\n"
                f"Сума: <b>{req['amount_uah']:.2f} грн</b>\n\n"
                "Дякуємо за оплату 💚"
            ),
            reply_markup=main_menu()
        )
        return

    if call.data.startswith("admin_topup_cancel:"):
        request_id = int(call.data.split(":")[1])
        req = get_topup_request(request_id)

        if not req or req["status"] != "waiting_admin_confirm":
            bot.answer_callback_query(call.id, "Заявка вже оброблена.")
            return

        update_topup_request_status(request_id, "canceled")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.answer_callback_query(call.id, "Поповнення скасовано.")

        bot.send_message(
            req["user_id"],
            (
                "❌ Вашу заявку на поповнення скасовано.\n\n"
                "Якщо це помилка — зверніться в підтримку."
            ),
            reply_markup=main_menu()
        )
        return

    if call.data.startswith("admin_buy_confirm:"):
        request_id = int(call.data.split(":")[1])
        req = get_buy_request(request_id)

        if not req or req["status"] != "pending":
            bot.answer_callback_query(call.id, "Заявка вже оброблена.")
            return

        update_buy_request_status(request_id, "confirmed")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.answer_callback_query(call.id, "Покупку підтверджено.")

        bot.send_message(
            req["user_id"],
            (
                "<b>✅ Вашу заявку на покупку Stars підтверджено!</b>\n\n"
                f"Кількість: <b>{req['stars_amount']} ⭐️</b>"
            ),
            reply_markup=main_menu()
        )
        return

    if call.data.startswith("admin_buy_cancel:"):
        request_id = int(call.data.split(":")[1])
        req = get_buy_request(request_id)

        if not req or req["status"] != "pending":
            bot.answer_callback_query(call.id, "Заявка вже оброблена.")
            return

        update_balance(req["user_id"], req["price"])
        update_buy_request_status(request_id, "canceled")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
        bot.answer_callback_query(call.id, "Покупку скасовано.")

        bot.send_message(
            req["user_id"],
            (
                "❌ Вашу заявку на покупку Stars скасовано.\n\n"
                f"На баланс повернуто <b>{req['price']:.2f} грн</b>."
            ),
            reply_markup=main_menu()
        )
        return