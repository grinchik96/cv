#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFilter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
HTML_SOURCE = ROOT / "index.html"
PHOTO_SOURCE = ROOT / "photo.jpg"
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUTPUT_PDF = OUTPUT_DIR / "anton-grinchenko-resume.pdf"
PHOTO_RENDERED = TMP_DIR / "photo-circle.png"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 15 * mm
BOTTOM_MARGIN = 16 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
CARD_HORIZONTAL_PADDING = 13
CARD_INNER_WIDTH = CONTENT_WIDTH - CARD_HORIZONTAL_PADDING * 2

COLORS = {
    "canopy": colors.HexColor("#2D5016"),
    "moss": colors.HexColor("#4A7C2E"),
    "fern": colors.HexColor("#6B9B4E"),
    "bark": colors.HexColor("#3E2C1C"),
    "parchment": colors.HexColor("#F5F0E8"),
    "linen": colors.HexColor("#FDFBF7"),
    "sage": colors.HexColor("#A8C896"),
    "sunlight": colors.HexColor("#E8D44D"),
    "card_border": colors.HexColor("#C9D9B9"),
    "intro_fill": colors.HexColor("#EDF4E5"),
}

FONT_REGULAR = "Resume-Regular"
FONT_BOLD = "Resume-Bold"
FONT_ITALIC = "Resume-Italic"
FONT_BOLD_ITALIC = "Resume-BoldItalic"


def register_fonts() -> None:
    font_paths = {
        FONT_REGULAR: Path("/System/Library/Fonts/HelveticaNeue.ttc"),
        FONT_BOLD: Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        FONT_ITALIC: Path("/System/Library/Fonts/Supplemental/Arial Italic.ttf"),
        FONT_BOLD_ITALIC: Path("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"),
    }
    missing = [str(path) for path in font_paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required font files: {', '.join(missing)}")
    for name, path in font_paths.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))


def ensure_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def make_circular_photo(source: Path, destination: Path, size: int = 900) -> Path:
    image = Image.open(source).convert("RGBA")
    inner_width = int(size * 0.78)
    inner_height = round(inner_width * image.height / image.width)
    image = image.resize((inner_width, inner_height), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size + 80, size + 80), (0, 0, 0, 0))

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((18, 24, size + 62, size + 68), fill=(62, 44, 28, 52))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(shadow)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    circle = Image.new("RGBA", (size, size), (253, 251, 247, 255))
    image_x = (size - inner_width) // 2
    image_y = int(size * 0.04)
    circle.alpha_composite(image, (image_x, image_y))
    circle.putalpha(mask)

    border = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.ellipse((4, 4, size - 5, size - 5), outline=(168, 200, 150, 255), width=8)

    canvas.alpha_composite(circle, (40, 40))
    canvas.alpha_composite(border, (40, 40))
    canvas.save(destination)
    return destination


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "ResumeName",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=24.5,
            leading=27,
            textColor=COLORS["canopy"],
            spaceAfter=2,
        ),
        "role": ParagraphStyle(
            "ResumeRole",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=11.4,
            leading=13.5,
            textColor=COLORS["moss"],
            spaceAfter=4,
        ),
        "contact": ParagraphStyle(
            "ResumeContact",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.9,
            leading=12.2,
            textColor=COLORS["bark"],
        ),
        "location": ParagraphStyle(
            "ResumeLocation",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.4,
            leading=11,
            textColor=COLORS["bark"],
        ),
        "summary": ParagraphStyle(
            "ResumeSummary",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9.9,
            leading=13.4,
            textColor=COLORS["bark"],
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "ResumeBullet",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9.4,
            leading=13.0,
            textColor=COLORS["bark"],
            leftIndent=0,
            firstLineIndent=0,
            spaceAfter=3,
        ),
        "section": ParagraphStyle(
            "ResumeSection",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=15.5,
            leading=18,
            textColor=COLORS["canopy"],
            spaceAfter=0,
        ),
        "card_title": ParagraphStyle(
            "ResumeCardTitle",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=12.2,
            leading=14.2,
            textColor=COLORS["moss"],
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "ResumeMeta",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=10.4,
            textColor=COLORS["bark"],
        ),
        "intro": ParagraphStyle(
            "ResumeIntro",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9.3,
            leading=13.0,
            textColor=COLORS["bark"],
            spaceAfter=3,
        ),
        "track": ParagraphStyle(
            "ResumeTrack",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9.2,
            leading=11.2,
            textColor=COLORS["moss"],
            spaceAfter=4,
            spaceBefore=1,
        ),
        "school": ParagraphStyle(
            "ResumeSchool",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9.8,
            leading=12.0,
            textColor=COLORS["canopy"],
            spaceAfter=2,
        ),
        "course": ParagraphStyle(
            "ResumeCourse",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=9.2,
            leading=11.4,
            textColor=COLORS["canopy"],
            spaceAfter=1,
        ),
        "course_detail": ParagraphStyle(
            "ResumeCourseDetail",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=8.8,
            leading=11.4,
            textColor=COLORS["bark"],
        ),
        "footer": ParagraphStyle(
            "ResumeFooter",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=7.6,
            leading=9,
            textColor=COLORS["sage"],
            alignment=TA_CENTER,
        ),
    }


