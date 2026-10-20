"""
Database module for Kazakhstan Restaurant Booking System
SQLite database handling restaurants, tables, menus, and bookings.
"""

import sqlite3
import json
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_FILE = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "booking.db")
)

def get_db_connection() -> sqlite3.Connection:
    global DB_FILE
    try:
        conn = sqlite3.connect(DB_FILE, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"[DB ERROR] Failed connecting to {DB_FILE}: {e}")
        local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "booking.db")
        if DB_FILE != local_db:
            print(f"[DB FALLBACK] Switching to local DB: {local_db}")
            DB_FILE = local_db
            conn = sqlite3.connect(DB_FILE, timeout=15.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        raise

def init_db():
    """Initializes the database schema and seeds initial Kazakhstan restaurants if empty."""
    global DB_FILE
    # Ensure the directory for the database file exists (important on Railway /data volume)
    db_dir = os.path.dirname(DB_FILE)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            print(f"[DB WARNING] Could not create directory {db_dir}: {e}")

    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[DB CRITICAL] Database initialization failed: {e}")
        return

    try:
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
        except Exception as e:
            print(f"[DB NOTE] PRAGMA WAL mode skipped (using standard mode): {e}")

        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            rating REAL DEFAULT 4.8,
            avg_check INTEGER DEFAULT 8000,
            cover_image TEXT,
            description TEXT,
            working_hours TEXT DEFAULT '11:00 - 00:00',
            two_gis_url TEXT,
            instagram_url TEXT,
            whatsapp_url TEXT,
            telegram_url TEXT,
            website_url TEXT,
            admin_tg_id INTEGER,
            access_key TEXT UNIQUE,
            subscription_status TEXT DEFAULT 'active',
            subscription_plan TEXT DEFAULT 'pro',
            subscription_expires_at TEXT,
            owner_name TEXT,
            owner_phone TEXT
        );

        CREATE TABLE IF NOT EXISTS menu_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🍽️',
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            weight TEXT,
            image_url TEXT,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES menu_categories (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            table_number INTEGER NOT NULL,
            seats INTEGER NOT NULL,
            zone_type TEXT DEFAULT 'Зал',
            description TEXT,
            position_x INTEGER DEFAULT 0,
            position_y INTEGER DEFAULT 0,
            shape TEXT DEFAULT 'circle',
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE,
            UNIQUE (restaurant_id, table_number)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            guest_tg_id INTEGER,
            guest_username TEXT,
            guest_name TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            guests_count INTEGER NOT NULL,
            wishes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE,
            FOREIGN KEY (table_id) REFERENCES tables (id) ON DELETE CASCADE
        );

        -- Performance indexes for frequently queried columns
        CREATE INDEX IF NOT EXISTS idx_bookings_restaurant_date
            ON bookings (restaurant_id, booking_date);

        CREATE INDEX IF NOT EXISTS idx_bookings_guest_tg_id
            ON bookings (guest_tg_id);

        CREATE INDEX IF NOT EXISTS idx_bookings_table_id
            ON bookings (table_id);

        CREATE INDEX IF NOT EXISTS idx_bookings_status
            ON bookings (status);

        CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant
            ON menu_items (restaurant_id, category_id);

        CREATE INDEX IF NOT EXISTS idx_tables_restaurant
            ON tables (restaurant_id);

        CREATE TABLE IF NOT EXISTS bot_admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'super_admin',
            added_at TEXT NOT NULL,
            added_by INTEGER DEFAULT 0
        );
        """)

        conn.commit()

        # Seed initial bot admins from environment
        env_admins = {348581961, 742645245}
        raw_env_admins = os.environ.get("ADMIN_CHAT_IDS") or os.environ.get("ADMIN_CHAT_ID", "348581961,742645245")
        for item in re.split(r"[,; ]+", str(raw_env_admins).strip()):
            if item.isdigit():
                env_admins.add(int(item))

        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for a_id in env_admins:
            cursor.execute("""
                INSERT INTO bot_admins (user_id, role, added_at, added_by)
                VALUES (?, 'super_admin', ?, 0)
                ON CONFLICT(user_id) DO NOTHING
            """, (a_id, now_iso))
        conn.commit()

        # Migrate existing DB: ensure social media, 2GIS and subscription security columns exist
        migration_cols = [
            ("instagram_url", "TEXT"),
            ("whatsapp_url", "TEXT"),
            ("telegram_url", "TEXT"),
            ("website_url", "TEXT"),
            ("access_key", "TEXT"),
            ("subscription_status", "TEXT DEFAULT 'active'"),
            ("subscription_plan", "TEXT DEFAULT 'pro'"),
            ("subscription_expires_at", "TEXT"),
            ("owner_name", "TEXT"),
            ("owner_phone", "TEXT")
        ]
        for col_name, col_type in migration_cols:
            try:
                cursor.execute(f"ALTER TABLE restaurants ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass
        conn.commit()

        # Ensure all existing restaurants have unique access_key and subscription_expires_at
        cursor.execute("SELECT id, name, access_key, subscription_expires_at FROM restaurants")
        existing_rests = cursor.fetchall()
        for r in existing_rests:
            r_id = r["id"]
            r_name = r["name"]
            r_key = r["access_key"]
            r_exp = r["subscription_expires_at"]
            updates = []
            params = []
            if not r_key:
                clean_name = re.sub(r'[^A-Za-z0-9]', '', r_name.upper())[:8] or "REST"
                new_key = f"RKZ-{clean_name}-{secrets.token_hex(2).upper()}"
                updates.append("access_key = ?")
                params.append(new_key)
            if not r_exp:
                # 365 days active subscription for seeded restaurants
                default_exp = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d 23:59:59")
                updates.append("subscription_expires_at = ?")
                params.append(default_exp)
                updates.append("subscription_status = 'active'")
                updates.append("subscription_plan = 'pro'")
            if updates:
                params.append(r_id)
                cursor.execute(f"UPDATE restaurants SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

        # Check if restaurants already exist
        cursor.execute("SELECT COUNT(*) as cnt FROM restaurants")
        count = cursor.fetchone()["cnt"]

        if count == 0:
            seed_data(conn)

        # Ensure authentic Shymkent restaurants exist
        cursor.execute("SELECT COUNT(*) as cnt FROM restaurants WHERE city = 'Шымкент'")
        if cursor.fetchone()["cnt"] == 0:
            seed_shymkent_data(cursor)
            conn.commit()
    finally:
        conn.close()

def seed_data(conn: sqlite3.Connection):
    """Populates authentic demo data for popular restaurants in Kazakhstan."""
    cursor = conn.cursor()

    # Restaurants
    restaurants_data = [
        (
            1,
            "La Terrazza",
            "Алматы",
            "Итальянская, Средиземноморская",
            "ул. Сатпаева, 29/6 (БЦ Сары-Арка)",
            "+7 (727) 315-05-05",
            4.9,
            12000,
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
            "Премиальный итальянский ресторан с панорамной террасой, авторской пастой ручной работы и коллекцией вин Старого Света.",
            "12:00 - 00:00",
            "https://2gis.kz/almaty",
            348581961
        ),
        (
            2,
            "Чайхана NAVAT",
            "Алматы",
            "Восточная, Казахская, Узбекская",
            "пр. Достык, 48 (уг. ул. Шевченко)",
            "+7 (701) 777-11-22",
            4.8,
            8500,
            "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80",
            "Атмосфера восточного гостеприимства: праздничный казан-кебаб, бешбармак из конины, нежнейшие манты и авторские чаи.",
            "10:00 - 02:00",
            "https://2gis.kz/almaty",
            348581961
        ),
        (
            3,
            "Sandyq (Сандық)",
            "Астана",
            "Национальная казахская",
            "пр. Кабанбай батыра, 15/1",
            "+7 (7172) 65-43-21",
            4.95,
            15000,
            "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80",
            "Ресторан высокой казахской кухни с этно-интерьером музейного уровня, традиционными рецептами кочевников и живой музыкой кобыза.",
            "12:00 - 01:00",
            "https://2gis.kz/astana",
            348581961
        ),
        (
            4,
            "Del Papa",
            "Алматы",
            "Итальянская, Домашняя",
            "ул. Гоголя, 87 (уг. ул. Панфилова)",
            "+7 (727) 222-33-44",
            4.7,
            7000,
            "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800&q=80",
            "Уютная семейная траттория в историческом центре Алматы. Хрустящая пицца из дровяной печи и домашняя атмосфера.",
            "11:00 - 23:00",
            "https://2gis.kz/almaty",
            348581961
        )
    ]

    cursor.executemany("""
        INSERT INTO restaurants 
        (id, name, city, cuisine, address, phone, rating, avg_check, cover_image, description, working_hours, two_gis_url, admin_tg_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, restaurants_data)

    # Categories & Menu items for La Terrazza
    cursor.executemany("""
        INSERT INTO menu_categories (id, restaurant_id, name, icon, sort_order) VALUES (?, ?, ?, ?, ?)
    """, [
        (1, 1, "Антипасти и Закуски", "🧀", 1),
        (2, 1, "Паста и Ризотто", "🍝", 2),
        (3, 1, "Горячие блюда & Стейки", "🥩", 3),
        (4, 1, "Десерты", "🍰", 4),
        (5, 1, "Напитки и Винная карта", "🍷", 5),
        # Navat categories
        (6, 2, "Национальные блюда", "🍲", 1),
        (7, 2, "Шашлыки на углях", "🍢", 2),
        (8, 2, "Салаты и Закуски", "🥗", 3),
        (9, 2, "Выпечка и Самса", "🥟", 4),
        (10, 2, "Восточные чаи", "🫖", 5),
        # Sandyq categories
        (11, 3, "Ханское меню", "👑", 1),
        (12, 3, "Мясные деликатесы", "🍖", 2),
        (13, 3, "Десерты кочевников", "🍯", 3),
        # Del Papa
        (14, 4, "Пицца из печи", "🍕", 1),
        (15, 4, "Паста Fresca", "🍝", 2),
        (16, 4, "Напитки и Лимонады", "🍹", 3),
    ])

    # Menu items
    menu_items_data = [
        # La Terrazza
        (1, 1, "Брускетты с вялеными томатами и страчателлой", "Хрустящая чиабатта, нежная страчателла, бальзамик и свежий базилик", 3900, "220 г", "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=600&q=80"),
        (1, 1, "Карпаччо из мраморной говядины", "Тончайшие слайсы выдержанной говядины с трюфельным маслом и пармезаном", 5800, "180 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
        (1, 2, "Тальятелле с камчатским крабом и томатами черри", "Свежая домашняя паста, фаланги краба, белое вино, чеснок и петрушка", 8900, "320 г", "https://images.unsplash.com/photo-1621996346565-e3d5d6281084?w=600&q=80"),
        (1, 2, "Ризотто с белыми грибами и трюфельной пеной", "Рис Карнароли, белые грибы из местных предгорий, сливочное масло, пармезан", 6200, "290 г", "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=600&q=80"),
        (1, 3, "Стейк Рибай Black Angus", "Премиальная мраморная говядина зернового откорма на гриле Josper", 14500, "350 г", "https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80"),
        (1, 3, "Филе сибаса с пюре из батата и спаржей", "Филе дикого сибаса, крем из батата, соус бер-блан", 9800, "300 г", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80"),
        (1, 4, "Классический Тирамису", "Воздушное печенье савоярди, эспрессо, маскарпоне и какао", 3200, "180 г", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=600&q=80"),
        (1, 5, "Лимонад маракуйя-эстрагон", "Освежающий натуральный лимонад собственного приготовления", 2200, "450 мл", "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&q=80"),

        # NAVAT
        (2, 6, "Бешбармак праздничный по-казахски", "Отборная конина, казы, жая, тончайшее домашнее тесто и туздык", 5900, "450 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
        (2, 6, "Чайханский плов из баранины", "Рис лазер, сочная молодая баранина, желтая морковь, барбарис и чеснок", 3600, "380 г", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80"),
        (2, 7, "Шашлык из каре ягненка", "Нежнейшее мясо молодого барашка на березовых углях с маринованным луком", 4200, "250 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
        (2, 7, "Люля-кебаб из говядины", "Рубленый сочный фарш со специями, запеченный на шпажке", 2900, "220 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80"),
        (2, 8, "Салат Ачичук", "Тонко нарезанные спелые томаты, сладкий лук и стручковый перец", 1900, "200 г", "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&q=80"),
        (2, 9, "Самса тандырная с мясом", "Хрустящее слоеное тесто, рубленая говядина и курдюк", 950, "150 г", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80"),
        (2, 10, "Ташкентский чай с мятой и лимоном", "Смесь черного и зеленого чая, горная мята, лимон, нават", 1800, "800 мл", "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&q=80"),

        # Sandyq
        (3, 11, "Хан-Табак с деликатесами из конины", "Ассорти из казы, карта, жал, жая с горячим баурсаком", 18500, "900 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
        (3, 11, "Сырне из ягненка в казане", "Томленое в собственном соку мясо молодого барашка с картофелем и травами", 7800, "420 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
        (3, 12, "Казы домашнее", "Традиционная колбаса из конины по старинному степному рецепту", 4500, "200 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80"),
        (3, 13, "Чизкейк из иримшика с медом", "Нежнейший творожный десерт из традиционного сладкого творога", 3400, "170 г", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&q=80"),

        # Del Papa
        (4, 14, "Пицца Четыре Сыра", "Моцарелла, Горгонзола, Пармезан, Скаморца на тонком тесте", 4200, "430 г", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&q=80"),
        (4, 14, "Пицца Пепперони острая", "Пряная салями пепперони, томатный соус пелати, моцарелла", 3900, "410 г", "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=600&q=80"),
        (4, 15, "Феттуччине Альфредо с цыпленком", "Паста собственного приготовления, нежное филе цыпленка, сливочно-грибной соус", 3800, "330 г", "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?w=600&q=80"),
        (4, 16, "Домашний клубничный лимонад", "Свежая клубника, базилик, содовая и тростниковый сахар", 1900, "500 мл", "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&q=80")
    ]

    cursor.executemany("""
        INSERT INTO menu_items (restaurant_id, category_id, title, description, price, weight, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, menu_items_data)

    # Tables layout for each restaurant
    tables_data = []
    for rest_id in [1, 2, 3, 4]:
        tables_data.extend([
            (rest_id, 1, 2, "У окна", "Уютный столик на двоих с видом на город", 10, 20, "round"),
            (rest_id, 2, 4, "Основной зал", "Комфортный стол для семьи или компании", 35, 20, "rect"),
            (rest_id, 3, 2, "VIP-зона", "Приватный столик с мягкими креслами", 65, 20, "round"),
            (rest_id, 4, 6, "Основной зал", "Просторный стол с мягким диваном", 10, 60, "rect"),
            (rest_id, 5, 4, "У окна", "Светлый столик у панорамного окна", 35, 60, "rect"),
            (rest_id, 6, 8, "VIP-зал", "Большой банкетный стол для праздника", 65, 60, "rect"),
            (rest_id, 7, 4, "Терраса", "Столик на свежем воздухе с красивым видом", 90, 20, "round"),
            (rest_id, 8, 2, "Терраса", "Романтический столик на двоих на террасе", 90, 60, "round")
        ])

    cursor.executemany("""
        INSERT INTO tables (restaurant_id, table_number, seats, zone_type, description, position_x, position_y, shape)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, tables_data)

    # Add a couple of demo bookings for today and tomorrow to test occupancy
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    demo_bookings = [
        (1, 1, 123456, "arman_kz", "Арман Сериков", "+7 (777) 234-56-78", today, "19:00", 2, "Юбилей, столик у окна", "confirmed", datetime.now().isoformat()),
        (1, 4, 654321, "dana_almaty", "Дана Мусина", "+7 (701) 987-65-43", today, "20:00", 6, "Нужен детский стульчик", "pending", datetime.now().isoformat()),
        (2, 10, 999888, "berik_88", "Берик Жумабаев", "+7 (705) 555-44-33", tomorrow, "18:30", 4, "Деловой ужин", "confirmed", datetime.now().isoformat())
    ]

    cursor.executemany("""
        INSERT INTO bookings 
        (restaurant_id, table_id, guest_tg_id, guest_username, guest_name, guest_phone, booking_date, booking_time, guests_count, wishes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_bookings)

    conn.commit()

# --- Repository Query Functions ---

def get_all_restaurants(city: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM restaurants WHERE 1=1"
        params = []

        if city and city != "Все" and city.lower() != "all":
            query += " AND city = ?"
            params.append(city)

        if search:
            query += " AND (name LIKE ? OR cuisine LIKE ? OR address LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY rating DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_restaurant_by_id(restaurant_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_restaurant_menu(restaurant_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM menu_categories 
            WHERE restaurant_id = ? 
            ORDER BY sort_order ASC, id ASC
        """, (restaurant_id,))
        categories = [dict(c) for c in cursor.fetchall()]

        cursor.execute("""
            SELECT * FROM menu_items 
            WHERE restaurant_id = ? AND is_available = 1
            ORDER BY id ASC
        """, (restaurant_id,))
        items = [dict(item) for item in cursor.fetchall()]

        # Nest items into categories
        result = []
        for cat in categories:
            cat_items = [it for it in items if it["category_id"] == cat["id"]]
            cat["items"] = cat_items
            result.append(cat)
        return result
    finally:
        conn.close()

def get_table_by_number(restaurant_id: int, table_number: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tables WHERE restaurant_id = ? AND table_number = ?", (restaurant_id, table_number))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_restaurant_tables_with_availability(
    restaurant_id: int, 
    date: str, 
    time_slot: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns all tables for the restaurant with an 'is_available' boolean
    based on active bookings on the given date (and optionally within 2 hours of time_slot).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tables WHERE restaurant_id = ? ORDER BY table_number ASC", (restaurant_id,))
        tables = [dict(t) for t in cursor.fetchall()]

        # Find booked table IDs on this date where status not rejected/cancelled
        query = """
            SELECT table_id, booking_time, status, guest_name 
            FROM bookings 
            WHERE restaurant_id = ? 
              AND booking_date = ? 
              AND status IN ('pending', 'confirmed')
        """
        params = [restaurant_id, date]

        cursor.execute(query, params)
        bookings = cursor.fetchall()
    finally:
        conn.close()

    # Determine availability: if a table has a booking within +/- 2 hours of requested time_slot
    # If time_slot is not provided, any booking today marks it as busy for demo
    busy_table_ids = set()
    booking_map = {}

    for b in bookings:
        t_id = b["table_id"]
        b_time = (b["booking_time"] or "")[:5].strip()
        
        if time_slot:
            try:
                dt_req = datetime.strptime(time_slot[:5].strip(), "%H:%M")
                dt_book = datetime.strptime(b_time, "%H:%M")
                diff_minutes = abs((dt_req - dt_book).total_seconds()) / 60
                # A standard booking lasts 2 hours (120 mins)
                if diff_minutes < 120:
                    busy_table_ids.add(t_id)
                    booking_map[t_id] = dict(b)
            except Exception:
                busy_table_ids.add(t_id)
                booking_map[t_id] = dict(b)
        else:
            busy_table_ids.add(t_id)
            booking_map[t_id] = dict(b)

    for t in tables:
        t["is_available"] = t["id"] not in busy_table_ids
        if t["id"] in busy_table_ids:
            t["current_booking"] = booking_map.get(t["id"])

    return tables

def create_booking(
    restaurant_id: int,
    table_id: int,
    guest_tg_id: Optional[int],
    guest_username: Optional[str],
    guest_name: str,
    guest_phone: str,
    booking_date: str,
    booking_time: str,
    guests_count: int,
    wishes: Optional[str] = ""
) -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bookings 
            (restaurant_id, table_id, guest_tg_id, guest_username, guest_name, guest_phone, 
             booking_date, booking_time, guests_count, wishes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            restaurant_id,
            table_id,
            guest_tg_id,
            guest_username,
            guest_name,
            guest_phone,
            booking_date,
            booking_time,
            guests_count,
            wishes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        booking_id = cursor.lastrowid
        conn.commit()
        return booking_id
    finally:
        conn.close()

def get_booking_details(booking_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.*, 
                   r.name as restaurant_name, 
                   r.address as restaurant_address,
                   r.phone as restaurant_phone,
                   r.admin_tg_id,
                   t.table_number, 
                   t.seats as table_seats, 
                   t.zone_type as table_zone
            FROM bookings b
            JOIN restaurants r ON b.restaurant_id = r.id
            JOIN tables t ON b.table_id = t.id
            WHERE b.id = ?
        """, (booking_id,))

        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_bookings(
    guest_tg_id: Optional[int] = None,
    booking_ids: Optional[List[int]] = None,
    phone: Optional[str] = None
) -> List[Dict[str, Any]]:
    conditions = []
    params = []

    if guest_tg_id:
        conditions.append("b.guest_tg_id = ?")
        params.append(guest_tg_id)

    if booking_ids:
        placeholders = ",".join("?" for _ in booking_ids)
        conditions.append(f"b.id IN ({placeholders})")
        params.extend(booking_ids)

    if phone:
        conditions.append("b.guest_phone = ?")
        params.append(phone)

    if not conditions:
        return []

    where_clause = " OR ".join(conditions)
    query = f"""
        SELECT b.*, 
               r.name as restaurant_name, 
               r.address as restaurant_address,
               r.phone as restaurant_phone,
               r.two_gis_url as restaurant_two_gis,
               r.cover_image as restaurant_cover,
               t.table_number, 
               t.zone_type as table_zone
        FROM bookings b
        JOIN restaurants r ON b.restaurant_id = r.id
        JOIN tables t ON b.table_id = t.id
        WHERE {where_clause}
        ORDER BY b.booking_date DESC, b.booking_time DESC, b.id DESC
    """

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def get_admin_bookings(restaurant_id: Optional[int] = None, date: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        query = """
            SELECT b.*, 
                   r.name as restaurant_name, 
                   t.table_number, 
                   t.seats as table_seats,
                   t.zone_type as table_zone
            FROM bookings b
            JOIN restaurants r ON b.restaurant_id = r.id
            JOIN tables t ON b.table_id = t.id
            WHERE 1=1
        """
        params = []

        if restaurant_id:
            query += " AND b.restaurant_id = ?"
            params.append(restaurant_id)

        if date:
            query += " AND b.booking_date = ?"
            params.append(date)

        query += " ORDER BY b.booking_date ASC, b.booking_time ASC, b.id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_booking_status(booking_id: int, new_status: str) -> bool:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE bookings 
            SET status = ? 
            WHERE id = ?
        """, (new_status, booking_id))

        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def create_restaurant(
    name: str,
    city: str,
    cuisine: str,
    address: str,
    phone: str,
    rating: float = 4.8,
    avg_check: int = 8000,
    cover_image: str = "",
    description: str = "",
    working_hours: str = "11:00 - 00:00",
    two_gis_url: str = "",
    instagram_url: str = "",
    whatsapp_url: str = "",
    telegram_url: str = "",
    website_url: str = "",
    admin_tg_id: Optional[int] = None,
    access_key: Optional[str] = None,
    subscription_status: str = "active",
    subscription_plan: str = "pro",
    subscription_expires_at: Optional[str] = None,
    subscription_days: Optional[int] = None,
    owner_name: str = "",
    owner_phone: str = "",
    **kwargs
) -> int:
    """Registers a new restaurant in the system and provisions default starter tables and menu categories."""
    if not cover_image and "photo_url" in kwargs:
        cover_image = kwargs["photo_url"]

    # Generate access key if not provided
    if not access_key:
        access_key = generate_unique_access_key(name)

    # Calculate expiration date
    if not subscription_expires_at:
        days = subscription_days if subscription_days is not None else (7 if subscription_status == "trial" else 30)
        subscription_expires_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d 23:59:59")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO restaurants 
            (name, city, cuisine, address, phone, rating, avg_check, cover_image, description, 
             working_hours, two_gis_url, instagram_url, whatsapp_url, telegram_url, website_url, 
             admin_tg_id, access_key, subscription_status, subscription_plan, subscription_expires_at,
             owner_name, owner_phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, city, cuisine, address, phone, rating, avg_check, cover_image, description,
            working_hours, two_gis_url, instagram_url, whatsapp_url, telegram_url, website_url, 
            admin_tg_id, access_key, subscription_status, subscription_plan, subscription_expires_at,
            owner_name, owner_phone
        ))
        rest_id = cursor.lastrowid

        # Provision starter menu categories
        starter_cats = [
            ("Закуски и Салаты", "🥗", 1),
            ("Основные блюда", "🥩", 2),
            ("Десерты", "🍰", 3),
            ("Напитки", "🍹", 4)
        ]
        for cat_name, icon, sort_o in starter_cats:
            cursor.execute("""
                INSERT INTO menu_categories (restaurant_id, name, icon, sort_order)
                VALUES (?, ?, ?, ?)
            """, (rest_id, cat_name, icon, sort_o))

        # Provision default tables (8 tables of varying zones)
        starter_tables = [
            (1, 2, "У окна", "Уютный столик у окна"),
            (2, 2, "У окна", "Панорамный столик"),
            (3, 4, "Основной зал", "Семейный столик"),
            (4, 4, "Основной зал", "Столик в центре зала"),
            (5, 6, "Диванная зона", "Комфортный стол с диваном"),
            (6, 6, "Летняя терраса", "Столик на свежем воздухе"),
            (7, 8, "VIP-кабина", "Приватный зал"),
            (8, 10, "Банкетная зона", "Большой праздничный стол")
        ]
        for num, seats, zone, desc in starter_tables:
            cursor.execute("""
                INSERT INTO tables (restaurant_id, table_number, seats, zone_type, description)
                VALUES (?, ?, ?, ?, ?)
            """, (rest_id, num, seats, zone, desc))

        conn.commit()
        return rest_id
    finally:
        conn.close()

def update_restaurant(restaurant_id: int, **fields) -> bool:
    """Updates restaurant profile fields including social links, working hours, 2GIS, subscription, etc."""
    if "photo_url" in fields and "cover_image" not in fields:
        fields["cover_image"] = fields.pop("photo_url")
    allowed = {
        "name", "city", "cuisine", "address", "phone", "rating", "avg_check",
        "cover_image", "description", "working_hours", "two_gis_url",
        "instagram_url", "whatsapp_url", "telegram_url", "website_url",
        "access_key", "subscription_status", "subscription_plan", 
        "subscription_expires_at", "owner_name", "owner_phone"
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values())
    values.append(restaurant_id)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE restaurants SET {set_clause} WHERE id = ?", values)
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def add_menu_item(
    restaurant_id: int,
    category_name: str,
    title: str = "",
    price: int = 0,
    description: str = "",
    weight: str = "",
    image_url: str = "",
    **kwargs
) -> int:
    """Adds a new dish into the restaurant menu, creating the category if needed."""
    if not title and "name" in kwargs:
        title = kwargs["name"]
    if not image_url and "photo_url" in kwargs:
        image_url = kwargs["photo_url"]

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM menu_categories WHERE restaurant_id = ? AND LOWER(name) = LOWER(?)
        """, (restaurant_id, category_name.strip()))
        row = cursor.fetchone()

        if row:
            cat_id = row["id"]
        else:
            cursor.execute("""
                INSERT INTO menu_categories (restaurant_id, name, icon, sort_order)
                VALUES (?, ?, '🍽️', 99)
            """, (restaurant_id, category_name.strip()))
            cat_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO menu_items (restaurant_id, category_id, title, description, price, weight, image_url, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (restaurant_id, cat_id, title.strip(), description.strip(), price, weight.strip(), image_url.strip()))
        item_id = cursor.lastrowid
        conn.commit()
        return item_id
    finally:
        conn.close()

def delete_menu_item(item_id: int) -> bool:
    """Removes a dish from the menu."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def add_table(
    restaurant_id: int,
    table_number: int,
    seats: int = 4,
    zone_type: str = "Основной зал",
    description: str = "",
    shape: str = "rect",
    **kwargs
) -> int:
    """Adds a table to the restaurant floor plan."""
    if "capacity" in kwargs and not seats:
        seats = int(kwargs["capacity"])
    if "zone" in kwargs and (zone_type == "Основной зал" or not zone_type):
        zone_type = kwargs["zone"]

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tables (restaurant_id, table_number, seats, zone_type, description, shape)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (restaurant_id, table_number, seats, zone_type, description, shape))
        table_id = cursor.lastrowid
        conn.commit()
        return table_id
    finally:
        conn.close()

def delete_table(table_id: int) -> bool:
    """Deletes a table from the restaurant."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tables WHERE id = ?", (table_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

# =========================================================================
# SUBSCRIPTION & LICENSE ACCESS CONTROL HELPERS
# =========================================================================

def generate_unique_access_key(name: str = "") -> str:
    """Generates a memorable unique license key in format RKZ-<SLUG>-<HEX>."""
    clean = re.sub(r'[^A-Za-z0-9]', '', (name or "REST").upper())[:8] or "REST"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        while True:
            rnd = secrets.token_hex(2).upper()
            key = f"RKZ-{clean}-{rnd}"
            cursor.execute("SELECT id FROM restaurants WHERE access_key = ?", (key,))
            if not cursor.fetchone():
                return key
    finally:
        conn.close()

def get_subscription_details(rest: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates active/trial/expired status and days remaining for a restaurant."""
    status = rest.get("subscription_status") or "active"
    plan = rest.get("subscription_plan") or "pro"
    expires_str = rest.get("subscription_expires_at")
    
    if not expires_str:
        expires_dt = datetime.now() + timedelta(days=30)
    else:
        try:
            if "T" in expires_str:
                expires_dt = datetime.fromisoformat(expires_str)
            elif len(expires_str) == 10:
                expires_dt = datetime.strptime(expires_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            else:
                expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            expires_dt = datetime.now() + timedelta(days=30)

    now = datetime.now()
    days_left = (expires_dt.date() - now.date()).days
    is_expired = days_left < 0 or (expires_dt < now)
    is_blocked = (status == "blocked")
    
    effective_status = "blocked" if is_blocked else ("expired" if is_expired else status)

    return {
        "status": effective_status,
        "raw_status": status,
        "plan": plan,
        "expires_at": expires_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at_human": expires_dt.strftime("%d.%m.%Y"),
        "days_left": max(0, days_left) if not is_expired else days_left,
        "is_active": (not is_expired and not is_blocked),
        "is_trial": (status == "trial" and not is_expired and not is_blocked),
        "is_expired": is_expired,
        "is_blocked": is_blocked
    }

def get_restaurant_by_access_key(access_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves restaurant by license access key with computed subscription details."""
    if not access_key:
        return None
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE access_key = ?", (access_key.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        rest = dict(row)
        rest["subscription_info"] = get_subscription_details(rest)
        return rest
    finally:
        conn.close()

def is_subscription_active(restaurant_id: int) -> Dict[str, Any]:
    """Checks whether a restaurant has an active subscription or valid trial."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        row = cursor.fetchone()
        if not row:
            return {"is_active": False, "status": "not_found", "is_expired": True, "days_left": 0}
        return get_subscription_details(dict(row))
    finally:
        conn.close()

def extend_subscription(
    restaurant_id: int, 
    days: int = 0, 
    new_expiry_date: Optional[str] = None, 
    status: Optional[str] = None, 
    plan: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Extends subscription by N days or sets a specific expiry date.
    Resets status from expired/blocked to active/trial.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        row = cursor.fetchone()
        if not row:
            return None
        rest = dict(row)
        
        current_exp_str = rest.get("subscription_expires_at")
        now = datetime.now()
        current_dt = now
        if current_exp_str:
            try:
                if len(current_exp_str) == 10:
                    dt = datetime.strptime(current_exp_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                else:
                    dt = datetime.strptime(current_exp_str, "%Y-%m-%d %H:%M:%S")
                if dt > now:
                    current_dt = dt
            except Exception:
                pass
        
        if new_expiry_date:
            try:
                if len(new_expiry_date) == 10:
                    final_dt = datetime.strptime(new_expiry_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                else:
                    final_dt = datetime.strptime(new_expiry_date, "%Y-%m-%d %H:%M:%S")
            except Exception:
                final_dt = current_dt + timedelta(days=days if days > 0 else 30)
        elif days > 0:
            final_dt = current_dt + timedelta(days=days)
        else:
            final_dt = current_dt

        new_expires_str = final_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        new_status = status or rest.get("subscription_status") or "active"
        if new_status in ["expired", "blocked"] and (days > 0 or new_expiry_date):
            new_status = "active"

        new_plan = plan or rest.get("subscription_plan") or "pro"

        cursor.execute("""
            UPDATE restaurants 
            SET subscription_expires_at = ?, subscription_status = ?, subscription_plan = ?
            WHERE id = ?
        """, (new_expires_str, new_status, new_plan, restaurant_id))
        conn.commit()

        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        updated_row = cursor.fetchone()
        updated_rest = dict(updated_row)
        updated_rest["subscription_info"] = get_subscription_details(updated_rest)
        return updated_rest
    finally:
        conn.close()

def set_subscription_status(restaurant_id: int, status: str) -> bool:
    """Sets raw subscription status: 'active', 'trial', 'blocked', 'expired'."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE restaurants SET subscription_status = ? WHERE id = ?", (status, restaurant_id))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()

def regenerate_access_key(restaurant_id: int) -> Optional[str]:
    """Generates and sets a new unique license access key for the restaurant."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM restaurants WHERE id = ?", (restaurant_id,))
        row = cursor.fetchone()
        if not row:
            return None
        new_key = generate_unique_access_key(row["name"])
        cursor.execute("UPDATE restaurants SET access_key = ? WHERE id = ?", (new_key, restaurant_id))
        conn.commit()
        return new_key
    finally:
        conn.close()

def get_all_subscriptions() -> List[Dict[str, Any]]:
    """Returns all restaurants with full subscription details, keys, and usage statistics."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, city, phone, cuisine, address, 
                   access_key, subscription_status, subscription_plan, 
                   subscription_expires_at, owner_name, owner_phone,
                   (SELECT COUNT(*) FROM bookings WHERE restaurant_id = restaurants.id) as total_bookings,
                   (SELECT COUNT(*) FROM tables WHERE restaurant_id = restaurants.id) as total_tables
            FROM restaurants
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["subscription_info"] = get_subscription_details(d)
            result.append(d)
        return result
    finally:
        conn.close()

def delete_restaurant(restaurant_id: int) -> bool:
    """Deletes a restaurant and cascades tables, menus, and bookings."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM restaurants WHERE id = ?", (restaurant_id,))
        affected = cursor.rowcount
        conn.commit()
        return affected > 0
    finally:
        conn.close()


# =========================================================================
# BOT ADMINISTRATORS MANAGEMENT
# =========================================================================

def get_bot_admins() -> List[Dict[str, Any]]:
    """Returns list of all bot administrators."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, role, added_at, added_by 
            FROM bot_admins 
            ORDER BY added_at ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[DB ERROR] get_bot_admins failed: {e}")
        return []
    finally:
        conn.close()

def is_bot_admin(user_id: int) -> bool:
    """Checks whether user_id is an authorized bot administrator."""
    if not user_id:
        return False
    try:
        u_id = int(user_id)
    except (ValueError, TypeError):
        return False

    # Check env var fallback first
    raw_env_admins = os.environ.get("ADMIN_CHAT_IDS") or os.environ.get("ADMIN_CHAT_ID", "348581961,742645245")
    for item in re.split(r"[,; ]+", str(raw_env_admins).strip()):
        if item.isdigit() and int(item) == u_id:
            return True

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM bot_admins WHERE user_id = ?", (u_id,))
        return cursor.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()

def add_bot_admin(user_id: int, username: str = None, full_name: str = None, added_by: int = 0) -> bool:
    """Adds or updates a bot administrator."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_user = username.lstrip("@") if username else None
        cursor.execute("""
            INSERT INTO bot_admins (user_id, username, full_name, role, added_at, added_by)
            VALUES (?, ?, ?, 'super_admin', ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, bot_admins.username),
                full_name = COALESCE(excluded.full_name, bot_admins.full_name)
        """, (int(user_id), clean_user, full_name, now_iso, added_by))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] add_bot_admin failed: {e}")
        return False
    finally:
        conn.close()

def remove_bot_admin(user_id: int) -> bool:
    """Removes a bot administrator."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bot_admins WHERE user_id = ?", (int(user_id),))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[DB ERROR] remove_bot_admin failed: {e}")
        return False
    finally:
        conn.close()




SHYMKENT_RESTAURANTS = [
    {
        "id": 101,
        "name": "Sandyq Qainar (Сандық Қайнар)",
        "city": "Шымкент",
        "cuisine": "Национальная казахская, Высокая кочевая",
        "address": "пр. Байдибек би, 126 (комплекс Kainar)",
        "phone": "+7 (7252) 99-88-00",
        "rating": 4.95,
        "avg_check": 14000,
        "cover_image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80",
        "description": "Флагманский этно-ресторан высокой казахской кухни в парковой зоне Шымкента. Аутентичные блюда кочевников, Хан-Табак, бешбармак из молодого жеребенка, живое звучание кобыза и VIP-юрты.",
        "working_hours": "12:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Sandyq%20Qainar",
        "instagram_url": "https://instagram.com/sandyq_restaurant",
        "whatsapp_url": "https://wa.me/77252998800",
        "owner_name": "Кайрат Сатыбалдиев",
        "owner_phone": "+7 (701) 998-80-01",
        "categories": [
            ("Ханское меню & Деликатесы", "👑", 1),
            ("Мясные блюда в казане", "🍖", 2),
            ("Традиционные закуски и Казы", "🥩", 3),
            ("Десерты кочевников & Чай", "🍯", 4)
        ],
        "menu_items": [
            ("Хан-Табак с деликатесами из конины", "Ассорти из казы, карта, жал, жая с пышными баурсаками и сорпой", 19500, "1100 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
            ("Бешбармак из молодого жеребенка", "Тончайшее домашнее тесто, отборное мясо, луковый туздык и бульон", 7200, "500 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
            ("Сырне из ягненка топленое", "Мясо молодого ягненка, томленое 4 часа в казане с травами и овощами", 8900, "450 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
            ("Казы домашнее премиум", "Традиционная колбаса из реберной конины по старинному рецепту", 4800, "220 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80"),
            ("Балқаймақ с горячими баурсаками", "Томленые сливки с горным медом и хрустящими баурсаками", 3200, "250 г", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&q=80"),
            ("Чай степной с травами и талканом", "Авторский травяной сбор, молоко, талкан, сливочное масло", 2400, "900 мл", "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Столик для двоих с видом на фонтанный комплекс", 15, 20, "round"),
            (2, 4, "Основной зал", "Семейный стол с резными деревянными стульями", 40, 20, "rect"),
            (3, 6, "Основной зал", "Большой круглый стол с мягкими диванами", 70, 20, "round"),
            (4, 10, "VIP-юрта", "Приватная ханская юрта с низким дастарханом", 20, 65, "rect"),
            (5, 12, "VIP-зал", "Роскошный банкетный кабинет для құдалық и переговоров", 55, 65, "rect"),
            (6, 4, "Терраса", "Столик на парковой террасе с вечерней подсветкой", 85, 65, "round")
        ]
    },
    {
        "id": 102,
        "name": "BarVilla by Meyram Group",
        "city": "Шымкент",
        "cuisine": "Европейская, Стейк-хаус, Гриль",
        "address": "ул. Желтоксан, 9/2 (парк им. Абая)",
        "phone": "+7 (7252) 53-99-99",
        "rating": 4.9,
        "avg_check": 13500,
        "cover_image": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80",
        "description": "Премиальный ресторан парковой кухни от Meyram Group. Блюда на открытом огне в печи Josper, выдержанные мраморные стейки, панорамная летняя терраса среди вековых дубов.",
        "working_hours": "12:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/BarVilla",
        "instagram_url": "https://instagram.com/barvilla_shymkent",
        "whatsapp_url": "https://wa.me/77252539999",
        "owner_name": "Данияр Мамытов",
        "owner_phone": "+7 (701) 539-99-90",
        "categories": [
            ("Стейки & Josper Гриль", "🥩", 1),
            ("Холодные закуски & Тартары", "🥗", 2),
            ("Горячие блюда & Морепродукты", "🐟", 3),
            ("Винная карта & Коктейли", "🍸", 4)
        ],
        "menu_items": [
            ("Стейк Рибай Прайм зернового откорма", "Выдержанная говядина Black Angus на углях с перечным соусом", 16500, "380 г", "https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80"),
            ("Тартар из мраморной говядины с бриошью", "Рубленая вырезка, трюфельный айоли, каперсы, хрустящий тост", 5600, "190 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
            ("Филе лосося с кремом из сельдерея", "Свежий лосось на гриле, соус цитронет, спаржа на углях", 11200, "280 г", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80"),
            ("Салат с хрустящими баклажанами и страчателлой", "Баклажаны фри, сладкие томаты, нежный сыр, соус сладкий чили", 4600, "260 г", "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&q=80"),
            ("Фондан из бельгийского шоколада", "Горячий десерт с жидким центром и шариком ванильного пломбира", 3400, "160 г", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Панорамный столик с видом на парковую аллею", 15, 25, "round"),
            (2, 4, "Основной зал", "Столик рядом с открытой зоной Josper-гриля", 45, 25, "rect"),
            (3, 4, "Терраса", "Стол на свежем воздухе под кронами деревьев", 75, 25, "round"),
            (4, 6, "Терраса", "Просторный диванный стол на летней веранде", 15, 70, "rect"),
            (5, 8, "VIP-кабина", "Закрытая стеклянная вилла для важных гостей", 50, 70, "rect"),
            (6, 2, "Chef's Table", "Высокий столик у стойки шеф-повара", 85, 70, "round")
        ]
    },
    {
        "id": 103,
        "name": "Mozzarella by Meyram Group",
        "city": "Шымкент",
        "cuisine": "Итальянская, Средиземноморская, Суши",
        "address": "ул. Тыныбаева, 33 (ЖК «Яссауи»)",
        "phone": "+7 (7252) 55-00-55",
        "rating": 4.85,
        "avg_check": 9500,
        "cover_image": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800&q=80",
        "description": "Культовый итальянский ресторан Шымкента. Хрустящая пицца из неаполитанской дровяной печи, свежая домашняя паста, морепродукты и нежнейший тирамису.",
        "working_hours": "11:00 - 00:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Mozzarella",
        "instagram_url": "https://instagram.com/mozzarella_shymkent",
        "whatsapp_url": "https://wa.me/77252550055",
        "owner_name": "Елена Ким",
        "owner_phone": "+7 (701) 550-05-50",
        "categories": [
            ("Неаполитанская пицца", "🍕", 1),
            ("Паста Fresca & Ризотто", "🍝", 2),
            ("Антипасти & Салаты", "🥗", 3),
            ("Японское меню & Роллы", "🍱", 4)
        ],
        "menu_items": [
            ("Пицца Буррата со спелыми томатами", "Хрустящий бортик, цельная сливочная буррата, песто, руккола", 5900, "420 г", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&q=80"),
            ("Спагетти Frutti di Mare с морепродуктами", "Креветки, мидии, кальмары, соус из томатов San Marzano", 6800, "340 г", "https://images.unsplash.com/photo-1621996346565-e3d5d6281084?w=600&q=80"),
            ("Ролл Филадельфия Люкс", "Охлажденный норвежский лосось, сливочный сыр, авокадо", 5400, "260 г", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=600&q=80"),
            ("Ризотто с белыми грибами и трюфелем", "Рис Карнароли, пармезан 24 месяца, ароматное трюфельное масло", 5200, "280 г", "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=600&q=80"),
            ("Классический Тирамису", "Маскарпоне, савоярди, пропитка эспрессо с марсалой", 3100, "170 г", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Уютный романтичный столик у витражных окон", 15, 20, "round"),
            (2, 4, "Основной зал", "Столик рядом с витриной открытой кухни", 45, 20, "rect"),
            (3, 4, "Основной зал", "Комфортный стол с бархатными креслами", 75, 20, "rect"),
            (4, 6, "VIP-кабина", "Семейная кабина в глубине зала", 25, 65, "rect"),
            (5, 8, "VIP-зал", "Приватный зал для дней рождений", 65, 65, "rect")
        ]
    },
    {
        "id": 104,
        "name": "Чайхана Көк-Сарай (Кок-Сарай)",
        "city": "Шымкент",
        "cuisine": "Узбекская, Восточная, Чайхана",
        "address": "пр. Байдибек би / ул. Жолдасбекова, 24",
        "phone": "+7 (7252) 43-22-11",
        "rating": 4.9,
        "avg_check": 5500,
        "cover_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
        "description": "Легендарная шымкентская чайхана. Настоящий самаркандский и ташкентский плов на курдюке, сочные шашлыки из баранины, хрустящая тандырная самса и уютные восточные топчаны.",
        "working_hours": "10:00 - 02:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Кок-Сарай",
        "instagram_url": "https://instagram.com/koksaray_shymkent",
        "whatsapp_url": "https://wa.me/77252432211",
        "owner_name": "Алишер Назаров",
        "owner_phone": "+7 (702) 432-21-10",
        "categories": [
            ("Праздничные пловы в казане", "🍲", 1),
            ("Шашлыки на углях", "🍢", 2),
            ("Самса из тандыра и Выпечка", "🥟", 3),
            ("Чайханские чаи и Сладости", "🫖", 4)
        ],
        "menu_items": [
            ("Чайханский плов с бараниной и казы", "Рис лазер, сочное мясо ягненка, желтая морковь, чеснок, перец", 3800, "420 г", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80"),
            ("Шашлык из каре ягненка 'Уч-панжа'", "Три шампура нежнейшего каре на саксауле с луком и сумахом", 4600, "280 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
            ("Люля-кебаб из отборной говядины", "Сочный фарш со специями, завернутый в тонкий лаваш", 2900, "230 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80"),
            ("Самса парки с рубленой говядиной", "Слоеное тесто, рубленое мясо, курдюк, черный кунжут", 950, "160 г", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80"),
            ("Салат Ачичук классический", "Тончайшие слайсы спелых южных томатов со сладким луком", 1800, "220 г", "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&q=80"),
            ("Чай Ташкентский со специями и наватом", "Зеленый и черный чай, горная мята, лимон, нават", 1700, "900 мл", "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&q=80")
        ],
        "tables": [
            (1, 4, "Основной зал", "Классический стол с мягкими стульями", 15, 20, "rect"),
            (2, 6, "Основной зал", "Просторный стол для семейного обеда", 45, 20, "rect"),
            (3, 8, "Топчан", "Традиционный топчан с коврами и подушками", 80, 20, "rect"),
            (4, 10, "Топчан", "Большой топчан в саду для компании друзей", 20, 65, "rect"),
            (5, 12, "VIP-кабина", "Отдельная кабина с кондиционером и TV", 60, 65, "rect")
        ]
    },
    {
        "id": 105,
        "name": "Камшат Family",
        "city": "Шымкент",
        "cuisine": "Казахская, Восточная, Европейская",
        "address": "пр. Кунаева, 27/1 (1–3 этажи)",
        "phone": "+7 (7252) 53-00-11",
        "rating": 4.8,
        "avg_check": 6800,
        "cover_image": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800&q=80",
        "description": "Популярный ресторанный комплекс для семейных торжеств и больших компаний. Просторные залы, панорамные террасы, VIP-кабины, отменные шашлыки и богатый дастархан.",
        "working_hours": "11:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Камшат%20Family",
        "instagram_url": "https://instagram.com/kamshat_family",
        "whatsapp_url": "https://wa.me/77252530011",
        "owner_name": "Камшат Утегенова",
        "owner_phone": "+7 (701) 530-01-10",
        "categories": [
            ("Мясные блюда на садже", "🥘", 1),
            ("Шашлычный двор", "🍢", 2),
            ("Супы и Манты", "🥣", 3),
            ("Выпечка & Напитки", "🥐", 4)
        ],
        "menu_items": [
            ("Садж из телятины с овощами гриль", "Горячая сковорода садж, сочное филе, картофель, томаты, баклажаны", 7900, "700 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
            ("Манты с рубленой бараниной", "Тонкое тесто, сочная начинка из мяса и тыквы, подаются со сметаной", 3200, "320 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
            ("Шашлык из мякоти барашка", "Традиционный шымкентский шашлык, маринованный в минеральной воде", 3900, "240 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
            ("Сорпа по-казахски с баурсаками", "Наваристый бульон из конины с казы и зеленью", 2400, "350 мл", "https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80")
        ],
        "tables": [
            (1, 4, "Основной зал", "Удобный столик рядом с детской зоной", 15, 25, "rect"),
            (2, 6, "Основной зал", "Семейный стол у панорамных окон", 50, 25, "rect"),
            (3, 8, "Терраса", "Стол на крыше 3-го этажа с видом на Кунаева", 80, 25, "round"),
            (4, 10, "VIP-кабина", "Просторная кабина для семейных торжеств", 30, 70, "rect"),
            (5, 14, "Банкетный зал", "Большой стол для юбилеев и встреч", 70, 70, "rect")
        ]
    },
    {
        "id": 106,
        "name": "Bozjyra (Бозжыра)",
        "city": "Шымкент",
        "cuisine": "Национальная казахская, Авторская",
        "address": "пр. Кунаева, 13",
        "phone": "+7 (701) 333-77-88",
        "rating": 4.9,
        "avg_check": 8500,
        "cover_image": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&q=80",
        "description": "Этно-ресторан современной казахской гастрономии. Древние рецепты южного Казахстана, нежнейшее сырне в казане, карын-бүрме, баурсаки и степные чаи с травами.",
        "working_hours": "11:00 - 00:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Bozjyra",
        "instagram_url": "https://instagram.com/bozjyra_restaurant",
        "whatsapp_url": "https://wa.me/77013337788",
        "owner_name": "Бахытжан Жусупов",
        "owner_phone": "+7 (701) 333-77-80",
        "categories": [
            ("Мясные рецепты предков", "🍖", 1),
            ("Казахские супы & Сорпа", "🍲", 2),
            ("Национальные деликатесы", "🥩", 3),
            ("Чайная церемония", "🫖", 4)
        ],
        "menu_items": [
            ("Карын-бүрме томленое в золе", "Баранина с диким луком и травами, запеченная по древней технологии", 8500, "500 г", "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80"),
            ("Куырдак из парной ягнятины", "Печень, сердце, сочное мясо, молодой картофель и ароматный лук", 5200, "380 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
            ("Ассорти казы и жая", "Выдержанные мясные деликатесы с горчичным соусом", 4600, "200 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Уютный столик с видом на сквер", 15, 20, "round"),
            (2, 4, "Основной зал", "Столик с этническими войлочными панно", 50, 20, "rect"),
            (3, 6, "Основной зал", "Круглый деревянный стол", 85, 20, "round"),
            (4, 8, "VIP-кабина", "Кабина в стиле кочевой юрты", 30, 65, "rect"),
            (5, 12, "VIP-зал", "Большой зал для торжественных обедов", 75, 65, "rect")
        ]
    },
    {
        "id": 107,
        "name": "Kazakhasia (Rixos Khadisha Shymkent)",
        "city": "Шымкент",
        "cuisine": "Паназиатская, Европейская, Фьюжн",
        "address": "ул. Желтоксан, 17 (отель Rixos Khadisha, 1 этаж)",
        "phone": "+7 (7252) 66-00-00",
        "rating": 4.95,
        "avg_check": 20000,
        "cover_image": "https://images.unsplash.com/photo-1578474846511-04ba529f0b88?w=800&q=80",
        "description": "Флагманский 5-звездочный ресторан премиум-класса при отеле Rixos Khadisha. Открытая шоу-кухня, изысканные роллы, пекинская утка, премиальные стейки и коллекционные вина.",
        "working_hours": "12:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Rixos%20Khadisha%20Kazakhasia",
        "instagram_url": "https://instagram.com/rixoskhadishashymkent",
        "whatsapp_url": "https://wa.me/77252660000",
        "owner_name": "Rixos Management",
        "owner_phone": "+7 (701) 660-00-01",
        "categories": [
            ("Азиатские деликатесы & WOK", "🥢", 1),
            ("Суши, Сашими & Роллы", "🍣", 2),
            ("Премиальные стейки & Гриль", "🥩", 3),
            ("Винная карта Гранд Крю", "🍷", 4)
        ],
        "menu_items": [
            ("Утка по-пекински фирменная", "Хрустящая корочка, тонкие блинчики, соус хойсин, огурец и порей", 18500, "800 г", "https://images.unsplash.com/photo-1518492104633-130d0cc84637?w=600&q=80"),
            ("Стейк Вагю А5 на раскаленном камне", "Легендарная японская мраморная говядина высочайшей категории", 29000, "200 г", "https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80"),
            ("Ролл Дракон с угрем и трюфельным сыром", "Копченый угорь, авокадо, икра тобико, соус унаги", 7800, "280 г", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=600&q=80"),
            ("Том Ям с гигантскими креветками", "Аутентичный тайский суп на кокосовом молоке с лемонграссом", 6500, "380 мл", "https://images.unsplash.com/photo-1548943487-a2e4e43b4853?w=600&q=80")
        ],
        "tables": [
            (1, 2, "Chef's Table", "Премиум-место у открытой шоу-кухни", 15, 25, "round"),
            (2, 4, "Основной зал", "Мягкая зона с дизайнерским освещением", 45, 25, "rect"),
            (3, 4, "Основной зал", "Элегантный столик для деловых встреч", 75, 25, "rect"),
            (4, 6, "VIP-кабинет", "Приватный кабинет Rixos Lounge", 25, 70, "rect"),
            (5, 10, "VIP-кабинет", "Представительский президентский зал", 70, 70, "rect")
        ]
    },
    {
        "id": 108,
        "name": "Baiken Resto Bar & Terrace",
        "city": "Шымкент",
        "cuisine": "Европейская, Стейки, Барная классика",
        "address": "пр. Байдибек би, 136/6в",
        "phone": "+7 (702) 888-99-11",
        "rating": 4.8,
        "avg_check": 10500,
        "cover_image": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=800&q=80",
        "description": "Атмосферный панорамный ресто-бар на проспекте Байдибек би. Авторская кухня, живая музыка, летняя терраса с видом на ночные огни города и авторские коктейли.",
        "working_hours": "17:00 - 03:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Baiken%20Resto%20Bar",
        "instagram_url": "https://instagram.com/baiken_restobar",
        "whatsapp_url": "https://wa.me/77028889911",
        "owner_name": "Байкен Амиров",
        "owner_phone": "+7 (702) 888-99-10",
        "categories": [
            ("Мясо на гриле & Бургеры", "🍔", 1),
            ("Закуски к коктейлям & Тапас", "🍟", 2),
            ("Авторская барная карта", "🍸", 3)
        ],
        "menu_items": [
            ("Бургер Baiken с котлетой Black Angus", "Бриошь, трюфельный соус, сыр чеддер, карамелизированный лук", 4900, "380 г", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&q=80"),
            ("Стейк Стриплойн с перечным соусом", "Мраморная говядина, молодой картофель с розмарином", 11500, "340 г", "https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80"),
            ("Креветки темпура с васаби-майонезом", "Тигровые креветки в хрустящем кляре с азиатским дипом", 5200, "200 г", "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Панорамный вид на проспект Байдибек би", 15, 20, "round"),
            (2, 4, "Терраса", "Летняя терраса на свежем воздухе", 50, 20, "rect"),
            (3, 4, "Основной зал", "Столик рядом со сценой с живым звуком", 80, 20, "rect"),
            (4, 6, "Терраса", "Большой диван на открытой террасе", 25, 65, "rect"),
            (5, 8, "VIP-лаундж", "Отдельная мягкая зона для компаний", 70, 65, "rect")
        ]
    },
    {
        "id": 109,
        "name": "Grand Береке",
        "city": "Шымкент",
        "cuisine": "Казахская, Восточная, Банкетная",
        "address": "пр. Байдибек би, 22а",
        "phone": "+7 (7252) 40-77-77",
        "rating": 4.75,
        "avg_check": 8000,
        "cover_image": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=800&q=80",
        "description": "Большой ресторанный комплекс традиционного шымкентского гостеприимства. Залы «Абырой» для почетных гостей, топчаны с коврами, блюда на садже и праздничный бешбармак.",
        "working_hours": "11:00 - 02:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Grand%20Береке",
        "instagram_url": "https://instagram.com/grand_bereke_shymkent",
        "whatsapp_url": "https://wa.me/77252407777",
        "owner_name": "Нурлан Куанышев",
        "owner_phone": "+7 (701) 407-77-70",
        "categories": [
            ("Праздничный дастархан", "🥘", 1),
            ("Шашлыки & Гриль", "🍢", 2),
            ("Холодные закуски & Салаты", "🥗", 3)
        ],
        "menu_items": [
            ("Ассорти шашлыков 'Гранд Береке'", "Баранина, говядина, куриные крылышки, люля-кебаб, овощи гриль", 14500, "1200 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
            ("Бешбармак Абырой с казы и жая", "Традиционная подача на медном табаке с туздыком", 6500, "450 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80")
        ],
        "tables": [
            (1, 4, "Основной зал", "Стол в просторном банкетном зале", 20, 20, "rect"),
            (2, 6, "Основной зал", "Стол для семейного ужина", 55, 20, "rect"),
            (3, 8, "Топчан", "Топчан с подушками и традиционными коврами", 85, 20, "rect"),
            (4, 12, "VIP-кабина", "Большая кабина для уважаемых гостей", 30, 65, "rect"),
            (5, 16, "VIP-зал", "Зал торжеств с караоке", 75, 65, "rect")
        ]
    },
    {
        "id": 110,
        "name": "Jeti Tandir (Жеті Тандыр)",
        "city": "Шымкент",
        "cuisine": "Восточная, Шашлычная, Тандырная",
        "address": "просп. Тауке хана, 161",
        "phone": "+7 (707) 717-77-70",
        "rating": 4.8,
        "avg_check": 5000,
        "cover_image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80",
        "description": "Народный ресторан кавказской и восточной кухни. Знаменитые метровые шашлыки, румяный лаваш из глиняного тандыра, сытные мясные блюда и демократичная атмосфера.",
        "working_hours": "10:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Jeti%20Tandir",
        "instagram_url": "https://instagram.com/jeti_tandir",
        "whatsapp_url": "https://wa.me/77077177770",
        "owner_name": "Рустам Каримов",
        "owner_phone": "+7 (707) 717-77-71",
        "categories": [
            ("Шашлычный рай", "🍢", 1),
            ("Тандырные лепешки & Самса", "🥟", 2),
            ("Первые блюда", "🍲", 3)
        ],
        "menu_items": [
            ("Метровый шашлык из баранины", "Огромный фирменный шампур отборного мяса на компанию", 7800, "650 г", "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80"),
            ("Шашлык из печени в жировой сетке", "Нежнейшая печень со специями в хрустящей жировой пленке", 2800, "220 г", "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80"),
            ("Горячая тандырная лепешка", "Прямо из глиняной печи с кунжутом", 350, "200 г", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80")
        ],
        "tables": [
            (1, 4, "Основной зал", "Простой и удобный деревянный столик", 20, 25, "rect"),
            (2, 6, "Основной зал", "Стол для дружеских посиделок", 55, 25, "rect"),
            (3, 8, "Топчан", "Топчан на свежем воздухе", 85, 25, "rect"),
            (4, 10, "VIP-кабина", "Отдельная кабина для компании", 40, 70, "rect")
        ]
    },
    {
        "id": 111,
        "name": "Vinopark Restaurant",
        "city": "Шымкент",
        "cuisine": "Европейская, Средиземноморская, Винная карта",
        "address": "ул. Туркестанская, 55",
        "phone": "+7 (7252) 39-20-20",
        "rating": 4.85,
        "avg_check": 11500,
        "cover_image": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=800&q=80",
        "description": "Элегантный винный ресторан для ценителей высокой кухни. Собственная энотека, ризотто с трюфелем, утиная грудка Магре, сырные плато и камерная романтическая атмосфера.",
        "working_hours": "13:00 - 01:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Vinopark",
        "instagram_url": "https://instagram.com/vinopark_restaurant",
        "whatsapp_url": "https://wa.me/77252392020",
        "owner_name": "Артур Цой",
        "owner_phone": "+7 (701) 392-02-00",
        "categories": [
            ("Эногастрономия & Закуски", "🧀", 1),
            ("Основные блюда & Птица", "🥩", 2),
            ("Винная карта", "🍷", 3)
        ],
        "menu_items": [
            ("Утиная грудка Магре с вишневым соусом", "Нежнейшее утиное филе medium rare с пюре из пастернака", 7800, "260 г", "https://images.unsplash.com/photo-1514944298352-70b9794025a1?w=600&q=80"),
            ("Сырная тарелка Гранд Резерв", "Пармезан, Дор Блю, Бри, козий сыр, орехи, инжирный джем", 6200, "240 г", "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Камерный столик для романтического свидания", 20, 20, "round"),
            (2, 4, "Основной зал", "Столик рядом с винной стеклянной комнатой", 55, 20, "rect"),
            (3, 6, "Основной зал", "Диванный столик для дегустаций", 85, 20, "rect"),
            (4, 8, "VIP-комната", "Приватная дегустационная комната", 50, 65, "rect")
        ]
    },
    {
        "id": 112,
        "name": "Madlen Палуба",
        "city": "Шымкент",
        "cuisine": "Европейская, Десерты, Завтраки, Кофейня",
        "address": "ул. Толе би, 41а (у парка Кен-Баба)",
        "phone": "+7 (7252) 53-62-62",
        "rating": 4.8,
        "avg_check": 4500,
        "cover_image": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80",
        "description": "Легендарная городская кондитерская-кофейня на берегу озера. Фирменные завтраки, венские десерты, круассаны ручной работы, отличный эспрессо и уютная палуба над водой.",
        "working_hours": "08:30 - 23:30",
        "two_gis_url": "https://2gis.kz/shymkent/search/Madlen",
        "instagram_url": "https://instagram.com/madlen_kz",
        "whatsapp_url": "https://wa.me/77252536262",
        "owner_name": "Сеть Madlen",
        "owner_phone": "+7 (701) 536-26-20",
        "categories": [
            ("Завтраки целый день", "🍳", 1),
            ("Венские десерты & Торты", "🍰", 2),
            ("Кофе & Авторские чаи", "☕", 3)
        ],
        "menu_items": [
            ("Шымкентский завтрак с каймаком", "Горячие лепешки, густой каймак, горный мед, яйца пашот", 3200, "350 г", "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=600&q=80"),
            ("Фирменный торт Наполеон Madlen", "Хрустящие тонкие коржи со сливочно-заварным кремом", 1850, "160 г", "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=600&q=80"),
            ("Капучино на миндальном молоке", "Свежеобжаренная 100% арабика, плотная шелковистая пенка", 1400, "300 мл", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&q=80")
        ],
        "tables": [
            (1, 2, "Палуба у воды", "Столик у самой кромки воды с видом на лебедей", 15, 20, "round"),
            (2, 4, "Палуба у воды", "Семейный стол на открытом воздухе", 50, 20, "rect"),
            (3, 4, "Основной зал", "Мягкий диванный столик в кондитерском зале", 80, 20, "rect"),
            (4, 6, "Основной зал", "Большой стол для семейных встреч с детьми", 45, 65, "rect")
        ]
    },
    {
        "id": 113,
        "name": "KEBEJE",
        "city": "Шымкент",
        "cuisine": "Национальная казахская, Домашняя",
        "address": "ул. Казыбек би, 40",
        "phone": "+7 (701) 450-50-50",
        "rating": 4.85,
        "avg_check": 7200,
        "cover_image": "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=800&q=80",
        "description": "Самобытный этно-ресторан в центре Шымкента. Сочный куырдак из свежего мяса, пышные баурсаки, домашний кымыз, наваристая сорпа и тёплый колорит казахского аула.",
        "working_hours": "11:00 - 23:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/KEBEJE",
        "instagram_url": "https://instagram.com/kebeje_shymkent",
        "whatsapp_url": "https://wa.me/77014505050",
        "owner_name": "Алмас Тулегенов",
        "owner_phone": "+7 (701) 450-50-51",
        "categories": [
            ("Казахские блюда в глиняной посуде", "🍲", 1),
            ("Мясные деликатесы", "🥩", 2),
            ("Кымыз, Шубат и Чай", "🥛", 3)
        ],
        "menu_items": [
            ("Куырдак по-шымкентски", "Парная баранина, картофель, лук, свежая зелень в чугунном горшочке", 4800, "380 г", "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=600&q=80"),
            ("Баурсаки золотистые с каймаком", "Пышные горячие баурсаки прямо из фритюра с домашним каймаком", 1600, "250 г", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Столик с видом на историческую улицу", 20, 20, "round"),
            (2, 4, "Основной зал", "Деревянный стол с национальным орнаментом", 55, 20, "rect"),
            (3, 8, "Топчан", "Топчан с шелковыми подушками", 85, 20, "rect"),
            (4, 10, "VIP-кабина", "Отдельная юрта-комната", 50, 65, "rect")
        ]
    },
    {
        "id": 114,
        "name": "Meat and Sea Restaurant",
        "city": "Шымкент",
        "cuisine": "Стейки, Морепродукты, Средиземноморская",
        "address": "ул. Желтоксан, 17",
        "phone": "+7 (7252) 99-11-22",
        "rating": 4.9,
        "avg_check": 14500,
        "cover_image": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&q=80",
        "description": "Ресторан премиальных стейков и свежих морепродуктов. Устричный бар, лобстеры, дорадо на гриле и выдержанные стейки Томагавк для гурманов.",
        "working_hours": "12:00 - 00:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Meat%20and%20Sea",
        "instagram_url": "https://instagram.com/meatandsea_shymkent",
        "whatsapp_url": "https://wa.me/77252991122",
        "owner_name": "Мурат Идрисов",
        "owner_phone": "+7 (701) 991-12-20",
        "categories": [
            ("Свежие морепродукты & Устрицы", "🦪", 1),
            ("Dry-Aged Стейки", "🥩", 2),
            ("Средиземноморские салаты", "🥗", 3)
        ],
        "menu_items": [
            ("Стейк Томагавк сухого вызревания", "Огромный стейк на кости 28 дней вызревания с чесночным маслом", 22000, "850 г", "https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80"),
            ("Дорадо на гриле с травами", "Свежая рыба на углях с соусом сальса верде и печеным лимоном", 8900, "360 г", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Столик с видом на парк", 20, 20, "round"),
            (2, 4, "Основной зал", "Стол рядом с ледяной витриной устриц", 55, 20, "rect"),
            (3, 6, "Основной зал", "Большой стол для ценителей стейков", 85, 20, "rect"),
            (4, 8, "VIP-кабинет", "Приватный зал для переговоров", 50, 65, "rect")
        ]
    },
    {
        "id": 115,
        "name": "Wok-Wok (Meyram Group)",
        "city": "Шымкент",
        "cuisine": "Паназиатская, Тайская, Японская",
        "address": "ул. Байтерекова, 98",
        "phone": "+7 (7252) 58-44-00",
        "rating": 4.8,
        "avg_check": 6500,
        "cover_image": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800&q=80",
        "description": "Стильный паназиатский ресторан от Meyram Group. Острый Том Ям с креветками, лапша Pad Thai из вока, хрустящие гедза и авторские роллы в ярком интерьере.",
        "working_hours": "11:30 - 00:00",
        "two_gis_url": "https://2gis.kz/shymkent/search/Wok-Wok",
        "instagram_url": "https://instagram.com/wokwok_shymkent",
        "whatsapp_url": "https://wa.me/77252584400",
        "owner_name": "Meyram Group",
        "owner_phone": "+7 (701) 584-40-00",
        "categories": [
            ("Лапша WOK & Рис", "🍜", 1),
            ("Супы & Рамен", "🥣", 2),
            ("Суши & Роллы", "🍣", 3)
        ],
        "menu_items": [
            ("Лапша Пад Тай с тигровыми креветками", "Рисовая лапша, креветки, ростки сои, арахис, тамариндовый соус", 4200, "340 г", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&q=80"),
            ("Рамен со свиной грудинкой тясю", "Густой 12-часовой бульон, пшеничная лапша, маринованное яйцо", 3800, "450 мл", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&q=80")
        ],
        "tables": [
            (1, 2, "У окна", "Яркий столик с неоновой подсветкой", 20, 20, "round"),
            (2, 4, "Основной зал", "Столик рядом с открытой зоной вок-кухни", 55, 20, "rect"),
            (3, 6, "Основной зал", "Просторный диванный стол", 85, 20, "rect"),
            (4, 8, "VIP-лаундж", "Отдельная зона с караоке", 50, 65, "rect")
        ]
    }
]



def seed_shymkent_data(cursor: sqlite3.Cursor):
    """Seeds authentic Shymkent restaurants into database."""
    exp_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d 23:59:59")
    cat_id_counter = 1000
    item_id_counter = 2000

    for r in SHYMKENT_RESTAURANTS:
        r_id = r["id"]
        clean_tag = re.sub(r'[^A-Za-z0-9]', '', r['name'].split()[0].upper())[:8] or "SHYM"
        access_key = f"RKZ-{clean_tag}-{secrets.token_hex(2).upper()}"

        cursor.execute("""
            INSERT INTO restaurants (
                id, name, city, cuisine, address, phone, rating, avg_check, cover_image,
                description, working_hours, two_gis_url, admin_tg_id, instagram_url,
                whatsapp_url, access_key, subscription_status, subscription_plan,
                subscription_expires_at, owner_name, owner_phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 348581961, ?, ?, ?, 'active', 'pro', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                city=excluded.city,
                cuisine=excluded.cuisine,
                address=excluded.address,
                phone=excluded.phone,
                rating=excluded.rating,
                avg_check=excluded.avg_check,
                cover_image=excluded.cover_image,
                description=excluded.description,
                working_hours=excluded.working_hours,
                two_gis_url=excluded.two_gis_url,
                instagram_url=excluded.instagram_url,
                whatsapp_url=excluded.whatsapp_url,
                owner_name=excluded.owner_name,
                owner_phone=excluded.owner_phone
        """, (
            r_id, r["name"], r["city"], r["cuisine"], r["address"], r["phone"],
            r["rating"], r["avg_check"], r["cover_image"], r["description"],
            r["working_hours"], r["two_gis_url"], r["instagram_url"], r["whatsapp_url"],
            access_key, exp_date, r["owner_name"], r["owner_phone"]
        ))

        cursor.execute("DELETE FROM tables WHERE restaurant_id = ?", (r_id,))
        cursor.execute("DELETE FROM menu_items WHERE restaurant_id = ?", (r_id,))
        cursor.execute("DELETE FROM menu_categories WHERE restaurant_id = ?", (r_id,))

        cat_map = {}
        for c_title, c_icon, c_sort in r["categories"]:
            cat_id_counter += 1
            cursor.execute("""
                INSERT INTO menu_categories (id, restaurant_id, name, icon, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (cat_id_counter, r_id, c_title, c_icon, c_sort))
            cat_map[c_sort] = cat_id_counter

        for idx, (title, desc, price, weight, img) in enumerate(r["menu_items"]):
            cat_id = cat_map.get(1 if idx < 2 else (2 if idx < 4 else 3), list(cat_map.values())[0])
            item_id_counter += 1
            cursor.execute("""
                INSERT INTO menu_items (id, restaurant_id, category_id, title, description, price, weight, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id_counter, r_id, cat_id, title, desc, price, weight, img))

        for t_num, seats, zone, desc, px, py, shape in r["tables"]:
            cursor.execute("""
                INSERT INTO tables (restaurant_id, table_number, seats, zone_type, description, position_x, position_y, shape)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (r_id, t_num, seats, zone, desc, px, py, shape))
