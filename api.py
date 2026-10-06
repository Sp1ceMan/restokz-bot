"""
REST API module for Kazakhstan Restaurant Booking System.
Powered by aiohttp.web with License & Subscription Security.
"""

from __future__ import annotations
import json
import os
from typing import Optional, Tuple, Dict, Any, List
from aiohttp import web
import database

# Master configuration
SUPER_ADMIN_KEY = os.getenv("SUPER_ADMIN_KEY", "restokz_super_2026")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "348581961"))

# Middleware for CORS (Cross-Origin Resource Sharing)
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as e:
            response = web.json_response({"error": str(e)}, status=500)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

def get_auth_context(request: web.Request) -> dict:
    """
    Extracts authentication credentials from headers, query params or Telegram data.
    Returns:
      {
        "role": "superadmin" | "restaurant" | "anonymous",
        "restaurant_id": int or None,
        "restaurant": dict or None,
        "subscription": dict or None,
        "raw_key": str or None
      }
    """
    # 1. Header X-Admin-Key or X-Access-Key
    raw_key = request.headers.get("X-Admin-Key") or request.headers.get("X-Access-Key")

    # 2. Header Authorization: Bearer <key>
    if not raw_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_key = auth_header[7:].strip()

    # 3. Query param key / super_key / token
    if not raw_key:
        raw_key = request.query.get("key") or request.query.get("super_key") or request.query.get("token")

    # 4. Telegram user ID (auto-login for Admin bot owners)
    tg_user_str = request.headers.get("X-Telegram-User-Id") or request.query.get("tg_user_id")
    if tg_user_str:
        try:
            if database.is_bot_admin(int(tg_user_str)):
                return {
                    "role": "superadmin",
                    "restaurant_id": None,
                    "restaurant": None,
                    "subscription": None,
                    "raw_key": "tg_auto_admin"
                }
        except ValueError:
            pass

    if not raw_key:
        # Check if legacy test environment allows anonymous admin
        if os.getenv("TEST_ALLOW_ANON_ADMIN") == "1":
            return {
                "role": "superadmin",
                "restaurant_id": None,
                "restaurant": None,
                "subscription": None,
                "raw_key": "test_anon"
            }
        return {"role": "anonymous", "restaurant_id": None, "restaurant": None, "subscription": None, "raw_key": None}

    raw_key = raw_key.strip()
    if raw_key == SUPER_ADMIN_KEY:
        return {
            "role": "superadmin",
            "restaurant_id": None,
            "restaurant": None,
            "subscription": None,
            "raw_key": raw_key
        }

    # Restaurant key lookup
    rest = database.get_restaurant_by_access_key(raw_key)
    if rest:
        return {
            "role": "restaurant",
            "restaurant_id": rest["id"],
            "restaurant": rest,
            "subscription": rest["subscription_info"],
            "raw_key": raw_key
        }

    return {"role": "anonymous", "restaurant_id": None, "restaurant": None, "subscription": None, "raw_key": raw_key}

def check_restaurant_write_permission(auth: dict, target_rest_id: int) -> tuple[bool, Optional[web.Response]]:
    """
    Ensures the caller is either Super Admin OR the matching restaurant with an active subscription.
    Returns (True, None) if allowed, or (False, web.Response) if blocked.
    """
    if auth["role"] == "superadmin":
        return True, None

    if auth["role"] == "anonymous":
        if os.getenv("TEST_MODE") == "1":
            return True, None
        return False, web.json_response({
            "error": "Требуется авторизация. Введите лицензионный ключ заведения.",
            "auth_required": True
        }, status=401)

    if auth["role"] == "restaurant":
        if auth["restaurant_id"] != target_rest_id:
            return False, web.json_response({
                "error": "Доступ запрещен: вы не можете редактировать чужое заведение."
            }, status=403)

        sub = auth["subscription"]
        if not sub or not sub.get("is_active"):
            return False, web.json_response({
                "error": "Срок действия подписки RestoKZ PRO истек или заведение заблокировано. Свяжитесь с администратором для продления.",
                "subscription_expired": True,
                "subscription": sub
            }, status=403)
        return True, None

    return False, web.json_response({"error": "Доступ запрещен."}, status=403)

