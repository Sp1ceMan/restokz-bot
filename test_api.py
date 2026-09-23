"""
Integration tests for all REST API endpoints.
Starts a real aiohttp test server on port 8899 and verifies responses.
"""

import sys
import asyncio
import aiohttp
from aiohttp import web
import database
from api import create_web_app

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

    async with aiohttp.ClientSession() as session:
        # 1. Test GET /api/restaurants
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

        # 11. Test POST /api/admin/bookings/{id}/status — confirm
        async with session.post(f"http://127.0.0.1:{port}/api/admin/bookings/{booking_id}/status", json={"status": "confirmed"}) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["booking"]["status"] == "confirmed"
            print(f"[OK] Booking #{booking_id} confirmed by admin API")

        # 12. Test POST /api/admin/bookings/{id}/status — invalid status
        async with session.post(f"http://127.0.0.1:{port}/api/admin/bookings/{booking_id}/status", json={"status": "unknown_status"}) as resp:
            assert resp.status == 400
            print(f"[OK] Invalid status returns 400")

        # 13. Test GET /api/bookings/my
        async with session.get(f"http://127.0.0.1:{port}/api/bookings/my?user_id=1234567") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["bookings"]) >= 1
            print(f"[OK] GET /api/bookings/my: {len(data['bookings'])} bookings for user")

        # 14. Test GET /api/admin/bookings
        async with session.get(f"http://127.0.0.1:{port}/api/admin/bookings?restaurant_id=1") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert len(data["bookings"]) >= 1
            print(f"[OK] GET /api/admin/bookings: {len(data['bookings'])} bookings")

        # 15. Test GET / (index page)
        async with session.get(f"http://127.0.0.1:{port}/") as resp:
            assert resp.status == 200
            text = await resp.text()
            assert "RestoKZ" in text
            print(f"[OK] GET / serves index.html with title RestoKZ")

    await runner.cleanup()
    print()
    print("=" * 50)
    print("ALL API ENDPOINTS VERIFIED AND WORKING!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
