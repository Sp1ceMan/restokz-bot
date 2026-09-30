import os
import sys
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -------------------------------------------------------------
# PALETTE DEFINITIONS (Quiet Luxury Dark Theme)
# -------------------------------------------------------------
COLOR_BG = RGBColor(14, 16, 19)          # #0E1013 (Deep Obsidian)
COLOR_CARD = RGBColor(21, 23, 29)        # #15171D (Card Charcoal)
COLOR_CARD_ALT = RGBColor(28, 31, 38)    # #1C1F26 (Elevated Card)
COLOR_BORDER = RGBColor(197, 168, 128)   # #C5A880 (Luxury Gold)
COLOR_BORDER_SUBTLE = RGBColor(50, 55, 65)

COLOR_GOLD = RGBColor(197, 168, 128)     # Primary Gold
COLOR_GOLD_LIGHT = RGBColor(223, 202, 171) # Light Gold Text
COLOR_WHITE = RGBColor(244, 242, 238)    # Clean Off-White
COLOR_MUTED = RGBColor(156, 163, 175)    # Slate/Zinc Grey

COLOR_EMERALD = RGBColor(52, 211, 153)   # Green #34D399
COLOR_SKY = RGBColor(56, 189, 248)       # Blue #38BDF8
COLOR_ROSE = RGBColor(251, 113, 133)     # Rose #FB7185
COLOR_AMBER = RGBColor(251, 191, 36)     # Amber #FBBF24

FONT_TITLE = 'Playfair Display'
FONT_BODY = 'Plus Jakarta Sans'
FONT_FALLBACK_TITLE = 'Georgia'
FONT_FALLBACK_BODY = 'Segoe UI'

ASSETS_DIR = r'd:\bot\presentation_assets'

