from bot_loader import bot
from db import init_db

import stars_buy
import profile
import topup
import admin
import handlers


def run():
    init_db()
    print("Bot started...")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("ERROR:", e)


if __name__ == "__main__":
    run()