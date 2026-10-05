"""
Main Telegram Bot & Server for Kazakhstan Restaurant Booking System.
Runs Aiogram 3 bot and aiohttp REST API server concurrently.
"""

from __future__ import annotations
import asyncio
import json
import html
import os
import re
import sys
import subprocess
from typing import Optional, Dict, List, Any

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
from api import create_web_app, SUPER_ADMIN_KEY

# --- Configuration ---
_env_token = os.getenv("BOT_TOKEN", "")
if not _env_token:
    # WARNING: Hardcoded token is for development only!
    # In production, set BOT_TOKEN environment variable.
    print("[WARNING] BOT_TOKEN env variable not set! Using hardcoded fallback.")
    _env_token = "8992817194:AAH0Q0K35pCfS_ZHLBoTP334KsSfECUT5PY"
TOKEN = _env_token

# Custom domain for RestoKZ WebApp
WEBAPP_BASE_URL = os.getenv("WEBAPP_URL", "https://resto.cortexishub.com/")

# Admin Telegram user IDs (Primary owner + multi-admin support)
PRIMARY_ADMIN_ID = 348581961
raw_admin_env = os.getenv("ADMIN_CHAT_IDS") or os.getenv("ADMIN_CHAT_ID", str(PRIMARY_ADMIN_ID))
ADMIN_CHAT_ID = int(raw_admin_env.split(",")[0].strip()) if raw_admin_env else PRIMARY_ADMIN_ID

def is_admin(user_id: Optional[int]) -> bool:
    """Checks whether user_id is an authorized bot administrator."""
    if not user_id:
        return False
    return database.is_bot_admin(user_id)

def get_admin_recipients(booking: dict = None) -> List[int]:
    """Returns list of Telegram user IDs who should receive admin alerts."""
    recipients = set()
    if booking and booking.get("admin_tg_id"):
        recipients.add(booking["admin_tg_id"])
    for a in database.get_bot_admins():
        recipients.add(a["user_id"])
    if not recipients:
        recipients.add(ADMIN_CHAT_ID)
    return list(recipients)

# HTTP port — Railway sets PORT automatically; locally defaults to 8080
PORT = int(os.getenv("PORT", "8080"))

def get_api_url() -> str:
    """
    Returns the public HTTPS URL of this API server.
    Priority:
      1. API_BASE_URL or TUNNEL_URL env var (explicit override)
      2. RAILWAY_PUBLIC_DOMAIN env var (set automatically by Railway)
      3. Default production URL on Railway
    """
    # 1. Explicit override via env
    env_url = (os.getenv("API_BASE_URL") or os.getenv("TUNNEL_URL", "")).strip()
    if env_url:
        return env_url

    # 2. Railway auto-injects RAILWAY_PUBLIC_DOMAIN (e.g. "restokz-bot-production.up.railway.app")
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain}"

    # 3. Default production Railway backend
    return "https://restokz-bot-production.up.railway.app"

def get_webapp_url(tab: str = None, user_id: int = None) -> str:
    """Builds the full WebApp URL with API backend and credentials injected."""
    api_url = get_api_url()
    base = WEBAPP_BASE_URL.rstrip("/")
    if tab == "admin":
        url = f"{base}/admin.html?api={api_url}"
        if user_id and is_admin(user_id):
            url += f"&super_key={SUPER_ADMIN_KEY}&tg_user_id={user_id}"
        return url
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
    if is_admin(user_id):
        buttons.append([
            KeyboardButton(text="👑 Терминал RestoKZ PRO", web_app=WebAppInfo(url=get_webapp_url("admin", user_id))),
            KeyboardButton(text="🛡️ Управление подписками")
        ])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = html.escape(message.from_user.first_name)
    kb = get_main_keyboard(message.from_user.id)

    inline_rows = []
    if is_admin(message.from_user.id):
        inline_rows.append([
            InlineKeyboardButton(
                text="👑 Терминал RestoKZ PRO (Хостес & Подписки)",
                web_app=WebAppInfo(url=get_webapp_url("admin", message.from_user.id))
            )
        ])
    inline_rows.append([
        InlineKeyboardButton(
            text="🚀 Открыть каталог ресторанов",
            web_app=WebAppInfo(url=get_webapp_url())
        )
    ])
    inline_rows.append([
        InlineKeyboardButton(
            text="📋 Мои брони",
            web_app=WebAppInfo(url=get_webapp_url("my_bookings"))
        ),
        InlineKeyboardButton(
            text="ℹ️ О сервисе",
            callback_data="about_service"
        )
    ])

    inline_kb = InlineKeyboardMarkup(inline_keyboard=inline_rows)

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

