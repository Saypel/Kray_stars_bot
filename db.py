import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()
cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        reg_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buy_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        target_type TEXT,
        target_username TEXT,
        stars_amount INTEGER,
        price REAL,
        status TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topup_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        method TEXT,
        amount REAL,
        amount_uah REAL,
        memo TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sell_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        stars_amount INTEGER,
        payout_method TEXT,
        payout_details TEXT,
        contact_phone TEXT,
        payout_amount REAL,
        payout_currency TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    conn.commit()


def add_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("""
        INSERT INTO users (user_id, username, balance, reg_date)
        VALUES (?, ?, ?, ?)
        """, (user_id, username or "", 0, datetime.now().strftime("%d.%m.%Y %H:%M")))
    else:
        cursor.execute("""
        UPDATE users
        SET username = ?
        WHERE user_id = ?
        """, (username or "", user_id))

    conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()


def update_balance(user_id, amount):
    cursor.execute("""
    UPDATE users
    SET balance = balance + ?
    WHERE user_id = ?
    """, (amount, user_id))
    conn.commit()


def create_buy_request(user_id, username, target_type, target_username, stars_amount, price):
    cursor.execute("""
    INSERT INTO buy_requests (
        user_id, username, target_type, target_username,
        stars_amount, price, status, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        target_type,
        target_username,
        stars_amount,
        price,
        "pending",
        datetime.now().strftime("%d.%m.%Y %H:%M")
    ))
    conn.commit()
    return cursor.lastrowid


def get_buy_request(request_id):
    cursor.execute("SELECT * FROM buy_requests WHERE id = ?", (request_id,))
    return cursor.fetchone()


def update_buy_request_status(request_id, status):
    cursor.execute("""
    UPDATE buy_requests
    SET status = ?
    WHERE id = ?
    """, (status, request_id))
    conn.commit()


def create_topup_request(user_id, username, method, amount, amount_uah, memo):
    cursor.execute("""
    INSERT INTO topup_requests (
        user_id, username, method, amount, amount_uah, memo, status, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        method,
        amount,
        amount_uah,
        memo,
        "waiting_admin_confirm",
        datetime.now().strftime("%d.%m.%Y %H:%M")
    ))
    conn.commit()
    return cursor.lastrowid


def get_topup_request(request_id):
    cursor.execute("SELECT * FROM topup_requests WHERE id = ?", (request_id,))
    return cursor.fetchone()


def update_topup_request_status(request_id, status):
    cursor.execute("""
    UPDATE topup_requests
    SET status = ?
    WHERE id = ?
    """, (status, request_id))
    conn.commit()


def create_sell_request(user_id, username, stars_amount, payout_method, payout_details, contact_phone, payout_amount, payout_currency, status="waiting_payment"):
    cursor.execute("""
    INSERT INTO sell_requests (
        user_id, username, stars_amount, payout_method, payout_details,
        contact_phone, payout_amount, payout_currency, status, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        stars_amount,
        payout_method,
        payout_details,
        contact_phone,
        payout_amount,
        payout_currency,
        status,
        datetime.now().strftime("%d.%m.%Y %H:%M")
    ))
    conn.commit()
    return cursor.lastrowid


def get_sell_request(request_id):
    cursor.execute("SELECT * FROM sell_requests WHERE id = ?", (request_id,))
    return cursor.fetchone()


def update_sell_request_status(request_id, status):
    cursor.execute("""
    UPDATE sell_requests
    SET status = ?
    WHERE id = ?
    """, (status, request_id))
    conn.commit()