# Helper to check asset
def get_asset(filename):
    p = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(p):
        return p
    return None

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, eyebrow, title, subtitle):
        # Eyebrow pill
        eyebrow_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf = eyebrow_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = eyebrow.upper()
        p.font.name = FONT_FALLBACK_BODY
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_GOLD

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.55))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_FALLBACK_TITLE
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

        # Subtitle
        if subtitle:
            sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(0.35))
            tf = sub_box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.text = subtitle
            p.font.name = FONT_FALLBACK_BODY
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_MUTED

    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD, border_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1)
        else:
            card.line.fill.background()
        return card

    def add_picture_frame(slide, img_path, left, top, width, height):
        # Card shadow frame behind
        frame = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left - Inches(0.04), top - Inches(0.04), width + Inches(0.08), height + Inches(0.08))
        frame.fill.solid()
        frame.fill.fore_color.rgb = COLOR_CARD_ALT
        frame.line.color.rgb = COLOR_BORDER
        frame.line.width = Pt(1.5)
        # Image
        slide.shapes.add_picture(img_path, left, top, width, height)

    # =========================================================================
    # SLIDE 1: COVER / TITLE SLIDE
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)

    # Accent decorative glow bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.08), Inches(3.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_GOLD
    bar.line.fill.background()

    # Title text box
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(1.4), Inches(7.5), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "👑 RESTOKZ & RESTOKZ PRO"
    p0.font.name = FONT_FALLBACK_BODY
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_GOLD

    p1 = tf.add_paragraph()
    p1.text = "Цифровая экосистема бронирования и управления посадкой"
    p1.font.name = FONT_FALLBACK_TITLE
    p1.font.size = Pt(30)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE
    p1.space_before = Pt(12)

    p2 = tf.add_paragraph()
    p2.text = "Устранение No-Show • Полный контроль зала • Выручка ресторанов без комиссий агрегаторов"
    p2.font.name = FONT_FALLBACK_BODY
    p2.font.size = Pt(14)
    p2.font.color.rgb = COLOR_GOLD_LIGHT
    p2.space_before = Pt(10)

    # 3 Pills on cover
    pills = [
        ("📱 Telegram Mini App", "Бронирование гостем за 30 сек"),
        ("🪑 Терминал Хостес PRO", "Живая интерактивная карта зала"),
        ("⚡ Облачная платформа", "Мгновенные статусы и пуш-уведомления")
    ]
    for i, (head, sub) in enumerate(pills):
        c = add_card(slide, Inches(1.1 + i * 2.5), Inches(5.6), Inches(2.35), Inches(1.1), COLOR_CARD, COLOR_GOLD)
        tb_c = slide.shapes.add_textbox(Inches(1.15 + i * 2.5), Inches(5.65), Inches(2.25), Inches(1.0))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        p_c1 = tf_c.paragraphs[0]
        p_c1.text = head
        p_c1.font.size = Pt(11)
        p_c1.font.bold = True
        p_c1.font.color.rgb = COLOR_WHITE
        p_c2 = tf_c.add_paragraph()
        p_c2.text = sub
        p_c2.font.size = Pt(9.5)
        p_c2.font.color.rgb = COLOR_MUTED
        p_c2.space_before = Pt(3)

    # Hero visual on right
    hero_img = get_asset('admin_terminal_mobile.png')
    if hero_img:
        add_picture_frame(slide, hero_img, Inches(9.2), Inches(1.2), Inches(2.6), Inches(5.6))

    hero_guest = get_asset('guest_catalog_mobile.png')
    if hero_guest:
        add_picture_frame(slide, hero_guest, Inches(10.7), Inches(1.7), Inches(2.2), Inches(4.7))

    # =========================================================================
    # SLIDE 2: ПРОБЛЕМА РЫНКА (PAIN POINTS)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Проблема рынка", "Почему рестораны Казахстана теряют до 25% выручки каждый уикенд?", "Исследование 20+ заведений (Шымкент, Алматы, Астана) выявило системный кризис ручного управления бронями")

    pains = [
        ("1. Хаос в WhatsApp и бумажных журналах", 
         "📞 Ручная переписка отнимает до 3-4 часов времени хостес в день\n"
         "⏳ В часы пик до 30% входящих звонков и сообщений остаются без ответа\n"
         "📝 Потери броней из-за неразборчивых записей, путаницы столов и смен\n"
         "📉 Нет единой прозрачной истории гостя и его предпочтений",
         COLOR_ROSE),

        ("2. Эпидемия No-Show и пустые брони", 
         "❌ 20-25% забронированных столов в пятницу и субботу пустуют\n"
         "🤷 Гости бронируют сразу 2-3 места и приходят в одно, не предупреждая\n"
         "💸 Ресторан отказывает реальным гостям («у нас всё занято»), а стол пуст\n"
         "💔 Прямые финансовые потери: от 80 000 до 350 000 ₸ за один вечер",
         COLOR_AMBER),

        ("3. Ловушка агрегаторов и тяжелых систем", 
         "💳 Агрегаторы берут 10-15% комиссии или от 500 ₸ за каждого гостя\n"
         "💻 Кассовые ERP (iiko, R-Keeper) перегружены и неудобны на смартфонах\n"
         "📱 У хостес нет легкого мобильного терминала для оперативной посадки\n"
         "🔒 Данные гостей остаются у сторонних сервисов, а не у ресторана",
         COLOR_SKY)
    ]

    for i, (title, desc, accent) in enumerate(pains):
        x = Inches(0.8 + i * 3.95)
        card = add_card(slide, x, Inches(1.8), Inches(3.8), Inches(5.1), COLOR_CARD, accent)
        
        # Header inside card
        tb = slide.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.4), Inches(4.7))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = accent

        for line in desc.split('\n'):
            p_line = tf.add_paragraph()
            p_line.text = line
            p_line.font.size = Pt(11)
            p_line.font.color.rgb = COLOR_WHITE
            p_line.space_before = Pt(8)

    # =========================================================================
    # SLIDE 3: РЕШЕНИЕ RESTOKZ (THE SOLUTION)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Решение платформы", "RestoKZ: Единая двусторонняя цифровая экосистема", "Связка клиента и ресторана в режиме реального времени без сторонних приложений")

    # Left: Guest side
    card_guest = add_card(slide, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), COLOR_CARD, COLOR_SKY)
    tb_g = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.1), Inches(4.7))
    tf_g = tb_g.text_frame
    tf_g.word_wrap = True
    
    p = tf_g.paragraphs[0]
    p.text = "🍽 ДЛЯ ГОСТЯ (B2C WEBAPP)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_SKY

    p_sub = tf_g.add_paragraph()
    p_sub.text = "Telegram Mini App — открывается мгновенно в 1 клик"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = COLOR_GOLD_LIGHT
    p_sub.space_before = Pt(4)

    g_points = [
        "⚡ Бронирование за 30 секунд без скачивания приложений из App Store",
        "🪑 Интерактивный выбор понравившегося столика на реальной схеме зала",
        "📖 Просмотр фото интерьера, актуального меню и среднего чека",
        "🔔 Автоматические статусы и напоминания в Telegram (защита от забывчивости)",
        "🌐 Поддержка 3 языков (Казахский, Русский, Английский)"
    ]
    for pt in g_points:
        p_pt = tf_g.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_WHITE
        p_pt.space_before = Pt(10)

    # Right: Restaurant Hostess side
    card_admin = add_card(slide, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), COLOR_CARD, COLOR_GOLD)
    tb_a = slide.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.7))
    tf_a = tb_a.text_frame
    tf_a.word_wrap = True

    p = tf_a.paragraphs[0]
    p.text = "👑 ДЛЯ РЕСТОРАНА (RESTOKZ PRO B2B)"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    p_sub = tf_a.add_paragraph()
    p_sub.text = "Мобильный терминал хостес и управляющего"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = COLOR_GOLD_LIGHT
    p_sub.space_before = Pt(4)

    a_points = [
        "📋 Живой журнал заявок со статусами (Новые, В брони, За столом, Отмена)",
        "🎯 Умные контекстные кнопки действий в 1 клик (Подтвердить / Посадить)",
        "🗺 Интерактивная карта зала с цветовой занятостью столов в реальном времени",
        "⏱ Контроль рабочей смены хостес, живой таймер и итоговый Z-отчет",
        "🔔 Мгновенные звуковые консьерж-уведомления (Chime) о новых бронях"
    ]
    for pt in a_points:
        p_pt = tf_a.add_paragraph()
        p_pt.text = pt
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_WHITE
        p_pt.space_before = Pt(10)

    # =========================================================================
    # SLIDE 4: ВИЗУАЛ ГОСТЯ (GUEST EXPERIENCE)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Интерфейс гостя", "Telegram Mini App: Бронирование столика в 3 касания", "Максимальная конверсия за счет нулевого трения — без логинов, SMS и паролей")

    # Left features card
    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.5), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    steps = [
        ("1. Умный каталог ресторанов", "Гость выбирает город (Алматы, Астана, Шымкент), фильтрует по кухне (Казахская, Итальянская, Восточная) и находит любимое заведение."),
        ("2. Выбор даты, времени и компании", "Удобная сетка тайм-слотов (обед, ужин, пиковые часы) и количества гостей. Система сразу показывает свободные столики."),
        ("3. Интерактивная схема зала", "Гость может выбрать конкретное место: панорамное окно, летняя терраса, VIP-кабина, топчан или банкетный дастархан."),
        ("4. Меню и детальная информация", "Цены, фирменные блюда, фотографии интерьера, геолокация и прямой переход в 2GIS / Instagram."),
        ("5. Автоматическое подтверждение", "Билет бронирования с уникальным ID сохраняется в Telegram. За 2 часа до визита бот отправляет вежливое напоминание.")
    ]

    for i, (title, desc) in enumerate(steps):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = title
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_GOLD
        if i > 0: p_h.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10.5)
        p_d.font.color.rgb = COLOR_WHITE
        p_d.space_before = Pt(2)

    # Right images
    img1 = get_asset('guest_catalog_mobile.png')
    img2 = get_asset('guest_restaurant_modal.png')
    if img1:
        add_picture_frame(slide, img1, Inches(7.6), Inches(1.8), Inches(2.4), Inches(5.1))
    if img2:
        add_picture_frame(slide, img2, Inches(10.3), Inches(1.8), Inches(2.4), Inches(5.1))

    # =========================================================================
    # SLIDE 5: ТЕРМИНАЛ ХОСТЕС (HOSTESS TERMINAL)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Терминал Ресторана", "RestoKZ PRO: Журнал броней с контекстными действиями", "Специально разработан под экраны смартфонов хостес с крупными шрифтами и тактильным откликом")

    # Left features card
    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.5), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    features = [
        ("⚡ Контекстные умные действия в 1 клик", "Кнопки динамически подстраиваются под статус заявки:\n• Ожидает: [✅ Подтвердить] + [❌ Отказ]\n• Подтверждена: [🥂 Посадить за стол] + [Отмена]\n• Гости сидят: [🔓 Стол освободился] + [↩ В бронь]"),
        ("🔍 Мгновенный поиск и фильтрация", "Поиск за доли секунды по имени гостя, номеру телефона или #ID заявки. Сегментный переключатель дат: «Все дни | Сегодня | Завтра»."),
        ("📊 Живой KPI-дашборд смены", "Крупные показатели вверху экрана: сколько заявок ждут ответа (⏳), сколько столов в брони (✅) и сколько гостей обслужено за смену (👥)."),
        ("🔔 Звуковые консьерж-уведомления (Chime)", "При поступлении новой онлайн-заявки терминал издает благородный мягкий гонг (Web Audio API), чтобы хостес не пропустила гостя."),
        ("🛡 Исключение ошибок человеческого фактора", "Невозможно случайно удалить бронь или повторно отменить уже отклоненную заявку. Полная синхронизация с базой данных.")
    ]

    for i, (title, desc) in enumerate(features):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = title
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_GOLD
        if i > 0: p_h.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_WHITE
        p_d.space_before = Pt(2)

    # Right images (Mobile + Desktop)
    img_admin = get_asset('admin_terminal_mobile.png')
    img_desk = get_asset('admin_desktop_terminal.png')
    if img_admin:
        add_picture_frame(slide, img_admin, Inches(7.6), Inches(1.8), Inches(2.4), Inches(5.1))
    if img_desk:
        add_picture_frame(slide, img_desk, Inches(10.2), Inches(2.5), Inches(2.6), Inches(3.8))

    # =========================================================================
    # SLIDE 6: КАРТА ЗАЛА И ШАХМАТКА СТОЛОВ (FLOOR MAP)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Схема рассадки", "Интерактивная карта зала: Наглядный контроль занятости", "Никаких накладок, путаницы столов и потери контроля в часы пиковой загрузки")

    # Left text
    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.5), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    floor_items = [
        ("🟢 Наглядная цветовая легенда статусов", "• Изумрудный: стол свободен для посадки\n• Золотой: стол подтвержден в бронь на выбранное время\n• Лазурный: гости уже сидят за столом\n• Янтарный: новая заявка ожидает подтверждения"),
        ("⚡ Посадка от двери в 2 клика (Walk-in)", "Гости пришли с улицы без брони? Хостес просто тапает на свободный стол в зале — карточка посадки открывается мгновенно."),
        ("🛡 Защита от овербукинга и коллизий", "Система автоматически блокирует стол на 2 часа вокруг времени брони. Никаких конфликтов из-за посадки двух компаний на один диван."),
        ("🏢 Зонирование ресторана", "Четкое разделение на зоны: основной зал, панорамные окна, летняя терраса, тихая зона, топчаны и VIP-кабины.")
    ]

    for i, (title, desc) in enumerate(floor_items):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = title
        p_h.font.size = Pt(13)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_EMERALD
        if i > 0: p_h.space_before = Pt(12)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = COLOR_WHITE
        p_d.space_before = Pt(3)

    img_floor = get_asset('admin_floor_map.png')
    if img_floor:
        add_picture_frame(slide, img_floor, Inches(8.5), Inches(1.8), Inches(2.45), Inches(5.1))

    # =========================================================================
    # SLIDE 7: УПРАВЛЕНИЕ СМЕНОЙ И Z-ОТЧЕТЫ (SHIFT MANAGEMENT)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Управление персоналом", "Рабочая смена и Z-отчётность: Полная прозрачность для владельца", "Хостес подотчетна системе, а управляющий видит реальные цифры загрузки зала")

    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.5), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    shift_items = [
        ("⏱ Интерактивный статус-бар смены", "В шапке терминала отображается пульсирующий статус с живым таймером (например, «● Смена 3ч 45м»). Данные сохраняются при перезагрузках."),
        ("📊 Автоматический подсчет метрик смены", "Терминал в реальном времени считает:\n• Количество поступивших и обработанных заявок\n• Суммарное количество реально посаженных гостей\n• Количество отмен и отказов с причинами"),
        ("🏁 Закрытие смены по кнопке и Z-отчет", "Хостес не может просто уйти — по окончании дня она нажимает «Завершить рабочую смену». Формируется итоговая сводка смены для передачи управляющему."),
        ("👤 Персональная ответственность", "Каждая смена привязана к имени дежурного администратора, исключая перекладывание вины за потерянные брони.")
    ]

    for i, (title, desc) in enumerate(shift_items):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = title
        p_h.font.size = Pt(13)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_GOLD
        if i > 0: p_h.space_before = Pt(10)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = COLOR_WHITE
        p_d.space_before = Pt(3)

    img_shift = get_asset('admin_shift_modal.png')
    if img_shift:
        add_picture_frame(slide, img_shift, Inches(8.5), Inches(1.8), Inches(2.45), Inches(5.1))

    # =========================================================================
    # SLIDE 8: МУЛЬТИЛОКАЦИЯ И БОКОВОЕ МЕНЮ (DRAWER & PICKER)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Современный UX/UI", "Мультилокация и быстрое управление сетью ресторанов", "Замена устаревших браузерных элементов на премиальные Bottom Sheets и боковое меню")

    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.5), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.9), Inches(4.7))
    tf = tb.text_frame
    tf.word_wrap = True

    ux_items = [
        ("🏛 Кастомный Luxury Bottom Sheet выбора заведения", "Вместо архаичного селектора — современная шторка с поиском, бейджами городов, количеством столов и моментальным переключением филиалов."),
        ("☰ Боковое меню (Side Drawer)", "Все служебные функции аккуратно спрятаны под гамбургер-меню, освобождая экран терминала для главного — броней и карты зала."),
        ("🌐 Трехъязычный интерфейс (RU / KZ / EN)", "Крупные удобные кнопки переключения языка для сотрудников и гостей в любом регионе Казахстана."),
        ("🍽 Быстрый переход «Терминал ↔ Витрина гостя»", "Хостес может в любой момент открыть клиентскую витрину и увидеть свой ресторан глазами гостя."),
        ("⚡ Тактильный отклик и анимации", "Плавная физика сжатия кнопок (Spring physics), адаптивность под Home Bar iPhone (Safe Area).")
    ]

    for i, (title, desc) in enumerate(ux_items):
        p_h = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_h.text = title
        p_h.font.size = Pt(12)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_GOLD_LIGHT
        if i > 0: p_h.space_before = Pt(8)

        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_WHITE
        p_d.space_before = Pt(2)

    img_picker = get_asset('admin_rest_picker.png')
    img_drawer = get_asset('admin_drawer_menu.png')
    if img_picker:
        add_picture_frame(slide, img_picker, Inches(7.6), Inches(1.8), Inches(2.4), Inches(5.1))
    if img_drawer:
        add_picture_frame(slide, img_drawer, Inches(10.3), Inches(1.8), Inches(2.4), Inches(5.1))

    # =========================================================================
    # SLIDE 9: КОНСТРУКТОР РЕСТОРАНА И МЕНЮ (ADMIN BACKOFFICE)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Настройка и кастомизация", "Конструктор зала и Управление рестораном", "Полная автономия заведения — добавление точек, настройка столов и блюд за 5 минут")

    cols = [
        ("🏢 Профиль & Соцсети", 
         "• Редактирование адреса, телефона и режима работы\n"
         "• Прямые кликабельные ссылки на 2GIS, Instagram, WhatsApp\n"
         "• Указание среднего чека и концепта кухни\n"
         "• Регистрация нового филиала сети в 1 клик",
         COLOR_SKY),

        ("🍽 Электронное Меню", 
         "• Добавление блюд по категориям (Основные, Закуски, Напитки)\n"
         "• Загрузка фото, указание граммовки и актуальных цен\n"
         "• Мгновенное скрытие блюд на «стоп-листе»\n"
         "• Синхронизация меню с витриной гостя",
         COLOR_GOLD),

        ("🪑 Конструктор Столов", 
         "• Добавление новых столиков в зал с номерами\n"
         "• Настройка вместимости (2, 4, 6, 8, 10, 12+ персон)\n"
         "• Выбор зоны (У окна, Терраса, VIP, Топчан)\n"
         "• Описание столика (у камина, панорамный вид)",
         COLOR_EMERALD)
    ]

    for i, (title, desc, color) in enumerate(cols):
        x = Inches(0.8 + i * 3.95)
        add_card(slide, x, Inches(1.8), Inches(3.8), Inches(5.1), COLOR_CARD, color)
        tb = slide.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.4), Inches(4.7))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = color

        for line in desc.split('\n'):
            p_line = tf.add_paragraph()
            p_line.text = line
            p_line.font.size = Pt(11)
            p_line.font.color.rgb = COLOR_WHITE
            p_line.space_before = Pt(8)

    # =========================================================================
    # SLIDE 10: СРАВНЕНИЕ И ПРЕИМУЩЕСТВА (COMPETITIVE ADVANTAGE)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Ценностное предложение", "Сравнение: Почему RestoKZ PRO выигрывает рынок?", "Сравнение традиционного подхода, сторонних агрегаторов и решения RestoKZ PRO")

    # Table comparison
    table_shape = slide.shapes.add_table(6, 4, Inches(0.8), Inches(1.8), Inches(11.73), Inches(4.9))
    table = table_shape.table

    # Set column widths
    table.columns[0].width = Inches(3.0)
    table.columns[1].width = Inches(2.9)
    table.columns[2].width = Inches(2.9)
    table.columns[3].width = Inches(2.93)

    headers = ["Критерий / Параметр", "Тетрадь + WhatsApp", "Агрегаторы (2GIS / Restolife)", "👑 RestoKZ PRO"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_CARD_ALT if j < 3 else COLOR_GOLD
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_GOLD if j < 3 else COLOR_BG
        p.alignment = PP_ALIGN.CENTER

    rows_data = [
        ("Скорость бронирования", "10-25 минут (долгие ответы)", "3-5 минут (сторонний сайт)", "⚡ 30 секунд (внутри Telegram)"),
        ("Защита от No-Show (неявки)", "❌ 0% (гости просто не приходят)", "⚠️ Слабая (смс-уведомление)", "🛡 Высокая (напоминания + статусы)"),
        ("Комиссия за гостей", "0 ₸, но скрытые потери от No-Show", "💸 10-15% с чека или 500₸/гость", "✅ 0% (фиксированная подписка)"),
        ("Карта зала и шахматка", "❌ Нет (ручные каракули)", "❌ Только список броней", "🗺 Интерактивная живая карта"),
        ("Удобство со смартфона", "❌ Постоянный стресс и переписки", "⚠️ Громоздкий десктопный кабинет", "📱 Легкий мобильный веб-терминал")
    ]

    for i, row in enumerate(rows_data):
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD if j < 3 else RGBColor(28, 32, 42)
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = COLOR_WHITE if j < 3 else COLOR_GOLD_LIGHT
            if j == 3: p.font.bold = True
            if j > 0: p.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 11: ЭКОНОМИКА И ТАРИФЫ (UNIT ECONOMICS & PRICING)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Бизнес-модель", "Тарифные планы и окупаемость для заведения", "Окупается за 1 спасенную бронь банкета на 8-10 человек в месяц")

    plans = [
        ("ТАРИФ «СТАРТ»", "35 000 ₸", "в месяц за заведение",
         [
             "✓ До 12 столиков в заведении",
             "✓ Гостевой Telegram Mini App",
             "✓ Журнал онлайн-бронирований",
             "✓ Напоминания гостям в Telegram",
             "✓ Техническая поддержка 7 дней"
         ], COLOR_CARD, COLOR_BORDER_SUBTLE, COLOR_WHITE),

        ("ТАРИФ «PRO ХИТ»", "49 000 ₸", "в месяц за заведение (Рекомендуемый)",
         [
             "✓ Неограниченное число столов",
             "✓ Интерактивная карта зала и шахматка",
             "✓ Управление рабочей сменой и Z-отчет",
             "✓ Звуковые уведомления (Chime)",
             "✓ Модуль Walk-in (бронь от двери)",
             "✓ Приоритетная поддержка 24/7"
         ], COLOR_CARD_ALT, COLOR_GOLD, COLOR_GOLD),

        ("ТАРИФ «СЕТЬ / VIP»", "65 000 ₸", "в месяц за точку (для сетей)",
         [
             "✓ Всё, что входит в тариф PRO",
             "✓ Единый мультилокационный кабинет",
             "✓ Неограниченное число филиалов сети",
             "✓ Персональный менеджер внедрения",
             "✓ Кастомизация под брендбук ресторана"
         ], COLOR_CARD, COLOR_BORDER_SUBTLE, COLOR_SKY)
    ]

    for i, (name, price, sub, bullets, bg_col, b_col, name_col) in enumerate(plans):
        x = Inches(0.8 + i * 3.95)
        add_card(slide, x, Inches(1.8), Inches(3.8), Inches(5.1), bg_col, b_col)
        tb = slide.shapes.add_textbox(x + Inches(0.2), Inches(2.0), Inches(3.4), Inches(4.7))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = name
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = name_col

        p_pr = tf.add_paragraph()
        p_pr.text = price
        p_pr.font.size = Pt(28)
        p_pr.font.bold = True
        p_pr.font.color.rgb = COLOR_WHITE
        p_pr.space_before = Pt(6)

        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(9.5)
        p_sub.font.color.rgb = COLOR_MUTED
        p_sub.space_before = Pt(2)

        for b in bullets:
            p_b = tf.add_paragraph()
            p_b.text = b
            p_b.font.size = Pt(10.5)
            p_b.font.color.rgb = COLOR_WHITE
            p_b.space_before = Pt(8)

    # =========================================================================
    # SLIDE 12: ДОРОЖНАЯ КАРТА И ДЕМО (ROADMAP & DEMO)
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    set_bg(slide)
    add_header(slide, "Развитие и контакты", "Дорожная карта RestoKZ & Живое тестирование", "Готовое рабочее решение, готовое к пилотному запуску в ресторанах уже сегодня")

    # Left: Roadmap
    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.0), Inches(5.1), COLOR_CARD, COLOR_BORDER_SUBTLE)
    tb_r = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.4), Inches(4.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True

    p = tf_r.paragraphs[0]
    p.text = "🗺 ДОРОЖНАЯ КАРТА ПРОЕКТА"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    roadmap = [
        ("Реализовано (v2.4 Live)", "• Полноценный гостевой WebApp с выбором залов и блюд\n• Терминал хостес с интерактивной шахматкой столов\n• Управление сменой, Z-отчеты и звуковые гонг-оповещения\n• Мультилокация и регистрация ресторанов", COLOR_EMERALD),
        ("Q4 2026: Kaspi QR Депозиты", "• Интеграция онлайн-депозитов через Kaspi QR для банкетов\n• 100% защита от неявки гостей (No-Show)", COLOR_SKY),
        ("Q1 2027: AI-Консьерж & WhatsApp", "• Голосовой AI-ассистент для приема броней по телефону\n• Официальный WhatsApp Business API шлюз", COLOR_AMBER)
    ]

    for stage, items, col in roadmap:
        p_s = tf_r.add_paragraph()
        p_s.text = stage
        p_s.font.size = Pt(11.5)
        p_s.font.bold = True
        p_s.font.color.rgb = col
        p_s.space_before = Pt(10)

        for line in items.split('\n'):
            p_it = tf_r.add_paragraph()
            p_it.text = line
            p_it.font.size = Pt(10)
            p_it.font.color.rgb = COLOR_WHITE
            p_it.space_before = Pt(2)

    # Right: Live Demo Links
    add_card(slide, Inches(7.2), Inches(1.8), Inches(5.3), Inches(5.1), COLOR_CARD, COLOR_GOLD)
    tb_d = slide.shapes.add_textbox(Inches(7.5), Inches(2.0), Inches(4.7), Inches(4.7))
    tf_d = tb_d.text_frame
    tf_d.word_wrap = True

    p = tf_d.paragraphs[0]
    p.text = "🚀 ПРОТЕСТИРУЙТЕ СИСТЕМУ ПРЯМО СЕЙЧАС"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_GOLD

    demo_info = [
        ("🍽 Гостевое приложение (Live Демо):", "https://sp1ceman.github.io/restokz-bot/"),
        ("👑 Терминал хостес RestoKZ PRO:", "https://sp1ceman.github.io/restokz-bot/admin.html"),
        ("💬 Telegram бот:", "@RestoKZ_Bot"),
        ("💼 Готовность к внедрению:", "Запуск пилотного ресторана занимает менее 1 дня без необходимости покупки дорогого оборудования — работает на любом смартфоне хостес.")
    ]

    for title, val in demo_info:
        p_t = tf_d.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_GOLD_LIGHT
        p_t.space_before = Pt(10)

        p_v = tf_d.add_paragraph()
        p_v.text = val
        p_v.font.size = Pt(10.5)
        p_v.font.color.rgb = COLOR_WHITE
        p_v.space_before = Pt(2)

    # Save
    out_path = r'd:\bot\RestoKZ_Presentation.pptx'
    prs.save(out_path)
    print(f"Presentation successfully created at: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")

if __name__ == '__main__':
    create_deck()