def build_subscriptions_text_and_keyboard():
    subs = database.get_all_subscriptions()
    active_count = sum(1 for s in subs if s["subscription_info"]["is_active"] and not s["subscription_info"]["is_trial"])
    trial_count = sum(1 for s in subs if s["subscription_info"]["is_trial"])
    expired_count = sum(1 for s in subs if not s["subscription_info"]["is_active"])

    text = (
        "👑 <b>Управление лицензиями & Подписками RestoKZ PRO</b>\n\n"
        f"📊 Всего подключено: <b>{len(subs)}</b> заведений\n"
        f"🟢 Активных подписок: <b>{active_count}</b>\n"
        f"🟡 На тестировании (Trial): <b>{trial_count}</b>\n"
        f"🔴 Истекших / Блок: <b>{expired_count}</b>\n\n"
        "<i>Нажмите на кнопки заведений ниже для быстрого продления или смены статуса:</i>\n"
    )

    inline_rows = []
    for s in subs:
        sub_info = s["subscription_info"]
        status_icon = "🟢" if sub_info["is_active"] and not sub_info["is_trial"] else ("🟡" if sub_info["is_trial"] else "🔴")
        r_name = s["name"]
        days = sub_info["days_left"]
        r_id = s["id"]
        key = s.get("access_key") or "—"

        text += (
            f"\n{status_icon} <b>{r_name}</b> ({s['city']})\n"
            f"├ Статус: <b>{sub_info['status'].upper()}</b> (осталось <b>{days} дн.</b>)\n"
            f"├ До: <code>{sub_info['expires_at_human']}</code> | Тариф: <b>{sub_info['plan'].upper()}</b>\n"
            f"└ 🔑 Ключ: <code>{key}</code>\n"
        )

        inline_rows.append([
            InlineKeyboardButton(text=f"{r_name[:12]}: +30 дн", callback_data=f"sub_ext_{r_id}_30"),
            InlineKeyboardButton(text=f"+7 дн тест", callback_data=f"sub_ext_{r_id}_7")
        ])

    inline_rows.append([
        InlineKeyboardButton(
            text="👑 Открыть панель лицензий в WebApp", 
            web_app=WebAppInfo(url=get_webapp_url("admin", user_id or ADMIN_CHAT_ID))
        )
    ])
    return text, InlineKeyboardMarkup(inline_keyboard=inline_rows)

def build_admins_text_and_keyboard() -> tuple:
    """Builds formatted list of bot administrators and inline control buttons."""
    admins = database.get_bot_admins()
    text = (
        "👑 <b>СПИСОК АДМИНИСТРАТОРОВ RestoKZ PRO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Все администраторы имеют полный доступ к:\n"
        "• Терминалу управления заведениями и залами\n"
        "• Уведомлениям о бронированиях в Telegram\n"
        "• Подтверждению и отмене броней\n"
        "• Управлению тарифами и лицензиями\n\n"
    )

    inline_rows = []
    for a in admins:
        u_id = a["user_id"]
        u_name = a.get("full_name") or "Администратор"
        u_login = f"@{a['username']}" if a.get("username") else "—"
        added_at = a.get("added_at") or "—"
        is_owner = (u_id == PRIMARY_ADMIN_ID)
        badge = "⭐️ Владелец (Owner)" if is_owner else "👑 Super Admin"

        text += (
            f"👤 <b>{html.escape(u_name)}</b> {badge}\n"
            f"├ ID: <code>{u_id}</code>\n"
            f"├ Telegram: {u_login}\n"
            f"└ Добавлен: <code>{added_at}</code>\n\n"
        )

        if not is_owner:
            inline_rows.append([
                InlineKeyboardButton(
                    text=f"❌ Удалить админа {u_id}",
                    callback_data=f"del_admin_{u_id}"
                )
            ])

    text += (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "➕ <b>Чтобы добавить нового админа:</b>\n"
        "Отправьте команду:\n"
        "<code>/addadmin &lt;TG_ID&gt; [Имя]</code>\n"
        "<i>Например: <code>/addadmin 123456789 Дамир</code></i>"
    )

    inline_rows.append([
        InlineKeyboardButton(text="🔄 Обновить список", callback_data="btn_show_admins")
    ])

    return text, InlineKeyboardMarkup(inline_keyboard=inline_rows)

