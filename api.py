"""
REST API module for Kazakhstan Restaurant Booking System.
Powered by aiohttp.web.
"""

import json
from aiohttp import web
import database

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

async def get_admin_bookings_endpoint(request: web.Request) -> web.Response:
    rest_id_str = request.query.get("restaurant_id")
    date = request.query.get("date")

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

    ok = database.update_booking_status(booking_id, new_status)
    if not ok:
        return web.json_response({"error": "Booking not found or not updated"}, status=404)

    booking = database.get_booking_details(booking_id)

    # Notify guest on Telegram
    bot_notify_status = request.app.get("bot_notify_status_change")
    if bot_notify_status and booking:
        try:
            await bot_notify_status(booking, new_status)
        except Exception as e:
            print(f"Error notifying guest: {e}")

    return web.json_response({"success": True, "booking": booking})

async def index_page(request: web.Request) -> web.FileResponse:
    import os
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    return web.FileResponse(index_path)

async def admin_page(request: web.Request) -> web.FileResponse:
    import os
    admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin.html")
    return web.FileResponse(admin_path)

def create_web_app(notify_booking_func=None, notify_status_func=None) -> web.Application:
    app = web.Application(middlewares=[cors_middleware])

    if notify_booking_func:
        app["bot_notify_new_booking"] = notify_booking_func
    if notify_status_func:
        app["bot_notify_status_change"] = notify_status_func

    # API routes
    app.router.add_get("/api/restaurants", get_restaurants)
    app.router.add_get("/api/restaurants/{id}", get_restaurant)
    app.router.add_get("/api/restaurants/{id}/menu", get_restaurant_menu)
    app.router.add_get("/api/restaurants/{id}/tables", get_restaurant_tables)
    app.router.add_post("/api/bookings", create_booking_endpoint)
    app.router.add_get("/api/bookings/my", get_my_bookings)
    app.router.add_get("/api/admin/bookings", get_admin_bookings_endpoint)
    app.router.add_post("/api/admin/bookings/{id}/status", update_booking_status_endpoint)

    # Static HTML
    app.router.add_get("/", index_page)
    app.router.add_get("/index.html", index_page)
    app.router.add_get("/admin", admin_page)
    app.router.add_get("/admin.html", admin_page)

    return app
