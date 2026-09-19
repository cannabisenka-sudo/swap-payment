import asyncio
import json
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from dotenv import load_dotenv

from database.db import init_db, create_order


# =========================
# Настройки
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise RuntimeError("Токен бота не найден!")


WEB_APP_URL = "https://cannabisenka-sudo.github.io/swap-payment/"


# =========================
# Telegram
# =========================

dp = Dispatcher()


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🚀 Открыть SwapPayment",
                web_app=WebAppInfo(url=WEB_APP_URL),
            )
        ]
    ],
    resize_keyboard=True,
)


# =========================
# Проверка администратора
# =========================

def is_admin(user_id):
    return ADMIN_ID != 0 and user_id == ADMIN_ID


# =========================
# Пользователь
# =========================

def save_user(message: Message):
    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (telegram_id, first_name, username)
        VALUES (?, ?, ?)
        """,
        (
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username,
        ),
    )

    connection.commit()
    connection.close()


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    save_user(message)

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в SwapPayment.\n\n"
        "Нажми кнопку ниже, чтобы открыть обменник.",
        reply_markup=start_keyboard,
    )


# =========================
# /id
# =========================

@dp.message(F.text == "/id")
async def id_handler(message: Message):
    await message.answer(
        f"🆔 Твой Telegram ID:\n\n"
        f"{message.from_user.id}"
    )


# =========================
# Кнопки статуса
# =========================

def order_keyboard(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟡 В работе",
                    callback_data=f"status:{order_id}:working",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Выполнена",
                    callback_data=f"status:{order_id}:completed",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменена",
                    callback_data=f"status:{order_id}:cancelled",
                )
            ],
        ]
    )


# =========================
# Названия статусов
# =========================

def status_text(status):
    statuses = {
        "new": "🆕 Новая",
        "working": "🟡 В работе",
        "completed": "✅ Выполнена",
        "cancelled": "❌ Отменена",
    }

    return statuses.get(status, status)


# =========================
# Текст заявки
# =========================

def order_text(order):
    order_id, currency, amount, result, status = order

    return (
        f"📋 Заявка №{order_id}\n\n"
        f"Валюта: {currency}\n"
        f"Сумма: {amount}\n"
        f"Получаете: {result}\n\n"
        f"Статус: {status_text(status)}"
    )


# =========================
# Уведомление клиенту
# =========================

def client_status_text(order_id, status):
    messages = {
        "working": (
            f"🟡 Ваша заявка №{order_id} взята в работу.\n\n"
            "Ожидайте завершения обмена."
        ),
        "completed": (
            f"✅ Ваша заявка №{order_id} выполнена.\n\n"
            "Спасибо за использование SwapPayment!"
        ),
        "cancelled": (
            f"❌ Ваша заявка №{order_id} отменена.\n\n"
            "Если это произошло по ошибке, свяжитесь с администратором."
        ),
    }

    return messages.get(status)


# =========================
# /orders
# =========================

@dp.message(F.text == "/orders")
async def orders_handler(message: Message):

    if not is_admin(message.from_user.id):
        await message.answer(
            "❌ У вас нет доступа к списку заявок."
        )
        return

    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, currency, amount, result, status
        FROM orders
        ORDER BY id DESC
        """
    )

    orders = cursor.fetchall()
    connection.close()

    if not orders:
        await message.answer("📋 Заявок пока нет.")
        return

    for order in orders:
        await message.answer(
            order_text(order),
            reply_markup=order_keyboard(order[0]),
        )


# =========================
# Изменение статуса
# =========================

@dp.callback_query(F.data.startswith("status:"))
async def change_status(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer(
            "❌ У вас нет доступа.",
            show_alert=True,
        )
        return

    try:
        _, order_id, new_status = callback.data.split(":")
        order_id = int(order_id)

    except (ValueError, AttributeError):
        await callback.answer("❌ Ошибка")
        return

    connection = sqlite3.connect("swap.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, telegram_id, currency, amount, result, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    )

    order = cursor.fetchone()

    if not order:
        connection.close()

        await callback.answer(
            "❌ Заявка не найдена",
            show_alert=True,
        )
        return

    (
        order_id,
        client_id,
        currency,
        amount,
        result,
        old_status,
    ) = order

    # Если статус уже такой же
    if old_status == new_status:
        connection.close()

        await callback.answer(
            f"Статус уже: {status_text(new_status)}"
        )
        return

    # Меняем статус
    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (new_status, order_id),
    )

    connection.commit()

    updated_order = (
        order_id,
        currency,
        amount,
        result,
        new_status,
    )

    connection.close()

    # Обновляем сообщение администратора
    await callback.message.edit_text(
        order_text(updated_order),
        reply_markup=order_keyboard(order_id),
    )

    # Уведомляем клиента
    client_message = client_status_text(
        order_id,
        new_status,
    )

    if client_message:

        try:
            await callback.bot.send_message(
                chat_id=client_id,
                text=client_message,
            )

        except Exception as error:
            print(
                f"❌ Не удалось уведомить клиента "
                f"{client_id}: {error}"
            )

    await callback.answer("Статус изменён ✅")


# =========================
# Получение заявки из Mini App
# =========================

@dp.message(lambda message: message.web_app_data)
async def webapp_order(message: Message):

    try:
        data = json.loads(message.web_app_data.data)

        currency = data["currency"]
        amount = data["amount"]
        result = data["result"]

    except (json.JSONDecodeError, KeyError, TypeError) as error:

        print(f"❌ Ошибка данных Mini App: {error}")

        await message.answer(
            "❌ Не удалось обработать заявку.\n"
            "Попробуйте ещё раз."
        )

        return

    save_user(message)

    order_id = create_order(
        telegram_id=message.from_user.id,
        currency=currency,
        amount=amount,
        result=result,
    )

    # Сообщение клиенту
    await message.answer(
        f"✅ Заявка №{order_id} создана!\n\n"
        f"Валюта: {currency}\n"
        f"Сумма: {amount}\n"
        f"Получаете: {result}"
    )

    # =========================
    # Уведомление администратора
    # =========================

    if ADMIN_ID != 0:

        admin_text = (
            f"🔔 НОВАЯ ЗАЯВКА №{order_id}\n\n"
            f"👤 Клиент: {message.from_user.first_name}\n"
            f"🆔 Telegram ID: {message.from_user.id}\n\n"
            f"💱 Валюта: {currency}\n"
            f"💰 Сумма: {amount}\n"
            f"💵 Получает: {result}\n\n"
            f"Статус: 🆕 Новая"
        )

        try:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                reply_markup=order_keyboard(order_id),
            )

        except Exception as error:
            print(
                f"❌ Не удалось отправить уведомление "
                f"администратору: {error}"
            )

    print(
        f"Новая заявка #{order_id}: "
        f"{data}"
    )


# =========================
# Запуск
# =========================

async def main():

    init_db()

    bot = Bot(token=TOKEN)

    print("✅ Бот запущен!")

    try:
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())