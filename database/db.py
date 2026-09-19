import sqlite3


def init_db():
    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "telegram_id INTEGER PRIMARY KEY,"
        "first_name TEXT,"
        "username TEXT"
        ")"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS orders ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "telegram_id INTEGER,"
        "currency TEXT,"
        "amount REAL,"
        "result TEXT,"
        "status TEXT DEFAULT 'new'"
        ")"
    )

    try:
        cursor.execute(
            "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'new'"
        )
    except sqlite3.OperationalError:
        pass

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS settings ("
        "key TEXT PRIMARY KEY,"
        "value TEXT"
        ")"
    )

    default_rates = {
        "USDT": "99",
        "TON": "245",
        "BTC": "10250000",
    }

    for key, value in default_rates.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (f"rate_{key}", value),
        )

    connection.commit()
    connection.close()


def create_order(telegram_id, currency, amount, result):
    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO orders "
        "(telegram_id, currency, amount, result, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            telegram_id,
            currency,
            amount,
            result,
            "new",
        ),
    )

    connection.commit()

    order_id = cursor.lastrowid

    connection.close()

    return order_id


def get_rates():
    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT key, value FROM settings WHERE key LIKE 'rate_%'"
    )

    rows = cursor.fetchall()

    connection.close()

    rates = {}

    for key, value in rows:
        currency = key.replace("rate_", "")
        rates[currency] = float(value)

    return rates


def set_rate(currency, value):
    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (f"rate_{currency}", str(value)),
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("База данных создана.")