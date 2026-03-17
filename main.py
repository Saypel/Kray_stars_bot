from bot_loader import bot
from db import init_db

# Імпорти (важливо щоб були)
import stars_buy
import profile
import topup
import admin
import subscription
import handlers  # залишаємо останнім


def run():
    init_db()
    print("Bot started...")

    bot.infinity_polling(timeout=60, long_polling_timeout=60)


if __name__ == "__main__":
    run()