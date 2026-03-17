from bot_loader import bot
from db import add_user, get_user
from keyboards import main_menu
from utils import safe_username
from telebot import types


@bot.message_handler(func=lambda m: m.text == "👤 Профіль")
def profile_handler(message):
    add_user(message.from_user.id, message.from_user.username)
    user = get_user(message.from_user.id)

    text = (
        "<b>👤 Ваш профіль</b>\n\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"Username: <b>{safe_username(user['username'])}</b>\n"
        f"Дата реєстрації: <b>{user['reg_date']}</b>\n"
        f"Баланс: <b>{user['balance']:.2f} грн</b>"
    )

    # кнопки тільки для профілю
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 Поповнити баланс")
    kb.row("🔙 Назад")

    bot.send_message(message.chat.id, text, reply_markup=kb)