@dp.message(F.text == "🛡️ Управление подписками")
@dp.message(Command("subscriptions"))
@dp.message(Command("subs"))
async def cmd_subscriptions(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора платформы.")
        return
    text, kb = build_subscriptions_text_and_keyboard(message.from_user.id)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("sub_ext_"))
async def cb_extend_subscription(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    parts = callback.data.split("_")
    rest_id = int(parts[2])
    days = int(parts[3])

    status = "trial" if days <= 14 else "active"
    updated = database.extend_subscription(rest_id, days=days, status=status)
    if not updated:
        await callback.answer("Ресторан не найден", show_alert=True)
        return

    sub_info = updated["subscription_info"]
    await callback.answer(f"✅ Подписка для {updated['name']} продлена на +{days} дней!\nДействует до {sub_info['expires_at_human']}", show_alert=True)

    # Refresh message
    text, kb = build_subscriptions_text_and_keyboard(callback.from_user.id)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора заведения.")
        return

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Открыть панель ресторана (Хостес)",
                web_app=WebAppInfo(url=get_webapp_url("admin", message.from_user.id))
            )
        ],
        [
            InlineKeyboardButton(
                text="🛡️ Управление подписками & Лицензиями",
                callback_data="btn_show_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Список администраторов бота",
                callback_data="btn_show_admins"
            )
        ]
    ])
    await message.answer(
        "👋 <b>Панель Супер-Администратора RestoKZ PRO</b>\n\n"
        "Здесь вы можете управлять всеми заведениями, просматривать бронирования, назначать администраторов, а также выдавать и продлевать подписки ресторанам.",
        reply_markup=admin_kb,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "btn_show_subscriptions")
async def cb_show_subscriptions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await callback.answer()
    text, kb = build_subscriptions_text_and_keyboard(callback.from_user.id)
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "btn_show_admins")
async def cb_show_admins(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    await callback.answer()
    text, kb = build_admins_text_and_keyboard()
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("del_admin_"))
async def cb_del_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    try:
        target_id = int(callback.data.split("_")[2])
    except Exception:
        await callback.answer("Неверный ID", show_alert=True)
        return

    if target_id == PRIMARY_ADMIN_ID:
        await callback.answer("❌ Нельзя удалить создателя бота!", show_alert=True)
        return

    database.remove_bot_admin(target_id)
    await callback.answer(f"✅ Администратор {target_id} удален!", show_alert=True)
    text, kb = build_admins_text_and_keyboard()
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass

