"""
System-level tests for the Kazakhstan Restaurant Booking System.
Tests database logic and table availability directly, without HTTP.
"""

import sys
import asyncio

# Fix console encoding on Windows (cp1251 cannot render emoji/Cyrillic from some contexts)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import database


def ok(msg: str):
    print(f"[OK] {msg}")


def fail(msg: str):
    print(f"[FAIL] {msg}")
    raise AssertionError(msg)


async def run_tests():
    print("=" * 50)
    print("Testing database & API...")
    print("=" * 50)
    database.init_db()

    # 1. Test get_restaurants
    rests = database.get_all_restaurants()
    if len(rests) >= 4:
        ok(f"Restaurants check: {len(rests)} found")
    else:
        fail(f"Expected >=4 restaurants, got {len(rests)}")

    # 2. Test city filter
    almaty = database.get_all_restaurants(city="Алматы")
    if len(almaty) >= 1:
        ok(f"City filter (Алматы): {len(almaty)} found")
    else:
        fail("City filter for Алматы returned empty")

    # 3. Test search filter
    searched = database.get_all_restaurants(search="La Terrazza")
    if len(searched) >= 1 and searched[0]["name"] == "La Terrazza":
        ok(f"Search filter: found '{searched[0]['name']}'")
    else:
        fail("Search filter for 'La Terrazza' failed")

    # 4. Test menu
    menu = database.get_restaurant_menu(1)
    if len(menu) > 0:
        ok(f"Menu categories check: {len(menu)} categories")
    else:
        fail("Menu empty")

    total_items = sum(len(cat["items"]) for cat in menu)
    if total_items > 0:
        ok(f"Menu items check: {total_items} items total")
    else:
        fail("No menu items found")

    # 5. Test get restaurant by id
    rest = database.get_restaurant_by_id(1)
    if rest and rest["name"] == "La Terrazza":
        ok(f"get_restaurant_by_id(1): '{rest['name']}'")
    else:
        fail("get_restaurant_by_id(1) failed")

    # Nonexistent restaurant
    no_rest = database.get_restaurant_by_id(9999)
    if no_rest is None:
        ok("get_restaurant_by_id(9999) correctly returns None")
    else:
        fail("get_restaurant_by_id(9999) should return None")

    # 6. Test create booking
    booking_id = database.create_booking(
        restaurant_id=1,
        table_id=2,
        guest_tg_id=348581961,
        guest_username="test_guest",
        guest_name="Тест Тестов",
        guest_phone="+7 (777) 123-45-67",
        booking_date="2030-01-15",
        booking_time="19:00",
        guests_count=4,
        wishes="Окно"
    )
    if booking_id > 0:
        ok(f"Booking created ID: {booking_id}")
    else:
        fail("Booking creation failed")

    # 7. Test get booking details
    booking = database.get_booking_details(booking_id)
    if booking["guest_name"] == "Тест Тестов" and booking["restaurant_name"] == "La Terrazza":
        ok(f"Booking details: {booking['guest_name']} at {booking['restaurant_name']}, table #{booking['table_number']}")
    else:
        fail(f"Booking details mismatch: {booking}")

    # 8. Test status update
    ok_status = database.update_booking_status(booking_id, "confirmed")
    booking = database.get_booking_details(booking_id)
    if ok_status and booking["status"] == "confirmed":
        ok(f"Booking status updated to: {booking['status']}")
    else:
        fail("Status update failed")

    # 9. Test tables availability — table 2 should be busy at 19:00 on 2030-01-15
    tables = database.get_restaurant_tables_with_availability(1, "2030-01-15", "19:00")
    t2 = next((t for t in tables if t["id"] == 2), None)
    if t2 is None:
        fail("Table id=2 not found in tables list")
    if not t2["is_available"]:
        ok(f"Table availability check: Table #{t2['table_number']} correctly marked as occupied")
    else:
        fail("Table 2 should be busy at 19:00 (booking just created)")

    # 10. Test table is available at a different time slot
    tables_free = database.get_restaurant_tables_with_availability(1, "2030-01-15", "12:00")
    t2_free = next((t for t in tables_free if t["id"] == 2), None)
    if t2_free and t2_free["is_available"]:
        ok("Table #2 is correctly free at 12:00 (>2hrs from 19:00 booking)")
    else:
        fail("Table #2 should be free at 12:00 — it's more than 2 hours away from booking")

    # 11. Test user bookings
    user_bookings = database.get_user_bookings(348581961)
    if len(user_bookings) >= 1:
        ok(f"User bookings: {len(user_bookings)} found for tg_id 348581961")
    else:
        fail("get_user_bookings returned empty for test user")

    # 12. Test admin bookings
    admin_bookings = database.get_admin_bookings(restaurant_id=1)
    if len(admin_bookings) >= 1:
        ok(f"Admin bookings for restaurant 1: {len(admin_bookings)} found")
    else:
        fail("get_admin_bookings returned empty")

    # 13. Test update_booking_status returns False for invalid id
    result = database.update_booking_status(99999999, "confirmed")
    if not result:
        ok("update_booking_status(99999999) correctly returns False")
    else:
        fail("update_booking_status should return False for nonexistent booking")

    print()
    print("=" * 50)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_tests())
