"""
Main Telegram Bot & Server for Kazakhstan Restaurant Booking System.
Runs Aiogram 3 bot and aiohttp REST API server concurrently.
"""

import asyncio
import json
import html
import os
import re
import sys
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, 
    CallbackQuery,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo
)

import database
from api import create_web_app

# --- Configuration ---
_env_token = os.getenv("BOT_TOKEN", "")
if not _env_token:
    # WARNING: Hardcoded token is for development only!
    # In production, set BOT_TOKEN environment variable.
    print("[WARNING] BOT_TOKEN env variable not set! Using hardcoded fallback.")
    _env_token = "8992817194:AAH0Q0K35pCfS_ZHLBoTP334KsSfECUT5PY"
TOKEN = _env_token

# GitHub Pages URL where the SPA frontend is automatically deployed on every git push
WEBAPP_BASE_URL = os.getenv("WEBAPP_URL", "https://sp1ceman.github.io/restokz-bot/")

# Admin Telegram user ID
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "348581961"))

# HTTP port — Railway sets PORT automatically; locally defaults to 8080
PORT = int(os.getenv("PORT", "8080"))

def get_api_url() -> str:
    """
    Returns the public HTTPS URL of this API server.
    Priority:
      1. TUNNEL_URL env var (explicit override — also used for Railway static domain)
      2. RAILWAY_PUBLIC_DOMAIN env var (set automatically by Railway)
      3. tunnel_url.txt file (written by tunnel.py for local development)
      4. Fallback to localtunnel default subdomain
    """
    # 1. Explicit override via env
    env_url = os.getenv("TUNNEL_URL", "").strip()
    if env_url:
        return env_url

    # 2. Railway auto-injects RAILWAY_PUBLIC_DOMAIN (e.g. "restokz.up.railway.app")
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain}"

    # 3. Local development: tunnel.py writes the URL to tunnel_url.txt
    try:
        txt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tunnel_url.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                saved = f.read().strip()
                if saved.startswith("http"):
                    return saved
    except Exception:
        pass

    # 4. Fallback
    return "https://restokz-app.loca.lt"