def esc(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullet(text: str, styles_map: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"• {text}", styles_map["bullet"])


class BadgeCloud(Flowable):
    def __init__(
        self,
        labels: list[str],
        font_name: str = FONT_BOLD,
        font_size: float = 8.1,
        padding_x: float = 4.6,
        padding_y: float = 2.4,
        gap_x: float = 4.2,
        gap_y: float = 5.2,
    ) -> None:
        super().__init__()
        self.labels = labels
        self.font_name = font_name
        self.font_size = font_size
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.gap_x = gap_x
        self.gap_y = gap_y
        self.lines: list[list[tuple[str, float]]] = []
        self.line_height = self.font_size + self.padding_y * 2 + 1.4
        self.total_height = 0.0

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.lines = []
        current: list[tuple[str, float]] = []
        current_width = 0.0

        for label in self.labels:
            badge_width = pdfmetrics.stringWidth(label, self.font_name, self.font_size) + self.padding_x * 2
            if current and current_width + self.gap_x + badge_width > availWidth:
                self.lines.append(current)
                current = [(label, badge_width)]
                current_width = badge_width
            else:
                if current:
                    current_width += self.gap_x + badge_width
                else:
                    current_width = badge_width
                current.append((label, badge_width))

        if current:
            self.lines.append(current)

        if not self.lines:
            self.lines = [[]]

        self.total_height = len(self.lines) * self.line_height + max(0, len(self.lines) - 1) * self.gap_y
        return availWidth, self.total_height

    def draw(self) -> None:
        canv = self.canv
        y = self.total_height - self.line_height
        for line in self.lines:
            x = 0
            for label, badge_width in line:
                canv.setFillColor(COLORS["intro_fill"])
                canv.setStrokeColor(colors.Color(74 / 255.0, 124 / 255.0, 46 / 255.0, alpha=0.25))
                canv.roundRect(x, y, badge_width, self.line_height, 5, fill=1, stroke=1)
                canv.setFillColor(COLORS["moss"])
                canv.setFont(self.font_name, self.font_size)
                text_y = y + (self.line_height - self.font_size) / 2.0 - 0.4
                canv.drawString(x + self.padding_x, text_y, label)
                x += badge_width + self.gap_x
            y -= self.line_height + self.gap_y


def divider(width: float = CONTENT_WIDTH) -> HRFlowable:
    return HRFlowable(
        width=width,
        thickness=1,
        color=colors.Color(168 / 255.0, 200 / 255.0, 150 / 255.0, alpha=0.42),
        spaceBefore=6,
        spaceAfter=12,
    )


def section_header(title: str, styles_map: dict[str, ParagraphStyle]) -> list[Flowable]:
    return [
        para(esc(title), styles_map["section"]),
        Spacer(1, 4),
        HRFlowable(
            width=CONTENT_WIDTH,
            thickness=2,
            color=colors.Color(74 / 255.0, 124 / 255.0, 46 / 255.0, alpha=0.28),
            spaceBefore=0,
            spaceAfter=11,
        ),
    ]


def intro_box(content: list[Flowable]) -> Table:
    table = Table([[content]], colWidths=[CARD_INNER_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["intro_fill"]),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.Color(168 / 255.0, 200 / 255.0, 150 / 255.0, alpha=0.6)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def card_table(content: list[Flowable]) -> Table:
    table = Table([[content]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["linen"]),
                ("BOX", (0, 0), (-1, -1), 0.9, COLORS["card_border"]),
                ("LEFTPADDING", (0, 0), (-1, -1), CARD_HORIZONTAL_PADDING),
                ("RIGHTPADDING", (0, 0), (-1, -1), CARD_HORIZONTAL_PADDING),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def build_header(styles_map: dict[str, ParagraphStyle], photo_path: Path) -> Table:
    left = [
        para("Антон Гринченко", styles_map["name"]),
        para("Product Lead / AI Product &amp; Transformation", styles_map["role"]),
        para(
            'Моб.: +7 (921) 260-46-21 · E-mail: <link href="mailto:grinchik_96@icloud.com">grinchik_96@icloud.com</link> · TG: <link href="https://t.me/agrinchenko">@agrinchenko</link>',
            styles_map["contact"],
        ),
        para("Калининград, remote.", styles_map["location"]),
    ]
    photo = RLImage(str(photo_path), width=38 * mm, height=38 * mm)
    table = Table([[left, photo]], colWidths=[CONTENT_WIDTH - 38 * mm - 10 * mm, 38 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def build_experience_card(
    styles_map: dict[str, ParagraphStyle],
    company: str,
    company_url: str | None,
    title: str,
    date_badge: str,
    industry: str | None,
    intro_paragraphs: list[str],
    intro_bullets: list[str],
    tracks: list[tuple[str, list[str]]],
) -> KeepTogether:
    company_markup = esc(company)
    if company_url:
        company_markup = f'<link href="{company_url}">{company_markup}</link>'
    title_markup = f"{company_markup} — {esc(title)}"

    content: list[Flowable] = [para(title_markup, styles_map["card_title"])]
    meta_bits = [f'<font color="#4A7C2E">{esc(date_badge)}</font>']
    if industry:
        meta_bits.append(esc(industry))
    content.append(para(" · ".join(meta_bits), styles_map["meta"]))
    content.append(Spacer(1, 4))

    intro_content: list[Flowable] = []
    for paragraph_text in intro_paragraphs:
        intro_content.append(para(paragraph_text, styles_map["intro"]))
    for bullet_text in intro_bullets:
        intro_content.append(bullet(bullet_text, styles_map))
    if intro_content:
        content.append(intro_box(intro_content))
        content.append(Spacer(1, 7))

    for track_title, bullets in tracks:
        content.append(para(esc(track_title), styles_map["track"]))
        for item in bullets:
            content.append(bullet(item, styles_map))
        content.append(Spacer(1, 2))

    return KeepTogether([card_table(content)])


def build_resume_story(styles_map: dict[str, ParagraphStyle], photo_path: Path) -> list[Flowable]:
    story: list[Flowable] = []

    story.append(build_header(styles_map, photo_path))
    story.append(Spacer(1, 10))
    story.append(divider())

    summary_items = [
        "7+ лет в продукте и коммерции (B2C, B2B, B2C2B).",
        "Запуск продуктов с нуля и развитие текущих.",
        "Стартапы и крупный бизнес.",
        "P&amp;L ownership, stakeholder alignment.",
        "Управление командами до 18 человек (разработка, маркетинг, продажи, саппорт).",
        "Полный цикл: discovery → go-to-market → growth.",
        "Самоходный, работаю руками: фин. моделирование, исследования, ai-прототипирование.",
        "Сильный ai-скиллсет: автоматизация рутины, создание mvp-прототипов, агентов.",
        "Опыт ai-автоматизации на уровне компании с доказанной экономией для бизнеса в десятках миллионах рублей.",
    ]
    story.append(para("Бизнес-ориентированный продуктовый лидер с коммерческим бэкграундом и ai-first подходом.", styles_map["summary"]))
    for item in summary_items:
        story.append(bullet(item, styles_map))

    story.append(Spacer(1, 6))
    story.append(divider())
    story.extend(section_header("Опыт", styles_map))

    story.append(
        build_experience_card(
            styles_map,
            "Нетология",
            "https://netology.ru",
            "Product Lead, Ai-transformation driver",
            "Май 2025 — наст.вр. · 9 мес",
            "EdTech, B2B, B2C2B",
            [
                "Руковожу развитием цифровой платформы для B2B-сегмента в полном продуктовом цикле.",
            ],
            [
                "HR-кабинет + LMS. SMB, Enterprise, SaaS.",
                "Команда разработки в кросс-функциональном управлении",
                "Координация с маркетингом, продажами, бизнесом, ИБ, архитектурой.",
                "Ответственность на уровне ROI от разработки.",
                "Развитие ai-культуры в компании, внедрение автоматизаций.",
            ],
            [
                (
                    "Product track:",
                    [
                        "Сделал результат разработки измеримым показателем с коммитом на финансовые метрики за счёт внедрения системного discovery (сбор гипотез → приоритезация → тестирование без разработки) с вовлечением стейкхолдеров. <b>Продуктовые инициативы обеспечили 50% выручки B2B бизнес-юнита в Q4 2025.</b>",
                        "Для SaaS продукта (SMB) нашёл точки роста retention, <b>увеличив показатель в продление годовой подписки на 15 п.п.</b> по первой когорте → <b>увеличение MAU сотрудников х2, CSI HR-менеджеров с 3,5 до 4,2.</b>",
                    ],
                ),
                (
                    "Ai track:",
                    [
                        "Совместно с академическим директором разработал и внедрил каскад ai-агентов в процесс производства образовательного контента → <b>в 5 раз увеличили объём генерируемых контентных единиц в месяц без увеличения штата и потери качества.</b>",
                        "Внедрил AI-агента для подготовки PRD (cursor, python, skills, mcp) в продуктовые команды → <b>время на описание задач и проектов -60%, уточнения и ошибки в реализации сведены к нулю.</b>",
                    ],
                ),
            ],
        )
    )

    story.append(
        build_experience_card(
            styles_map,
            "Maximum Education",
            "https://maximumtest.ru",
            "Product Owner / Руководитель бизнес-юнита",
            "Июнь 2023 — Декабрь 2024 · 1 год 7 мес",
            "EdTech, B2C",
            [
                "Maximum Education поглотил Умназию — образовался автономный бизнес-юнит, который я возглавил.",
            ],
            [
                "Отвечал за P&amp;L юнита (курсы для детей 6-14 лет), стратегию развития.",
                "Коммерческая команда в прямом подчинении (18 человек). В кросс-функциональном: project-менеджер IT-команды, методисты, аналитики.",
            ],
            [
                (
                    "Key results:",
                    [
                        "<b>Вырастил выручку направления YoY на 340%</b> при целевом FCF",
                        "<b>Увеличил новые продажи в 2,5x</b> → аналитика, точки роста, новые воронки маркетинга и продаж",
                        "<b>Поднял годовой LTV на 28%</b> → JTBD-сегментация, исследование аудитории, корректировка CJM",
                        "Запустил новый продукт → <b>+40% к выручке BU в первый квартал</b> (discovery, product vision, UE, go-to-market, delivery, найм команды)",
                    ],
                ),
            ],
        )
    )

    story.append(
        build_experience_card(
            styles_map,
            "Smart (институт Vill)",
            "https://vill-institute.com",
            "Growth Product Owner",
            "Ноябрь 2022 — Май 2023 · 7 мес",
            "EdTech, B2C",
            [],
            [
                "Пришёл под конкретную задачу — найти, запустить и масштабировать новый продукт в нише ДПО.",
                "Отвечал за discovery, go-to-market стратегию и коммерческие показатели: выручка, средний чек, маржинальность.",
            ],
            [
                (
                    "Results:",
                    [
                        "Запустил продукт с <b>выполнением плана продаж на 130%</b> во второй месяц",
                        "<b>Вырастил выручку x3</b>, вывел на рентабельность с отрицательных значений",
                        "<b>Конверсия C2 (заявка → покупка) x1,5</b> за счёт перестройки взаимодействия маркетинга и продаж",
                    ],
                ),
            ],
        )
    )

    story.append(
        build_experience_card(
            styles_map,
            "Умназия",
            "https://umnazia.ru",
            "Product Manager, Monetization & Retention",
            "Сентябрь 2020 — Октябрь 2022 · 2 года",
            "EdTech, B2C",
            [
                "Присоединился к EdTech-стартапу после привлечения инвестиций.",
            ],
            [
                "Вместе с компанией прошёл pivot и тесты рынков USA / Latam.",
                "Отвечал за воронки монетизации трафика и удержание пользователей: конверсия первой сессии, онбординг, retention, LTV.",
            ],
            [
                (
                    "Results:",
                    [
                        "<b>Конверсия первой сессии (C1) для платного трафика: 3% → 4,5%, CPL -30%</b> (cusdev, A/B-тесты, UX-интервью)",
                        "<b>Конверсия из регистрации в активацию +20 п.п.</b> → новая воронка онбординга",
                        "<b>Monthly retention +8 п.п.</b> → когортный анализ, RFM-сегментация, триггерные цепочки возврата",
                        "<b>LTV +25%</b> → ценовые эксперименты, апсейл-воронки, оптимизация CJM по сегментам",
                        "Построил модель юнит-экономики продукта: <b>целевые CAC/LTV по сегментам</b> → основа для решений по каналам и ценообразованию",
                    ],
                ),
            ],
        )
    )

    story.append(
        build_experience_card(
            styles_map,
            "LSF",
            None,
            "Продюсер онлайн-школ",
            "Май 2017 — Июль 2019 · 2 года 3 мес",
            None,
            [],
            [],
            [
                (
                    "Summary:",
                    [
                        "Запуск 17 рентабельных онлайн-школ с нуля, совокупный оборот 20 млн ₽/мес. Рост от стартапа из 3 человек до команды из 17.",
                    ],
                )
            ],
        )
    )

    story.append(Spacer(1, 2))
    story.append(divider())
    story.extend(section_header("Навыки", styles_map))

    story.append(para("Product / Business", styles_map["track"]))
    story.append(
        BadgeCloud(
            [
                "P&L",
                "Product Strategy",
                "Discovery",
                "Delivery",
                "Юнит-экономика",
                "Growth",
                "A/B-тесты",
                "Analytics",
                "Cross-functional Leadership",
            ]
        )
    )
    story.append(Spacer(1, 6))

    story.append(para("AI &amp; Tech", styles_map["track"]))
    story.append(
        BadgeCloud(
            [
                "Prompt Engineering",
                "Context Engineering",
                "Claude Code CLI",
                "Cursor",
                "Codex CLI",
                "MCP",
                "AI-агенты",
                "LLM-автоматизация процессов",
            ]
        )
    )
    story.append(Spacer(1, 6))

    story.append(para("Tools", styles_map["track"]))
    story.append(
        BadgeCloud(
            [
                "Amplitude",
                "FineBI / Power BI / DataLens / Superset",
                "Figma",
                "Notion",
                "Jira",
                "Miro",
            ]
        )
    )

    story.append(Spacer(1, 10))
    story.append(divider())
    story.extend(section_header("Образование", styles_map))
    story.append(para("Балтийский федеральный университет им. И. Канта, Калининград", styles_map["school"]))
    story.append(para("Институт экономики и менеджмента, Маркетинг. Бакалавр, 2014–2018", styles_map["intro"]))

    story.append(Spacer(1, 10))
    story.append(divider())
    story.extend(section_header("Курсы", styles_map))
    course_items = [
        ("AI-assisted development — Глеб Кудрявцев, 2026", "полный цикл: идея → продукт, через AI-инструменты"),
        ("Технические знания для продакта — ProductDo, 2025", "архитектура, API, метрики, риски"),
        ("Как делать продукт, который клиенты будут покупать — Ваня Замесин, 2022", "JTBD, интервью"),
    ]
    for name, detail in course_items:
        story.append(para(name, styles_map["course"]))
        story.append(para(detail, styles_map["course_detail"]))
        story.append(Spacer(1, 4))

    return story


def draw_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(COLORS["parchment"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)

    canvas.setFillColor(COLORS["canopy"])
    canvas.rect(0, PAGE_HEIGHT - 4, PAGE_WIDTH, 4, stroke=0, fill=1)

    canvas.setFillColor(COLORS["sage"])
    canvas.setFont(FONT_REGULAR, 7.6)
    canvas.drawCentredString(PAGE_WIDTH / 2.0, 9.5 * mm, "2026 · Антон Гринченко")
    canvas.restoreState()


def build_pdf() -> Path:
    ensure_directories()
    register_fonts()
    if not HTML_SOURCE.exists():
        raise FileNotFoundError(f"Missing source HTML: {HTML_SOURCE}")
    if not PHOTO_SOURCE.exists():
        raise FileNotFoundError(f"Missing source photo: {PHOTO_SOURCE}")

    photo_path = make_circular_photo(PHOTO_SOURCE, PHOTO_RENDERED)
    style_map = styles()
    story = build_resume_story(style_map, photo_path)

    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Антон Гринченко — Resume",
        author="Антон Гринченко",
        subject="Resume PDF",
    )
    frame = Frame(
        LEFT_MARGIN,
        BOTTOM_MARGIN,
        CONTENT_WIDTH,
        PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="resume",
    )
    doc.addPageTemplates([PageTemplate(id="resume", frames=[frame], onPage=draw_page)])
    doc.build(story)
    return OUTPUT_PDF


def main() -> None:
    pdf = build_pdf()
    print(pdf)


if __name__ == "__main__":
    main()
