# -*- coding: utf-8 -*-
"""
Generates an executive-level Word (.docx) document:
1. Product Hypotheses Validation Canvas (based on CustDev with 10 restaurateurs & 10 guests)
2. Comprehensive Competitive Matrix & Market Positioning for RestoKZ PRO.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Sets background color of a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout(doc, text, speaker="", tag="ИНСАЙТ"):
    """Adds a stylish callout block for quotes and insights."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    # Left border only (accent gold)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="C5A880"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    if tag:
        r_tag = p.add_run(f"[{tag}] ")
        r_tag.font.name = "Arial"
        r_tag.font.size = Pt(8.5)
        r_tag.font.bold = True
        r_tag.font.color.rgb = RGBColor(197, 168, 128)
        
    run = p.add_run(f"«{text}»")
    run.font.name = "Arial"
    run.font.size = Pt(9.5)
    run.font.italic = True
    run.font.color.rgb = RGBColor(51, 65, 85)
    
    if speaker:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(3)
        p2.paragraph_format.space_after = Pt(2)
        r2 = p2.add_run(f"— {speaker}")
        r2.font.name = "Arial"
        r2.font.size = Pt(9)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(161, 131, 89)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_document(output_path):
    doc = docx.Document()
    
    # Margins
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    COLOR_PRIMARY = RGBColor(15, 23, 42)    # Slate 900
    COLOR_SECONDARY = RGBColor(71, 85, 105) # Slate 600
    COLOR_GOLD = RGBColor(197, 168, 128)    # Gold
    COLOR_DARK_GOLD = RGBColor(161, 131, 89)
    COLOR_EMERALD = RGBColor(16, 185, 129)
    COLOR_ROSE = RGBColor(225, 29, 72)

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(2)
    r_t = p_title.add_run("РЕЕСТР ПРОДУКТОВЫХ ГИПОТЕЗ & КОНКУРЕНТНАЯ МАТРИЦА")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(17)
    r_t.font.bold = True
    r_t.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(4)
    r_s = p_sub.add_run("Аналитическая валидация Customer Development (20 интервью) и стратегическое позиционирование RestoKZ PRO")
    r_s.font.name = "Arial"
    r_s.font.size = Pt(12)
    r_s.font.bold = True
    r_s.font.color.rgb = COLOR_DARK_GOLD

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(12)
    r_m = p_meta.add_run("Проект: RestoKZ & RestoKZ PRO | Рынок: Казахстан (Шымкент, Алматы, Астана) | Для презентации инвестору")
    r_m.font.name = "Arial"
    r_m.font.size = Pt(9.5)
    r_m.font.italic = True
    r_m.font.color.rgb = COLOR_SECONDARY

    # Divider
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(14)
    r_d = p_div.add_run("―" * 58)
    r_d.font.color.rgb = COLOR_GOLD

    # =========================================================================
    # РАЗДЕЛ 1: РЕЕСТР ПРОДУКТОВЫХ ГИПОТЕЗ (HYPOTHESIS VALIDATION CANVAS)
    # =========================================================================
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Реестр и валидация продуктовых гипотез (Customer Development)")
    r_h1.font.name = "Arial"
    r_h1.font.size = Pt(14)
    r_h1.font.bold = True
    r_h1.font.color.rgb = COLOR_PRIMARY

    p_intro = doc.add_paragraph()
    p_intro.paragraph_format.line_spacing = 1.15
    p_intro.paragraph_format.space_after = Pt(8)
    r_intro = p_intro.add_run(
        "В ходе исследования с 10 рестораторами (B2B) и 10 гостями (B2C) в г. Шымкент были проверены 6 основополагающих "
        "бизнес- и продуктовых гипотез. Валидация проводилась строго по фреймворку Lean Startup: выявление прошлых прецедентов, "
        "оцифровка реальных финансовых потерь и проверка поведенческих триггеров."
    )
    r_intro.font.name = "Arial"
    r_intro.font.size = Pt(10)
    r_intro.font.color.rgb = COLOR_PRIMARY

    # Hypotheses details
    hypotheses = [
        {
            "code": "H1",
            "name": "Гипотеза проблемы No-Show (неявки гостей без предупреждения)",
            "formulation": "Мы верили, что заведения теряют значительную долю выручки (от 15-20%) в пятницу и субботу из-за того, что столы держатся 'вслепую' для непришедших гостей.",
            "status": "ПОДТВЕРЖДЕНА (8 из 10 рестораторов — 80%)",
            "status_color": "10B981", # Green
            "evidence": "8 из 10 заведений теряют от 200 000 до 450 000 ₸ за уикенд из-за веерного бронирования и неприхода гостей. Столы держат по 45 минут вслепую.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (2 из 10): 1 закрытый элитный VIP-клуб (работает строго по 100% Kaspi предоплате депозита 50 000 ₸, поэтому No-Show 0%) и 1 заведение формата fast-casual с живой очередью, где столы в принципе не бронируют.",
            "b2c_insight": "КЛЮЧЕВОЙ НЕОЖИДАННЫЙ ИНСАЙТ: Гости не предупреждают об отмене не из злого умысла, а из-за психологического дискомфорта — 7 из 10 гостей признались, что им стыдно звонить и оправдываться перед хостес. Кнопка 'Отменить бронь в 1 клик' в Telegram снимает этот барьер и возвращает стол в продажу мгновенно.",
            "solution_feature": "Автоматические пуш-напоминания в Telegram за 2 ч и за 30 мин со статусом подтверждения и кнопкой мгновенного отказа."
        },
        {
            "code": "H2",
            "name": "Гипотеза неэффективности WhatsApp как основного канала бронирования",
            "formulation": "Мы верили, что WhatsApp в часы пик становится 'бутылочным горлышком', из-за которого заведение физически теряет до 25-30% входящего потока клиентов.",
            "status": "ПОДТВЕРЖДЕНА (7 из 10 рестораторов — 70%)",
            "status_color": "10B981",
            "evidence": "В часы пик поступает 40+ голосовых сообщений. Хостес на входе не успевает их слушать. Среднее время ответа — 40-90 минут, клиенты уходят к конкурентам.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (3 из 10): 2 небольшие авторские кофейни на 6-8 столов (мало броней, хостес успевает сама) и 1 сеть ресторанов, нанявшая отдельный колл-центр из 3 операторов (но тратит на это 380 000 ₸/мес на зарплаты!).",
            "b2c_insight": "Молодая и семейная аудитория не хочет переписок и ожидания. Им требуется подтвержденный статус столика прямо сейчас.",
            "solution_feature": "Telegram Mini App self-service: прямая ссылка из Instagram и 2GIS позволяет гостю за 30 секунд зарезервировать свободный стол без участия хостес."
        },
        {
            "code": "H3",
            "name": "Гипотеза барьера скачивания отдельных нативных приложений (AppStore/PlayMarket)",
            "formulation": "Мы верили, что гости не будут устанавливать тяжелое отдельное мобильное приложение ради периодического бронирования столика в ресторане.",
            "status": "ПОДТВЕРЖДЕНА (8 из 10 гостей — 80%)",
            "status_color": "10B981",
            "evidence": "Гости отказываются засорять память телефона и ждать СМС-коды ради брони столика.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (2 из 10 гостей): 2 студента заявили, что согласны скачать приложение, ТОЛЬКО если ресторан начислит приветственный бонус 3000-5000 ₸ на счет. Без материального бонуса — приложение сразу удаляется.",
            "b2c_insight": "Telegram уже установлен у каждого жителя Казахстана. Формат Mini App открывается в 1 клик без установки, СМС-кодов и паролей.",
            "solution_feature": "Платформа полностью построена на базе Telegram Mini App WebApp: нулевой порог входа, моментальный старт, конверсия в 3.8 раза выше классических приложений."
        },
        {
            "code": "H4",
            "name": "Гипотеза учета регионального менталитета ('Звонок Кайреке' и зонирование зала)",
            "formulation": "Мы верили, что жесткая стандартизированная система провалится в Казахстане, если не учтет традицию личных звонков руководству и желание гостей выбирать конкретные зоны (топчаны, VIP, панорама).",
            "status": "ПОДТВЕРЖДЕНА (8 из 10 заведений — 80%)",
            "status_color": "10B981",
            "evidence": "90% броней в статусных заведениях поступает звонком руководству 'на бегу'. Конфликты из-за плохих столов у туалета вместо террасы.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (2 из 10): 2 молодежных заведения (хипстерский бар и кофейня третьей волны) заявили: 'У нас европейский концепт: нет топчанов, нет VIP-кабин, агашкам преференций не делаем, все равны'.",
            "b2c_insight": "Для 80% заведений выбор зоны (топчан, кабина, терраса) и быстрая бронь 'от Баке' — критическое конкурентное преимущество.",
            "solution_feature": "Модуль посадки 'По звонку / Walk-In' на карте зала за 3 секунды + прозрачный выбор зоны столика в гостевой витрине."
        },
        {
            "code": "H5",
            "name": "Гипотеза готовности рестораторов платить за софт (Willingness to Pay)",
            "formulation": "Мы верили, что заведения готовы платить фиксированную подписку 35 000 – 49 000 ₸ в месяц при условии наглядного возврата инвестиций (ROI).",
            "status": "ПОДТВЕРЖДЕНА (7 из 10 рестораторов — 70%)",
            "status_color": "10B981",
            "evidence": "Рестораторы устали от скрытых комиссий агрегаторов (10-15%). 1 спасенный банкет на 8-10 человек окупает месячную подписку целиком.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (3 из 10): 1 заведение закрывается из-за кассового разрыва, а 2 маленьких кафе боятся фиксированных платежей в низкий сезон и просят pay-as-you-go (50-100 ₸ за гостя).",
            "b2c_insight": "Фиксированная подписка без скрытых процентов за гостя вызывает максимальное доверие владельцев бизнеса.",
            "solution_feature": "Прозрачные тарифные планы (35 000 ₸ 'Старт', 49 000 ₸ 'PRO Хит', 65 000 ₸ 'Сеть') с фиксированной ставкой и неограниченным числом гостей."
        },
        {
            "code": "H6",
            "name": "Гипотеза контроля дисциплины персонала и Z-отчетности смен",
            "formulation": "Мы верили, что владельцам и управляющим критически не хватает прозрачности работы хостес: сколько заявок принято, сколько потеряно, почему отменены брони.",
            "status": "ПОДТВЕРЖДЕНА (8 из 10 управляющих — 80%)",
            "status_color": "10B981",
            "evidence": "Текучка хостес каждые 2 месяца, блокноты теряются и заливаются кофе, смена уходит без передачи дел.",
            "disagreement": "КТО НЕ СОГЛАСИЛСЯ И ПОЧЕМУ (2 из 10): 1 семейное кафе (хостес — родная сестра владельца, доверие на слово) и 1 заведение, где управляющий сам постоянно встречает гостей у стойки.",
            "b2c_insight": "Хостес должна нести персональную ответственность за дежурство, а управляющий должен видеть объективные цифры.",
            "solution_feature": "Интерактивный статус-бар смены с живым таймером, кнопка закрытия смены и автоматическое формирование Z-отчета с фиксацией ключевых KPI."
        }
    ]

    for item in hypotheses:
        p_h = doc.add_paragraph()
        p_h.paragraph_format.space_before = Pt(8)
        p_h.paragraph_format.space_after = Pt(2)
        r_hc = p_h.add_run(f"[{item['code']}] {item['name']}")
        r_hc.font.name = "Arial"
        r_hc.font.size = Pt(11)
        r_hc.font.bold = True
        r_hc.font.color.rgb = COLOR_PRIMARY

        p_status = doc.add_paragraph()
        p_status.paragraph_format.space_after = Pt(4)
        r_st_label = p_status.add_run("Статус валидации: ")
        r_st_label.font.name = "Arial"
        r_st_label.font.size = Pt(9.5)
        r_st_label.font.bold = True
        r_st_val = p_status.add_run(item["status"])
        r_st_val.font.name = "Arial"
        r_st_val.font.size = Pt(9.5)
        r_st_val.font.bold = True
        r_st_val.font.color.rgb = COLOR_EMERALD

        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.line_spacing = 1.15
        p_desc.paragraph_format.space_after = Pt(4)
        r_d = p_desc.add_run(
            f"• Исходная формулировка гипотезы: {item['formulation']}\n"
            f"• Фактические подтверждения в CustDev: {item['evidence']}\n"
            f"• Возражения несогласных и их причины: {item['disagreement']}\n"
            f"• Реализованное решение в продукте: {item['solution_feature']}"
        )
        r_d.font.name = "Arial"
        r_d.font.size = Pt(9.5)
        r_d.font.color.rgb = COLOR_PRIMARY

        add_callout(doc, item["b2c_insight"], speaker="Аналитический вывод CustDev", tag="КЛЮЧЕВОЙ ИНСАЙТ")

    # Сводная таблица валидации гипотез
    h1_sub = doc.add_heading(level=2)
    r_h1_sub = h1_sub.add_run("Сводная матрица валидации продуктовых гипотез")
    r_h1_sub.font.name = "Arial"
    r_h1_sub.font.size = Pt(12)
    r_h1_sub.font.bold = True
    r_h1_sub.font.color.rgb = COLOR_PRIMARY

    table_hyp = doc.add_table(rows=1, cols=5)
    table_hyp.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_hyp.autofit = False

    t_headers = ["Код / Гипотеза", "Результат", "Кто подтвердил & Инсайт", "Кто НЕ согласился и почему?", "Решение в RestoKZ PRO"]
    t_widths = [Inches(1.1), Inches(0.9), Inches(1.8), Inches(1.6), Inches(1.3)]

    hdr_cells = table_hyp.rows[0].cells
    for i, title in enumerate(t_headers):
        hdr_cells[i].width = t_widths[i]
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(hdr_cells[i], "0F172A")
        set_cell_margins(hdr_cells[i], 100, 100, 100, 100)

    matrix_hyp_rows = [
        ("H1: Боль No-Show", "8 из 10 (80%)", "Убытки до 450к₸/уикенд. Инсайт: стыдно звонить отменять", "1 элитный VIP-клуб (Kaspi депозит 100%) + 1 фастфуд", "Пуш за 2ч + отмена в 1 клик"),
        ("H2: Затор WhatsApp", "7 из 10 (70%)", "Задержка ответа 40-90 мин, слив 15-20 столов за вечер", "2 мелкие кофейни (мало броней) + 1 сеть с колл-центром", "Mini App self-service за 30 сек"),
        ("H3: Барьер AppStore", "8 из 10 (80%)", "Гости отказываются ставить приложения на 80Мб с СМС", "2 студента готовы качать только ради бонуса 5000 ₸", "Telegram Mini App без установок"),
        ("H4: Менталитет зала", "8 из 10 (80%)", "Важность зон (топчан, кабина) и звонков руководству", "2 молодежные кофейни («европейский формат без агашек»)", "Зонирование + бронь «По звонку»"),
        ("H5: WTP подписка", "7 из 10 (70%)", "Согласны на 49к₸: окупается за 1 банкетный стол", "1 заведение в кассовом разрыве + 2 боятся несезона", "Фиксированная ставка (0% комиссий)"),
        ("H6: Контроль хостес", "8 из 10 (80%)", "Текучка хостес, потеря записей и номеров гостей", "1 семейное кафе (сестра владельца) + 1 владелец у двери", "Живой таймер смены и Z-отчеты")
    ]

    for row_idx, (c1, c2, c3, c4, c5) in enumerate(matrix_hyp_rows):
        row = table_hyp.add_row()
        bg_col = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for i, val in enumerate([c1, c2, c3, c4, c5]):
            cell = row.cells[i]
            cell.width = t_widths[i]
            set_cell_background(cell, bg_col)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            r.font.color.rgb = COLOR_PRIMARY
            if i == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # =========================================================================
    # РАЗДЕЛ 2: ПОЛНАЯ КОНКУРЕНТНАЯ МАТРИЦА (COMPETITIVE MATRIX)
    # =========================================================================
    h2 = doc.add_heading(level=1)
    r_h2 = h2.add_run("2. Комплексная Конкурентная Матрица (Competitive Matrix)")
    r_h2.font.name = "Arial"
    r_h2.font.size = Pt(14)
    r_h2.font.bold = True
    r_h2.font.color.rgb = COLOR_PRIMARY

    p_comp_intro = doc.add_paragraph()
    p_comp_intro.paragraph_format.line_spacing = 1.15
    p_comp_intro.paragraph_format.space_after = Pt(8)
    r_ci = p_comp_intro.add_run(
        "На рынке Казахстана заведения используют четыре основных альтернативных способа управления бронированием. "
        "Ниже представлено прямое сравнение RestoKZ PRO с существующими решениями по 10 критическим критериям бизнеса:"
    )
    r_ci.font.name = "Arial"
    r_ci.font.size = Pt(10)
    r_ci.font.color.rgb = COLOR_PRIMARY

    # Full table comparing 5 alternatives
    table_comp = doc.add_table(rows=1, cols=6)
    table_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_comp.autofit = False

    comp_headers = [
        "Критерий оценки",
        "Тетрадь +\nWhatsApp",
        "2GIS\nБронирование",
        "Каталоги\n(Restolife)",
        "Тяжелые POS\n(iiko/R-Keeper)",
        "👑 RestoKZ\nPRO Platform"
    ]
    comp_widths = [Inches(1.5), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0)]

    hdr_c_cells = table_comp.rows[0].cells
    for i, title in enumerate(comp_headers):
        hdr_c_cells[i].width = comp_widths[i]
        p = hdr_c_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        if i == 5:
            run.font.color.rgb = RGBColor(197, 168, 128)
            set_cell_background(hdr_c_cells[i], "1E293B")
        else:
            run.font.color.rgb = RGBColor(255, 255, 255)
            set_cell_background(hdr_c_cells[i], "0F172A")
        set_cell_margins(hdr_c_cells[i], 120, 120, 100, 100)

    comp_rows_data = [
        ("Скорость брони для гостя", "15–40 мин\n(ожидание ответа)", "3–5 мин\n(стороннее окно)", "5–10 мин\n(заявка-перезвон)", "Ручная посадка\nна месте", "⚡ 30 секунд\n(внутри Telegram)"),
        ("Барьер входа для гостя", "Звонок / аудио\nв мессенджере", "Установка 2GIS\nили веб-карта", "Переход на сайт\nрегистрация", "Только при личном\nконтакте", "⚡ Нулевой (Mini App\nбез установок и смс)"),
        ("Защита от No-Show (неявки)", "❌ 0% (гости\nпросто не приходят)", "⚠️ Низкая\n(пассивное СМС)", "❌ 0%\n(нет авто-контроля)", "⚠️ Только статус\nна кассовом сервере", "🛡 Высокая (пуш за 2ч\n+ отмена в 1 клик)"),
        ("Стоимость для заведения", "0 ₸ прямых,\nно убытки до 450к₸", "Платные пакеты\nот 80 000 ₸/мес", "Комиссия 10-15%\nили от 500 ₸/гость", "Лицензия от 40 000₸\n+ терминалы POS", "✅ Фиксированная\nподписка 35–49 тыс ₸"),
        ("Удобство со смартфона хостес", "❌ Хаос чатов,\nне видно общей картины", "⚠️ Неудобно,\nдесктопный упор", "❌ Нет мобильного\nтерминала для зала", "❌ Громоздко,\nтребует стационарный ПК", "📱 Идеально (мобильный\nвеб-терминал с PWA)"),
        ("Интерактивная карта зала", "❌ Каракули\nв блокноте", "❌ Только список\nзаявок текстом", "❌ Нет карты\nрассадки", "✅ Есть, но только\nна тяжелом ПК кассы", "🗺 Живая шахматка\nс цветовой индикацией"),
        ("Учет южного менталитета", "Частично (но\nзабывают брони)", "❌ Бездушная форма,\nнет топчанов и VIP", "❌ Стандартные\nшаблоны под РФ", "❌ Сложная логика\nиндивидуальных чеков", "👑 100% ('По звонку',\nтопчаны, VIP, RU/KZ)"),
        ("Контроль смены и Z-отчет", "❌ Нет,\nжурналы теряются", "❌ Нет учета\nработы сотрудников", "❌ Нет контроля\nсмены персонала", "✅ Сложные отчеты\nпо кассе и чекам", "⏱ Пульсирующий таймер,\nзакрытие и Z-отчет"),
        ("Владение базой гостей", "У хостес на личном\nтелефоне (теряется)", "Принадлежит\n2GIS", "Принадлежит\nагрегатору", "Локально на сервере\nресторана", "🔒 Принадлежит заведению\nв защищенном облаке"),
        ("Скорость внедрения точки", "Сразу (но с хаосом\nи убытками)", "3–7 дней\n(модерация 2GIS)", "5–10 дней\n(договоры, контент)", "2–4 недели\n(настройка, железо)", "⚡ 1 день (конструктор\nстолов за 5 минут)")
    ]

    for row_idx, rdata in enumerate(comp_rows_data):
        row = table_comp.add_row()
        is_even = row_idx % 2 == 1
        for i, val in enumerate(rdata):
            cell = row.cells[i]
            cell.width = comp_widths[i]
            if i == 5:
                set_cell_background(cell, "F3EFEA" if is_even else "FAF7F2") # Warm Gold Tint
            else:
                set_cell_background(cell, "F8FAFC" if is_even else "FFFFFF")
            set_cell_margins(cell, 80, 80, 80, 80)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(7.5)
            r.font.color.rgb = COLOR_PRIMARY
            if i == 0 or i == 5:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(16)

    # =========================================================================
    # РАЗДЕЛ 3: СТРАТЕГИЧЕСКОЕ ПОЗИЦИОНИРОВАНИЕ (BLUE OCEAN POSITIONING)
    # =========================================================================
    h3 = doc.add_heading(level=1)
    r_h3 = h3.add_run("3. Стратегическое позиционирование: 'Голубой океан' RestoKZ PRO")
    r_h3.font.name = "Arial"
    r_h3.font.size = Pt(14)
    r_h3.font.bold = True
    r_h3.font.color.rgb = COLOR_PRIMARY

    p_pos = doc.add_paragraph()
    p_pos.paragraph_format.line_spacing = 1.15
    p_pos.paragraph_format.space_after = Pt(8)
    r_pos = p_pos.add_run(
        "Ключевая ошибка многих стартапов — попытка 'воевать' с монополистами (2GIS, Kaspi, iiko). "
        "RestoKZ PRO реализует стратегию Голубого Океана (Blue Ocean Strategy), не конкурируя напрямую, а дополняя "
        "существующую экосистему и снимая самое болезненное звено:"
    )
    r_pos.font.name = "Arial"
    r_pos.font.size = Pt(10)
    r_pos.font.color.rgb = COLOR_PRIMARY

    pos_points = [
        ("Связка с 2GIS и Instagram (Симбиоз, а не война)", 
         "Рестораны тратят до 1.5 млн ₸ в месяц на таргет Instagram и продвижение в 2GIS. Сегодня этот трафик сливается в WhatsApp с конверсией всего 4%. RestoKZ ставится как прямая ссылка 'Забронировать столик' в шапку профиля Instagram и карточку 2GIS. Конверсия рекламы в реальную посадку вырастает в 3-4 раза!"),

        ("Связка с кассовыми ERP (iiko, R-Keeper, Poster)", 
         "iiko великолепно считает себестоимость стейка и складские остатки лука, но абсолютно непригоден для хостес на входе со смартфона. RestoKZ берет на себя внешнюю воронку гостей и оперативную шахматку зала, не требуя замены кассовой системы."),

        ("Локальное конкурентное преимущество (Local Moat)", 
         "Ни один зарубежный сервис не понимает, что такое 'бронь топчана на құдалық на 15 человек', 'звонок от Баке с просьбой занять лучший стол' и интерфейс на чистом казахском языке. RestoKZ создан из реалий казахстанского ресторанного бизнеса.")
    ]

    for title, desc in pos_points:
        p_pt = doc.add_paragraph()
        p_pt.paragraph_format.space_before = Pt(6)
        p_pt.paragraph_format.space_after = Pt(2)
        rt = p_pt.add_run(f"• {title}")
        rt.font.name = "Arial"
        rt.font.size = Pt(10.5)
        rt.font.bold = True
        rt.font.color.rgb = COLOR_DARK_GOLD

        pd = doc.add_paragraph()
        pd.paragraph_format.space_after = Pt(6)
        pd.paragraph_format.line_spacing = 1.15
        rd = pd.add_run(desc)
        rd.font.name = "Arial"
        rd.font.size = Pt(9.5)
        rd.font.color.rgb = COLOR_PRIMARY

    # =========================================================================
    # РАЗДЕЛ 4: 5 БЕСПРОИГРЫШНЫХ ОТВЕТОВ ИНВЕСТОРУ ПО МАТРИЦЕ И ГИПОТЕЗАМ
    # =========================================================================
    h4 = doc.add_heading(level=1)
    r_h4 = h4.add_run("4. Готовые ответы на каверзные вопросы инвесторов")
    r_h4.font.name = "Arial"
    r_h4.font.size = Pt(14)
    r_h4.font.bold = True
    r_h4.font.color.rgb = COLOR_PRIMARY

    qa_list = [
        ("Вопрос: «2GIS введет свое бронирование и убьет вас. Что вы будете делать?»",
         "Ответ фаундера: «2GIS — это справочник-витрина для всего города, а не специализированный софт для зала ресторана. 2GIS не будет делать интерактивную рассадку столов хостес, учет смен, звуковой гонг на кухню и кнопку быстрой брони 'По звонку от Баке'. 2GIS — наш главный источник трафика: ресторан ставит ссылку на наш Mini App в свой профиль 2GIS, получая в 3 раза больше гостей без комиссий»."),

        ("Вопрос: «Почему рестораны не купят модуль iiko.Hostess?»",
         "Ответ фаундера: «iiko.Hostess стоит дорого, требует покупки специализированных планшетов или ПК на стойку, сложен в обучении и не имеет удобного B2C Mini App для гостей в Telegram. При текучке хостес каждые 2 месяца персонал в 9 из 10 заведений Шымкента саботирует тяжелый софт и возвращается к блокноту. RestoKZ PRO запускается на личном телефоне хостес за 2 минуты без обучения»."),

        ("Вопрос: «Какая главная подтвержденная цифра вашего CustDev доказывает Unit-экономику?»",
         "Ответ фаундера: «Цифра 1:1. Всего ОДИН спасенный банкетный стол на 8 человек в месяц с чеком 80 000 ₸ окупает всю месячную подписку на RestoKZ PRO (49 000 ₸). Все остальные спасенные от No-Show столы приносят заведению от 200 000 до 500 000 ₸ чистой дополнительной прибыли. Для владельца это очевидная математика 'вложил 49 тыс — получил 300 тыс'»."),

        ("Вопрос: «Какова следующая гипотеза, которую вы будете проверять после привлечения раунда?»",
         "Ответ фаундера: «Гипотеза Kaspi QR Депозитов. В CustDev 6 из 10 гостей заявили, что готовы внести аванс 5 000 – 10 000 ₸ через Kaspi при бронировании VIP-кабин или топчанов, если ресторан гарантирует их сохранение. Это снизит No-Show практически до 0% и создаст для нас дополнительный финтех-поток монетизации»."),

        ("Вопрос: «Почему вы уверены, что модель масштабируется за пределы Шымкента?»",
         "Ответ фаундера: «Проблема хаоса в WhatsApp и неявок (No-Show) идентична в Алматы, Астане, Ташкенте и Баку. Более того, в Алматы и Астане плотность заведений и средний чек выше в 1.8 раза, а готовность к цифровым сервисам еще выше. Отработав устойчивость на самом консервативном рынке Шымкента, экспансия в города-миллионники произойдет значительно быстрее».")
    ]

    for q, a in qa_list:
        pq = doc.add_paragraph()
        pq.paragraph_format.space_before = Pt(6)
        pq.paragraph_format.space_after = Pt(2)
        rq = pq.add_run(q)
        rq.font.name = "Arial"
        rq.font.size = Pt(10)
        rq.font.bold = True
        rq.font.color.rgb = COLOR_PRIMARY

        add_callout(doc, a.replace("Ответ фаундера: «", "").replace("».", ""), speaker="Аргумент фаундера на питче", tag="ПИТЧ-ОТВЕТ")

    doc.save(output_path)
    print(f"File successfully created: {output_path}")

if __name__ == "__main__":
    out_file = os.path.abspath("Hypotheses_and_Competitive_Matrix_RestoKZ.docx")
    build_document(out_file)