def get_webapp_url(tab: str = None) -> str:
    """Builds the full WebApp URL with API backend injected as a query parameter."""
    api_url = get_api_url()
    base = WEBAPP_BASE_URL.rstrip("/")
    if tab == "admin":
        return f"{base}/admin.html?api={api_url}"
    url = f"{base}/?api={api_url}"
    if tab:
        url += f"&tab={tab}"
    return url

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Returns main reply keyboard with WebApp launch buttons."""
    buttons = [
        [KeyboardButton(text="🍽 Забронировать столик", web_app=WebAppInfo(url=get_webapp_url()))],
        [KeyboardButton(text="📋 Мои бронирования", web_app=WebAppInfo(url=get_webapp_url("my_bookings")))]
    ]

    # If the user is an admin or restaurant manager, give direct access to the restaurant panel
    if user_id == ADMIN_CHAT_ID:
        buttons.append([KeyboardButton(text="👑 Панель ресторана", web_app=WebAppInfo(url=get_webapp_url("admin")))])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = html.escape(message.from_user.first_name)
    kb = get_main_keyboard(message.from_user.id)

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Открыть каталог ресторанов",
                web_app=WebAppInfo(url=get_webapp_url())
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Мои брони",
                web_app=WebAppInfo(url=get_webapp_url("my_bookings"))
            ),
            InlineKeyboardButton(
                text="ℹ️ О сервисе",
                callback_data="about_service"
            )
        ]
    ])

    text = (
        f"Саламатсыз ба, <b>{user_name}</b>! 👋\n\n"
        "Добро пожаловать в единую систему онлайн-бронирования ресторанов Казахстана! 🇰🇿🍽\n\n"
        "С нашим сервисом вы можете:\n"
        "• 🔍 Выбирать лучшие рестораны в <b>Алматы, Астане и Шымкенте</b>\n"
        "• 📖 Изучать актуальное <b>меню с ценами в тенге (₸)</b>\n"
        "• 🪑 Бронировать конкретный <b>столик на интерактивной схеме</b>\n"
        "• ⚡ Получать моментальное подтверждение от заведения\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение:"
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")
    await message.answer("Или откройте сразу через меню:", reply_markup=inline_kb)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        await message.answer("У вас нет прав администратора заведения.")
        return

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Открыть панель ресторана (Хостес)",
                web_app=WebAppInfo(url=get_webapp_url("admin"))
            )
        ]
    ])
    await message.answer(
        "👋 <b>Панель администратора заведения</b>\n\n"
        "Здесь вы можете в реальном времени видеть бронирования, контакты гостей, управлять статусами и занятостью столиков.",
        reply_markup=admin_kb,
        parse_mode="HTML"
    )

@dp.message(Command("my_bookings"))
async def cmd_my_bookings(message: Message):
    bookings = database.get_user_bookings(message.from_user.id)
    if not bookings:
        await message.answer(
            "У вас пока нет активных бронирований.\n"
            "Нажмите «🍽 Забронировать столик», чтобы выбрать ресторан!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    text = "📋 <b>Ваши бронирования:</b>\n\n"
    for b in bookings[:5]:
        status_icon = {
            "pending": "⏳ В ожидании",
            "confirmed": "✅ Подтверждено",
            "rejected": "❌ Отклонено",
            "completed": "🏁 Завершено"
        }.get(b["status"], b["status"])

        text += (
            f"📍 <b>{b['restaurant_name']}</b>\n"
            f"📅 {b['booking_date']} в {b['booking_time']}\n"
            f"🪑 Стол №{b['table_number']} ({b['table_zone']}) | {b['guests_count']} чел.\n"
            f"Статус: <b>{status_icon}</b>\n\n"
        )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📱 Открыть в приложении", 
            web_app=WebAppInfo(url=get_webapp_url("my_bookings"))
        )
    ]])
    await message.answer(text, reply_markup=inline_kb, parse_mode="HTML")

@dp.callback_query(F.data == "about_service")
async def cb_about_service(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🇰🇿 <b>О сервисе RestoKZ:</b>\n\n"
        "Мы объединяем лучшие заведения Казахстана в удобном Telegram Mini App формате. "
        "Никаких долгих звонков — бронируйте любимый столик за 10 секунд прямо в Telegram!",
        parse_mode="HTML"
    )

# --- Booking Status Callback Handlers (Admin buttons) ---

@dp.callback_query(F.data.startswith("app_confirm_"))
async def admin_confirm_booking(callback: CallbackQuery):
    try:
        booking_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка в ID брони", show_alert=True)
        return

    booking = database.get_booking_details(booking_id)
    if not booking:
        await callback.answer("Бронь не найдена", show_alert=True)
        return

    admin_id = booking.get("admin_tg_id") or ADMIN_CHAT_ID
    if callback.from_user.id != admin_id and callback.from_user.id != ADMIN_CHAT_ID:
        await callback.answer("У вас нет прав для управления этой бронью", show_alert=True)
        return

    database.update_booking_status(booking_id, "confirmed")
    updated_booking = database.get_booking_details(booking_id)

    # Notify Guest
    await notify_guest_status_change(updated_booking, "confirmed")

    # Update Admin Message
    orig_text = callback.message.html_text or ""
    # Strip old status lines if any
    clean_text = re.sub(r"\n\n.*СТАТУС:.*", "", orig_text)
    new_text = f"{clean_text}\n\n✅ <b>СТАТУС: ПОДТВЕРЖДЕНО МЕНЕДЖЕРОМ</b>"

    await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
    await callback.answer("Бронь успешно подтверждена!")

@dp.callback_query(F.data.startswith("app_cancel_"))
async def admin_cancel_booking(callback: CallbackQuery):
    try:
        booking_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка в ID брони", show_alert=True)
        return

    booking = database.get_booking_details(booking_id)
    if not booking:
        await callback.answer("Бронь не найдена", show_alert=True)
        return

    admin_id = booking.get("admin_tg_id") or ADMIN_CHAT_ID
    if callback.from_user.id != admin_id and callback.from_user.id != ADMIN_CHAT_ID:
        await callback.answer("У вас нет прав для управления этой бронью", show_alert=True)
        return

    database.update_booking_status(booking_id, "rejected")
    updated_booking = database.get_booking_details(booking_id)

    # Notify Guest
    await notify_guest_status_change(updated_booking, "rejected")

    # Update Admin Message
    orig_text = callback.message.html_text or ""
    clean_text = re.sub(r"\n\n.*СТАТУС:.*", "", orig_text)
    new_text = f"{clean_text}\n\n❌ <b>СТАТУС: ОТКЛОНЕНО МЕНЕДЖЕРОМ</b>"

    await callback.message.edit_text(new_text, parse_mode="HTML", reply_markup=None)
    await callback.answer("Бронь отклонена.")

# --- Backward compatibility: handle direct web_app_data if submitted via keyboard ---
# --- WebApp direct data handler (if submitted via tg.sendData) ---
@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        restaurant_id = int(data.get("restaurant_id", 1))
        table_num = int(data.get("table_number") or data.get("number", 1))
        table = database.get_table_by_number(restaurant_id, table_num)
        table_id = table["id"] if table else int(data.get("table_id", 1))

        guests_count = int(data.get("guests_count", 2))
        booking_date = str(data.get("booking_date") or data.get("date") or "сегодня")
        booking_time = str(data.get("booking_time") or data.get("time") or "19:00")
        guest_name = str(data.get("guest_name") or message.from_user.full_name)
        guest_phone = str(data.get("guest_phone") or data.get("phone") or "не указан")
        wishes = str(data.get("wishes") or "")

        # Save to SQLite database
        booking_id = database.create_booking(
            restaurant_id=restaurant_id,
            table_id=table_id,
            guest_tg_id=message.from_user.id,
            guest_username=message.from_user.username,
            guest_name=guest_name,
            guest_phone=guest_phone,
            booking_date=booking_date,
            booking_time=booking_time,
            guests_count=guests_count,
            wishes=wishes
        )
        booking = database.get_booking_details(booking_id)

        await message.answer(
            f"⏳ <b>Заявка #{booking_id} на Стол №{table_num} отправлена!</b>\n"
            f"📍 Ресторан: <b>{html.escape(booking['restaurant_name'])}</b>\n"
            f"📅 Дата и время: <b>{booking_date} в {booking_time}</b>\n\n"
            "Ожидайте подтверждения от администратора заведения...",
            parse_mode="HTML"
        )

        # Notify Admin via unified card with confirm/cancel buttons
        if booking:
            await notify_admin_new_booking(booking)
    except Exception as e:
        print(f"Error handling web_app_data: {e}")

# --- Notification Functions invoked from REST API ---

async def notify_admin_new_booking(booking: dict):
    """Sends detailed reservation card to the restaurant admin on Telegram."""
    admin_id = booking.get("admin_tg_id") or ADMIN_CHAT_ID
    booking_id = booking["id"]
    guest_username = f"@{booking['guest_username']}" if booking.get("guest_username") else "не указан"
    phone = booking["guest_phone"]
    phone_clean = re.sub(r"[^\d+]", "", phone)

    text = (
        f"🚨 <b>НОВАЯ ЗАЯВКА НА БРОНИРОВАНИЕ #{booking_id}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>Ресторан:</b> {html.escape(booking['restaurant_name'])}\n"
        f"📅 <b>Дата и время:</b> {booking['booking_date']} в {booking['booking_time']}\n"
        f"👥 <b>Количество гостей:</b> {booking['guests_count']} чел.\n"
        f"🪑 <b>Столик:</b> №{booking['table_number']} ({booking.get('table_zone', 'Зал')}, до {booking.get('table_seats', 4)} чел.)\n\n"
        f"👤 <b>Гость:</b> {html.escape(booking['guest_name'])}\n"
        f"🔗 <b>Telegram:</b> {guest_username}\n"
        f"📞 <b>Телефон:</b> <code>{html.escape(phone)}</code>\n"
        f"💬 <b>Пожелания:</b> {html.escape(booking.get('wishes') or 'Нет особых пожеланий')}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите действие:"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"app_confirm_{booking_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"app_cancel_{booking_id}")
        ]
    ])

    try:
        await bot.send_message(chat_id=admin_id, text=text, reply_markup=admin_kb, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to send admin notification to {admin_id}: {e}")

async def notify_guest_status_change(booking: dict, status: str):
    """Sends immediate status update to the guest via Telegram bot."""
    guest_tg_id = booking.get("guest_tg_id")
    if not guest_tg_id:
        return

    rest_name = html.escape(booking["restaurant_name"])
    rest_addr = html.escape(booking.get("restaurant_address", ""))
    rest_phone = html.escape(booking.get("restaurant_phone", ""))
    table_num = booking["table_number"]
    date_str = booking["booking_date"]
    time_str = booking["booking_time"]
    guests_cnt = booking["guests_count"]

    if status == "confirmed":
        text = (
            f"🎉 <b>Ваша бронь подтверждена!</b>\n\n"
            f"📍 <b>Ресторан:</b> {rest_name}\n"
            f"🏢 <b>Адрес:</b> {rest_addr}\n"
            f"📅 <b>Дата и время:</b> {date_str} в {time_str}\n"
            f"🪑 <b>Столик:</b> №{table_num} ({guests_cnt} чел.)\n"
            f"📞 <b>Контакты заведения:</b> {rest_phone}\n\n"
            "Ждем вас в назначенное время! Приятного вечера! ✨"
        )
    elif status == "rejected":
        text = (
            f"😔 <b>Заявка на бронирование отклонена</b>\n\n"
            f"К сожалению, ресторан «{rest_name}» не может принять бронь на <b>Стол №{table_num}</b> ({date_str} в {time_str}).\n\n"
            "Возможно, на это время зал полностью занят. Пожалуйста, откройте каталог и выберите другое время или столик:"
        )
    elif status == "completed":
        text = (
            f"🍽️ <b>Визит завершен</b>\n\n"
            f"Спасибо, что посетили ресторан «{rest_name}»! Надеемся, вам всё понравилось.\n"
            "Будем рады видеть вас снова! ✨"
        )
    elif status == "cancelled":
        text = (
            f"🚫 <b>Бронирование отменено</b>\n\n"
            f"Ваша бронь на Стол №{table_num} ({date_str} в {time_str}) в ресторане «{rest_name}» была отменена."
        )
    else:
        text = f"Статус вашей брони #{booking['id']} в «{rest_name}» изменен на: <b>{status}</b>."

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Мои бронирования", web_app=WebAppInfo(url=get_webapp_url("my_bookings")))
    ]])

    try:
        await bot.send_message(chat_id=guest_tg_id, text=text, reply_markup=inline_kb, parse_mode="HTML")
    except Exception as e:
        print(f"Failed to send guest notification to {guest_tg_id}: {e}")

# --- Main Entry Point ---

async def main():
    print("=" * 55)
    print("  RestoKZ — Restaurant Booking System")
    print("=" * 55)
    print(f"[DB]  Путь к базе данных: {database.DB_FILE}")
    print("Инициализация базы данных...")
    database.init_db()
    print("[OK] База данных готова.")

    # Create aiohttp web app
    app = create_web_app(
        notify_booking_func=notify_admin_new_booking,
        notify_status_func=notify_guest_status_change
    )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    try:
        await site.start()
        print(f"[OK] API сервер запущен на http://0.0.0.0:{PORT}")
    except OSError as e:
        # Port already in use (code 98 on Linux, 10048 on Windows)
        if e.errno in (98, 10048) or getattr(e, 'winerror', None) == 10048:
            print(f"\n[ERROR] Порт {PORT} уже занят!")
            print(f"        Остановите старый процесс или измените PORT.\n")
            await runner.cleanup()
            return
        raise

    api_url = get_api_url()
    print(f"[OK] Публичный API: {api_url}")
    print(f"[OK] WebApp URL:    {get_webapp_url()}")
    print(f"[OK] Admin TG ID:  {ADMIN_CHAT_ID}")
    print("=" * 55)
    print("[OK] Запуск Telegram бота RestoKZ (polling)...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        print("[SHUTDOWN] Остановка сервера...")
        await runner.cleanup()
        await bot.session.close()
        print("[SHUTDOWN] Сервер остановлен.")

if __name__ == "__main__":
    asyncio.run(main())