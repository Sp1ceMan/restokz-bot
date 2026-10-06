"""
Integration tests for all REST API endpoints.
Starts a real aiohttp test server on port 8899 and verifies responses,
including security, license key authentication, and subscription management.
"""

import sys
import asyncio
import aiohttp
from aiohttp import web
import database
from api import create_web_app, SUPER_ADMIN_KEY

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass


async def test_api_endpoints():
    database.init_db()
    app = create_web_app()

    runner = web.AppRunner(app)
    await runner.setup()
    port = 8899
    site = web.TCPSite(runner, host="127.0.0.1", port=port)
    await site.start()
    print(f"Test server running on port {port}")

    admin_headers = {"X-Admin-Key": SUPER_ADMIN_KEY}

    async with aiohttp.ClientSession() as session:
        # 1. Test GET /api/restaurants (Public)
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["restaurants"]) >= 4
            print(f"[OK] GET /api/restaurants: {len(data['restaurants'])} restaurants")

        # 2. Test GET /api/restaurants with city filter
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants?city=Алматы") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert all(r["city"] == "Алматы" for r in data["restaurants"])
            print(f"[OK] GET /api/restaurants?city=Алматы: {len(data['restaurants'])} results")

        # 3. Test GET /api/restaurants/1 (existing)
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants/1") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["restaurant"]["name"] == "La Terrazza"
            print(f"[OK] GET /api/restaurants/1: '{data['restaurant']['name']}'")

        # 4. Test GET /api/restaurants/9999 (not found → 404)
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants/9999") as resp:
            assert resp.status == 404
            data = await resp.json()
            assert "error" in data
            print(f"[OK] GET /api/restaurants/9999 returns 404 as expected")

        # 5. Test GET /api/restaurants/abc (invalid id → 400)
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants/abc") as resp:
            assert resp.status == 400
            print(f"[OK] GET /api/restaurants/abc returns 400 as expected")

        # 6. Test GET /api/restaurants/1/menu
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants/1/menu") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["menu"]) > 0
            total_items = sum(len(cat["items"]) for cat in data["menu"])
            print(f"[OK] GET /api/restaurants/1/menu: {len(data['menu'])} categories, {total_items} items")

        # 7. Test GET /api/restaurants/1/tables
        async with session.get(f"http://127.0.0.1:{port}/api/restaurants/1/tables?date=2030-01-15&time=19:00") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["tables"]) > 0
            print(f"[OK] GET /api/restaurants/1/tables: {len(data['tables'])} tables")

        # 8. Test POST /api/bookings — normal case
        payload = {
            "restaurant_id": 1,
            "table_id": 5,
            "guest_tg_id": 1234567,
            "guest_username": "client_kz",
            "guest_name": "Кайрат Нуртас",
            "guest_phone": "+7 (777) 999-88-77",
            "booking_date": "2030-01-20",
            "booking_time": "20:00",
            "guests_count": 4,
            "wishes": "VIP обслуживание"
        }
        async with session.post(f"http://127.0.0.1:{port}/api/bookings", json=payload) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["success"] is True
            booking_id = data["booking"]["id"]
            print(f"[OK] POST /api/bookings created booking #{booking_id}")

        # 9. Test POST /api/bookings with null guest_tg_id (edge case)
        payload_no_tg = {
            "restaurant_id": 1,
            "table_id": 6,
            "guest_tg_id": None,
            "guest_name": "Аноним",
            "guest_phone": "+7 (777) 000-00-00",
            "booking_date": "2030-01-21",
            "booking_time": "14:00",
            "guests_count": 2
        }
        async with session.post(f"http://127.0.0.1:{port}/api/bookings", json=payload_no_tg) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["success"] is True
            print(f"[OK] POST /api/bookings with null guest_tg_id works correctly")

        # 10. Test POST /api/bookings — missing required field
        bad_payload = {"restaurant_id": 1, "table_id": 5}
        async with session.post(f"http://127.0.0.1:{port}/api/bookings", json=bad_payload) as resp:
            assert resp.status == 400
            data = await resp.json()
            assert "error" in data
            print(f"[OK] POST /api/bookings with missing fields returns 400")

        # 10a. Test POST /api/bookings — invalid guests_count (0 or >50)
        invalid_count_payload = {**payload, "guests_count": 0}
        async with session.post(f"http://127.0.0.1:{port}/api/bookings", json=invalid_count_payload) as resp:
            assert resp.status == 400
            print(f"[OK] POST /api/bookings with guests_count=0 returns 400")

        # 10b. Test POST /api/bookings — too short guest_name
        invalid_name_payload = {**payload, "guest_name": "A"}
        async with session.post(f"http://127.0.0.1:{port}/api/bookings", json=invalid_name_payload) as resp:
            assert resp.status == 400
            print(f"[OK] POST /api/bookings with 1-char name returns 400")

        # -------------------------------------------------------------
        # SECURITY & SUBSCRIPTION ACCESS CONTROL TESTS
        # -------------------------------------------------------------

        # 11. Security Test: Unauthorized restaurant creation attempt -> MUST BE 403 FORBIDDEN
        fake_rest_payload = {
            "name": "Нелегальный Ресторан",
            "city": "Алматы",
            "cuisine": "Пиратская",
            "address": "ул. Без Оплаты, 1",
            "phone": "+7 700 000 00 00"
        }
        async with session.post(f"http://127.0.0.1:{port}/api/restaurants", json=fake_rest_payload) as resp:
            assert resp.status == 403
            err_data = await resp.json()
            assert "заблокировано" in err_data.get("error", "").lower() or "запрещен" in err_data.get("error", "").lower()
            print(f"[OK] Security: Unauthorized restaurant creation blocked (403 Forbidden)")

        # 12. Security Test: Authorized restaurant creation by Super Admin -> MUST BE 200 OK
        valid_rest_payload = {
            "name": "Grand Palace VIP",
            "city": "Шымкент",
            "cuisine": "Казахская, Европейская",
            "address": "пр. Байдибек би, 120",
            "phone": "+7 (7252) 55-44-33",
            "subscription_plan": "pro",
            "subscription_days": 14,
            "subscription_status": "trial",
            "owner_name": "Ерлан Бауыржанулы",
            "owner_phone": "+7 701 111 22 33"
        }
        async with session.post(f"http://127.0.0.1:{port}/api/restaurants", json=valid_rest_payload, headers=admin_headers) as resp:
            assert resp.status == 200
            new_rest_data = await resp.json()
            assert new_rest_data["success"] is True
            new_rest_id = new_rest_data["id"]
            new_rest_key = new_rest_data["restaurant"]["access_key"]
            assert new_rest_key.startswith("RKZ-")
            assert new_rest_data["restaurant"]["subscription_info"]["is_trial"] is True
            print(f"[OK] Super Admin: Created restaurant #{new_rest_id} with key '{new_rest_key}' (14d trial)")

        # 13. Test POST /api/auth/verify with Super Admin key
        async with session.post(f"http://127.0.0.1:{port}/api/auth/verify", json={"key": SUPER_ADMIN_KEY}) as resp:
            assert resp.status == 200
            auth_res = await resp.json()
            assert auth_res["valid"] is True
            assert auth_res["role"] == "superadmin"
            print(f"[OK] Auth verify: Super Admin key recognized correctly")

        # 14. Test POST /api/auth/verify with restaurant license key
        async with session.post(f"http://127.0.0.1:{port}/api/auth/verify", json={"key": new_rest_key}) as resp:
            assert resp.status == 200
            auth_res = await resp.json()
            assert auth_res["valid"] is True
            assert auth_res["role"] == "restaurant"
            assert auth_res["restaurant_id"] == new_rest_id
            assert auth_res["subscription"]["is_active"] is True
            print(f"[OK] Auth verify: Restaurant license key recognized for '{auth_res['restaurant']['name']}'")

        # 15. Test POST /api/auth/verify with invalid key -> 401
        async with session.post(f"http://127.0.0.1:{port}/api/auth/verify", json={"key": "INVALID-KEY-1234"}) as resp:
            assert resp.status == 401
            print(f"[OK] Auth verify: Invalid key rejected with 401")

        # 16. Test GET /api/admin/subscriptions (Super Admin only)
        async with session.get(f"http://127.0.0.1:{port}/api/admin/subscriptions", headers=admin_headers) as resp:
            assert resp.status == 200
            subs_data = await resp.json()
            assert len(subs_data["subscriptions"]) >= 5
            print(f"[OK] Super Admin: GET /api/admin/subscriptions returned {len(subs_data['subscriptions'])} restaurants")

        # 17. Test POST /api/admin/subscriptions/{id}/extend (+30 days)
        extend_payload = {"days": 30, "status": "active", "plan": "pro"}
        async with session.post(f"http://127.0.0.1:{port}/api/admin/subscriptions/{new_rest_id}/extend", json=extend_payload, headers=admin_headers) as resp:
            assert resp.status == 200
            ext_data = await resp.json()
            assert ext_data["success"] is True
            assert ext_data["restaurant"]["subscription_info"]["days_left"] >= 40
            print(f"[OK] Super Admin: Extended subscription for restaurant #{new_rest_id} (+30 days)")

        # 18. Test POST /api/admin/bookings/{id}/status with Admin Key
        async with session.post(f"http://127.0.0.1:{port}/api/admin/bookings/{booking_id}/status", json={"status": "confirmed"}, headers=admin_headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["booking"]["status"] == "confirmed"
            print(f"[OK] Booking #{booking_id} confirmed by authenticated admin API")

        # 19. Test POST /api/admin/bookings/{id}/status — invalid status
        async with session.post(f"http://127.0.0.1:{port}/api/admin/bookings/{booking_id}/status", json={"status": "unknown_status"}, headers=admin_headers) as resp:
            assert resp.status == 400
            print(f"[OK] Invalid status returns 400")

        # 20. Test GET /api/bookings/my
        async with session.get(f"http://127.0.0.1:{port}/api/bookings/my?user_id=1234567") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["bookings"]) >= 1
            print(f"[OK] GET /api/bookings/my: {len(data['bookings'])} bookings for user")

        # 20b. Test POST /api/bookings/{id}/cancel
        async with session.post(f"http://127.0.0.1:{port}/api/bookings/{booking_id}/cancel") as resp:
            assert resp.status == 200
            cancel_data = await resp.json()
            assert cancel_data["success"] is True
            assert cancel_data["booking"]["status"] == "cancelled"
            print(f"[OK] Booking #{booking_id} cancelled by guest API")

        # 21. Test GET /api/admin/bookings with Admin Key
        async with session.get(f"http://127.0.0.1:{port}/api/admin/bookings?restaurant_id=1", headers=admin_headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["bookings"]) >= 1
            print(f"[OK] GET /api/admin/bookings: {len(data['bookings'])} bookings")

        # 22. Test GET / (index page)
        async with session.get(f"http://127.0.0.1:{port}/") as resp:
            assert resp.status == 200
            text = await resp.text()
            assert "RestoKZ" in text
            print(f"[OK] GET / serves index.html with title RestoKZ")

    await runner.cleanup()
    print()
    print("=" * 50)
    print("ALL API ENDPOINTS & SECURITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