@dp.message(Command("admins"))
async def cmd_admins(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    text, kb = build_admins_text_and_keyboard()
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.message(Command("addadmin"))
async def cmd_add_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав супер-администратора.")
        return

    target_id = None
    target_username = None
    target_name = None

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) >= 2 and parts[1].isdigit():
        target_id = int(parts[1])
        if len(parts) >= 3:
            target_name = parts[2].strip()
    elif message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username
        target_name = message.reply_to_message.from_user.full_name
        if len(parts) >= 2:
            target_name = parts[1].strip()

    if not target_id:
        await message.answer(
            "ℹ️ <b>Как назначить нового администратора:</b>\n\n"
            "1. Отправьте команду с Telegram ID человека:\n"
            "<code>/addadmin 123456789 Дамир</code>\n\n"
            "2. Либо ответьте (reply) командой <code>/addadmin</code> на сообщение нужного человека в чате.\n\n"
            "<i>(Узнать Telegram ID собеседник может в боте @userinfobot или переслав любое сообщение)</i>",
            parse_mode="HTML"
        )
        return

    database.add_bot_admin(
        user_id=target_id,
        username=target_username,
        full_name=target_name or f"Админ #{target_id}",
        added_by=message.from_user.id
    )

    try:
        await bot.send_message(
            chat_id=target_id,
            text="👑 <b>Поздравляем! Вам выданы права администратора RestoKZ PRO.</b>\n\n"
                 "Вам стали доступны:\n"
                 "• Терминал управления ресторанами и рассадкой гостей\n"
                 "• Уведомления о новых бронированиях с кнопками подтверждения\n"
                 "• Управление лицензиями и заведениями (/admin, /subs)\n\n"
                 "Нажмите /start чтобы обновить меню бота.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ <b>Новый администратор успешно добавлен!</b>\n\n"
        f"👤 ID: <code>{target_id}</code>\n"
        f"📝 Имя: <b>{html.escape(target_name or 'Администратор')}</b>\n"
        f"🔑 Статус: <b>Super Admin</b>\n\n"
        f"Пользователь получил полный доступ к терминалу и уведомлениям о бронированиях.",
        parse_mode="HTML"
    )

@dp.message(Command("deladmin"))
async def cmd_del_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав супер-администратора.")
        return

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: <code>/deladmin &lt;TG_ID&gt;</code>", parse_mode="HTML")
        return

    target_id = int(parts[1])
    if target_id == PRIMARY_ADMIN_ID:
        await message.answer("❌ Нельзя удалить создателя и главного владельца бота.")
        return

    success = database.remove_bot_admin(target_id)
    if success:
        await message.answer(f"✅ Администратор с ID <code>{target_id}</code> успешно удален.", parse_mode="HTML")
    else:
        await message.answer(f"Пользователь с ID <code>{target_id}</code> не найден в списке администраторов.", parse_mode="HTML")

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

    admin_id = booking.get("admin_tg_id")
    if callback.from_user.id != admin_id and not is_admin(callback.from_user.id):
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

    admin_id = booking.get("admin_tg_id")
    if callback.from_user.id != admin_id and not is_admin(callback.from_user.id):
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
    """Sends detailed reservation card to all restaurant admins on Telegram."""
    recipients = get_admin_recipients(booking)
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

    for a_id in recipients:
        try:
            await bot.send_message(chat_id=a_id, text=text, reply_markup=admin_kb, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to send admin notification to {a_id}: {e}")

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
    try:
        database.init_db()
        print("[OK] База данных готова.")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации базы данных: {e}")

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
    admins = database.get_bot_admins()
    admin_list_str = ", ".join(f"{a['user_id']} ({a.get('full_name') or 'Admin'})" for a in admins)
    print(f"[OK] Администраторы: {admin_list_str or ADMIN_CHAT_ID}")
    print("=" * 55)
    print("[OK] Запуск Telegram бота RestoKZ (polling)...")

    try:
        # Clear any lingering webhook and drop old updates
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            print("[OK] Telegram webhook очищен.")
        except Exception as e:
            print(f"[WARNING] Не удалось сбросить webhook: {e}")

        # Polling retry loop — prevents container crash during deployment rolling restarts
        while True:
            try:
                await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[WARNING] Ошибка Telegram polling: {e}. Повторная попытка через 5 сек...")
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[ERROR] Неперехваченная ошибка в bot.py: {e}")
    finally:
        print("[SHUTDOWN] Остановка сервера...")
        try:
            await runner.cleanup()
        except Exception:
            pass
        try:
            await bot.session.close()
        except Exception:
            pass
        print("[SHUTDOWN] Сервер остановлен.")

if __name__ == "__main__":
    asyncio.run(main())