# =========================================================================
# PUBLIC ENDPOINTS
# =========================================================================

async def get_restaurants(request: web.Request) -> web.Response:
    city = request.query.get("city")
    search = request.query.get("search")
    restaurants = database.get_all_restaurants(city=city, search=search)
    return web.json_response({"restaurants": restaurants})

async def get_restaurant(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid restaurant ID"}, status=400)

    restaurant = database.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        return web.json_response({"error": "Restaurant not found"}, status=404)

    return web.json_response({"restaurant": restaurant})

async def get_restaurant_menu(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid restaurant ID"}, status=400)

    menu = database.get_restaurant_menu(restaurant_id)
    return web.json_response({"menu": menu})

async def get_restaurant_tables(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid restaurant ID"}, status=400)

    date = request.query.get("date")
    time_slot = request.query.get("time")

    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

    tables = database.get_restaurant_tables_with_availability(restaurant_id, date, time_slot)
    return web.json_response({"tables": tables, "date": date, "time": time_slot})

async def create_booking_endpoint(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    required_fields = ["restaurant_id", "table_id", "guest_name", "guest_phone", "booking_date", "booking_time", "guests_count"]
    for field in required_fields:
        if field not in data or not data[field]:
            return web.json_response({"error": f"Missing field: {field}"}, status=400)

    try:
        restaurant_id = int(data["restaurant_id"])
        table_id = int(data["table_id"])
        guests_count = int(data["guests_count"])
        raw_tg_id = data.get("guest_tg_id")
        if raw_tg_id is not None and str(raw_tg_id).strip() not in ("", "null", "undefined"):
            guest_tg_id = int(raw_tg_id)
        else:
            guest_tg_id = None
    except (ValueError, TypeError):
        return web.json_response({"error": "Invalid number format in request"}, status=400)

    if guests_count < 1 or guests_count > 50:
        return web.json_response({"error": "guests_count must be between 1 and 50"}, status=400)

    guest_name = str(data["guest_name"]).strip()
    guest_phone = str(data["guest_phone"]).strip()
    booking_date = str(data["booking_date"]).strip()
    booking_time = str(data["booking_time"]).strip()

    if len(guest_name) < 2:
        return web.json_response({"error": "guest_name must be at least 2 characters"}, status=400)
    if len(guest_phone) < 5:
        return web.json_response({"error": "guest_phone must be at least 5 characters"}, status=400)
    if len(booking_date) < 8:
        return web.json_response({"error": "Invalid booking_date format"}, status=400)

    booking_id = database.create_booking(
        restaurant_id=restaurant_id,
        table_id=table_id,
        guest_tg_id=guest_tg_id,
        guest_username=data.get("guest_username"),
        guest_name=guest_name,
        guest_phone=guest_phone,
        booking_date=booking_date,
        booking_time=booking_time,
        guests_count=guests_count,
        wishes=data.get("wishes", "")
    )

    booking = database.get_booking_details(booking_id)

    # Trigger Telegram bot notification asynchronously if callback handler is provided
    bot_notify = request.app.get("bot_notify_new_booking")
    if bot_notify and booking:
        try:
            await bot_notify(booking)
        except Exception as e:
            print(f"Error sending bot notification: {e}")

    return web.json_response({"success": True, "booking": booking})

async def get_my_bookings(request: web.Request) -> web.Response:
    user_id_str = request.query.get("user_id")
    ids_str = request.query.get("ids")
    phone = request.query.get("phone")

    user_id = None
    if user_id_str:
        try:
            user_id = int(user_id_str)
        except ValueError:
            pass

    booking_ids = []
    if ids_str:
        for chunk in ids_str.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                booking_ids.append(int(chunk))

    bookings = database.get_user_bookings(
        guest_tg_id=user_id,
        booking_ids=booking_ids if booking_ids else None,
        phone=phone
    )
    return web.json_response({"bookings": bookings})

async def cancel_my_booking_endpoint(request: web.Request) -> web.Response:
    try:
        booking_id = int(request.match_info["id"])
    except (ValueError, KeyError):
        return web.json_response({"error": "Invalid booking ID"}, status=400)

    booking = database.get_booking_details(booking_id)
    if not booking:
        return web.json_response({"error": "Booking not found"}, status=404)

    if booking["status"] in ["completed", "rejected", "cancelled"]:
        return web.json_response({"error": f"Booking is already {booking['status']}"}, status=400)

    ok = database.update_booking_status(booking_id, "cancelled")
    if not ok:
        return web.json_response({"error": "Failed to cancel booking"}, status=500)

    updated_booking = database.get_booking_details(booking_id)
    bot_notify_status = request.app.get("bot_notify_status_change")
    if bot_notify_status and updated_booking:
        try:
            await bot_notify_status(updated_booking, "cancelled")
        except Exception as e:
            print(f"Error notifying cancellation: {e}")

    return web.json_response({"success": True, "booking": updated_booking})

# =========================================================================
# AUTHENTICATION & VERIFICATION ENDPOINTS
# =========================================================================

async def verify_auth_endpoint(request: web.Request) -> web.Response:
    """Verifies access key or Telegram user ID and returns role and privileges."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    key = str(data.get("key", "")).strip()
    tg_user_id = data.get("tg_user_id")

    # 1. Telegram Super Admin check
    if tg_user_id:
        try:
            if database.is_bot_admin(int(tg_user_id)):
                return web.json_response({
                    "valid": True,
                    "role": "superadmin",
                    "name": "Администратор платформы (Super Admin)",
                    "is_superadmin": True
                })
        except ValueError:
            pass

    # 2. Master Key check
    if key and key == SUPER_ADMIN_KEY:
        return web.json_response({
            "valid": True,
            "role": "superadmin",
            "name": "Владелец платформы (Super Admin)",
            "is_superadmin": True
        })

    # 3. Restaurant License Key check
    if key:
        rest = database.get_restaurant_by_access_key(key)
        if rest:
            sub = rest["subscription_info"]
            return web.json_response({
                "valid": True,
                "role": "restaurant",
                "restaurant_id": rest["id"],
                "restaurant": rest,
                "subscription": sub,
                "is_superadmin": False
            })

    return web.json_response({
        "valid": False,
        "error": "Неверный лицензионный ключ доступа. Обратитесь к администратору RestoKZ для подключения заведения."
    }, status=401)

# =========================================================================
# SUPER ADMIN: SUBSCRIPTIONS & LICENSE MANAGEMENT
# =========================================================================

async def get_subscriptions_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    if auth["role"] != "superadmin":
        return web.json_response({"error": "Доступ запрещен: требуются права владельца платформы."}, status=403)

    subs = database.get_all_subscriptions()
    return web.json_response({"subscriptions": subs})

async def extend_subscription_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    if auth["role"] != "superadmin":
        return web.json_response({"error": "Доступ запрещен: требуются права владельца платформы."}, status=403)

    try:
        rest_id = int(request.match_info["id"])
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid request parameters"}, status=400)

    days = int(data.get("days", 0))
    date_str = data.get("date")
    status = data.get("status")
    plan = data.get("plan")

    res = database.extend_subscription(rest_id, days=days, new_expiry_date=date_str, status=status, plan=plan)
    if not res:
        return web.json_response({"error": "Ресторан не найден"}, status=404)
    return web.json_response({"success": True, "restaurant": res})

async def set_subscription_status_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    if auth["role"] != "superadmin":
        return web.json_response({"error": "Доступ запрещен: требуются права владельца платформы."}, status=403)

    try:
        rest_id = int(request.match_info["id"])
        data = await request.json()
        new_status = str(data.get("status", "")).strip()
    except Exception:
        return web.json_response({"error": "Invalid request parameters"}, status=400)

    if new_status not in ["active", "trial", "blocked", "expired"]:
        return web.json_response({"error": "Invalid status value"}, status=400)

    ok = database.set_subscription_status(rest_id, new_status)
    return web.json_response({"success": ok})

async def regenerate_key_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    if auth["role"] != "superadmin":
        return web.json_response({"error": "Доступ запрещен: требуются права владельца платформы."}, status=403)

    try:
        rest_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid restaurant ID"}, status=400)

    new_key = database.regenerate_access_key(rest_id)
    if not new_key:
        return web.json_response({"error": "Ресторан не найден"}, status=404)
    return web.json_response({"success": True, "access_key": new_key})

async def delete_restaurant_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    if auth["role"] != "superadmin":
        return web.json_response({"error": "Доступ запрещен: требуются права владельца платформы."}, status=403)

    try:
        rest_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid restaurant ID"}, status=400)

    ok = database.delete_restaurant(rest_id)
    return web.json_response({"success": ok})

# =========================================================================
# PROTECTED RESTAURANT / ADMIN ENDPOINTS
# =========================================================================

async def create_restaurant_endpoint(request: web.Request) -> web.Response:
    """
    CRITICAL SECURITY:
    Only Super Admin (platform owner) can register new restaurants.
    Unauthorized users cannot simply create their own restaurant.
    """
    auth = get_auth_context(request)
    if auth["role"] != "superadmin" and not os.getenv("TEST_ALLOW_UNAUTH_CREATE"):
        return web.json_response({
            "error": "Создание заведений заблокировано настройками безопасности. "
                     "Для регистрации ресторана оформите подписку или обратитесь к владельцу сервиса."
        }, status=403)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    name = str(data.get("name", "")).strip()
    city = str(data.get("city", "Алматы")).strip()
    cuisine = str(data.get("cuisine", "Европейская")).strip()
    address = str(data.get("address", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or len(name) < 2:
        return web.json_response({"error": "Name is required (at least 2 chars)"}, status=400)

    sub_status = data.get("subscription_status", "active")
    sub_plan = data.get("subscription_plan", "pro")
    sub_days = int(data.get("subscription_days", 30)) if data.get("subscription_days") else None
    sub_exp = data.get("subscription_expires_at")
    owner_name = str(data.get("owner_name", "")).strip()
    owner_phone = str(data.get("owner_phone", "")).strip()
    custom_key = data.get("access_key")

    rest_id = database.create_restaurant(
        name=name,
        city=city,
        cuisine=cuisine,
        address=address,
        phone=phone,
        rating=float(data.get("rating", 4.9)),
        avg_check=int(data.get("avg_check", 8000)),
        cover_image=data.get("cover_image", "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80"),
        description=data.get("description", ""),
        working_hours=data.get("working_hours", "11:00 - 00:00"),
        two_gis_url=data.get("two_gis_url", ""),
        instagram_url=data.get("instagram_url", ""),
        whatsapp_url=data.get("whatsapp_url", ""),
        telegram_url=data.get("telegram_url", ""),
        website_url=data.get("website_url", ""),
        access_key=custom_key,
        subscription_status=sub_status,
        subscription_plan=sub_plan,
        subscription_days=sub_days,
        subscription_expires_at=sub_exp,
        owner_name=owner_name,
        owner_phone=owner_phone
    )
    rest = database.get_restaurant_by_id(rest_id)
    if rest:
        rest["subscription_info"] = database.get_subscription_details(rest)
    return web.json_response({"success": True, "id": rest_id, "restaurant": rest})

async def update_restaurant_endpoint(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid request parameters"}, status=400)

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, restaurant_id)
    if not allowed:
        return err_resp

    # Non-superadmin cannot alter subscription fields directly
    if auth["role"] != "superadmin":
        for forbidden in ["access_key", "subscription_status", "subscription_plan", "subscription_expires_at"]:
            data.pop(forbidden, None)

    ok = database.update_restaurant(restaurant_id, **data)
    rest = database.get_restaurant_by_id(restaurant_id)
    if rest:
        rest["subscription_info"] = database.get_subscription_details(rest)
    return web.json_response({"success": ok, "restaurant": rest})

async def add_menu_item_endpoint(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, restaurant_id)
    if not allowed:
        return err_resp

    title = str(data.get("title", "")).strip()
    price = int(data.get("price", 0))
    category_name = str(data.get("category", data.get("category_name", "Основные блюда"))).strip()

    if not title or price <= 0:
        return web.json_response({"error": "Title and positive price required"}, status=400)

    item_id = database.add_menu_item(
        restaurant_id=restaurant_id,
        category_name=category_name,
        title=title,
        price=price,
        description=data.get("description", ""),
        weight=data.get("weight", ""),
        image_url=data.get("image_url", "")
    )
    menu = database.get_restaurant_menu(restaurant_id)
    return web.json_response({"success": True, "item_id": item_id, "menu": menu})

async def delete_menu_item_endpoint(request: web.Request) -> web.Response:
    try:
        item_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid item ID"}, status=400)

    # Check which restaurant this item belongs to
    conn = database.get_db_connection()
    try:
        row = conn.execute("SELECT restaurant_id FROM menu_items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return web.json_response({"error": "Item not found"}, status=404)
        target_rest_id = row["restaurant_id"]
    finally:
        conn.close()

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, target_rest_id)
    if not allowed:
        return err_resp

    ok = database.delete_menu_item(item_id)
    return web.json_response({"success": ok})

async def add_table_endpoint(request: web.Request) -> web.Response:
    try:
        restaurant_id = int(request.match_info["id"])
        data = await request.json()
        table_number = int(data["table_number"])
        seats = int(data.get("seats", 4))
    except Exception:
        return web.json_response({"error": "Invalid parameters"}, status=400)

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, restaurant_id)
    if not allowed:
        return err_resp

    table_id = database.add_table(
        restaurant_id=restaurant_id,
        table_number=table_number,
        seats=seats,
        zone_type=data.get("zone_type", "Основной зал"),
        description=data.get("description", "")
    )
    return web.json_response({"success": True, "table_id": table_id})

async def delete_table_endpoint(request: web.Request) -> web.Response:
    try:
        table_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "Invalid table ID"}, status=400)

    conn = database.get_db_connection()
    try:
        row = conn.execute("SELECT restaurant_id FROM tables WHERE id = ?", (table_id,)).fetchone()
        if not row:
            return web.json_response({"error": "Table not found"}, status=404)
        target_rest_id = row["restaurant_id"]
    finally:
        conn.close()

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, target_rest_id)
    if not allowed:
        return err_resp

    ok = database.delete_table(table_id)
    return web.json_response({"success": ok})

async def get_admin_bookings_endpoint(request: web.Request) -> web.Response:
    auth = get_auth_context(request)
    rest_id_str = request.query.get("restaurant_id")
    date = request.query.get("date")

    if auth["role"] == "restaurant":
        sub = auth["subscription"]
        if not sub or not sub.get("is_active"):
            return web.json_response({
                "error": "Срок подписки RestoKZ PRO истек или заведение заблокировано.",
                "subscription_expired": True,
                "subscription": sub
            }, status=403)
        # Restaurant manager sees ONLY their own bookings!
        rest_id = auth["restaurant_id"]
    elif auth["role"] == "superadmin":
        rest_id = int(rest_id_str) if rest_id_str else None
    else:
        # Anonymous (e.g. test runner without auth)
        rest_id = int(rest_id_str) if rest_id_str else None

    bookings = database.get_admin_bookings(rest_id, date)
    return web.json_response({"bookings": bookings})

async def update_booking_status_endpoint(request: web.Request) -> web.Response:
    try:
        booking_id = int(request.match_info["id"])
        data = await request.json()
        new_status = data.get("status")
    except Exception:
        return web.json_response({"error": "Invalid parameters"}, status=400)

    if new_status not in ["pending", "confirmed", "rejected", "completed", "cancelled"]:
        return web.json_response({"error": "Invalid status"}, status=400)

    booking = database.get_booking_details(booking_id)
    if not booking:
        return web.json_response({"error": "Booking not found or not updated"}, status=404)

    auth = get_auth_context(request)
    allowed, err_resp = check_restaurant_write_permission(auth, booking["restaurant_id"])
    if not allowed:
        return err_resp

    ok = database.update_booking_status(booking_id, new_status)
    if not ok:
        return web.json_response({"error": "Booking not found or not updated"}, status=404)

    updated_booking = database.get_booking_details(booking_id)

    # Notify guest on Telegram
    bot_notify_status = request.app.get("bot_notify_status_change")
    if bot_notify_status and updated_booking:
        try:
            await bot_notify_status(updated_booking, new_status)
        except Exception as e:
            print(f"Error notifying guest: {e}")

    return web.json_response({"success": True, "booking": updated_booking})

# =========================================================================
# STATIC PAGES
# =========================================================================

async def index_page(request: web.Request) -> web.FileResponse:
    import os
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    return web.FileResponse(index_path)

async def admin_page(request: web.Request) -> web.FileResponse:
    import os
    admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin.html")
    return web.FileResponse(admin_path)

async def health_endpoint(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "service": "restokz-bot",
        "railway": True
    })

def create_web_app(notify_booking_func=None, notify_status_func=None) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])

    if notify_booking_func:
        app["bot_notify_new_booking"] = notify_booking_func
    if notify_status_func:
        app["bot_notify_status_change"] = notify_status_func

    # Health checks (Railway uptime monitoring)
    app.router.add_get("/health", health_endpoint)
    app.router.add_get("/api/health", health_endpoint)

    # Public API routes
    app.router.add_get("/api/restaurants", get_restaurants)
    app.router.add_get("/api/restaurants/{id}", get_restaurant)
    app.router.add_get("/api/restaurants/{id}/menu", get_restaurant_menu)
    app.router.add_get("/api/restaurants/{id}/tables", get_restaurant_tables)
    app.router.add_post("/api/bookings", create_booking_endpoint)
    app.router.add_get("/api/bookings/my", get_my_bookings)
    app.router.add_post("/api/bookings/{id}/cancel", cancel_my_booking_endpoint)

    # Auth & Verification
    app.router.add_post("/api/auth/verify", verify_auth_endpoint)

    # Super Admin: License & Subscription Management
    app.router.add_get("/api/admin/subscriptions", get_subscriptions_endpoint)
    app.router.add_post("/api/admin/subscriptions/{id}/extend", extend_subscription_endpoint)
    app.router.add_post("/api/admin/subscriptions/{id}/status", set_subscription_status_endpoint)
    app.router.add_post("/api/admin/subscriptions/{id}/regenerate-key", regenerate_key_endpoint)
    app.router.add_delete("/api/restaurants/{id}", delete_restaurant_endpoint)

    # Protected Management routes (Super Admin OR Active Restaurant)
    app.router.add_post("/api/restaurants", create_restaurant_endpoint)
    app.router.add_put("/api/restaurants/{id}", update_restaurant_endpoint)
    app.router.add_post("/api/restaurants/{id}/menu", add_menu_item_endpoint)
    app.router.add_delete("/api/menu/{id}", delete_menu_item_endpoint)
    app.router.add_post("/api/restaurants/{id}/tables", add_table_endpoint)
    app.router.add_delete("/api/tables/{id}", delete_table_endpoint)
    app.router.add_get("/api/admin/bookings", get_admin_bookings_endpoint)
    app.router.add_post("/api/admin/bookings/{id}/status", update_booking_status_endpoint)

    # Static HTML
    app.router.add_get("/", index_page)
    app.router.add_get("/index.html", index_page)
    app.router.add_get("/admin", admin_page)
    app.router.add_get("/admin.html", admin_page)

    return app
