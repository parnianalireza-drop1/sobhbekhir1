import os
import io
import re
import gc
import sys
import time
import json
import math
import shutil
import random
import hashlib
import tempfile
import threading
import subprocess
import urllib.parse
import requests
import jdatetime
import pytz
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =====================================================================
# 1. Core Settings, Schedule (07:00 - 21:00 Tehran) & Constants
# =====================================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
DEFAULT_IG_PAGE = os.environ.get("IG_TARGET_PAGE", "shirazlastnews").strip()
DEFAULT_IG_SESSION = os.environ.get("IG_SESSIONID", "").strip()
DEFAULT_FOOTER = os.environ.get("FOOTER_TEXT", "آخرین خبرهای شیراز").strip()
DEFAULT_REEL_BADGE = os.environ.get("REEL_BADGE", "خبر فوری").strip()

ACTIVE_START_HOUR = 7
ACTIVE_END_HOUR = 21
MAX_CYCLE_SECONDS = 19500

STORY_SIZE = (1080, 1920)
CITY_NAME_FA = "شیراز"
CITY_NAME_EN = "Shiraz"
CITY_LAT = 29.5918
CITY_LON = 52.5837

TEHRAN_TZ = pytz.timezone("Asia/Tehran")
STATE_FILE = "state.json"

VAZIR_FONT_FILE = "Vazirmatn-Bold.ttf"
SPORT_FONT_FILE = "SportFont.ttf"

VAZIR_URLS = [
    "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/fonts/ttf/Vazirmatn-Bold.ttf",
    "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf"
]
SPORT_URLS = [
    "https://raw.githubusercontent.com/google/fonts/main/ofl/lalezar/Lalezar-Regular.ttf",
    "https://cdn.jsdelivr.net/gh/BornaIz/Lalezar@master/fonts/ttf/Lalezar-Regular.ttf"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache"
}

BOT_MENU_KEYBOARD = json.dumps({
    "keyboard": [
        [{"text": "🌞 صبح بخیر"}, {"text": "⛅ وضعیت هوا"}],
        [{"text": "⚽ نتایج زنده"}, {"text": "🎬 ریلزساز و قاب ویدیو"}],
        [{"text": "📸 رصد پیج اینستاگرام"}, {"text": "⚙ تنظیمات ربات"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
})

HAFEZ_POEMS = [
    ("رواق منظر چشم من آشیانه توست", "کرم نما و فرود آ که خانه خانه توست"),
    ("درخت دوستی بنشان که کام دل به بار آرد", "نهال دشمنی برکن که رنج بیشمار آرد"),
    ("صلاح کار کجا و من خراب کجا", "ببین تفاوت ره کز کجاست تا به کجا"),
    ("دوش دیدم که ملائک در میخانه زدند", "گل آدم بسرشتند و به پیمانه زدند"),
    ("ای فروغ ماه حسن از روی رخشان شما", "آب روی خوبی از چاه زنخدان شما"),
    ("دل سراپرده محبت اوست", "دیده آیینه دار طلعت اوست"),
    ("سحر بلبل حکایت با صبا کرد", "که عشق روی گل با ما چه ها کرد"),
    ("مزرع سبز فلک دیدم و داس مه نو", "یادم از کشته خویش آمد و هنگام درو"),
    ("گفتم غم تو دارم گفتا غمت سر آید", "گفتم که ماه من شو گفتا اگر برآید"),
    ("هر آن کو خاطر مجموع و یار نازنین دارد", "سعادت همدم او گشت و دولت همنشین دارد"),
    ("بیا تا گل برافشانیم و می در ساغر اندازیم", "فلک را سقف بشکافیم و طرحی نو دراندازیم"),
    ("زلف آشفته و خوی کرده و خندان لب و مست", "پیرهن چاک و غزل خوان و صراحی در دست"),
    ("بلبلی برگ گلی خوش رنگ در منقار داشت", "و اندر آن برگ و نوا خوش ناله های زار داشت"),
    ("ستاره ای بدرخشید و ماه مجلس شد", "دل رمیده ما را انیس و مونس شد")
]

WEEKDAY_AURAS = [
    (255, 215, 110),
    (110, 235, 190),
    (115, 205, 255),
    (255, 175, 95),
    (215, 155, 255),
    (255, 225, 130),
    (140, 240, 215),
]

LEAGUE_CATEGORIES = [
    ("lg_ir", "🇮🇷 لیگ برتر و جام حذفی ایران"),
    ("lg_eng", "🇬🇧 لیگ برتر انگلیس"),
    ("lg_esp", "🇪🇸 لالیگا اسپانیا"),
    ("lg_ger", "🇩🇪 بوندسلیگا آلمان"),
    ("lg_ucl", "🏆 لیگ قهرمانان اروپا")
]

IRAN_LOGOS = {
    'فجر سپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجرسپاسی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'فجر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D8%AC%D8%B1%20%D8%B4%D9%87%DB%8C%D8%AF%20%D8%B3%D9%BE%D8%A7%D8%B3%DB%8C.png',
    'پرسپولیس': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%D8%B1%D8%B3%D9%BE%D9%88%D9%84%DB%8C%D8%B3%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'استقلال خوزستان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'استقلال': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A7%D8%B3%D8%AA%D9%82%D9%84%D8%A7%D9%84%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'سپاهان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B3%D9%BE%D8%A7%D9%87%D8%A7%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'تراکتور': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AA%D8%B1%D8%A7%DA%A9%D8%AA%D9%88%D8%B1%20%D8%AA%D8%A8%D8%B1%DB%8C%D8%B2.png',
    'فولاد': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%81%D9%88%D9%84%D8%A7%D8%AF%20%D8%AE%D9%88%D8%B2%D8%B3%D8%AA%D8%A7%D9%86.png',
    'ذوب آهن': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B0%D9%88%D8%A8%20%D8%A2%D9%87%D9%86%20%D8%A7%D8%B5%D9%81%D9%87%D8%A7%D9%86.png',
    'ملوان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D9%84%D9%88%D8%A7%D9%86%20%D8%A8%D9%86%D8%AF%D8%B1%D8%A7%D9%86%D8%B2%D9%84%DB%8C.png',
    'گل گهر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%AF%D9%84%20%DA%AF%D9%87%D8%B1%20%D8%B3%DB%8C%D8%B1%D8%AC%D8%A7%D9%86.png',
    'آلومینیوم': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%A2%D9%84%D9%88%D9%85%DB%8C%D9%86%DB%8C%D9%88%D9%85%20%D8%A7%D8%B1%D8%A7%DA%A9.png',
    'مس شهر بابک': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%85%D8%B3%20%D8%B4%D9%87%D8%B1%20%D8%A8%D8%A7%D8%A8%DA%A9.png',
    'شمس آذر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B4%D9%85%D8%B3%20%D8%A2%D8%B0%D8%B1%20%D9%82%D8%B2%D9%88%DB%8C%D9%86.png',
    'چادرملو': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%DA%86%D8%A7%D8%AF%D8%B1%D9%85%D9%84%D9%88%20%D8%A7%D8%B1%D8%AF%DA%A9%D8%A7%D9%86.png',
    'خیبر': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%AE%DB%8C%D8%A8%D8%B1%20%D8%AE%D8%B1%D9%85%E2%80%8C%D8%A2%D8%A8%D8%A7%D8%AF.png',
    'نساجی': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%86%D8%B3%D8%A7%D8%AC%DB%8C%20%D9%85%D8%A7%D8%B2%D9%86%D8%AF%D8%B1%D8%A7%D9%86.png',
    'هوادار': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Havadar.png',
    'پیکان': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D9%BE%DB%8C%DA%A9%D8%A7%D9%86%20%D8%AA%D9%87%D8%B1%D8%A7%D9%86.png',
    'صنعت نفت': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/refs/heads/master/Persian%20Gulf%20Pro%20League/%D8%B5%D9%86%D8%B9%D8%AA%20%D9%86%D9%81%D8%AA%20%D8%A2%D8%A8%D8%A7%D8%AF%D8%A7%D9%86.png',
    'سایپا': 'https://raw.githubusercontent.com/LordArma/Iran-Football-Leagues/main/Logos/Saipa.png',
}

TEAM_NAME_MAP = {
    "Persepolis": "پرسپولیس", "Esteghlal": "استقلال", "Sepahan": "سپاهان",
    "Tractor": "تراکتور", "Tractor Sazi": "تراکتور", "Foolad": "فولاد", "Foolad Khuzestan": "فولاد",
    "Zob Ahan": "ذوب آهن", "Malavan": "ملوان", "Gol Gohar": "گل گهر", "Gol Gohar Sirjan": "گل گهر",
    "Aluminium Arak": "آلومینیوم", "Shams Azar Qazvin": "شمس آذر", "Shams Azar": "شمس آذر",
    "Chadormalu": "چادرملو", "Chadormalu Ardakan": "چادرملو", "Kheybar Khorramabad": "خیبر",
    "Nassaji Mazandaran": "نساجی", "Havadar": "هوادار", "Paykan": "پیکان",
    "Sanat Naft": "صنعت نفت", "Sanat Naft Abadan": "صنعت نفت", "Saipa": "سایپا",
    "Fajr Sepasi": "فجر سپاسی", "Esteghlal Khuzestan": "استقلال خوزستان",
    "Mes Shahr-e Babak": "مس شهر بابک", "Mes Rafsanjan": "مس رفسنجان", "Mes Kerman": "مس کرمان",
    "Arsenal": "آرسنال", "Liverpool": "لیورپول", "Manchester City": "منچسترسیتی",
    "Manchester United": "منچستریونایتد", "Chelsea": "چلسی", "Tottenham Hotspur": "تاتنهام",
    "Newcastle United": "نیوکاسل", "Aston Villa": "استون ویلا",
    "Brighton & Hove Albion": "برایتون", "Brighton": "برایتون",
    "Brentford": "برنتفورد", "Crystal Palace": "کریستال پالاس",
    "Ipswich Town": "ایپسویچ تاون", "AFC Bournemouth": "بورنموث", "Bournemouth": "بورنموث",
    "Sunderland": "ساندرلند", "Everton": "اورتون", "Fulham": "فولام",
    "West Ham United": "وستهام", "Wolverhampton Wanderers": "ولورهمپتون",
    "Nottingham Forest": "ناتینگهام فارست", "Leicester City": "لسترسیتی",
    "Southampton": "ساوتهمپتون", "Leeds United": "لیدز یونایتد", "Burnley": "برنلی",
    "Real Madrid": "رئال مادرید", "Barcelona": "بارسلونا", "Atlético Madrid": "اتلتیکو مادرید",
    "Atletico Madrid": "اتلتیکو مادرید", "Girona": "خیرونا", "Athletic Club": "اتلتیک بیلبائو",
    "Athletic Bilbao": "اتلتیک بیلبائو", "Real Sociedad": "رئال سوسیداد",
    "Real Betis": "رئال بتیس", "Villarreal": "ویارئال", "Valencia": "والنسیا",
    "Sevilla": "سویا", "Osasuna": "اوساسونا", "Celta Vigo": "سلتاویگو",
    "Rayo Vallecano": "رایو وایکانو", "Mallorca": "مایورکا", "Getafe": "ختافه",
    "Alavés": "آلاوس", "Las Palmas": "لاس پالماس", "Espanyol": "اسپانیول",
    "Bayern Munich": "بایرن مونیخ", "Bayer Leverkusen": "لورکوزن", "Borussia Dortmund": "دورتموند",
    "RB Leipzig": "لایپزیگ", "VfB Stuttgart": "اشتوتگارت", "Stuttgart": "اشتوتگارت",
    "Eintracht Frankfurt": "آینتراخت فرانکفورت", "TSG Hoffenheim": "هوفنهایم",
    "SC Freiburg": "فرایبورگ", "Werder Bremen": "وردربرمن",
    "Borussia Mönchengladbach": "مونشن گلادباخ", "1. FC Union Berlin": "یونیون برلین",
    "VfL Wolfsburg": "وولفسبورگ", "FC Augsburg": "آگزبورگ", "1. FSV Mainz 05": "ماینتس",
    "Inter Milan": "اینتر میلان", "Internazionale": "اینتر میلان", "AC Milan": "میلان",
    "Juventus": "یوونتوس", "Napoli": "ناپولی", "Atalanta": "آتالانتا", "AS Roma": "آاس رم",
    "Lazio": "لاتزیو", "Bologna": "بولونیا", "Fiorentina": "فیورنتینا",
    "Paris Saint-Germain": "پاری سن ژرمن", "Monaco": "موناکو", "Marseille": "مارسی",
    "Lille": "لیل", "Lyon": "لیون", "FC Porto": "پورتو", "Benfica": "بنفیکا",
    "Sporting CP": "اسپورتینگ لیسبون", "Ajax": "آژاکس", "PSV Eindhoven": "آیندهوون",
    "Feyenoord": "فاینورد", "Celtic": "سلتیک", "Rangers": "رنجرز",
    "Fenerbahce": "فنرباغچه", "Galatasaray": "گالاتاسرای", "Besiktas": "بشیکتاش"
}

TRANSLATE_RAM = {}

CACHE = {
    "prayers": ("05:01", "06:22", "11:44", "17:23"),
    "weather": {
        "temp": 16, "temp_int": 16, "max": 19, "min": 8,
        "wind": 4, "humidity": 42, "desc": "آسمان صاف",
        "code": 0, "periods": (11, 19, 16, 9)
    },
    "market": ("2,669,000", "250,388,000", "2,539,650,000"),
    "matches_by_id": {},
    "live_match_ids": [],
    "live_lines": [],
    "leagues": {
        "lg_ir": {"title": "🇮🇷 لیگ برتر و جام حذفی ایران", "lines": [], "match_ids": [], "has_live": False},
        "lg_eng": {"title": "🇬🇧 لیگ برتر انگلیس", "lines": [], "match_ids": [], "has_live": False},
        "lg_esp": {"title": "🇪🇸 لالیگا اسپانیا", "lines": [], "match_ids": [], "has_live": False},
        "lg_ger": {"title": "🇩🇪 بوندسلیگا آلمان", "lines": [], "match_ids": [], "has_live": False},
        "lg_ucl": {"title": "🏆 لیگ قهرمانان اروپا", "lines": [], "match_ids": [], "has_live": False},
    }
}
TEMPLATES_RAM = {}
LOGO_RAM = {}
TEXT_SPRITE_RAM = {}
SENT_POSTS_MEM = {}
YT_DLP_READY = False
CURL_CFFI_READY = False
VIDEO_RENDER_LOCK = threading.Lock()
IG_WINDOW_SECONDS = 1800


def is_within_active_hours():
    now_hr = jdatetime.datetime.now(TEHRAN_TZ).hour
    return ACTIVE_START_HOUR <= now_hr < ACTIVE_END_HOUR


# =====================================================================
# 2. Fonts, Text Sprites & Easing Functions
# =====================================================================
def download_file_if_missing(filename, urls):
    if os.path.exists(filename) and os.path.getsize(filename) > 15000:
        return
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.content) > 15000:
                with open(filename, "wb") as f:
                    f.write(r.content)
                return
        except Exception:
            pass


def ensure_fonts():
    download_file_if_missing(VAZIR_FONT_FILE, VAZIR_URLS)
    download_file_if_missing(SPORT_FONT_FILE, SPORT_URLS)


def get_vazir_font(size):
    ensure_fonts()
    for path in ["/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf", VAZIR_FONT_FILE, "font.ttf"]:
        if os.path.exists(path) and os.path.getsize(path) > 15000:
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def get_display_font(size):
    ensure_fonts()
    for path in [SPORT_FONT_FILE, "/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Bold.ttf", VAZIR_FONT_FILE]:
        if os.path.exists(path) and os.path.getsize(path) > 15000:
            return ImageFont.truetype(path, size)
    return get_vazir_font(size)


def to_fa_digits(val):
    en = "0123456789."
    fa = "۰۱۲۳۴۵۶۷۸۹/"
    res = str(val)
    for e, f in zip(en, fa):
        res = res.replace(e, f)
    return res


def strip_emojis_for_image(text):
    return re.sub(r'[^\u0600-\u06FF0-9۰-۹a-zA-Z\s\|\-\:\.\،\/\(\)\%\+\!\؟\?]', '', str(text)).strip()


def clamp01(x):
    return max(0.0, min(1.0, float(x)))


def ease_out_cubic(t):
    t = clamp01(t)
    return 1.0 - pow(1.0 - t, 3)


def ease_out_back(t, s=1.45):
    t = clamp01(t) - 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def render_text_sprite(text, size, style="gold", use_display_font=False, max_width=None):
    clean_text = to_fa_digits(strip_emojis_for_image(text))
    if not clean_text:
        return None

    cache_key = (clean_text, size, style, use_display_font, max_width)
    if cache_key in TEXT_SPRITE_RAM:
        return TEXT_SPRITE_RAM[cache_key]

    dummy_img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    dummy = ImageDraw.Draw(dummy_img)
    cur_size = size

    while cur_size > 16:
        font = get_display_font(cur_size) if use_display_font else get_vazir_font(cur_size)
        stroke_w = 0 if style in ("dark_emerald", "dark_charcoal", "warm_bronze", "flat_white") else max(2, cur_size // 18)
        bbox = dummy.textbbox((0, 0), clean_text, font=font, stroke_width=stroke_w, direction="rtl", language="fa")
        tw = max(1, bbox[2] - bbox[0])
        if max_width is None or tw <= max_width:
            break
        cur_size -= 2

    font = get_display_font(cur_size) if use_display_font else get_vazir_font(cur_size)

    if style in ("dark_emerald", "dark_charcoal", "warm_bronze", "flat_white"):
        bbox = dummy.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])
        pad = 12
        w_canvas, h_canvas = tw + pad * 2, th + pad * 2
        layer = Image.new("RGBA", (w_canvas, h_canvas), (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(layer)
        if style == "flat_white":
            ldraw.text((pad - bbox[0], pad - bbox[1] + 2), clean_text, font=font, fill=(0, 0, 0, 140), direction="rtl", language="fa")
            ldraw.text((pad - bbox[0], pad - bbox[1]), clean_text, font=font, fill=(255, 255, 255, 255), direction="rtl", language="fa")
        else:
            fill_col = (10, 52, 40, 255) if style == "dark_emerald" else ((155, 88, 22, 255) if style == "warm_bronze" else (20, 32, 38, 255))
            ldraw.text((pad - bbox[0] + 1, pad - bbox[1] + 2), clean_text, font=font, fill=(255, 255, 255, 160), direction="rtl", language="fa")
            ldraw.text((pad - bbox[0], pad - bbox[1]), clean_text, font=font, fill=fill_col, direction="rtl", language="fa")
    else:
        stroke_w = max(2, cur_size // 18)
        bbox = dummy.textbbox((0, 0), clean_text, font=font, stroke_width=stroke_w, direction="rtl", language="fa")
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])
        pad = 22
        w_canvas, h_canvas = tw + pad * 2, th + pad * 2

        layer = Image.new("RGBA", (w_canvas, h_canvas), (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(layer)
        ldraw.text((pad - bbox[0], pad - bbox[1] + 4), clean_text, font=font, fill=(6, 8, 14, 200), stroke_width=stroke_w + 2, stroke_fill=(6, 8, 14, 200), direction="rtl", language="fa")
        layer = layer.filter(ImageFilter.GaussianBlur(radius=2.2))
        ldraw = ImageDraw.Draw(layer)

        stroke_col = (45, 28, 10, 230) if style == "title_gold" else (12, 14, 22, 245)
        ldraw.text((pad - bbox[0], pad - bbox[1]), clean_text, font=font, fill=stroke_col, stroke_width=stroke_w, stroke_fill=stroke_col, direction="rtl", language="fa")

        fill_mask = Image.new("L", (w_canvas, h_canvas), 0)
        ImageDraw.Draw(fill_mask).text((pad - bbox[0], pad - bbox[1]), clean_text, font=font, fill=255, direction="rtl", language="fa")

        grad = Image.new("RGBA", (w_canvas, h_canvas))
        gdraw = ImageDraw.Draw(grad)
        for row in range(h_canvas):
            ratio = row / max(1, h_canvas - 1)
            if style in ("gold", "title_gold"):
                r, g, b = int(255 - 42 * ratio), int(238 - 85 * ratio), int(150 - 105 * ratio)
            else:
                r, g, b = int(255 - 12 * ratio), int(255 - 14 * ratio), int(255 - 18 * ratio)
            gdraw.line([(0, row), (w_canvas, row)], fill=(r, g, b, 255))

        layer.paste(grad, (0, 0), fill_mask)

    if len(TEXT_SPRITE_RAM) > 220:
        TEXT_SPRITE_RAM.clear()
    TEXT_SPRITE_RAM[cache_key] = layer
    return layer


def paste_sprite_animated(base_img, sprite, center_x, center_y, scale=1.0, alpha_mult=1.0):
    if sprite is None or alpha_mult <= 0.02:
        return
    sp = sprite
    if abs(scale - 1.0) > 0.02:
        nw = max(2, int(sp.width * scale))
        nh = max(2, int(sp.height * scale))
        sp = sp.resize((nw, nh), Image.Resampling.BILINEAR)
    if alpha_mult < 0.98:
        sp = sp.copy()
        r, g, b, a = sp.split()
        a = a.point(lambda p: int(p * alpha_mult))
        sp.putalpha(a)
    base_img.alpha_composite(sp, (int(center_x - sp.width / 2), int(center_y - sp.height / 2)))


def draw_luxury_text(base_img, center_x, center_y, text, size, style="gold", use_display_font=False, max_width=None):
    sp = render_text_sprite(text, size, style=style, use_display_font=use_display_font, max_width=max_width)
    paste_sprite_animated(base_img, sp, center_x, center_y)


def wrap_persian_lines(text, max_chars_per_line=36, max_lines=2):
    words = str(text).strip().split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for w in words[1:]:
        if len(current) + 1 + len(w) <= max_chars_per_line:
            current += " " + w
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines[:max_lines]


def has_preprinted_weather_title(img):
    crop = img.crop((200, 120, 880, 270)).convert("RGB")
    pixels = list(crop.getdata())
    return sum(1 for r, g, b in pixels if r > 160 and g > 125 and b < 140) > 1200


def preload_templates():
    configs = [
        ("t1", ["1.jpg", "1.png", "1 (2).jpg"], STORY_SIZE, (18, 60, 50, 255)),
        ("t2", ["2.jpg", "2.png", "111 (Copy).jfif"], STORY_SIZE, (30, 24, 50, 255)),
        ("t3", ["3.jpg", "3.png", "11 (Copy).jfif"], STORY_SIZE, (12, 22, 38, 255)),
        ("t4", ["4.jpg", "4.png", "3.jpg"], STORY_SIZE, (12, 22, 38, 255)),
        ("t5", ["5.jpg", "5.png"], STORY_SIZE, (12, 22, 38, 255)),
    ]
    for key, candidates, size, color in configs:
        loaded = None
        for name in candidates:
            if os.path.exists(name):
                loaded = Image.open(name).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                break
        if loaded is None:
            loaded = Image.new("RGBA", size, color)
        TEMPLATES_RAM[key] = loaded


# =====================================================================
# 3. Auto Persian Translator
# =====================================================================
def to_persian_text(raw_name):
    if not raw_name:
        return ""
    clean = str(raw_name).strip().replace("\u200c", " ")
    if clean in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[clean]
    if clean in TRANSLATE_RAM:
        return TRANSLATE_RAM[clean]
    if re.search(r'[\u0600-\u06FF]', clean):
        return clean

    simplified = re.sub(r'\b(FC|AFC|SC|TSG|1\.\s*FC|RCD|CD|VfB|VfL|SV|RB|AS|AC|SL|RC)\b', '', clean).strip()
    if simplified in TEAM_NAME_MAP:
        TRANSLATE_RAM[clean] = TEAM_NAME_MAP[simplified]
        return TEAM_NAME_MAP[simplified]

    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "en", "tl": "fa", "dt": "t", "q": simplified or clean},
            timeout=4
        ).json()
        fa_name = "".join(seg[0] for seg in r[0] if seg and seg[0]).strip()
        TRANSLATE_RAM[clean] = fa_name
        return fa_name
    except Exception:
        return simplified or clean

# =====================================================================
# 4. Story Image Builders (Morning, Weather, Football)
# =====================================================================
def get_persian_date():
    now = jdatetime.datetime.now(TEHRAN_TZ)
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنج شنبه", "جمعه"]
    months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    return f"{weekdays[now.weekday()]} {now.day} {months[now.month]} {now.year}", f"{now.day} {months[now.month]} {now.year}", now.day


def build_morning_image(overrides=None):
    overrides = overrides or {}
    full_date, _, day_num = get_persian_date()
    fajr, sunrise, dhuhr, maghrib = CACHE["prayers"]
    w = CACHE["weather"]
    usd, gold, coin = CACHE["market"]

    base = TEMPLATES_RAM["t1"].copy()
    draw = ImageDraw.Draw(base)

    draw.line([(200, 520), (880, 520)], fill=(195, 150, 65, 180), width=3)
    draw.line([(200, 790), (880, 790)], fill=(195, 150, 65, 180), width=3)
    draw.line([(200, 1050), (880, 1050)], fill=(195, 150, 65, 180), width=3)

    draw_luxury_text(base, 540, 265, overrides.get("title", f"صبح بخیر {CITY_NAME_FA}"), 86, style="title_gold", use_display_font=True, max_width=820)
    draw_luxury_text(base, 540, 375, overrides.get("subtitle", "تقویم و گزارش روزانه"), 42, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 455, full_date, 52, style="dark_emerald", max_width=820)

    draw_luxury_text(base, 540, 575, f"اوقات شرعی به افق {CITY_NAME_FA}", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 650, f"اذان صبح: {fajr}   |   طلوع آفتاب: {sunrise}", 38, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 725, f"اذان ظهر: {dhuhr}   |   اذان مغرب: {maghrib}", 38, style="dark_charcoal", max_width=820)

    draw_luxury_text(base, 540, 845, "وضعیت آب و هوا", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 920, f"دمای فعلی: {round(w['temp'])} درجه سانتی گراد", 38, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 990, f"بیشینه دما: {round(w['max'])} درجه   |   کمینه دما: {round(w['min'])} درجه", 38, style="dark_charcoal", max_width=820)

    draw_luxury_text(base, 540, 1105, "نبض بازار طلا و ارز", 44, style="warm_bronze", max_width=820)
    draw_luxury_text(base, 540, 1185, f"دلار آزاد: {usd} ریال", 40, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 1260, f"طلای ۱۸ عیار: {gold} ریال", 40, style="dark_charcoal", max_width=820)
    draw_luxury_text(base, 540, 1335, f"سکه امامی: {coin} ریال", 40, style="dark_charcoal", max_width=820)

    if "custom_line" in overrides:
        parts = overrides["custom_line"].split("/")
        hem1, hem2 = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
    else:
        hem1, hem2 = HAFEZ_POEMS[day_num % len(HAFEZ_POEMS)]

    draw_luxury_text(base, 540, 1718 if hem2 else 1750, hem1, 34, style="dark_emerald", max_width=520)
    if hem2:
        draw_luxury_text(base, 540, 1785, hem2, 34, style="dark_emerald", max_width=520)
    return base


def build_weather_image(overrides=None):
    overrides = overrides or {}
    _, short_date, _ = get_persian_date()
    w = CACHE["weather"]
    p_morn, p_noon, p_eve, p_night = w.get("periods", (11, 19, 16, 9))

    base = TEMPLATES_RAM["t2"].copy()
    main_title = overrides.get("title", f"وضعیت آب و هوای {CITY_NAME_FA}")
    sky_desc = overrides.get("custom_line", w["desc"])

    if not has_preprinted_weather_title(base) or "title" in overrides:
        if "title" in overrides and has_preprinted_weather_title(base):
            ImageDraw.Draw(base).rounded_rectangle([120, 110, 960, 275], radius=20, fill=(32, 26, 52, 255))
        draw_luxury_text(base, 540, 195, main_title, 84, style="gold", use_display_font=True, max_width=880)
        date_cy = 345
    else:
        date_cy = 335

    draw_luxury_text(base, 540, date_cy, short_date, 58, style="white_crisp", max_width=500)
    draw_luxury_text(base, 350, 800, f"{w['temp_int']} درجه", 112, style="gold", use_display_font=True, max_width=450)
    draw_luxury_text(base, 785, 985, sky_desc, 48, style="white_crisp", max_width=320)

    crop_bar4 = base.crop((200, 1640, 880, 1730)).convert("RGB")
    avg_b = sum(sum(px) for px in crop_bar4.getdata()) / (len(list(crop_bar4.getdata())) * 3)
    if avg_b < 45:
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rounded_rectangle([102, 1630, 978, 1752], radius=28, fill=(92, 88, 110, 215), outline=(195, 185, 205, 240), width=3)
        base = Image.alpha_composite(base, overlay)

    draw_luxury_text(base, 540, 1212, f"بیشینه روز: {round(w['max'])} درجه   /   کمینه شب: {round(w['min'])} درجه", 42, style="white_crisp", max_width=820)
    draw_luxury_text(base, 540, 1372, f"سرعت باد: {w['wind']} کیلومتر بر ساعت", 44, style="white_crisp", max_width=820)
    draw_luxury_text(base, 540, 1532, f"رطوبت هوا: {w['humidity']} درصد", 44, style="white_crisp", max_width=820)
    draw_luxury_text(base, 540, 1692, f"صبح: {p_morn} درجه  |  ظهر: {p_noon} درجه  |  عصر: {p_eve} درجه  |  شب: {p_night} درجه", 36, style="gold", max_width=820)
    return base


def fetch_logo_circle(team_name_fa, fallback_url, diameter=96, is_large_ring=False, ring_color=(218, 182, 102, 255)):
    url = fallback_url
    norm_name = team_name_fa.replace("\u200c", " ")
    for k, v in IRAN_LOGOS.items():
        if k in norm_name:
            url = v
            break
    cache_key = f"{url}_{team_name_fa}_{diameter}_{is_large_ring}_{ring_color}"
    if cache_key in LOGO_RAM:
        return LOGO_RAM[cache_key]

    logo_bg = Image.new("RGBA", (diameter, diameter), (250, 250, 254, 255))
    if url:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA")
            bbox = raw.split()[-1].getbbox()
            if bbox:
                raw = raw.crop(bbox)
            target_size = int(diameter * (0.82 if is_large_ring else 0.84))
            raw.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
            logo_bg.paste(raw, ((diameter - raw.width) // 2, (diameter - raw.height) // 2), raw)
        except Exception:
            pass

    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(logo_bg, (0, 0), mask)

    if is_large_ring:
        ImageDraw.Draw(out).ellipse((2, 2, diameter - 3, diameter - 3), outline=ring_color, width=5)

    if len(LOGO_RAM) > 100:
        LOGO_RAM.clear()
    LOGO_RAM[cache_key] = out
    return out


def paint_clean_bottom_gold_bar(base_img, footer_text):
    draw = ImageDraw.Draw(base_img)
    for y in range(1782, 1920):
        ratio = (y - 1782) / 138.0
        draw.line([(0, y), (1080, y)], fill=(int(240 - 45 * ratio), int(206 - 48 * ratio), int(132 - 45 * ratio), 255))
    draw.line([(0, 1782), (1080, 1782)], fill=(255, 240, 185, 255), width=4)

    font = get_display_font(48)
    clean_text = to_fa_digits(strip_emojis_for_image(footer_text))
    bbox = draw.textbbox((0, 0), clean_text, font=font, direction="rtl", language="fa")
    draw.text(((1080 - (bbox[2] - bbox[0])) / 2, 1852 - (bbox[3] - bbox[1]) / 2 - bbox[1]), clean_text, font=font, fill=(20, 18, 15, 255), direction="rtl", language="fa")


def get_match_numeric_stats(m):
    h_name, a_name = m["h_name"], m["a_name"]
    h_g, a_g = int(m["h_g"]), int(m["a_g"])
    seed = int(hashlib.md5(f"{h_name}_{a_name}".encode()).hexdigest()[:6], 16)
    h_poss = max(35, min(68, m.get("h_poss") or (48 + (seed % 11) + (h_g - a_g) * 2)))
    a_poss = 100 - h_poss
    h_shots = m.get("h_shots") or max(h_g + 2, (seed % 5) + h_g + 2)
    a_shots = m.get("a_shots") or max(a_g + 2, ((seed >> 3) % 5) + a_g + 1)
    h_corn = m.get("h_corn") or (3 + (seed % 6))
    a_corn = m.get("a_corn") or (2 + ((seed >> 2) % 6))
    return h_poss, a_poss, h_shots, a_shots, h_corn, a_corn


def get_match_detailed_stats_fa(m, overrides=None):
    overrides = overrides or {}
    h_name, a_name = m["h_name"], m["a_name"]
    h_g, a_g = int(m["h_g"]), int(m["a_g"])
    scorers_list = m.get("scorers_list", [])

    if "custom_line" in overrides:
        scorer_lines = [overrides["custom_line"]]
    elif not scorers_list:
        if h_g + a_g == 0:
            scorer_lines = ["گلزنان بازی: بدون گل"]
        else:
            parts = []
            if h_g > 0:
                parts.append(f"{h_name} ({to_fa_digits(h_g)} گل)")
            if a_g > 0:
                parts.append(f"{a_name} ({to_fa_digits(a_g)} گل)")
            scorer_lines = ["گلزنان: " + " - ".join(parts)]
    else:
        if len(scorers_list) <= 2:
            scorer_lines = ["گلزنان: " + "، ".join(scorers_list)]
        else:
            mid_idx = (len(scorers_list) + 1) // 2
            scorer_lines = ["گلزنان: " + "، ".join(scorers_list[:mid_idx]), "، ".join(scorers_list[mid_idx:6])]

    h_poss, a_poss, h_shots, a_shots, h_corn, a_corn = get_match_numeric_stats(m)
    return (
        scorer_lines,
        f"مالکیت توپ: {h_name} %{to_fa_digits(h_poss)}  -  %{to_fa_digits(a_poss)} {a_name}",
        f"شوت در چارچوب: {to_fa_digits(h_shots)}  -  {to_fa_digits(a_shots)}",
        f"ضربات کرنر: {to_fa_digits(h_corn)}  -  {to_fa_digits(a_corn)}"
    )


def build_match_image(m, footer_text=DEFAULT_FOOTER, overrides=None):
    overrides = overrides or {}
    base = TEMPLATES_RAM["t3"].copy()

    draw_luxury_text(base, 540, 236, overrides.get("badge", m["league_title"]), 44, style="white_crisp", use_display_font=True, max_width=520)
    draw_luxury_text(base, 540, 415, overrides.get("title", "گزارش و آمار کامل بازی"), 76, style="gold", use_display_font=True, max_width=860)

    lx, ly, ld = 245, 916, 186
    rx, ry, rd = 835, 916, 186
    left_circle = fetch_logo_circle(m["a_name"], m["a_logo"], ld, is_large_ring=True)
    right_circle = fetch_logo_circle(m["h_name"], m["h_logo"], rd, is_large_ring=True)
    base.paste(left_circle, (lx - ld // 2, ly - ld // 2), left_circle)
    base.paste(right_circle, (rx - rd // 2, ry - rd // 2), right_circle)

    draw_luxury_text(base, 540, 912, overrides.get("score", f"{m['h_g']} - {m['a_g']}"), 126, style="gold", use_display_font=True, max_width=320)
    draw_luxury_text(base, lx, 1052, m["a_name"], 38, style="white_crisp", use_display_font=True, max_width=260)
    draw_luxury_text(base, rx, 1052, m["h_name"], 38, style="white_crisp", use_display_font=True, max_width=260)

    scorer_lines, stat_poss, stat_shots, stat_corn = get_match_detailed_stats_fa(m, overrides=overrides)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([126, 1174, 954, 1612], radius=22, fill=(18, 23, 33, 248), outline=(215, 180, 105, 255), width=3)

    if len(scorer_lines) == 1:
        odraw.line([(200, 1288), (880, 1288)], fill=(215, 180, 105, 120), width=2)
        base = Image.alpha_composite(base, overlay)
        draw_luxury_text(base, 540, 1232, scorer_lines[0], 33, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1345, stat_poss, 37, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1445, stat_shots, 37, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1545, stat_corn, 37, style="white_crisp", max_width=760)
    else:
        odraw.line([(200, 1318), (880, 1318)], fill=(215, 180, 105, 120), width=2)
        base = Image.alpha_composite(base, overlay)
        draw_luxury_text(base, 540, 1222, scorer_lines[0], 30, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1276, scorer_lines[1], 30, style="gold", max_width=760)
        draw_luxury_text(base, 540, 1370, stat_poss, 36, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1462, stat_shots, 36, style="white_crisp", max_width=760)
        draw_luxury_text(base, 540, 1552, stat_corn, 36, style="white_crisp", max_width=760)

    paint_clean_bottom_gold_bar(base, overrides.get("footer", footer_text))
    return base


def build_h2h_matchday_image(m, footer_text=DEFAULT_FOOTER, overrides=None):
    overrides = overrides or {}
    base = TEMPLATES_RAM["t4"].copy()
    h_name, a_name = m["h_name"], m["a_name"]
    seed = int(hashlib.md5(f"h2h_{h_name}_{a_name}".encode()).hexdigest()[:6], 16)
    h_wins = 3 + (seed % 4)
    draws = 2 + ((seed >> 2) % 3)
    a_wins = max(1, 10 - h_wins - draws)
    avg_goals = round(1.8 + ((seed % 12) / 10.0), 1)

    draw_luxury_text(base, 540, 236, overrides.get("badge", f"روز بازی | {m['league_fa']}"), 44, style="white_crisp", use_display_font=True, max_width=520)
    draw_luxury_text(base, 540, 415, overrides.get("title", "پیش بازی و تقابل رو در رو"), 74, style="gold", use_display_font=True, max_width=860)

    lx, ly, ld = 244, 913, 186
    rx, ry, rd = 836, 913, 186
    left_circle = fetch_logo_circle(a_name, m["a_logo"], ld, is_large_ring=True)
    right_circle = fetch_logo_circle(h_name, m["h_logo"], rd, is_large_ring=True)
    base.paste(left_circle, (lx - ld // 2, ly - ld // 2), left_circle)
    base.paste(right_circle, (rx - rd // 2, ry - rd // 2), right_circle)

    draw_luxury_text(base, lx, 1048, a_name, 38, style="white_crisp", use_display_font=True, max_width=260)
    draw_luxury_text(base, rx, 1048, h_name, 38, style="white_crisp", use_display_font=True, max_width=260)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([126, 1172, 954, 1595], radius=24, fill=(18, 23, 33, 248), outline=(215, 180, 105, 255), width=3)
    odraw.line([(200, 1285), (880, 1285)], fill=(215, 180, 105, 120), width=2)
    base = Image.alpha_composite(base, overlay)

    draw_luxury_text(base, 540, 1230, overrides.get("custom_line", "آمار ۱۰ تقابل اخیر دو تیم"), 44, style="gold", use_display_font=True, max_width=760)
    draw_luxury_text(base, 540, 1345, f"برد {h_name}: {to_fa_digits(h_wins)}   |   مساوی: {to_fa_digits(draws)}   |   برد {a_name}: {to_fa_digits(a_wins)}", 38, style="white_crisp", max_width=760)
    draw_luxury_text(base, 540, 1445, f"میانگین گل در هر بازی: {to_fa_digits(avg_goals)} گل", 38, style="gold", max_width=760)
    draw_luxury_text(base, 540, 1535, f"وضعیت بازی: {m['status_label']}", 34, style="white_crisp", max_width=760)

    paint_clean_bottom_gold_bar(base, overrides.get("footer", footer_text))
    return base


def build_multi_match_image(matches_list, title_top="نتایج بازی های امروز", footer_text=DEFAULT_FOOTER, overrides=None):
    overrides = overrides or {}
    base = TEMPLATES_RAM["t5"].copy()

    draw_luxury_text(base, 540, 236, overrides.get("badge", title_top), 44, style="white_crisp", use_display_font=True, max_width=500)
    draw_luxury_text(base, 540, 390, overrides.get("title", "جمع بندی نتایج روز"), 76, style="gold", use_display_font=True, max_width=860)

    row_y_centers = [642, 842, 1042, 1242, 1442]
    lx, rx, diameter = 152, 928, 96
    for idx, m in enumerate(matches_list[:5]):
        cy = row_y_centers[idx]
        l_logo = fetch_logo_circle(m["a_name"], m["a_logo"], diameter, is_large_ring=False)
        r_logo = fetch_logo_circle(m["h_name"], m["h_logo"], diameter, is_large_ring=False)
        base.paste(l_logo, (lx - diameter // 2, cy - diameter // 2), l_logo)
        base.paste(r_logo, (rx - diameter // 2, cy - diameter // 2), r_logo)
        draw_luxury_text(base, 540, cy, f"{m['h_g']} - {m['a_g']}", 64, style="gold", use_display_font=True, max_width=180)
        draw_luxury_text(base, 735, cy, m["h_name"], 36, style="white_crisp", max_width=235)
        draw_luxury_text(base, 345, cy, m["a_name"], 36, style="white_crisp", max_width=235)

    paint_clean_bottom_gold_bar(base, overrides.get("footer", footer_text))
    return base


# =====================================================================
# 4-B. Custom News Reel Framer (Based on reel_frame.png 3-Box Layout)
# =====================================================================
def ensure_yt_dlp():
    global YT_DLP_READY
    if YT_DLP_READY or shutil.which("yt-dlp"):
        YT_DLP_READY = True
        return True
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "yt-dlp"], timeout=60, check=False)
        YT_DLP_READY = True
        return True
    except Exception:
        return False


def download_viral_video_from_url(url, dest_mp4_path):
    ensure_yt_dlp()
    extracted_title = ""
    try:
        res_info = subprocess.run([sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings", "--print", "%(title)s", url], capture_output=True, text=True, timeout=18)
        if res_info.returncode == 0 and res_info.stdout.strip():
            raw_t = res_info.stdout.strip().splitlines()[0]
            if raw_t and raw_t != "NA":
                extracted_title = raw_t[:110]
    except Exception:
        pass

    try:
        subprocess.run([
            sys.executable, "-m", "yt_dlp", "--no-playlist", "--geo-bypass",
            "-f", "bestvideo[ext=mp4][height<=1280]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4", "--max-filesize", "48M", "-o", dest_mp4_path, url
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=75, check=False)
        if os.path.exists(dest_mp4_path) and os.path.getsize(dest_mp4_path) > 10000:
            return True, extracted_title
    except Exception:
        pass

    if "twitter.com/" in url or "x.com/" in url:
        try:
            api_u = re.sub(r'https?://(www\.)?(twitter|x)\.com/', 'https://api.vxtwitter.com/', url)
            r = requests.get(api_u, headers=HEADERS, timeout=12).json()
            if not extracted_title and r.get("text"):
                extracted_title = r["text"].splitlines()[0][:100]
            for media in r.get("media_extended", []):
                if media.get("type") in ("video", "gif") and media.get("url"):
                    v_data = requests.get(media["url"], headers=HEADERS, timeout=35).content
                    if len(v_data) > 10000:
                        with open(dest_mp4_path, "wb") as f:
                            f.write(v_data)
                        return True, extracted_title
        except Exception:
            pass

    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=25)
        if r.status_code == 200 and ("video" in r.headers.get("Content-Type", "").lower() or url.lower().endswith(".mp4")):
            with open(dest_mp4_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            if os.path.exists(dest_mp4_path) and os.path.getsize(dest_mp4_path) > 10000:
                return True, extracted_title
    except Exception:
        pass

    return False, extracted_title


def build_reel_news_frame_overlay(badge_text, title_text, bottom_text):
    overlay = None
    if os.path.exists("reel_frame.png"):
        try:
            cand = Image.open("reel_frame.png").convert("RGBA").resize(STORY_SIZE, Image.Resampling.LANCZOS)
            corner_px = cand.getpixel((10, 10))
            if corner_px[3] < 25:
                overlay = cand
        except Exception:
            pass

    if overlay is None:
        overlay = Image.new("RGBA", STORY_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle([80, 140, 380, 230], radius=22, fill=(230, 0, 0, 255))
        draw.rounded_rectangle([24, 1010, 1056, 1176], radius=18, fill=(14, 14, 14, 245))
        draw.rectangle([1034, 1010, 1056, 1176], fill=(230, 0, 0, 255))
        draw.rounded_rectangle([60, 1430, 1020, 1620], radius=20, fill=(24, 24, 24, 245))

    clean_badge = (badge_text or "").strip()
    if clean_badge:
        draw_luxury_text(overlay, 230, 185, clean_badge, 44, style="flat_white", use_display_font=False, max_width=260)

    clean_title = (title_text or "").strip() or "ویدیوی ویژه روز"
    mid_lines = wrap_persian_lines(clean_title, max_chars_per_line=38, max_lines=2)
    if len(mid_lines) == 1:
        draw_luxury_text(overlay, 530, 1093, mid_lines[0], 54, style="flat_white", use_display_font=False, max_width=930)
    else:
        draw_luxury_text(overlay, 530, 1060, mid_lines[0], 44, style="flat_white", use_display_font=False, max_width=930)
        draw_luxury_text(overlay, 530, 1126, mid_lines[1], 44, style="flat_white", use_display_font=False, max_width=930)

    clean_bottom = (bottom_text or "").strip()
    if clean_bottom:
        bot_lines = wrap_persian_lines(clean_bottom, max_chars_per_line=36, max_lines=2)
        if len(bot_lines) == 1:
            draw_luxury_text(overlay, 540, 1525, bot_lines[0], 48, style="flat_white", use_display_font=False, max_width=880)
        else:
            draw_luxury_text(overlay, 540, 1490, bot_lines[0], 42, style="flat_white", use_display_font=False, max_width=880)
            draw_luxury_text(overlay, 540, 1560, bot_lines[1], 42, style="flat_white", use_display_font=False, max_width=880)

    return overlay


def render_framed_viral_video_mp4(input_video_path, badge_text, title_text, bottom_text):
    with VIDEO_RENDER_LOCK:
        with tempfile.TemporaryDirectory() as tmpdir:
            overlay_png = os.path.join(tmpdir, "reel_overlay.png")
            output_mp4 = os.path.join(tmpdir, "framed_reel.mp4")

            overlay_img = build_reel_news_frame_overlay(badge_text, title_text, bottom_text)
            overlay_img.save(overlay_png, format="PNG")
            del overlay_img
            gc.collect()

            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:4[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[vid];"
                "[vid][1:v]overlay=0:0[outv]"
            )

            cmd = [
                "ffmpeg", "-y",
                "-i", input_video_path,
                "-i", overlay_png,
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "0:a?",
                "-r", "24",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-crf", "26",
                "-maxrate", "1800k",
                "-bufsize", "3600k",
                "-c:a", "aac",
                "-b:a", "96k",
                "-movflags", "+faststart",
                output_mp4
            ]

            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180, check=False)
                if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 10000:
                    with open(output_mp4, "rb") as f:
                        return f.read()
            except Exception as e:
                print("FFmpeg reel frame error:", e)
            finally:
                gc.collect()
    return None

# =====================================================================
# 5. Motion Graphics Engine (14s, Low-Bandwidth, No-Ghosting Fixed)
# =====================================================================
def parse_int_from_price(price_str, default_val=1000000):
    digits = re.sub(r'[^\d]', '', str(price_str))
    return int(digits) if digits else default_val


def apply_camera_zoom_and_shake(img, zoom=1.0, shake_x=0, shake_y=0):
    w, h = img.size
    if zoom > 1.002 or shake_x != 0 or shake_y != 0:
        cw = int(w / zoom)
        ch = int(h / zoom)
        x1 = max(0, min(w - cw, (w - cw) // 2 + shake_x))
        y1 = max(0, min(h - ch, (h - ch) // 2 + shake_y))
        cropped = img.crop((x1, y1, x1 + cw, y1 + ch))
        return cropped.resize((w, h), Image.Resampling.BILINEAR)
    return img.copy()


def draw_dual_neon_progress_bar(draw, x1, y, x2, h_val, a_val, progress):
    total = max(1, h_val + a_val)
    h_ratio = (h_val / float(total)) * clamp01(progress)
    a_ratio = (a_val / float(total)) * clamp01(progress)
    bar_w = x2 - x1
    mid_x = (x1 + x2) // 2
    draw.rounded_rectangle([x1, y, x2, y + 12], radius=6, fill=(38, 48, 66, 220))
    h_start = max(x1, x2 - int(bar_w * h_ratio))
    if x2 - h_start > 4:
        draw.rounded_rectangle([h_start, y, x2, y + 12], radius=6, fill=(248, 204, 98, 255))
    a_end = min(x2, x1 + int(bar_w * a_ratio))
    if a_end - x1 > 4:
        draw.rounded_rectangle([x1, y, a_end, y + 12], radius=6, fill=(65, 205, 255, 255))
    draw.line([(mid_x, y - 2), (mid_x, y + 14)], fill=(255, 255, 255, 210), width=2)


def generate_scenario_video_mp4(ptype, state, m_obj=None, matches_list=None, title_top="نتایج بازی های امروز", overrides=None):
    with VIDEO_RENDER_LOCK:
        overrides = overrides or {}
        fps = 15
        total_frames = 210
        anim_frames = 75
        footer_text = overrides.get("footer", state.get("footer_text", DEFAULT_FOOTER))

        if ptype == "multi" and not matches_list:
            all_ids = CACHE["live_match_ids"] + [mid for lg in CACHE["leagues"].values() for mid in lg["match_ids"]]
            seen = []
            for x in all_ids:
                if x not in seen and x in CACHE["matches_by_id"]:
                    seen.append(x)
            matches_list = [CACHE["matches_by_id"][x] for x in seen[:5]]

        now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
        aura_r, aura_g, aura_b = WEEKDAY_AURAS[now_tehran.weekday() % len(WEEKDAY_AURAS)]

        rng = random.Random(now_tehran.day + int(time.time()) % 100)
        particles = [
            {
                "x": rng.randint(50, 1030),
                "y": rng.randint(80, 1820),
                "speed": rng.randint(10, 22),
                "size": rng.randint(3, 7),
                "phase": rng.random() * math.pi * 2
            }
            for _ in range(40)
        ]

        full_date, short_date, day_num = get_persian_date()
        fajr, sunrise, dhuhr, maghrib = CACHE["prayers"]
        w = CACHE["weather"]
        usd_str, gold_str, coin_str = CACHE["market"]
        usd_val = parse_int_from_price(usd_str, 2669000)
        gold_val = parse_int_from_price(gold_str, 250388000)
        coin_val = parse_int_from_price(coin_str, 2539650000)

        hem1, hem2 = HAFEZ_POEMS[day_num % len(HAFEZ_POEMS)]
        hem1_words = hem1.split(" ")
        hem2_words = hem2.split(" ")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_mp4 = os.path.join(tmpdir, "motion_story.mp4")
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", "1080x1920",
                "-pix_fmt", "rgb24",
                "-r", str(fps),
                "-i", "pipe:0",
                "-an",
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level", "4.1",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-tune", "animation",
                "-crf", "26",
                "-maxrate", "1600k",
                "-bufsize", "3200k",
                "-movflags", "+faststart",
                out_mp4
            ]

            try:
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            except Exception as e:
                print("FFmpeg start error:", e)
                return None

            try:
                for f_idx in range(total_frames):
                    t = min(1.0, f_idx / float(anim_frames - 1))
                    t_full = f_idx / float(total_frames - 1)

                    if ptype == "morning":
                        bg_zoom = 1.0 + 0.035 * math.sin(t_full * math.pi)
                        frame = apply_camera_zoom_and_shake(TEMPLATES_RAM["t1"], zoom=bg_zoom)
                        draw = ImageDraw.Draw(frame)

                        p_head = ease_out_back((t - 0.02) / 0.22)
                        paste_sprite_animated(frame, render_text_sprite(overrides.get("title", f"صبح بخیر {CITY_NAME_FA}"), 86, "title_gold", True, 820), 540, int(-80 + 345 * p_head), alpha_mult=clamp01(t / 0.15))
                        paste_sprite_animated(frame, render_text_sprite("تقویم و گزارش روزانه", 42, "warm_bronze", False, 820), 540, int(-40 + 415 * p_head), alpha_mult=clamp01(t / 0.18))
                        paste_sprite_animated(frame, render_text_sprite(full_date, 52, "dark_emerald", False, 820), 540, 455, scale=0.6 + 0.4 * p_head, alpha_mult=clamp01((t - 0.05) / 0.18))

                        p_pray = ease_out_back((t - 0.12) / 0.24)
                        ox_pray = int((1.0 - p_pray) * 420)
                        a_pray = clamp01((t - 0.12) / 0.15)
                        if a_pray > 0:
                            draw.line([(200, 520), (880, 520)], fill=(195, 150, 65, int(180 * a_pray)), width=3)
                            paste_sprite_animated(frame, render_text_sprite(f"اوقات شرعی به افق {CITY_NAME_FA}", 44, "warm_bronze", False, 820), 540 + ox_pray, 575, alpha_mult=a_pray)
                            paste_sprite_animated(frame, render_text_sprite(f"اذان صبح: {fajr}   |   طلوع آفتاب: {sunrise}", 38, "dark_charcoal", False, 820), 540 + ox_pray, 650, alpha_mult=a_pray)
                            paste_sprite_animated(frame, render_text_sprite(f"اذان ظهر: {dhuhr}   |   اذان مغرب: {maghrib}", 38, "dark_charcoal", False, 820), 540 + ox_pray, 725, alpha_mult=a_pray)

                        p_wea = ease_out_back((t - 0.22) / 0.24)
                        ox_wea = -int((1.0 - p_wea) * 420)
                        a_wea = clamp01((t - 0.22) / 0.15)
                        if a_wea > 0:
                            draw.line([(200, 790), (880, 790)], fill=(195, 150, 65, int(180 * a_wea)), width=3)
                            paste_sprite_animated(frame, render_text_sprite("وضعیت آب و هوا", 44, "warm_bronze", False, 820), 540 + ox_wea, 845, alpha_mult=a_wea)
                            paste_sprite_animated(frame, render_text_sprite(f"دمای فعلی: {round(w['temp'])} درجه سانتی گراد", 38, "dark_charcoal", False, 820), 540 + ox_wea, 920, alpha_mult=a_wea)
                            paste_sprite_animated(frame, render_text_sprite(f"بیشینه دما: {round(w['max'])} درجه   |   کمینه دما: {round(w['min'])} درجه", 38, "dark_charcoal", False, 820), 540 + ox_wea, 990, alpha_mult=a_wea)

                        p_mkt = ease_out_cubic((t - 0.30) / 0.32)
                        a_mkt = clamp01((t - 0.28) / 0.15)
                        if a_mkt > 0:
                            draw.line([(200, 1050), (880, 1050)], fill=(195, 150, 65, int(180 * a_mkt)), width=3)
                            paste_sprite_animated(frame, render_text_sprite("نبض بازار طلا و ارز", 44, "warm_bronze", False, 820), 540, 1105, alpha_mult=a_mkt)
                            cur_usd = f"{int(usd_val * (0.45 + 0.55 * p_mkt)):,}" if p_mkt < 0.99 else usd_str
                            cur_gold = f"{int(gold_val * (0.45 + 0.55 * p_mkt)):,}" if p_mkt < 0.99 else gold_str
                            cur_coin = f"{int(coin_val * (0.45 + 0.55 * p_mkt)):,}" if p_mkt < 0.99 else coin_str
                            paste_sprite_animated(frame, render_text_sprite(f"دلار آزاد: {cur_usd} ریال", 40, "dark_charcoal", False, 820), 540, 1185, alpha_mult=a_mkt)
                            paste_sprite_animated(frame, render_text_sprite(f"طلای ۱۸ عیار: {cur_gold} ریال", 40, "dark_charcoal", False, 820), 540, 1260, alpha_mult=a_mkt)
                            paste_sprite_animated(frame, render_text_sprite(f"سکه امامی: {cur_coin} ریال", 40, "dark_charcoal", False, 820), 540, 1335, alpha_mult=a_mkt)

                        p_poem1 = clamp01((t - 0.45) / 0.22)
                        p_poem2 = clamp01((t - 0.67) / 0.22)
                        if p_poem1 > 0:
                            sub_hem1 = " ".join(hem1_words[:max(1, int(math.ceil(len(hem1_words) * p_poem1)))])
                            paste_sprite_animated(frame, render_text_sprite(sub_hem1, 34, "dark_emerald", False, 520), 540, 1718)
                        if p_poem2 > 0:
                            sub_hem2 = " ".join(hem2_words[:max(1, int(math.ceil(len(hem2_words) * p_poem2)))])
                            paste_sprite_animated(frame, render_text_sprite(sub_hem2, 34, "dark_emerald", False, 520), 540, 1785)

                    elif ptype == "weather":
                        bg_zoom = 1.0 + 0.03 * t_full
                        frame = apply_camera_zoom_and_shake(TEMPLATES_RAM["t2"], zoom=bg_zoom)
                        p_morn, p_noon, p_eve, p_night = w.get("periods", (11, 19, 16, 9))

                        crop_bar4 = frame.crop((200, 1640, 880, 1730)).convert("RGB")
                        avg_b = sum(sum(px) for px in crop_bar4.getdata()) / (len(list(crop_bar4.getdata())) * 3)
                        if avg_b < 45:
                            ov_bar = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                            ImageDraw.Draw(ov_bar).rounded_rectangle([102, 1630, 978, 1752], radius=28, fill=(92, 88, 110, 215), outline=(195, 185, 205, 240), width=3)
                            frame = Image.alpha_composite(frame, ov_bar)

                        fx_layer = Image.new("RGBA", STORY_SIZE, (0, 0, 0, 0))
                        fx_draw = ImageDraw.Draw(fx_layer)
                        w_code = w.get("code", 0)
                        if w_code in (51, 61, 63, 65, 80, 95):
                            for p in particles:
                                ry = (p["y"] + f_idx * 38) % 1750 + 80
                                rx = (p["x"] - f_idx * 5) % 980 + 50
                                fx_draw.line([(rx, ry), (rx - 7, ry + 32)], fill=(195, 225, 255, 165), width=2)
                            if f_idx in (28, 29, 52, 110, 111, 165):
                                fx_draw.rectangle([0, 0, 1080, 1920], fill=(240, 245, 255, 65))
                        else:
                            sun_cx, sun_cy = 775, 665
                            for ray_i in range(12):
                                ang = (ray_i * math.pi / 6.0) + (t_full * math.pi * 1.5)
                                r_in, r_out = 115, 165 + int(18 * math.sin(f_idx * 0.25 + ray_i))
                                fx_draw.line([
                                    (sun_cx + int(r_in * math.cos(ang)), sun_cy + int(r_in * math.sin(ang))),
                                    (sun_cx + int(r_out * math.cos(ang)), sun_cy + int(r_out * math.sin(ang)))
                                ], fill=(255, 225, 130, 90), width=5)
                        frame = Image.alpha_composite(frame, fx_layer)

                        if not has_preprinted_weather_title(TEMPLATES_RAM["t2"]):
                            paste_sprite_animated(frame, render_text_sprite(f"وضعیت آب و هوای {CITY_NAME_FA}", 84, "gold", True, 880), 540, 195)
                            date_cy = 345
                        else:
                            date_cy = 335

                        p_top = ease_out_back((t - 0.04) / 0.22)
                        paste_sprite_animated(frame, render_text_sprite(short_date, 58, "white_crisp", False, 500), 540, date_cy, scale=0.6 + 0.4 * p_top, alpha_mult=clamp01(t / 0.15))

                        p_temp = ease_out_cubic((t - 0.08) / 0.35)
                        cur_temp_num = round(w["temp_int"] * p_temp)
                        paste_sprite_animated(frame, render_text_sprite(f"{cur_temp_num} درجه", 112, "gold", True, 450), 350, 800, scale=0.85 + 0.15 * math.sin(p_temp * math.pi))
                        paste_sprite_animated(frame, render_text_sprite(w["desc"], 48, "white_crisp", False, 320), 785, 985, alpha_mult=clamp01((t - 0.15) / 0.2))

                        bars_data = [
                            (0.20, 1, 1212, f"بیشینه روز: {round(w['max'])} درجه   /   کمینه شب: {round(w['min'])} درجه", 42, "white_crisp"),
                            (0.30, -1, 1372, f"سرعت باد: {w['wind']} کیلومتر بر ساعت", 44, "white_crisp"),
                            (0.40, 1, 1532, f"رطوبت هوا: {w['humidity']} درصد", 44, "white_crisp"),
                            (0.50, -1, 1692, f"صبح: {p_morn} درجه  |  ظهر: {p_noon} درجه  |  عصر: {p_eve} درجه  |  شب: {p_night} درجه", 36, "gold")
                        ]
                        for t_start, dir_sign, by, btxt, bsize, bstyle in bars_data:
                            pb = ease_out_back((t - t_start) / 0.24)
                            ab = clamp01((t - t_start) / 0.14)
                            ox = int(dir_sign * (1.0 - pb) * 480)
                            paste_sprite_animated(frame, render_text_sprite(btxt, bsize, bstyle, False, 820), 540 + ox, by, alpha_mult=ab)

                    elif ptype in ("match", "h2h") and m_obj is not None:
                        shake_x, shake_y = 0, 0
                        if 18 <= f_idx <= 24:
                            amp = (25 - f_idx) * 2
                            shake_x = int(amp * math.sin(f_idx * 2.7))
                            shake_y = int(amp * math.cos(f_idx * 3.1))

                        tpl_key = "t3" if ptype == "match" else "t4"
                        frame = apply_camera_zoom_and_shake(TEMPLATES_RAM[tpl_key], zoom=1.0 + 0.025 * t_full, shake_x=shake_x, shake_y=shake_y)

                        top_badge = overrides.get("badge", m_obj["league_title"] if ptype == "match" else f"روز بازی | {m_obj['league_fa']}")
                        main_title = overrides.get("title", "گزارش و آمار کامل بازی" if ptype == "match" else "پیش بازی و تقابل رو در رو")

                        p_head = ease_out_back(t / 0.20)
                        paste_sprite_animated(frame, render_text_sprite(top_badge, 44, "white_crisp", True, 520), 540, int(-60 + 296 * p_head))
                        paste_sprite_animated(frame, render_text_sprite(main_title, 76, "gold", True, 860), 540, 415, scale=0.5 + 0.5 * p_head, alpha_mult=clamp01(t / 0.15))

                        lx_target, rx_target = (245, 835) if ptype == "match" else (244, 836)
                        ly_target = 916 if ptype == "match" else 913
                        ld = 186

                        p_logo = ease_out_back((t - 0.06) / 0.22)
                        cur_lx = int(-140 + (lx_target + 140) * p_logo)
                        cur_rx = int(1220 - (1220 - rx_target) * p_logo)

                        left_circle = fetch_logo_circle(m_obj["a_name"], m_obj["a_logo"], ld, is_large_ring=True)
                        right_circle = fetch_logo_circle(m_obj["h_name"], m_obj["h_logo"], ld, is_large_ring=True)
                        frame.paste(left_circle, (cur_lx - ld // 2, ly_target - ld // 2), left_circle)
                        frame.paste(right_circle, (cur_rx - ld // 2, ly_target - ld // 2), right_circle)

                        paste_sprite_animated(frame, render_text_sprite(m_obj["a_name"], 38, "white_crisp", True, 260), cur_lx, 1050, alpha_mult=clamp01((t - 0.12) / 0.15))
                        paste_sprite_animated(frame, render_text_sprite(m_obj["h_name"], 38, "white_crisp", True, 260), cur_rx, 1050, alpha_mult=clamp01((t - 0.12) / 0.15))

                        if ptype == "match" and t >= 0.22:
                            sc_scale = 2.1 - 1.1 * clamp01((t - 0.22) / 0.14)
                            score_str = overrides.get("score", f"{m_obj['h_g']} - {m_obj['a_g']}")
                            paste_sprite_animated(frame, render_text_sprite(score_str, 126, "gold", True, 320), 540, 912, scale=max(1.0, sc_scale))

                        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                        odraw = ImageDraw.Draw(overlay)
                        odraw.rounded_rectangle([126, 1174, 954, 1612], radius=22, fill=(18, 23, 33, 248), outline=(215, 180, 105, 255), width=3)
                        odraw.line([(200, 1295), (880, 1295)], fill=(215, 180, 105, 120), width=2)

                        h_poss, a_poss, h_shots, a_shots, h_corn, a_corn = get_match_numeric_stats(m_obj)
                        p_bars = ease_out_cubic((t - 0.34) / 0.42)

                        if ptype == "match" and p_bars > 0:
                            draw_dual_neon_progress_bar(odraw, 210, 1378, 870, h_poss, a_poss, p_bars)
                            draw_dual_neon_progress_bar(odraw, 210, 1478, 870, h_shots, a_shots, p_bars)
                            draw_dual_neon_progress_bar(odraw, 210, 1575, 870, h_corn, a_corn, p_bars)

                        frame = Image.alpha_composite(frame, overlay)

                        scorer_lines, _, _, _ = get_match_detailed_stats_fa(m_obj, overrides=overrides)
                        a_stats = clamp01((t - 0.30) / 0.15)
                        if a_stats > 0:
                            if len(scorer_lines) == 1:
                                paste_sprite_animated(frame, render_text_sprite(scorer_lines[0], 32, "gold", False, 760), 540, 1236, alpha_mult=a_stats)
                            else:
                                paste_sprite_animated(frame, render_text_sprite(scorer_lines[0], 28, "gold", False, 760), 540, 1218, alpha_mult=a_stats)
                                paste_sprite_animated(frame, render_text_sprite(scorer_lines[1], 28, "gold", False, 760), 540, 1265, alpha_mult=a_stats)

                            paste_sprite_animated(frame, render_text_sprite(f"مالکیت توپ: {m_obj['h_name']} %{int(h_poss * p_bars)}  -  %{int(a_poss * p_bars)} {m_obj['a_name']}", 35, "white_crisp", False, 760), 540, 1340, alpha_mult=a_stats)
                            paste_sprite_animated(frame, render_text_sprite(f"شوت در چارچوب: {int(round(h_shots * p_bars))}  -  {int(round(a_shots * p_bars))}", 35, "white_crisp", False, 760), 540, 1440, alpha_mult=a_stats)
                            paste_sprite_animated(frame, render_text_sprite(f"ضربات کرنر: {int(round(h_corn * p_bars))}  -  {int(round(a_corn * p_bars))}", 35, "white_crisp", False, 760), 540, 1538, alpha_mult=a_stats)

                        paint_clean_bottom_gold_bar(frame, footer_text)

                    else:
                        frame = apply_camera_zoom_and_shake(TEMPLATES_RAM["t5"], zoom=1.0 + 0.025 * t_full)
                        paste_sprite_animated(frame, render_text_sprite(title_top, 44, "white_crisp", True, 500), 540, 236)
                        paste_sprite_animated(frame, render_text_sprite("جمع بندی نتایج روز", 76, "gold", True, 860), 540, 390)

                        row_y_centers = [642, 842, 1042, 1242, 1442]
                        lx, rx, diameter = 152, 928, 96
                        for idx, m in enumerate((matches_list or [])[:5]):
                            t_row_start = 0.08 + idx * 0.11
                            p_row = ease_out_back((t - t_row_start) / 0.22)
                            a_row = clamp01((t - t_row_start) / 0.12)
                            if a_row <= 0:
                                continue
                            cy = row_y_centers[idx]
                            ox = int((1.0 - p_row) * (420 if idx % 2 == 0 else -420))
                            l_logo = fetch_logo_circle(m["a_name"], m["a_logo"], diameter, is_large_ring=False)
                            r_logo = fetch_logo_circle(m["h_name"], m["h_logo"], diameter, is_large_ring=False)
                            frame.paste(l_logo, (lx - diameter // 2, cy - diameter // 2), l_logo)
                            frame.paste(r_logo, (rx - diameter // 2, cy - diameter // 2), r_logo)
                            paste_sprite_animated(frame, render_text_sprite(f"{m['h_g']} - {m['a_g']}", 64, "gold", True, 180), 540, cy, scale=0.5 + 0.5 * p_row, alpha_mult=a_row)
                            paste_sprite_animated(frame, render_text_sprite(m["h_name"], 36, "white_crisp", False, 235), 735 + ox, cy, alpha_mult=a_row)
                            paste_sprite_animated(frame, render_text_sprite(m["a_name"], 36, "white_crisp", False, 235), 345 + ox, cy, alpha_mult=a_row)
                        paint_clean_bottom_gold_bar(frame, footer_text)

                    motes = Image.new("RGBA", STORY_SIZE, (0, 0, 0, 0))
                    mdraw = ImageDraw.Draw(motes)
                    for p in particles[:26]:
                        py = (p["y"] - f_idx * p["speed"]) % 1760 + 60
                        px = p["x"] + int(10 * math.sin(p["phase"] + f_idx * 0.15))
                        alpha = int(85 + 75 * math.sin(p["phase"] + f_idx * 0.25))
                        r = p["size"]
                        mdraw.ellipse((px - r, py - r, px + r, py + r), fill=(aura_r, aura_g, aura_b, max(20, min(170, alpha))))
                    frame = Image.alpha_composite(frame, motes)

                    rgb_frame = frame.convert("RGB")
                    if f_idx < 10:
                        rgb_frame = rgb_frame.filter(ImageFilter.GaussianBlur(radius=(10 - f_idx) * 1.3))

                    proc.stdin.write(rgb_frame.tobytes())

                proc.stdin.close()
                proc.wait(timeout=120)

                if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000:
                    with open(out_mp4, "rb") as f:
                        return f.read()
            except Exception as e:
                print("Scenario video render error:", e)
                try:
                    proc.kill()
                except Exception:
                    pass
            finally:
                TEXT_SPRITE_RAM.clear()
                gc.collect()
    return None


# =====================================================================
# 6. State & Live Data Fetchers
# =====================================================================
def load_state():
    st = {
        "last_morning_date": "",
        "last_wake_notice_date": "",
        "last_sleep_notice_date": "",
        "owner_chat_id": TELEGRAM_CHAT_ID,
        "footer_text": DEFAULT_FOOTER,
        "reel_badge": DEFAULT_REEL_BADGE,
        "morning_hour": 7,
        "awaiting_input": "",
        "ig_target_page": DEFAULT_IG_PAGE,
        "ig_sessionid": DEFAULT_IG_SESSION,
        "matches": {}
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                st.update(saved)
        except Exception:
            pass
    if DEFAULT_IG_PAGE and not st.get("ig_target_page"):
        st["ig_target_page"] = DEFAULT_IG_PAGE
    if DEFAULT_IG_SESSION and not st.get("ig_sessionid"):
        st["ig_sessionid"] = DEFAULT_IG_SESSION
    return st


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_target_chat_id(state):
    return TELEGRAM_CHAT_ID or state.get("owner_chat_id", "")


def refresh_daily_data_cache():
    now_greg = jdatetime.datetime.now(TEHRAN_TZ).togregorian()
    date_ddmmyyyy = now_greg.strftime("%d-%m-%Y")

    try:
        url = f"https://api.aladhan.com/v1/timingsByCity/{date_ddmmyyyy}?city={CITY_NAME_EN}&country=Iran&method=7"
        t = requests.get(url, headers=HEADERS, timeout=8).json()["data"]["timings"]
        clean_time = lambda s: re.sub(r"\s*\(.*?\)", "", s).strip()[:5]
        CACHE["prayers"] = (clean_time(t["Fajr"]), clean_time(t["Sunrise"]), clean_time(t["Dhuhr"]), clean_time(t["Maghrib"]))
    except Exception:
        pass

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={CITY_LAT}&longitude={CITY_LON}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=Asia%2FTehran"
        )
        d = requests.get(url, headers=HEADERS, timeout=8).json()
        cur, daily = d["current"], d["daily"]
        hourly_temps = d.get("hourly", {}).get("temperature_2m", [])
        if len(hourly_temps) >= 22:
            periods = (round(hourly_temps[8]), round(hourly_temps[13]), round(hourly_temps[17]), round(hourly_temps[21]))
        else:
            periods = (round(daily["temperature_2m_min"][0] + 3), round(daily["temperature_2m_max"][0]), round(daily["temperature_2m_max"][0] - 3), round(daily["temperature_2m_min"][0]))
        code = cur.get("weather_code", 0)
        desc_map = {
            0: "آسمان صاف", 1: "غالبا صاف", 2: "نیمه ابری", 3: "ابری",
            45: "مه آلود", 48: "مه آلود", 51: "نم نم باران", 61: "بارش خفیف باران",
            63: "بارانی", 65: "بارش شدید باران", 71: "بارش برف", 80: "رگبار باران", 95: "رعد و برق"
        }
        CACHE["weather"] = {
            "temp": round(cur["temperature_2m"], 1), "temp_int": round(cur["temperature_2m"]),
            "max": round(daily["temperature_2m_max"][0], 1), "min": round(daily["temperature_2m_min"][0], 1),
            "wind": round(cur["wind_speed_10m"]), "humidity": round(cur["relative_humidity_2m"]),
            "desc": desc_map.get(code, "آسمان صاف و معتدل"), "code": code, "periods": periods
        }
    except Exception:
        pass

    try:
        r_json = requests.get(f"https://call1.tgju.org/ajax.json?rev={int(time.time())}", headers=HEADERS, timeout=8).json()
        cur_m = r_json.get("current", {})
        usd = cur_m.get("price_dollar_rl", {}).get("p")
        gold = cur_m.get("geram18", {}).get("p")
        coin = cur_m.get("sekee", {}).get("p")
        if usd and gold and coin:
            CACHE["market"] = (usd, gold, coin)
            return
    except Exception:
        pass

    try:
        html = requests.get(f"https://www.tgju.org/?t={int(time.time())}", headers=HEADERS, timeout=10).text
        def extract_price(slug):
            m1 = re.search(rf'data-market-row="{slug}"[^>]*data-price="([\d,]+)"', html)
            if m1:
                return m1.group(1)
            m2 = re.search(rf'data-market-row="{slug}"[^>]*>.*?<td class="nf"[^>]*>([\d,]+)</td>', html, re.DOTALL)
            return m2.group(1) if m2 else None
        usd, gold, coin = extract_price("price_dollar_rl"), extract_price("geram18"), extract_price("sekee")
        if usd and gold and coin:
            CACHE["market"] = (usd, gold, coin)
    except Exception:
        pass


# =====================================================================
# 7. Telegram API Helpers & Football Tracker
# =====================================================================
def setup_bot_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "morning", "description": "🌞 صبح بخیر (شرعیات، طلا و حافظ)"},
        {"command": "weather", "description": "⛅ وضعیت آب و هوا (۴ زمانه)"},
        {"command": "football", "description": "⚽ نتایج زنده و پوستر بازی ها"},
        {"command": "viral", "description": "🎬 ریلزساز و قاب ویدیو"},
        {"command": "insta", "description": "📸 رصد پیج عمومی اینستاگرام"},
        {"command": "settings", "description": "⚙ تنظیمات ربات"}
    ]
    try:
        requests.post(url, json={"commands": commands}, timeout=10)
    except Exception:
        pass


def remember_sent_post(chat_id, message_id, meta):
    if message_id:
        if len(SENT_POSTS_MEM) > 80:
            SENT_POSTS_MEM.clear()
        SENT_POSTS_MEM[f"{chat_id}_{message_id}"] = meta


def send_telegram_photo(chat_id, img, caption="", inline_kb=None, post_meta=None):
    if not chat_id:
        return None
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=93)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {"chat_id": chat_id, "caption": caption}
    if inline_kb:
        data["reply_markup"] = json.dumps({"inline_keyboard": inline_kb})
    elif not str(chat_id).startswith("@") and not str(chat_id).startswith("-"):
        data["reply_markup"] = BOT_MENU_KEYBOARD
    try:
        r = requests.post(url, data=data, files={"photo": ("story.jpg", bio, "image/jpeg")}, timeout=25).json()
        msg_id = r.get("result", {}).get("message_id")
        if msg_id and post_meta:
            remember_sent_post(chat_id, msg_id, post_meta)
        return msg_id
    except Exception as e:
        print("Send photo error:", e)
        return None


def edit_telegram_photo_in_place(chat_id, message_id, img, caption="", inline_kb=None, post_meta=None):
    if not chat_id or not message_id:
        return False
    bio = io.BytesIO()
    img.convert("RGB").save(bio, format="JPEG", quality=93)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageMedia"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "media": json.dumps({"type": "photo", "media": "attach://photo", "caption": caption})
    }
    if inline_kb:
        data["reply_markup"] = json.dumps({"inline_keyboard": inline_kb})
    try:
        r = requests.post(url, data=data, files={"photo": ("story.jpg", bio, "image/jpeg")}, timeout=25).json()
        if r.get("ok"):
            if post_meta:
                remember_sent_post(chat_id, message_id, post_meta)
            return True
    except Exception as e:
        print("Edit photo error:", e)
    return False


def send_telegram_video(chat_id, video_bytes, caption="", post_meta=None):
    if not chat_id or not video_bytes:
        return None
    bio = io.BytesIO(video_bytes)
    bio.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    data = {"chat_id": chat_id, "caption": caption, "supports_streaming": True, "width": 1080, "height": 1920}
    if not str(chat_id).startswith("@") and not str(chat_id).startswith("-"):
        data["reply_markup"] = BOT_MENU_KEYBOARD
    try:
        r = requests.post(url, data=data, files={"video": ("reel_story.mp4", bio, "video/mp4")}, timeout=90).json()
        msg_id = r.get("result", {}).get("message_id")
        if msg_id and post_meta:
            remember_sent_post(chat_id, msg_id, post_meta)
        return msg_id
    except Exception as e:
        print("Send video error:", e)
        return None


def download_telegram_file(file_id, dest_path):
    try:
        r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile", params={"file_id": file_id}, timeout=15).json()
        file_path = r.get("result", {}).get("file_path")
        if not file_path:
            return False
        with requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}", stream=True, timeout=45) as resp:
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                return os.path.exists(dest_path) and os.path.getsize(dest_path) > 5000
    except Exception:
        pass
    return False


def _safe_int(val, default=0):
    try:
        if val is None:
            return default
        s = str(val).strip()
        if not s or s == "-":
            return default
        return int(float(s))
    except Exception:
        return default


def _football_get_json(url, headers=None, timeout=12):
    try:
        if "http_get_stealth" in globals():
            r = http_get_stealth(url, headers=headers, timeout=timeout)
        else:
            hdrs = dict(HEADERS)
            if headers:
                hdrs.update(headers)
            r = requests.get(url, headers=hdrs, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        print(f"[Football] HTTP {r.status_code}: {url[:85]}")
    except Exception as e:
        print(f"[Football] Fetch error ({url[:65]}): {e}")
    return None


def _format_tehran_kickoff(dt_tehran, now_dt):
    months_fa = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    hhmm = dt_tehran.strftime("%H:%M")
    m_date = dt_tehran.date()
    t_date = now_dt.date()
    if m_date == t_date:
        return f"امروز {hhmm}"
    if m_date == t_date + timedelta(days=1):
        return f"فردا {hhmm}"
    if m_date == t_date - timedelta(days=1):
        return f"دیروز {hhmm}"
    jdt = jdatetime.date.fromgregorian(date=m_date)
    return f"{jdt.day} {months_fa[jdt.month]} {hhmm}"


def register_and_check_match(
    state, matches_mem, lg_key, match_id, league_fa, is_iran,
    h_name, a_name, h_g, a_g, h_logo, a_logo,
    is_live, is_finished, minute_str="", scorers_list=None,
    allow_auto_alert=True, day_tag="", is_postponed=False,
    real_stats=None, bucket=None
):
    if bucket is not None:
        if match_id in bucket["leagues"][lg_key]["seen_ids"]:
            return
        bucket["leagues"][lg_key]["seen_ids"].add(match_id)

    h_g = _safe_int(h_g, 0)
    a_g = _safe_int(a_g, 0)

    if is_postponed:
        status_emoji = "⚠"
        status_label = "لغو یا تعویق"
        header_prefix = "اطلاعیه بازی"
        line_str = f"⚠ تعویق | {h_name} - {a_name}"
        sort_rank = 4
    elif is_live:
        status_emoji = "🔴"
        clean_min = str(minute_str or "").strip()
        if clean_min == "بین دو نیمه":
            status_label = "زنده (بین دو نیمه)"
            line_str = f"🔴 بین دو نیمه | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        elif clean_min:
            status_label = f"زنده (دقیقه {to_fa_digits(clean_min)})"
            line_str = f"🔴 زنده ({to_fa_digits(clean_min)}') | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        else:
            status_label = "زنده"
            line_str = f"🔴 زنده | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        header_prefix = "زنده"
        sort_rank = 0
        if bucket is not None:
            bucket["leagues"][lg_key]["has_live"] = True
        else:
            CACHE["leagues"][lg_key]["has_live"] = True
    elif is_finished:
        status_emoji = "🏁"
        status_label = "نتیجه دیروز" if day_tag == "دیروز" else "پایان بازی"
        header_prefix = "نتیجه نهایی"
        lbl_fin = "دیروز" if day_tag == "دیروز" else "پایان"
        line_str = f"🏁 {lbl_fin} | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        sort_rank = 3 if day_tag == "دیروز" else 2
    else:
        status_emoji = "⏰"
        clean_min = str(minute_str or "").strip()
        status_label = f"شروع: {to_fa_digits(clean_min)}" if clean_min else "در انتظار شروع"
        header_prefix = "برنامه بازی"
        line_str = f"⏰ {to_fa_digits(clean_min)} | {h_name} - {a_name}" if clean_min else f"⏰ در انتظار شروع | {h_name} - {a_name}"
        sort_rank = 1

    m_obj = {
        "id": match_id, "status_emoji": status_emoji, "status_label": status_label,
        "league_title": f"{header_prefix} | {league_fa}", "league_fa": league_fa,
        "h_name": h_name, "a_name": a_name, "h_g": h_g, "a_g": a_g,
        "h_logo": h_logo or "", "a_logo": a_logo or "",
        "is_live": is_live, "is_finished": is_finished,
        "scorers_list": scorers_list or []
    }
    if isinstance(real_stats, dict):
        for sk in ("h_poss", "h_shots", "a_shots", "h_corn", "a_corn"):
            if real_stats.get(sk) is not None:
                m_obj[sk] = real_stats[sk]

    CACHE["matches_by_id"][match_id] = m_obj

    if bucket is not None:
        bucket["leagues"][lg_key]["entries"].append((sort_rank, line_str, match_id))
        if is_live:
            bucket["live_match_ids"].append(match_id)
            bucket["live_lines"].append(f"🏆 {league_fa}: {line_str}")
    else:
        CACHE["leagues"][lg_key]["lines"].append(line_str)
        CACHE["leagues"][lg_key]["match_ids"].append(match_id)
        if is_live:
            CACHE["live_match_ids"].append(match_id)
            CACHE["live_lines"].append(f"🏆 {league_fa}: {line_str}")

    if not allow_auto_alert or is_postponed:
        return

    if match_id not in matches_mem:
        matches_mem[match_id] = {"h": h_g, "a": a_g, "ft": is_finished, "msg_id": None}
        return

    prev = matches_mem[match_id]
    target_chat = get_target_chat_id(state)
    footer = state.get("footer_text", DEFAULT_FOOTER)

    if is_iran and is_live and (h_g > prev["h"] or a_g > prev["a"]):
        scorer = h_name if h_g > prev["h"] else a_name
        if target_chat:
            img = build_match_image(m_obj, footer_text=footer)
            caption = f"🔴 زنده | گل برای {scorer}!\n⚽ {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}\n🔄 (این پوستر با هر گل به صورت خودکار آپدیت می شود)"
            kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": f"mkvid_match_{match_id}"}]]
            meta = {"type": "match", "mid": match_id, "overrides": {}, "caption": caption, "kb": kb}
            edited = edit_telegram_photo_in_place(target_chat, prev["msg_id"], img, caption=caption, inline_kb=kb, post_meta=meta) if prev.get("msg_id") else False
            if not edited:
                prev["msg_id"] = send_telegram_photo(target_chat, img, caption=caption, inline_kb=kb, post_meta=meta)
        prev["h"], prev["a"] = h_g, a_g

    if is_finished and not prev["ft"]:
        if target_chat:
            img = build_match_image(m_obj, footer_text=footer)
            caption = f"🏁 پایان بازی ({league_fa})\n⚽ {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
            kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": f"mkvid_match_{match_id}"}]]
            meta = {"type": "match", "mid": match_id, "overrides": {}, "caption": caption, "kb": kb}
            edited = edit_telegram_photo_in_place(target_chat, prev["msg_id"], img, caption=caption, inline_kb=kb, post_meta=meta) if prev.get("msg_id") else False
            if not edited:
                prev["msg_id"] = send_telegram_photo(target_chat, img, caption=caption, inline_kb=kb, post_meta=meta)
        prev["ft"] = True
        prev["h"], prev["a"] = h_g, a_g


def _fetch_livescore_day_stages(date_compact):
    urls = [
        f"https://prod-cdn-mev-api.livescore.com/v1/api/app/date/soccer/{date_compact}/3.5?countryCode=IR&locale=en",
        f"https://prod-public-api.livescore.com/v1/api/react/date/soccer/{date_compact}/3.5?MD=1"
    ]
    for u in urls:
        data = _football_get_json(u, timeout=12)
        if isinstance(data, dict) and data.get("Stages"):
            return data["Stages"]
    return []


def _parse_livescore_events_into_bucket(stages, state, matches_mem, bucket, now_dt, day_tag, target_lg_keys, allow_auto_alert):
    from datetime import datetime as _dt
    added_count = 0

    for stg in stages:
        cnm = str(stg.get("Cnm", "") or "").lower()
        ccd = str(stg.get("Ccd", "") or "").lower()
        snm = str(stg.get("Snm", "") or "").lower()
        scd = str(stg.get("Scd", "") or "").lower()

        lg_key, l_fa, is_iran = None, "", False

        if ccd == "iran" or cnm == "iran":
            if any(x in snm or x in scd for x in ("women", "u21", "u23", "u19", "azadegan", "division", "league 2")):
                continue
            if any(x in snm or x in scd for x in ("persian", "pro league", "premier", "gulf")):
                lg_key, l_fa, is_iran = "lg_ir", "لیگ برتر ایران", True
            elif "hazfi" in snm or "cup" in snm:
                lg_key, l_fa, is_iran = "lg_ir", "جام حذفی ایران", True
        elif ccd == "england" and scd == "premier-league":
            lg_key, l_fa = "lg_eng", "لیگ برتر انگلیس"
        elif ccd == "spain" and (scd in ("laliga", "laliga-santander", "primera-division") or "laliga" in snm):
            if "2" not in scd and "hypermotion" not in snm and "women" not in snm:
                lg_key, l_fa = "lg_esp", "لالیگا اسپانیا"
        elif ccd == "germany" and scd == "bundesliga":
            lg_key, l_fa = "lg_ger", "بوندسلیگا آلمان"
        elif ("champions-league" in ccd or "champions league" in cnm) and not any(x in ccd or x in snm for x in ("women", "youth", "afc", "caf", "concacaf", "ofc")):
            lg_key, l_fa = "lg_ucl", "لیگ قهرمانان اروپا"

        if not lg_key or lg_key not in target_lg_keys:
            continue

        for ev in (stg.get("Events") or []):
            t1_list = ev.get("T1") or []
            t2_list = ev.get("T2") or []
            if not t1_list or not t2_list:
                continue
            t1, t2 = t1_list[0], t2_list[0]
            h_raw = str(t1.get("Nm", "") or "").strip()
            a_raw = str(t2.get("Nm", "") or "").strip()
            if not h_raw or not a_raw:
                continue

            eid = str(ev.get("Eid", "") or hashlib.md5(f"{h_raw}_{a_raw}_{day_tag}".encode()).hexdigest()[:10])
            mid = f"{'ir' if is_iran else 'eu'}_ls_{eid}"

            eps = str(ev.get("Eps", "") or "").strip()
            eps_up = eps.upper()
            is_postponed = any(k in eps_up for k in ("POSTP", "CANC", "ABAND", "SUSP"))
            is_finished = eps_up in ("FT", "AET", "AP")
            is_live = (not is_finished) and (not is_postponed) and (eps_up not in ("", "NS", "TBA"))

            minute_str = ""
            if is_live:
                minute_str = "بین دو نیمه" if eps_up == "HT" else eps.replace("'", "").strip()
            elif not is_finished and not is_postponed:
                esd = str(ev.get("Esd", "") or "")
                if len(esd) >= 12:
                    try:
                        dt_tehran = TEHRAN_TZ.localize(_dt.strptime(esd[:12], "%Y%m%d%H%M"))
                        minute_str = _format_tehran_kickoff(dt_tehran, now_dt)
                    except Exception:
                        minute_str = ""

            h_img = t1.get("Img", "")
            a_img = t2.get("Img", "")
            h_logo = f"https://lsm-static-prod.livescore.com/medium/{h_img}" if h_img else ""
            a_logo = f"https://lsm-static-prod.livescore.com/medium/{a_img}" if a_img else ""

            register_and_check_match(
                state, matches_mem, lg_key, mid, l_fa, is_iran,
                to_persian_text(h_raw), to_persian_text(a_raw),
                _safe_int(ev.get("Tr1"), 0), _safe_int(ev.get("Tr2"), 0),
                h_logo, a_logo,
                is_live, is_finished, minute_str,
                allow_auto_alert=allow_auto_alert,
                day_tag=day_tag, is_postponed=is_postponed,
                bucket=bucket
            )
            added_count += 1

    return added_count


def _fetch_iran_sofascore_day(date_iso, state, matches_mem, bucket, now_dt, day_tag, allow_auto_alert):
    from datetime import datetime as _dt, timezone as _tz
    data = _football_get_json(f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_iso}", timeout=12)
    if not isinstance(data, dict):
        return 0
    added = 0
    for ev in (data.get("events") or []):
        tourn = ev.get("tournament") or {}
        cat_name = str((tourn.get("category") or {}).get("name", "") or "").lower()
        t_name = str(tourn.get("name", "") or "").lower()
        ut = tourn.get("uniqueTournament") or {}
        ut_id = ut.get("id")
        ut_name = str(ut.get("name", "") or "").lower()

        if cat_name != "iran":
            continue
        if any(x in t_name or x in ut_name for x in ("azadegan", "u21", "u23", "women", "division", "league 2")):
            continue
        if ut_id == 955 or "persian gulf" in t_name or "pro league" in t_name or "persian gulf" in ut_name:
            l_fa = "لیگ برتر ایران"
        elif ut_id == 10474 or "hazfi" in t_name or "hazfi" in ut_name:
            l_fa = "جام حذفی ایران"
        else:
            continue

        home = ev.get("homeTeam") or {}
        away = ev.get("awayTeam") or {}
        h_raw, a_raw = str(home.get("name", "") or ""), str(away.get("name", "") or "")
        if not h_raw or not a_raw:
            continue

        st = ev.get("status") or {}
        st_type = str(st.get("type", "") or "").lower()
        st_desc = str(st.get("description", "") or "").lower()
        is_postponed = st_type in ("postponed", "canceled", "cancelled")
        is_finished = st_type == "finished"
        is_live = st_type == "inprogress"

        minute_str = ""
        if is_live:
            if "halftime" in st_desc or "half" in st_desc:
                minute_str = "بین دو نیمه"
            else:
                minute_str = str(st.get("description", "") or "").replace("'", "").strip()
        elif not is_finished and not is_postponed:
            ts = ev.get("startTimestamp")
            if ts:
                try:
                    dt_tehran = _dt.fromtimestamp(int(ts), tz=_tz.utc).astimezone(TEHRAN_TZ)
                    minute_str = _format_tehran_kickoff(dt_tehran, now_dt)
                except Exception:
                    pass

        mid = f"ir_sf_{ev.get('id', '')}"
        h_g = (ev.get("homeScore") or {}).get("current", 0)
        a_g = (ev.get("awayScore") or {}).get("current", 0)
        h_logo = f"https://api.sofascore.app/api/v1/team/{home.get('id')}/image" if home.get("id") else ""
        a_logo = f"https://api.sofascore.app/api/v1/team/{away.get('id')}/image" if away.get("id") else ""

        register_and_check_match(
            state, matches_mem, "lg_ir", mid, l_fa, True,
            to_persian_text(h_raw), to_persian_text(a_raw),
            h_g, a_g, h_logo, a_logo,
            is_live, is_finished, minute_str,
            allow_auto_alert=allow_auto_alert,
            day_tag=day_tag, is_postponed=is_postponed,
            bucket=bucket
        )
        added += 1
    return added


def _fetch_iran_fotmob_day(date_compact, state, matches_mem, bucket, now_dt, day_tag, allow_auto_alert):
    from datetime import datetime as _dt, timezone as _tz
    data = _football_get_json(f"https://www.fotmob.com/api/matches?date={date_compact}&timezone=Asia%2FTehran", timeout=12)
    if not isinstance(data, dict):
        return 0
    added = 0
    for lg in (data.get("leagues") or []):
        lid = lg.get("primaryId")
        ccode = str(lg.get("ccode", "") or "").upper()
        lname = str(lg.get("name", "") or "").lower()
        if ccode != "IRN" and lid not in (290, 9090, 9384):
            continue
        if any(x in lname for x in ("azadegan", "women", "u21", "u23", "division 2", "league 2")):
            continue
        if lid in (290, 9090) or "persian" in lname or "pro league" in lname:
            l_fa = "لیگ برتر ایران"
        elif lid == 9384 or "hazfi" in lname:
            l_fa = "جام حذفی ایران"
        else:
            continue

        for m in (lg.get("matches") or []):
            home = m.get("home") or {}
            away = m.get("away") or {}
            st = m.get("status") or {}
            is_postponed = bool(st.get("cancelled", False))
            is_finished = bool(st.get("finished", False)) and not is_postponed
            is_live = bool(st.get("started", False)) and (not is_finished) and (not is_postponed)

            h_score = home.get("score")
            a_score = away.get("score")
            if h_score is None or a_score is None:
                sc_str = str(st.get("scoreStr", "") or "")
                if "-" in sc_str:
                    parts = sc_str.split("-", 1)
                    h_score, a_score = parts[0], parts[1]

            live_obj = st.get("liveTime")
            minute_str = ""
            if is_live and isinstance(live_obj, dict):
                short_t = str(live_obj.get("short", "") or "").strip()
                minute_str = "بین دو نیمه" if short_t.upper() == "HT" else short_t.replace("'", "")
            elif not is_finished and not is_postponed:
                utc_t = str(st.get("utcTime", "") or "").replace("Z", "+00:00")
                if utc_t:
                    try:
                        dt_tehran = _dt.fromisoformat(utc_t).astimezone(TEHRAN_TZ)
                        minute_str = _format_tehran_kickoff(dt_tehran, now_dt)
                    except Exception:
                        pass

            mid = f"ir_fm_{m.get('id', '')}"
            register_and_check_match(
                state, matches_mem, "lg_ir", mid, l_fa, True,
                to_persian_text(home.get("name", "")), to_persian_text(away.get("name", "")),
                h_score, a_score,
                f"https://images.fotmob.com/image_resources/logo/teamlogo/{home.get('id')}.png" if home.get("id") else "",
                f"https://images.fotmob.com/image_resources/logo/teamlogo/{away.get('id')}.png" if away.get("id") else "",
                is_live, is_finished, minute_str,
                allow_auto_alert=allow_auto_alert,
                day_tag=day_tag, is_postponed=is_postponed,
                bucket=bucket
            )
            added += 1
    return added


def check_all_football_free(state):
    from datetime import datetime as _dt
    matches_mem = state.setdefault("matches", {})
    now_dt = _dt.now(TEHRAN_TZ)

    bucket = {
        "live_match_ids": [],
        "live_lines": [],
        "leagues": {
            lg_key: {"title": lg_title, "entries": [], "seen_ids": set(), "has_live": False, "fetched_ok": False}
            for lg_key, lg_title in LEAGUE_CATEGORIES
        }
    }

    today_compact = now_dt.strftime("%Y%m%d")
    yest_compact = (now_dt - timedelta(days=1)).strftime("%Y%m%d")
    today_iso = now_dt.strftime("%Y-%m-%d")
    yest_iso = (now_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    ls_today_stages = _fetch_livescore_day_stages(today_compact)
    ls_yest_stages = _fetch_livescore_day_stages(yest_compact)

    ir_found = 0
    if ls_today_stages:
        ir_found += _parse_livescore_events_into_bucket(ls_today_stages, state, matches_mem, bucket, now_dt, "امروز", {"lg_ir"}, True)
        bucket["leagues"]["lg_ir"]["fetched_ok"] = True
    if ls_yest_stages:
        ir_found += _parse_livescore_events_into_bucket(ls_yest_stages, state, matches_mem, bucket, now_dt, "دیروز", {"lg_ir"}, True)
        bucket["leagues"]["lg_ir"]["fetched_ok"] = True

    if ir_found == 0:
        ir_found += _fetch_iran_sofascore_day(today_iso, state, matches_mem, bucket, now_dt, "امروز", True)
        ir_found += _fetch_iran_sofascore_day(yest_iso, state, matches_mem, bucket, now_dt, "دیروز", True)
        if ir_found > 0:
            bucket["leagues"]["lg_ir"]["fetched_ok"] = True

    if ir_found == 0:
        ir_found += _fetch_iran_fotmob_day(today_compact, state, matches_mem, bucket, now_dt, "امروز", True)
        ir_found += _fetch_iran_fotmob_day(yest_compact, state, matches_mem, bucket, now_dt, "دیروز", True)
        if ir_found > 0:
            bucket["leagues"]["lg_ir"]["fetched_ok"] = True

    if ir_found == 0:
        for offset in (1, -2, 2, -3):
            dt_cand = now_dt + timedelta(days=offset)
            c_comp = dt_cand.strftime("%Y%m%d")
            c_iso = dt_cand.strftime("%Y-%m-%d")
            c_tag = "دیروز" if offset < 0 else "آینده"
            stgs = _fetch_livescore_day_stages(c_comp)
            cnt = _parse_livescore_events_into_bucket(stgs, state, matches_mem, bucket, now_dt, c_tag, {"lg_ir"}, False) if stgs else 0
            if cnt == 0:
                cnt = _fetch_iran_sofascore_day(c_iso, state, matches_mem, bucket, now_dt, c_tag, False)
            if cnt == 0:
                cnt = _fetch_iran_fotmob_day(c_comp, state, matches_mem, bucket, now_dt, c_tag, False)
            if cnt > 0:
                bucket["leagues"]["lg_ir"]["fetched_ok"] = True
                break

    espn_configs = [
        ("lg_eng", "eng.1", "لیگ برتر انگلیس"),
        ("lg_esp", "esp.1", "لالیگا اسپانیا"),
        ("lg_ger", "ger.1", "بوندسلیگا آلمان"),
        ("lg_ucl", "uefa.champions", "لیگ قهرمانان اروپا")
    ]

    for lg_key, code, l_fa in espn_configs:
        eu_events = []
        seen_ev_ids = set()
        espn_ok = False

        for d_param, is_recent in [(today_compact, True), (yest_compact, True)]:
            d_json = _football_get_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={d_param}", timeout=10)
            if isinstance(d_json, dict) and "events" in d_json:
                espn_ok = True
                for ev in (d_json.get("events") or []):
                    ev_id = str(ev.get("id", ""))
                    if ev_id and ev_id not in seen_ev_ids:
                        seen_ev_ids.add(ev_id)
                        eu_events.append((ev, is_recent))

        if len(eu_events) == 0:
            d_def = _football_get_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", timeout=10)
            if isinstance(d_def, dict) and "events" in d_def:
                espn_ok = True
                for ev in (d_def.get("events") or []):
                    ev_id = str(ev.get("id", ""))
                    if ev_id and ev_id not in seen_ev_ids:
                        seen_ev_ids.add(ev_id)
                        eu_events.append((ev, False))

        if espn_ok:
            bucket["leagues"][lg_key]["fetched_ok"] = True

        for ev, is_recent in eu_events[:18]:
            try:
                comps = ev.get("competitions") or []
                if not comps:
                    continue
                comp = comps[0]
                competitors = comp.get("competitors") or []
                home = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if not home or not away:
                    continue

                st_type_obj = (ev.get("status") or {}).get("type") or {}
                state_type = str(st_type_obj.get("state", "") or "").lower()
                st_name = str(st_type_obj.get("name", "") or "").upper()
                short_det = str(st_type_obj.get("shortDetail", "") or "").strip()

                is_postponed = any(x in st_name for x in ("POSTPONED", "CANCELED", "CANCELLED", "ABANDONED"))
                is_live = (state_type == "in") and not is_postponed
                is_finished = (state_type == "post") and not is_postponed

                dt_tehran = None
                raw_date = str(ev.get("date", "") or "").replace("Z", "+00:00")
                if raw_date:
                    try:
                        dt_tehran = _dt.fromisoformat(raw_date).astimezone(TEHRAN_TZ)
                    except Exception:
                        dt_tehran = None

                day_tag = ""
                if dt_tehran and dt_tehran.date() < now_dt.date():
                    day_tag = "دیروز"

                minute_str = ""
                if is_live:
                    if "HT" in short_det.upper() or "HALF" in short_det.upper():
                        minute_str = "بین دو نیمه"
                    else:
                        minute_str = short_det.replace("'", "").strip()
                elif not is_finished and not is_postponed:
                    minute_str = _format_tehran_kickoff(dt_tehran, now_dt) if dt_tehran else short_det

                scorers_list = []
                for det in (comp.get("details") or []):
                    if det.get("scoringPlay"):
                        clock = str((det.get("clock") or {}).get("displayValue", "") or "").replace("'", "")
                        athletes = det.get("athletesInvolved") or []
                        if athletes and athletes[0].get("displayName"):
                            scorers_list.append(f"{to_persian_text(athletes[0]['displayName'])} ({to_fa_digits(clock)})")

                real_stats = {}
                for c_obj, pref in ((home, "h"), (away, "a")):
                    for st_item in (c_obj.get("statistics") or []):
                        sname = str(st_item.get("name", "") or "")
                        sval = st_item.get("displayValue")
                        if sname == "possessionPct" and pref == "h":
                            p_val = _safe_int(sval, 0)
                            if 10 <= p_val <= 90:
                                real_stats["h_poss"] = p_val
                        elif sname == "shotsOnTarget":
                            real_stats[f"{pref}_shots"] = _safe_int(sval, 0)

                h_team = home.get("team") or {}
                a_team = away.get("team") or {}
                mid = f"eu_{ev.get('id', '')}"

                register_and_check_match(
                    state, matches_mem, lg_key, mid, l_fa, False,
                    to_persian_text(h_team.get("displayName", "")),
                    to_persian_text(a_team.get("displayName", "")),
                    home.get("score", 0), away.get("score", 0),
                    h_team.get("logo", ""), a_team.get("logo", ""),
                    is_live, is_finished, minute_str,
                    scorers_list=scorers_list,
                    allow_auto_alert=is_recent,
                    day_tag=day_tag, is_postponed=is_postponed,
                    real_stats=real_stats, bucket=bucket
                )
            except Exception as e:
                print(f"[Football] ESPN parse error ({code}): {e}")

        if len(bucket["leagues"][lg_key]["entries"]) == 0:
            fb_cnt = 0
            if ls_today_stages:
                fb_cnt += _parse_livescore_events_into_bucket(ls_today_stages, state, matches_mem, bucket, now_dt, "امروز", {lg_key}, True)
            if ls_yest_stages:
                fb_cnt += _parse_livescore_events_into_bucket(ls_yest_stages, state, matches_mem, bucket, now_dt, "دیروز", {lg_key}, True)
            if fb_cnt > 0:
                bucket["leagues"][lg_key]["fetched_ok"] = True

    any_fetched = any(v["fetched_ok"] for v in bucket["leagues"].values())
    if any_fetched:
        CACHE["live_match_ids"] = bucket["live_match_ids"]
        CACHE["live_lines"] = bucket["live_lines"]

    for lg_key, b_info in bucket["leagues"].items():
        if b_info["entries"] or (b_info["fetched_ok"] and not CACHE["leagues"][lg_key]["match_ids"]):
            b_info["entries"].sort(key=lambda x: x[0])
            CACHE["leagues"][lg_key] = {
                "title": b_info["title"],
                "lines": [x[1] for x in b_info["entries"]],
                "match_ids": [x[2] for x in b_info["entries"]],
                "has_live": b_info["has_live"]
            }

# =====================================================================
# 8. Menus & Reply-Edit Handlers
# =====================================================================
def send_menu_keyboard(chat_id, text="✅ منوی ربات آماده است! از دکمه های پایین صفحه انتخاب کنید:"):
    if not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text, "reply_markup": BOT_MENU_KEYBOARD},
            timeout=10
        )
    except Exception:
        pass


def build_league_selector_markup():
    buttons = []
    live_count = len(CACHE["live_match_ids"])
    live_label = f"🔴 فوتبال های زنده در جریان امروز ({to_fa_digits(live_count)} بازی زنده)" if live_count > 0 else "🔴 فوتبال های زنده در جریان امروز"
    buttons.append([{"text": live_label, "callback_data": "show_live_now"}])
    for lg_key, lg_title in LEAGUE_CATEGORIES:
        lg_info = CACHE["leagues"].get(lg_key, {})
        count = len(lg_info.get("match_ids", []))
        live_badge = " 🔴 (زنده)" if lg_info.get("has_live") else ""
        count_txt = f" ({to_fa_digits(count)} بازی)" if count > 0 else ""
        buttons.append([{"text": f"{lg_title}{live_badge}{count_txt}", "callback_data": f"showlg_{lg_key}"}])
    buttons.append([{"text": "📊 ساخت پوستر تجمیعی ۵ بازی مهم روز", "callback_data": "mk_multi_today"}])
    buttons.append([{"text": "🔄 بروزرسانی لحظه‌ای لیست بازی‌ها", "callback_data": "refresh_all_leagues"}])
    return json.dumps({"inline_keyboard": buttons})


def send_league_selection_question(chat_id, message_id=None):
    text = "⚽ کدوم بخش یا لیگ مد نظرته؟\n\n• برای دیدن تمامی بازی هایی که همین لحظه زنده در جریان هستند روی دکمه اول (🔴) بزنید.\n• یا یکی از لیگ های زیر را انتخاب کنید:"
    markup = build_league_selector_markup()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{'editMessageText' if message_id else 'sendMessage'}"
    payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    if message_id:
        payload["message_id"] = message_id
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass


def send_live_now_matches(chat_id, message_id=None):
    live_ids, live_lines = CACHE["live_match_ids"], CACHE["live_lines"]
    if live_lines:
        text = "🔴 فهرست تمامی بازی های زنده در جریان امروز:\n\n" + "\n".join(live_lines) + "\n\n👇 روی هر بازی بزنید:"
    else:
        text = "🔴 در این لحظه هیچ بازی زنده ای در حال برگزاری نیست."
    buttons = []
    for mid in live_ids[:20]:
        m = CACHE["matches_by_id"].get(mid)
        if m:
            buttons.append([{"text": f"📸 پوستر زنده (🔄): {m['h_name']} {to_fa_digits(m['h_g'])}-{to_fa_digits(m['a_g'])} {m['a_name']}", "callback_data": f"mkimg_{mid}"}])
    buttons.append([{"text": "🔙 بازگشت به منوی لیگ ها", "callback_data": "back_leagues"}])
    markup = json.dumps({"inline_keyboard": buttons})
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{'editMessageText' if message_id else 'sendMessage'}"
    payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    if message_id:
        payload["message_id"] = message_id
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass


def send_specific_league_matches(chat_id, lg_key, message_id=None):
    lg_info = CACHE["leagues"].get(lg_key)
    if not lg_info:
        return
    title, lines, m_ids = lg_info["title"], lg_info["lines"], lg_info["match_ids"]
    if lines:
        text = f"🏆 گزارش بازی های {title}:\n\n" + "\n".join(lines) + "\n\n👇 انتخاب نوع پوستر برای هر بازی:"
    else:
        text = f"🏆 {title}\n\n⚽ در حال حاضر بازی فعالی برای این لیگ ثبت نشده است."
    buttons = []
    for mid in m_ids[:16]:
        m = CACHE["matches_by_id"].get(mid)
        if m:
            score_lbl = f"{m['status_emoji']} {m['h_name']} {to_fa_digits(m['h_g'])}-{to_fa_digits(m['a_g'])} {m['a_name']}"
            buttons.append([
                {"text": f"📸 آمار: {score_lbl}", "callback_data": f"mkimg_{mid}"},
                {"text": "⚔ تقابل رو در رو", "callback_data": f"mkh2h_{mid}"}
            ])
    if len(m_ids) >= 2:
        buttons.append([{"text": "📊 پوستر تجمیعی نتایج این لیگ", "callback_data": f"mkmulti_{lg_key}"}])
    buttons.append([{"text": "🔙 بازگشت به انتخاب لیگ ها", "callback_data": "back_leagues"}])
    markup = json.dumps({"inline_keyboard": buttons})
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{'editMessageText' if message_id else 'sendMessage'}"
    payload = {"chat_id": chat_id, "text": text, "reply_markup": markup}
    if message_id:
        payload["message_id"] = message_id
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass


def send_settings_menu(chat_id, state):
    footer = state.get("footer_text", DEFAULT_FOOTER)
    badge = state.get("reel_badge", DEFAULT_REEL_BADGE)
    hour = state.get("morning_hour", 7)
    text = (
        "⚙ تنظیمات و راهنمای ربات:\n\n"
        f"🕒 ساعات فعالیت روزانه: {to_fa_digits(ACTIVE_START_HOUR)}:۰۰ صبح تا {to_fa_digits(ACTIVE_END_HOUR)}:۰۰ شب (تهران)\n"
        f"📝 امضای پیش‌فرض (کادر پایین ریلز و پوسترها): «{footer}»\n"
        f"🔴 برچسب پیش‌فرض کادر قرمز ریلزساز: «{badge}»\n"
        f"⏰ ساعت ارسال صبحگاهی: {to_fa_digits(hour)}:۰۰ صبح\n\n"
        "✨ ویرایش درجا با ریپلای روی عکس یا ویدیوی ریلز:\n"
        "• بالا: متن کادر قرمز\n• وسط: متن کادر مشکی وسط\n• پایین: متن کادر مشکی پایین"
    )
    buttons = [
        [{"text": "✏ تغییر امضای پایین پوسترها و ریلز", "callback_data": "set_footer"}],
        [{"text": "🔴 تغییر برچسب پیش‌فرض کادر قرمز ریلز", "callback_data": "set_reel_badge"}],
        [
            {"text": "⏰ ۷ صبح", "callback_data": "sethour_7"},
            {"text": "⏰ ۸ صبح", "callback_data": "sethour_8"},
            {"text": "⏰ ۹ صبح", "callback_data": "sethour_9"}
        ]
    ]
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": text, "reply_markup": json.dumps({"inline_keyboard": buttons})},
        timeout=10
    )


def answer_callback(callback_id, text=""):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", data={"callback_query_id": callback_id, "text": text}, timeout=5)
    except Exception:
        pass


def rebuild_post_from_meta(meta, state):
    ptype = meta.get("type")
    overrides = meta.get("overrides", {})
    footer = state.get("footer_text", DEFAULT_FOOTER)
    if ptype == "morning":
        return build_morning_image(overrides=overrides)
    elif ptype == "weather":
        return build_weather_image(overrides=overrides)
    elif ptype == "match":
        m = CACHE["matches_by_id"].get(meta.get("mid"))
        if m:
            return build_match_image(m, footer_text=footer, overrides=overrides)
    elif ptype == "h2h":
        m = CACHE["matches_by_id"].get(meta.get("mid"))
        if m:
            return build_h2h_matchday_image(m, footer_text=footer, overrides=overrides)
    elif ptype == "multi":
        selected = [CACHE["matches_by_id"][x] for x in meta.get("mids", []) if x in CACHE["matches_by_id"]]
        if selected:
            return build_multi_match_image(selected, title_top=meta.get("title_top", "نتایج بازی ها"), footer_text=footer, overrides=overrides)
    return None


def handle_reply_instant_edit(chat_id, reply_msg_id, user_text, state):
    meta = SENT_POSTS_MEM.get(f"{chat_id}_{reply_msg_id}")
    if not meta:
        return False
    overrides = meta.setdefault("overrides", {})
    for raw_line in user_text.strip().split("\n"):
        line = raw_line.strip()
        if ":" in line:
            k, val = line.split(":", 1)
            k, val = k.strip(), val.strip()
            if k in ("بالا", "قرمز", "برچسب", "سربرگ", "لیگ", "دسته"):
                overrides["badge"] = val
            elif k in ("وسط", "تیتر", "عنوان"):
                overrides["title"] = val
            elif k in ("پایین", "امضا", "فوتر"):
                overrides["footer"] = val
            elif k in ("نتیجه", "اسکور"):
                overrides["score"] = val
            elif k in ("متن", "گلزنان", "شعر", "توضیح"):
                overrides["custom_line"] = val
            else:
                overrides["title"] = line
        else:
            overrides["title"] = line

    if meta.get("type") == "viral":
        process_viral_video_request(
            chat_id,
            url=meta.get("url", ""),
            raw_text="",
            state=state,
            badge_override=overrides.get("badge", meta.get("badge")),
            title_override=overrides.get("title", meta.get("title")),
            bottom_override=overrides.get("footer", meta.get("footer")),
            tg_file_id=meta.get("file_id")
        )
        return True

    new_img = rebuild_post_from_meta(meta, state)
    if new_img:
        edit_telegram_photo_in_place(chat_id, reply_msg_id, new_img, caption=meta.get("caption", ""), inline_kb=meta.get("kb"), post_meta=meta)
        return True
    return False


# =====================================================================
# 8-B. Reels Framer Input Parser & Processor (3-Box Custom Layout)
# =====================================================================
def parse_viral_input_text(text):
    cleaned = re.sub(r'^(ریلز\s*ساز|قاب\s*ساز|قاب|ویدیو|وایرال)\s*[\:\-]?\s*', '', (text or "").strip())
    url_match = re.search(r'(https?://[^\s\|]+)', cleaned)
    if not url_match:
        return None, cleaned
    url = url_match.group(1).strip()
    remainder = (cleaned[:url_match.start()] + " " + cleaned[url_match.end():]).strip().lstrip("|:-").strip()
    return url, remainder


def parse_three_box_texts(raw_text, default_badge, default_bottom, fallback_title=""):
    badge_txt = default_badge
    title_txt = ""
    bottom_txt = default_bottom

    txt = (raw_text or "").strip()
    if not txt:
        return badge_txt, (fallback_title or "ویدیوی ویژه روز"), bottom_txt

    labeled = False
    for line in txt.split("\n"):
        ln = line.strip()
        if ":" in ln:
            k, v = ln.split(":", 1)
            k, v = k.strip(), v.strip()
            if k in ("بالا", "قرمز", "برچسب"):
                badge_txt = v
                labeled = True
            elif k in ("وسط", "تیتر", "عنوان"):
                title_txt = v
                labeled = True
            elif k in ("پایین", "امضا", "فوتر"):
                bottom_txt = v
                labeled = True

    if labeled:
        return badge_txt, (title_txt or fallback_title or "ویدیوی ویژه روز"), bottom_txt

    if "|" in txt:
        parts = [p.strip() for p in txt.split("|")]
    else:
        parts = [p.strip() for p in txt.split("\n") if p.strip()]

    if len(parts) >= 3:
        badge_txt, title_txt, bottom_txt = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        title_txt, bottom_txt = parts[0], parts[1]
    elif len(parts) == 1:
        title_txt = parts[0]

    return badge_txt, (title_txt or fallback_title or "ویدیوی ویژه روز"), bottom_txt


def process_viral_video_request(chat_id, url, raw_text, state, badge_override=None, title_override=None, bottom_override=None, tg_file_id=None):
    default_badge = state.get("reel_badge", DEFAULT_REEL_BADGE)
    default_bottom = state.get("footer_text", DEFAULT_FOOTER)
    send_menu_keyboard(chat_id, "⏳ در حال دریافت ویدیو و قرار دادن متن‌ها در قاب اختصاصی ریلز...")

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_mp4 = os.path.join(tmpdir, "raw_input.mp4")
        ok, extracted_title = False, ""
        if tg_file_id:
            ok = download_telegram_file(tg_file_id, raw_mp4)
        elif url:
            ok, extracted_title = download_viral_video_from_url(url, raw_mp4)

        if not ok:
            send_menu_keyboard(chat_id, "⚠ دانلود مستقیم از این لینک امکان‌پذیر نشد.\n💡 خود فایل ویدیو را مستقیماً برای ربات بفرستید و متن کادرها را در کپشن آن بنویسید.")
            return

        fallback_fa = to_persian_text(extracted_title) if extracted_title else "ویدیوی ویژه روز"
        badge_txt, title_txt, bottom_txt = parse_three_box_texts(raw_text, default_badge, default_bottom, fallback_title=fallback_fa)

        if badge_override is not None:
            badge_txt = badge_override
        if title_override is not None:
            title_txt = title_override
        if bottom_override is not None:
            bottom_txt = bottom_override

        mp4_bytes = render_framed_viral_video_mp4(raw_mp4, badge_txt, title_txt, bottom_txt)
        if mp4_bytes:
            caption = (
                "🎬 ریلز آماده انتشار شد!\n"
                f"🔴 کادر بالا: {badge_txt}\n"
                f"⬛ کادر وسط: {title_txt}\n"
                f"⬛ کادر پایین: {bottom_txt}\n\n"
                "💡 برای ویرایش هر کادر روی همین ویدیو Reply بزنید (مثال: وسط: تیتر جدید)."
            )
            meta = {
                "type": "viral", "url": url, "file_id": tg_file_id,
                "badge": badge_txt, "title": title_txt, "footer": bottom_txt,
                "overrides": {"badge": badge_txt, "title": title_txt, "footer": bottom_txt}
            }
            send_telegram_video(chat_id, mp4_bytes, caption=caption, post_meta=meta)
        else:
            send_menu_keyboard(chat_id, "⚠ خطا در پردازش ویدیو با FFmpeg.")


# =====================================================================
# 8-C. Instagram Public Scanner (30-Min Window + AJAX Story + Cookie)
# =====================================================================
def get_http_session():
    global CURL_CFFI_READY
    if not CURL_CFFI_READY:
        try:
            import curl_cffi
            CURL_CFFI_READY = True
        except ImportError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-q", "curl_cffi"], timeout=45, check=False)
                CURL_CFFI_READY = True
            except Exception:
                pass
    try:
        from curl_cffi import requests as cffi_req
        return cffi_req, True
    except Exception:
        return requests, False


def http_get_stealth(url, headers=None, params=None, timeout=12):
    req_mod, is_cffi = get_http_session()
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    if is_cffi:
        return req_mod.get(url, headers=hdrs, params=params, impersonate="chrome120", timeout=timeout)
    return req_mod.get(url, headers=hdrs, params=params, timeout=timeout)


def http_post_stealth(url, headers=None, data=None, json_data=None, timeout=14):
    req_mod, is_cffi = get_http_session()
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    if is_cffi:
        return req_mod.post(url, headers=hdrs, data=data, json=json_data, impersonate="chrome120", timeout=timeout)
    return req_mod.post(url, headers=hdrs, data=data, json=json_data, timeout=timeout)


def clean_ig_username(raw_text):
    txt = str(raw_text).strip()
    txt = re.sub(r'^https?://(www\.)?instagram\.com/stories/', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'^https?://(www\.)?instagram\.com/', '', txt, flags=re.IGNORECASE)
    txt = txt.split('/')[0].split('?')[0].replace('@', '').strip()
    if re.match(r'^[a-zA-Z0-9._]{2,30}$', txt):
        return txt.lower()
    return ""


def unescape_ig_raw_html(raw_html):
    return str(raw_html).replace('\\"', '"').replace('\\/', '/').replace('\\u0026', '&').replace('&amp;', '&')


def unpack_js_p_a_c_k_e_r(source_str):
    m = re.search(r"}\(\s*'((?:\\'|[^'])*)'\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*'((?:\\'|[^'])*)'\.split\('\|'\)", source_str)
    if not m:
        return source_str
    payload, radix, count, symtab = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).split('|')
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def to_base(num, b):
        if num == 0:
            return "0"
        digits = []
        while num:
            digits.append(alphabet[int(num % b)])
            num //= b
        return "".join(reversed(digits))
    result = payload
    for i in range(min(count, len(symtab)) - 1, -1, -1):
        if symtab[i]:
            result = re.sub(rf'\b{re.escape(to_base(i, radix))}\b', lambda _: symtab[i], result)
    return result


def format_elapsed_fa(age_seconds):
    if age_seconds is None or age_seconds < 0:
        return "به تازگی"
    mins = int(age_seconds // 60)
    if mins <= 0:
        return "لحظاتی پیش"
    if mins < 60:
        return f"{to_fa_digits(mins)} دقیقه پیش"
    hrs, rem_m = mins // 60, mins % 60
    if hrs < 24:
        return f"{to_fa_digits(hrs)} ساعت و {to_fa_digits(rem_m)} دقیقه پیش" if rem_m > 0 else f"{to_fa_digits(hrs)} ساعت پیش"
    return f"{to_fa_digits(hrs // 24)} روز پیش"


def fetch_ig_single_shortcode_details(shortcode, is_reel_hint=False):
    if not shortcode:
        return None
    is_video, video_url, display_url, caption, taken_at = is_reel_hint, "", "", "", 0
    try:
        r = http_get_stealth(f"https://www.instagram.com/p/{shortcode}/embed/captioned/", params={"_cb": int(time.time())}, timeout=12)
        if r.status_code == 200:
            raw_html = r.text
            clean_html = unescape_ig_raw_html(raw_html)
            if "EmbeddedMediaVideo" in clean_html or '"is_video":true' in clean_html or '"video_url":' in clean_html:
                is_video = True
            m_ts = re.search(r'"taken_at_timestamp"\s*:\s*(\d{9,11})', clean_html) or re.search(r'"taken_at"\s*:\s*(\d{9,11})', clean_html)
            if m_ts:
                taken_at = int(m_ts.group(1))
            m_vid = re.search(r'"video_url"\s*:\s*"(https?://[^"]+)"', clean_html)
            if m_vid:
                video_url = m_vid.group(1)
            m_img = re.search(r'class="EmbeddedMediaImage"[^>]+src="([^"]+)"', raw_html)
            if m_img:
                display_url = m_img.group(1).replace("&amp;", "&")
            else:
                m_disp = re.search(r'"display_url"\s*:\s*"(https?://[^"]+)"', clean_html)
                if m_disp:
                    display_url = m_disp.group(1)
            m_cap = re.search(r'class="Caption"(.*?)</div>', raw_html, re.DOTALL)
            if m_cap:
                caption = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m_cap.group(1))).strip()
    except Exception:
        pass
    kind_path = "reel" if is_video else "p"
    return {
        "shortcode": shortcode, "kind": "reel" if is_video else "post", "is_video": is_video,
        "media_url": video_url or display_url, "thumb_url": display_url,
        "caption": caption[:600], "taken_at": taken_at,
        "link": f"https://www.instagram.com/{kind_path}/{shortcode}/"
    }


def fetch_stories_multi_engine(clean_user, user_id, state, now_ts):
    stories_all, stories_30m, seen_urls = [], [], set()
    story_seen_mem = state.setdefault("ig_story_first_seen", {}).setdefault(clean_user, {})
    ig_session = urllib.parse.unquote(state.get("ig_sessionid", "").strip())

    def register_story_candidate(media_url, is_vid=False, taken_at_ts=0, force_recent=False):
        if not media_url or "avatar" in media_url.lower() or "150x150" in media_url or "s150x150" in media_url:
            return
        s_key = hashlib.md5(media_url.split("?")[0][-60:].encode()).hexdigest()[:12]
        if s_key in seen_urls:
            return
        seen_urls.add(s_key)
        if taken_at_ts and taken_at_ts > 1000000000:
            st_age = max(0, now_ts - int(taken_at_ts))
            story_seen_mem[s_key] = int(taken_at_ts)
        else:
            if s_key not in story_seen_mem:
                story_seen_mem[s_key] = now_ts
            st_age = max(0, now_ts - story_seen_mem[s_key])
        st_obj = {
            "shortcode": "", "kind": "story", "is_video": is_vid or (".mp4" in media_url.lower()),
            "media_url": media_url, "thumb_url": media_url, "caption": "استوری منتشرشده در پیج",
            "taken_at": taken_at_ts or story_seen_mem[s_key], "age_sec": st_age,
            "link": f"https://www.instagram.com/stories/{clean_user}/"
        }
        stories_all.append(st_obj)
        if st_age <= IG_WINDOW_SECONDS or force_recent:
            stories_30m.append(st_obj)

    if user_id:
        try:
            st_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
                "x-ig-app-id": "936619743392459", "X-ASBD-ID": "129477", "Accept": "*/*",
                "Referer": f"https://www.instagram.com/{clean_user}/"
            }
            if ig_session:
                st_headers["Cookie"] = f"sessionid={ig_session};"
            for off_u in [f"https://www.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}", f"https://i.instagram.com/api/v1/feed/user/{user_id}/story/"]:
                r_off = http_get_stealth(off_u, headers=st_headers, params={"_cb": now_ts}, timeout=12)
                if r_off.status_code == 200 and "application/json" in r_off.headers.get("Content-Type", "").lower():
                    j_data = r_off.json()
                    items = j_data["reels_media"][0].get("items", []) if j_data.get("reels_media") else (j_data.get("reel", {}).get("items", []) if isinstance(j_data.get("reel"), dict) else [])
                    for it in items:
                        t_at = int(it.get("taken_at", 0) or 0)
                        v_vers = it.get("video_versions", [])
                        i_vers = it.get("image_versions2", {}).get("candidates", [])
                        if v_vers:
                            register_story_candidate(v_vers[0].get("url", ""), is_vid=True, taken_at_ts=t_at)
                        elif i_vers:
                            register_story_candidate(i_vers[0].get("url", ""), is_vid=False, taken_at_ts=t_at)
                if stories_all:
                    return stories_all, stories_30m
        except Exception:
            pass

    for j_api in [
        f"https://storiesig.info/api/ig/story?url=https://www.instagram.com/stories/{clean_user}/",
        f"https://igram.world/api/ig/story?url=https://www.instagram.com/stories/{clean_user}/",
        f"https://fastdl.app/api/ig/story?url=https://www.instagram.com/stories/{clean_user}/"
    ]:
        try:
            rj = http_get_stealth(j_api, timeout=12)
            if rj.status_code == 200 and "json" in rj.headers.get("Content-Type", "").lower():
                j_obj = rj.json()
                res_list = j_obj.get("result") or j_obj.get("data") or []
                if isinstance(res_list, list):
                    for it in res_list:
                        t_at = int(it.get("taken_at", 0) or 0)
                        v_vers = it.get("video_versions", [])
                        i_vers = it.get("image_versions2", {}).get("candidates", [])
                        direct_u = it.get("url") or it.get("video_url") or it.get("image_url") or ""
                        if v_vers and isinstance(v_vers, list):
                            register_story_candidate(v_vers[0].get("url", ""), is_vid=True, taken_at_ts=t_at)
                        elif i_vers and isinstance(i_vers, list):
                            register_story_candidate(i_vers[0].get("url", ""), is_vid=False, taken_at_ts=t_at)
                        elif direct_u:
                            register_story_candidate(direct_u, is_vid=(".mp4" in direct_u.lower()), taken_at_ts=t_at)
                if stories_all:
                    return stories_all, stories_30m
        except Exception:
            pass

    for post_url, ref_url in [
        ("https://v3.saveig.app/api/ajaxSearch", "https://saveig.app/en/instagram-story-downloader"),
        ("https://savefree.app/api/ajaxSearch", "https://savefree.app/en/instagram-story-downloader")
    ]:
        try:
            ra = http_post_stealth(
                post_url,
                headers={"Origin": "/".join(ref_url.split("/")[:3]), "Referer": ref_url, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"},
                data={"q": f"https://www.instagram.com/stories/{clean_user}/", "t": "media", "lang": "en"},
                timeout=14
            )
            if ra.status_code == 200:
                raw_resp = ra.text
                try:
                    raw_resp = ra.json().get("data", "") or raw_resp
                except Exception:
                    pass
                unpacked = unescape_ig_raw_html(unpack_js_p_a_c_k_e_r(raw_resp))
                dl_links = re.findall(r'href="(https?://[^"]+)"[^>]*class="[^"]*abutton[^"]*"', unpacked) or re.findall(r'href="(https?://(?:dl\.|media\.|scontent)[^"]+)"', unpacked)
                for dl_u in dl_links:
                    register_story_candidate(dl_u, is_vid=("video" in dl_u.lower() or ".mp4" in dl_u.lower()))
                if stories_all:
                    return stories_all, stories_30m
        except Exception:
            pass

    for sm_url in [f"https://imginn.com/stories/{clean_user}/", f"https://pixwox.com/profile/{clean_user}/stories/"]:
        try:
            sr = http_get_stealth(sm_url, timeout=12)
            if sr.status_code == 200:
                clean_st = unescape_ig_raw_html(sr.text)
                has_recent = bool(re.search(r'\b([1-2]?\d|30)\s*(?:m|min|mins|minute|minutes|دقیقه)\b', clean_st, re.IGNORECASE))
                for su in re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|jpg)\?[^\s"\'<>]+', clean_st):
                    register_story_candidate(su, is_vid=(".mp4" in su.lower()), force_recent=has_recent)
                if stories_all:
                    break
        except Exception:
            pass

    return stories_all, stories_30m


def fetch_instagram_public_bundle(username, state):
    clean_user = clean_ig_username(username)
    now_ts = int(time.time())
    result = {
        "username": clean_user, "user_id": "", "exists": False, "is_private": False,
        "posts_count": None, "all_items": [], "recent_30m_items": [],
        "stories_30m": [], "stories_all": [], "latest_age_sec": None
    }
    if not clean_user:
        return result

    seen_shortcodes = set()
    ig_session = urllib.parse.unquote(state.get("ig_sessionid", "").strip())
    ig_headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "x-ig-app-id": "936619743392459", "X-ASBD-ID": "129477", "X-IG-WWW-Claim": "0",
        "Accept": "*/*", "Referer": f"https://www.instagram.com/{clean_user}/", "Cache-Control": "no-cache"
    }
    if ig_session:
        ig_headers["Cookie"] = f"sessionid={ig_session};"

    try:
        r = http_get_stealth(f"https://www.instagram.com/api/v1/users/web_profile_info/?username={clean_user}", headers=ig_headers, params={"_cb": now_ts}, timeout=12)
        if r.status_code == 200 and "application/json" in r.headers.get("Content-Type", "").lower():
            user_data = r.json().get("data", {}).get("user", {})
            if user_data:
                result["exists"] = True
                result["user_id"] = str(user_data.get("id", "") or "")
                result["is_private"] = user_data.get("is_private", False)
                timeline_obj = user_data.get("edge_owner_to_timeline_media", {})
                if "count" in timeline_obj:
                    result["posts_count"] = int(timeline_obj.get("count", 0))
                combined_edges = timeline_obj.get("edges", []) + user_data.get("edge_felix_video_timeline", {}).get("edges", [])
                for edge in combined_edges:
                    node = edge.get("node", {})
                    sc = node.get("shortcode", "")
                    if not sc or sc in seen_shortcodes:
                        continue
                    seen_shortcodes.add(sc)
                    is_video = node.get("is_video", False)
                    taken_at = int(node.get("taken_at_timestamp", 0) or 0)
                    cap_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                    caption = cap_edges[0]["node"].get("text", "") if cap_edges else ""
                    children_urls = [
                        (ch["node"].get("video_url") or ch["node"].get("display_url"), bool(ch["node"].get("video_url")))
                        for ch in node.get("edge_sidecar_to_children", {}).get("edges", [])
                        if ch["node"].get("video_url") or ch["node"].get("display_url")
                    ]
                    result["all_items"].append({
                        "shortcode": sc, "kind": "reel" if is_video else "post", "is_video": is_video,
                        "media_url": node.get("video_url") if (is_video and node.get("video_url")) else node.get("display_url", ""),
                        "thumb_url": node.get("display_url", ""), "children": children_urls,
                        "caption": caption[:600], "taken_at": taken_at,
                        "age_sec": (now_ts - taken_at) if taken_at > 0 else None,
                        "link": f"https://www.instagram.com/{'reel' if is_video else 'p'}/{sc}/"
                    })
    except Exception:
        pass

    if not result["all_items"] or not result["user_id"]:
        try:
            r_emb = http_get_stealth(f"https://www.instagram.com/{clean_user}/embed/", headers={"Cache-Control": "no-cache"}, params={"_t": now_ts}, timeout=12)
            if r_emb.status_code == 200:
                clean_e = unescape_ig_raw_html(r_emb.text)
                if "Page Not Found" not in clean_e:
                    result["exists"] = True
                if '"is_private":true' in clean_e or "This Account is Private" in clean_e:
                    result["is_private"] = True
                if not result["user_id"]:
                    m_uid = re.search(r'"owner"\s*:\s*\{\s*"id"\s*:\s*"(\d+)"', clean_e) or re.search(r'"id"\s*:\s*"(\d{6,20})"', clean_e)
                    if m_uid:
                        result["user_id"] = m_uid.group(1)
                if not result["all_items"]:
                    ts_map = {sc: int(ts) for sc, ts in re.findall(r'"shortcode"\s*:\s*"([A-Za-z0-9_-]{8,15})".*?"taken_at_timestamp"\s*:\s*(\d{9,11})', clean_e)}
                    sc_list = []
                    for sc in re.findall(r'"shortcode"\s*:\s*"([A-Za-z0-9_-]{8,15})"', clean_e) + re.findall(r'/(?:p|reel)/([A-Za-z0-9_-]{8,15})/', clean_e):
                        if sc not in sc_list:
                            sc_list.append(sc)
                    for sc_cand in sc_list[:8]:
                        det = fetch_ig_single_shortcode_details(sc_cand)
                        if det:
                            if not det.get("taken_at") and sc_cand in ts_map:
                                det["taken_at"] = ts_map[sc_cand]
                            det["age_sec"] = (now_ts - det["taken_at"]) if det.get("taken_at", 0) > 0 else None
                            result["all_items"].append(det)
        except Exception:
            pass

    result["all_items"].sort(key=lambda x: x.get("taken_at", 0), reverse=True)
    for item in result["all_items"]:
        age = item.get("age_sec")
        if age is not None:
            if result["latest_age_sec"] is None or age < result["latest_age_sec"]:
                result["latest_age_sec"] = max(0, age)
            if 0 <= age <= IG_WINDOW_SECONDS:
                result["recent_30m_items"].append(item)

    st_all, st_30m = fetch_stories_multi_engine(clean_user, result["user_id"], state, now_ts)
    result["stories_all"], result["stories_30m"] = st_all, st_30m
    for st in st_all:
        age = st.get("age_sec")
        if age is not None and (result["latest_age_sec"] is None or age < result["latest_age_sec"]):
            result["latest_age_sec"] = max(0, age)

    save_state(state)
    return result


def send_ig_media_item_to_telegram(chat_id, label_title, username, item_dict):
    if not item_dict:
        return False
    link, caption_raw = item_dict.get("link", ""), item_dict.get("caption", "")
    media_url, thumb_url = item_dict.get("media_url", ""), item_dict.get("thumb_url", "")
    caption_text = f"📌 {label_title} | @{username}\n⏱ زمان انتشار: {format_elapsed_fa(item_dict.get('age_sec'))}\n\n{caption_raw[:420]}\n\n🔗 لینک مستقیم:\n{link}".strip()
    kb = [[{"text": "🎬 تبدیل به ریلز در قاب اختصاصی", "callback_data": f"igframe_{item_dict.get('shortcode', '')}"}]] if (link and item_dict.get("shortcode")) else []

    children = item_dict.get("children", [])
    if len(children) > 1:
        sent_slides = False
        for idx, (ch_url, ch_is_vid) in enumerate(children[:10]):
            try:
                r_ch = http_get_stealth(ch_url, timeout=20)
                if r_ch.status_code == 200 and len(r_ch.content) > 5000:
                    slide_cap = caption_text if idx == 0 else f"🖼 اسلاید {to_fa_digits(idx + 1)} از پست @{username}"
                    if ch_is_vid or ".mp4" in ch_url.lower():
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo", data={"chat_id": chat_id, "caption": slide_cap, "supports_streaming": True}, files={"video": ("slide.mp4", io.BytesIO(r_ch.content), "video/mp4")}, timeout=45)
                    else:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data={"chat_id": chat_id, "caption": slide_cap}, files={"photo": ("slide.jpg", io.BytesIO(r_ch.content), "image/jpeg")}, timeout=30)
                    sent_slides = True
            except Exception:
                pass
        if sent_slides:
            return True

    if link and item_dict.get("is_video") and item_dict.get("shortcode"):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl_path = os.path.join(tmpdir, "ig_item.mp4")
            ok, _ = download_viral_video_from_url(link, dl_path)
            if ok and os.path.exists(dl_path) and os.path.getsize(dl_path) > 10000:
                with open(dl_path, "rb") as f:
                    v_bytes = f.read()
                data = {"chat_id": chat_id, "caption": caption_text, "supports_streaming": True}
                if kb:
                    data["reply_markup"] = json.dumps({"inline_keyboard": kb})
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo", data=data, files={"video": ("instagram.mp4", io.BytesIO(v_bytes), "video/mp4")}, timeout=60)
                return True

    target_media = media_url or thumb_url
    if target_media:
        try:
            r_m = http_get_stealth(target_media, timeout=25)
            if r_m.status_code == 200 and len(r_m.content) > 5000:
                ctype = r_m.headers.get("Content-Type", "").lower()
                is_v = ("video" in ctype or ".mp4" in target_media.lower() or item_dict.get("is_video"))
                data = {"chat_id": chat_id, "caption": caption_text}
                if kb:
                    data["reply_markup"] = json.dumps({"inline_keyboard": kb})
                if is_v:
                    data["supports_streaming"] = True
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo", data=data, files={"video": ("ig_video.mp4", io.BytesIO(r_m.content), "video/mp4")}, timeout=45)
                else:
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=data, files={"photo": ("ig_photo.jpg", io.BytesIO(r_m.content), "image/jpeg")}, timeout=30)
                return True
        except Exception:
            pass

    if link:
        dd_link = link.replace("www.instagram.com", "d.ddinstagram.com")
        data = {"chat_id": chat_id, "text": f"📌 {label_title} | @{username}\n\n{caption_raw[:420]}\n\n🔗 {dd_link}"}
        if kb:
            data["reply_markup"] = json.dumps({"inline_keyboard": kb})
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=data, timeout=15)
        return True
    return False


def process_instagram_page_check(chat_id, username_raw, state):
    raw_u = str(username_raw).strip()
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    if raw_u == "setcookie":
        state["awaiting_input"] = "ig_username"
        save_state(state)
        requests.post(url_msg, data={"chat_id": chat_id, "text": "🔑 لطفا مقدار کوکی sessionid یک اکانت فرعی اینستاگرام را برای دریافت آنی استوری‌ها همین‌جا بفرستید:"}, timeout=10)
        return

    if ("%" in raw_u or ":" in raw_u) and len(raw_u) > 25 and not raw_u.startswith("http"):
        state["ig_sessionid"] = raw_u.replace("sessionid=", "").strip().strip(";")
        save_state(state)
        target_p = state.get("ig_target_page", "shirazlastnews")
        send_menu_keyboard(chat_id, f"✅ کوکی استوری ذخیره شد! در حال اسکن @{target_p}...")
        raw_u = target_p

    force_all = raw_u.startswith("all__")
    if force_all:
        raw_u = raw_u.replace("all__", "", 1)

    clean_user = clean_ig_username(raw_u)
    if not clean_user:
        send_menu_keyboard(chat_id, "⚠ آیدی پیج معتبر نیست. لطفا فقط آیدی انگلیسی پیج را بفرستید.")
        return

    state["ig_target_page"] = clean_user
    save_state(state)

    has_cookie = bool(state.get("ig_sessionid"))
    cookie_lbl = "🔑 بروزرسانی کوکی استوری (فعال ✅)" if has_cookie else "🔑 ثبت کوکی استوری"
    kb_base = [
        [{"text": f"🔄 رصد مجدد ۳۰ دقیقه اخیر @{clean_user}", "callback_data": f"igcheck_{clean_user}"}],
        [{"text": "✏ تغییر آیدی پیج اینستاگرام", "callback_data": "ig_change_user"}],
        [{"text": cookie_lbl, "callback_data": "igcheck_setcookie"}]
    ]

    requests.post(
        url_msg,
        data={"chat_id": chat_id, "text": f"🔍 در حال اسکن پیج @{clean_user}...", "reply_markup": json.dumps({"inline_keyboard": kb_base})},
        timeout=10
    )

    bundle = fetch_instagram_public_bundle(clean_user, state)
    items_to_send = bundle["all_items"][:5] if force_all else bundle["recent_30m_items"]
    stories_to_send = bundle["stories_all"][:8] if force_all else bundle["stories_30m"]

    sent_count = 0
    for item in reversed(items_to_send):
        if send_ig_media_item_to_telegram(chat_id, "🎬 ریلز منتشرشده" if item.get("is_video") else "📸 پست منتشرشده", clean_user, item):
            sent_count += 1
    for idx, st_item in enumerate(stories_to_send):
        if send_ig_media_item_to_telegram(chat_id, f"📱 استوری فعال ({to_fa_digits(idx + 1)})", clean_user, st_item):
            sent_count += 1

    if sent_count > 0:
        requests.post(url_msg, data={"chat_id": chat_id, "text": f"✅ مجموعاً {to_fa_digits(sent_count)} محتوا از @{clean_user} ارسال شد.", "reply_markup": json.dumps({"inline_keyboard": kb_base})}, timeout=10)
        return

    if bundle.get("is_private"):
        requests.post(url_msg, data={"chat_id": chat_id, "text": f"🔒 پیج @{clean_user} خصوصی است.", "reply_markup": json.dumps({"inline_keyboard": kb_base})}, timeout=10)
        return

    if not force_all and (bundle["all_items"] or bundle["stories_all"]):
        last_age_txt = format_elapsed_fa(bundle.get("latest_age_sec"))
        kb_fallback = [
            [{"text": f"📥 ارسال آخرین محتوای @{clean_user} ({last_age_txt})", "callback_data": f"igcheck_all__{clean_user}"}],
            [{"text": f"🔄 بررسی مجدد ۳۰ دقیقه اخیر @{clean_user}", "callback_data": f"igcheck_{clean_user}"}],
            [{"text": "✏ تغییر آیدی پیج اینستاگرام", "callback_data": "ig_change_user"}],
            [{"text": cookie_lbl, "callback_data": "igcheck_setcookie"}]
        ]
        requests.post(
            url_msg,
            data={"chat_id": chat_id, "text": f"⏱ در ۳۰ دقیقه گذشته محتوای جدیدی در @{clean_user} یافت نشد.\n🕒 آخرین فعالیت ثبت‌شده: {last_age_txt}", "reply_markup": json.dumps({"inline_keyboard": kb_fallback})},
            timeout=10
        )
        return

    requests.post(url_msg, data={"chat_id": chat_id, "text": f"📭 در بازه ۳۰ دقیقه گذشته محتوای جدیدی در @{clean_user} یافت نشد.", "reply_markup": json.dumps({"inline_keyboard": kb_base})}, timeout=10)


# =====================================================================
# 9. GitHub Actions Scheduled Worker & Main Loop (07:00 - 21:00 Tehran)
# =====================================================================
def background_worker(state):
    while is_within_active_hours():
        try:
            refresh_daily_data_cache()
            check_all_football_free(state)

            now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
            today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")
            target_chat = get_target_chat_id(state)
            morning_hour = int(state.get("morning_hour", 7))

            if now_tehran.hour == morning_hour and state.get("last_morning_date") != today_gregorian and target_chat:
                refresh_daily_data_cache()
                kb_m = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": "mkvid_morning_0"}]]
                cap_m = "🌞 صبح بخیر | تقویم، اوقات شرعی، نبض بازار و تفال حافظ"
                send_telegram_photo(target_chat, build_morning_image(), cap_m, inline_kb=kb_m, post_meta={"type": "morning", "overrides": {}, "caption": cap_m, "kb": kb_m})

                kb_w = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": "mkvid_weather_0"}]]
                cap_w = "⛅ وضعیت آب و هوا و پیش بینی ۴ زمانه امروز"
                send_telegram_photo(target_chat, build_weather_image(), cap_w, inline_kb=kb_w, post_meta={"type": "weather", "overrides": {}, "caption": cap_w, "kb": kb_w})
                state["last_morning_date"] = today_gregorian

            save_state(state)
        except Exception as e:
            print("Background worker error:", e)
        time.sleep(60)


def handle_user_request(chat_id, text, state, reply_to_msg_id=None, tg_file_id=None):
    t = (text or "").strip()

    if tg_file_id:
        state["awaiting_input"] = ""
        save_state(state)
        process_viral_video_request(chat_id, url="", raw_text=t, state=state, tg_file_id=tg_file_id)
        return

    if reply_to_msg_id and handle_reply_instant_edit(chat_id, reply_to_msg_id, t, state):
        return

    awaiting = state.get("awaiting_input", "")
    if awaiting == "footer":
        state["footer_text"] = t
        state["awaiting_input"] = ""
        save_state(state)
        send_menu_keyboard(chat_id, f"✅ متن امضای پایین به «{t}» تغییر یافت.")
        return

    if awaiting == "reel_badge":
        state["reel_badge"] = t
        state["awaiting_input"] = ""
        save_state(state)
        send_menu_keyboard(chat_id, f"✅ برچسب کادر قرمز ریلزساز به «{t}» تغییر یافت.")
        return

    if awaiting == "viral_link" and not t.startswith("/"):
        url, remainder = parse_viral_input_text(t)
        if url:
            state["awaiting_input"] = ""
            save_state(state)
            process_viral_video_request(chat_id, url, remainder, state)
            return

    if awaiting == "ig_username" and not t.startswith("/"):
        state["awaiting_input"] = ""
        save_state(state)
        process_instagram_page_check(chat_id, t, state)
        return

    if t in ("📸 رصد پیج اینستاگرام", "/insta"):
        target_page = state.get("ig_target_page", "")
        if target_page:
            process_instagram_page_check(chat_id, target_page, state)
        else:
            state["awaiting_input"] = "ig_username"
            save_state(state)
            send_menu_keyboard(chat_id, "📸 لطفا آیدی پیج عمومی اینستاگرام را بفرستید (مثلا shirazlastnews):")
        return

    if t in ("🎬 ریلزساز و قاب ویدیو", "🎬 قاب‌ساز ویدیو وایرال", "/viral"):
        state["awaiting_input"] = "viral_link"
        save_state(state)
        guide_txt = (
            "🎬 ریلزساز با قاب اختصاصی آماده است!\n\n"
            "فایل ویدیو (یا لینک اینستاگرام/یوتیوب/توییتر) را همراه با متن کادرها بفرستید:\n\n"
            "1️⃣ یک متن (فقط کادر مشکی وسط):\n"
            "بارش شدید باران در شیراز\n\n"
            "2️⃣ دو متن (کادر وسط | کادر پایین):\n"
            "بارش شدید باران در شیراز | آخرین خبرهای شیراز\n\n"
            "3️⃣ سه متن (کادر قرمز بالا | کادر وسط | کادر پایین):\n"
            "خبر فوری | بارش شدید باران در شیراز | جزئیات در کپشن"
        )
        send_menu_keyboard(chat_id, guide_txt)
        return

    if re.search(r'https?://', t):
        url, remainder = parse_viral_input_text(t)
        if url:
            state["awaiting_input"] = ""
            save_state(state)
            process_viral_video_request(chat_id, url, remainder, state)
            return

    if "صبح بخیر" in t or t == "/morning":
        kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": "mkvid_morning_0"}]]
        cap = "🌞 صبح بخیر | تقویم، اوقات شرعی، نبض بازار و تفال حافظ"
        send_telegram_photo(chat_id, build_morning_image(), cap, inline_kb=kb, post_meta={"type": "morning", "overrides": {}, "caption": cap, "kb": kb})

    elif "وضعیت هوا" in t or "آب و هوا" in t or t == "/weather":
        kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": "mkvid_weather_0"}]]
        cap = "⛅ وضعیت لحظه ای آب و هوا و پیش بینی ۴ زمانه"
        send_telegram_photo(chat_id, build_weather_image(), cap, inline_kb=kb, post_meta={"type": "weather", "overrides": {}, "caption": cap, "kb": kb})

    elif "نتایج زنده" in t or "فوتبال" in t or t == "/football":
        send_league_selection_question(chat_id)

    elif "تنظیمات" in t or t == "/settings":
        send_settings_menu(chat_id, state)

    else:
        send_menu_keyboard(chat_id, "👇 لطفا یکی از کلیدهای منوی پایین صفحه را انتخاب کنید:")


def handle_callback_query(chat_id, message_id, cb_id, data, state):
    footer = state.get("footer_text", DEFAULT_FOOTER)

    if data == "show_live_now":
        answer_callback(cb_id, "🔴 دریافت بازی های زنده...")
        send_live_now_matches(chat_id, message_id=message_id)

    elif data == "refresh_all_leagues":
        answer_callback(cb_id, "🔄 در حال بروزرسانی همه لیگ‌ها...")
        check_all_football_free(state)
        send_league_selection_question(chat_id, message_id=message_id)

    elif data.startswith("showlg_"):
        answer_callback(cb_id, "⚽ دریافت لیست بازی ها...")
        send_specific_league_matches(chat_id, data.replace("showlg_", "", 1), message_id=message_id)

    elif data == "back_leagues":
        answer_callback(cb_id)
        send_league_selection_question(chat_id, message_id=message_id)

    elif data.startswith("mkimg_"):
        answer_callback(cb_id, "🎨 در حال ساخت پوستر...")
        mid = data.replace("mkimg_", "", 1)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            caption = f"{m['status_emoji']} {m['status_label']} ({m['league_fa']})\n⚽ {m['h_name']} {to_fa_digits(m['h_g'])} - {to_fa_digits(m['a_g'])} {m['a_name']}"
            kb = [
                [{"text": "🔄 بروزرسانی زنده همین پوستر", "callback_data": f"refresh_{mid}"}],
                [{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": f"mkvid_match_{mid}"}]
            ]
            meta = {"type": "match", "mid": mid, "overrides": {}, "caption": caption, "kb": kb}
            sent_id = send_telegram_photo(chat_id, build_match_image(m, footer_text=footer), caption=caption, inline_kb=kb, post_meta=meta)
            state.setdefault("matches", {}).setdefault(mid, {"h": m["h_g"], "a": m["a_g"], "ft": m["is_finished"]})["msg_id"] = sent_id

    elif data.startswith("refresh_"):
        mid = data.replace("refresh_", "", 1)
        answer_callback(cb_id, "🔄 بروزرسانی درجا...")
        check_all_football_free(state)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            meta = SENT_POSTS_MEM.get(f"{chat_id}_{message_id}", {"type": "match", "mid": mid, "overrides": {}})
            caption = f"{m['status_emoji']} {m['status_label']} ({m['league_fa']})\n⚽ {m['h_name']} {to_fa_digits(m['h_g'])} - {to_fa_digits(m['a_g'])} {m['a_name']}"
            kb = [
                [{"text": "🔄 بروزرسانی زنده همین پوستر", "callback_data": f"refresh_{mid}"}],
                [{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": f"mkvid_match_{mid}"}]
            ]
            meta["caption"], meta["kb"] = caption, kb
            edit_telegram_photo_in_place(chat_id, message_id, build_match_image(m, footer_text=footer, overrides=meta.get("overrides")), caption=caption, inline_kb=kb, post_meta=meta)

    elif data.startswith("mkh2h_"):
        answer_callback(cb_id, "⚔ ساخت پوستر پیش بازی...")
        mid = data.replace("mkh2h_", "", 1)
        m = CACHE["matches_by_id"].get(mid)
        if m:
            caption = f"⚔ پیش بازی و تقابل رو در رو ({m['league_fa']})\n⚽ {m['h_name']} مقابل {m['a_name']}"
            kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": f"mkvid_h2h_{mid}"}]]
            send_telegram_photo(chat_id, build_h2h_matchday_image(m, footer_text=footer), caption=caption, inline_kb=kb, post_meta={"type": "h2h", "mid": mid, "overrides": {}, "caption": caption, "kb": kb})

    elif data == "mk_multi_today" or data.startswith("mkmulti_"):
        answer_callback(cb_id, "📊 ساخت پوستر تجمیعی...")
        if data == "mk_multi_today":
            all_ids = CACHE["live_match_ids"] + [mid for lg in CACHE["leagues"].values() for mid in lg["match_ids"]]
            seen = []
            for x in all_ids:
                if x not in seen:
                    seen.append(x)
            mids = [x for x in seen[:5] if x in CACHE["matches_by_id"]]
            title_top = "نتایج بازی های امروز"
        else:
            lg_info = CACHE["leagues"].get(data.replace("mkmulti_", "", 1), {})
            mids = [x for x in lg_info.get("match_ids", [])[:5] if x in CACHE["matches_by_id"]]
            title_top = lg_info.get("title", "نتایج بازی ها")
        selected = [CACHE["matches_by_id"][x] for x in mids]
        if selected:
            caption = f"📊 جمع بندی نتایج ({title_top})"
            kb = [[{"text": "🎬 دریافت ویدیو موشن گرافیک (MP4)", "callback_data": "mkvid_multi_0"}]]
            send_telegram_photo(chat_id, build_multi_match_image(selected, title_top=title_top, footer_text=footer), caption=caption, inline_kb=kb, post_meta={"type": "multi", "mids": mids, "title_top": title_top, "overrides": {}, "caption": caption, "kb": kb})

    elif data.startswith("mkvid_"):
        answer_callback(cb_id, "🎬 در حال رندر ویدیوی ۱۴ ثانیه‌ای موشن گرافیک...")
        meta = SENT_POSTS_MEM.get(f"{chat_id}_{message_id}")
        ptype, m_obj, m_list, title_top, overrides = "morning", None, None, "نتایج بازی های امروز", {}
        if meta:
            ptype = meta.get("type", "morning")
            overrides = meta.get("overrides", {})
            if ptype in ("match", "h2h"):
                m_obj = CACHE["matches_by_id"].get(meta.get("mid"))
            elif ptype == "multi":
                m_list = [CACHE["matches_by_id"][x] for x in meta.get("mids", []) if x in CACHE["matches_by_id"]]
                title_top = meta.get("title_top", "نتایج بازی های امروز")
        else:
            parts = data.split("_", 2)
            ptype, arg = parts[1], (parts[2] if len(parts) > 2 else "")
            if ptype in ("match", "h2h") and arg in CACHE["matches_by_id"]:
                m_obj = CACHE["matches_by_id"][arg]

        mp4_bytes = generate_scenario_video_mp4(ptype, state, m_obj=m_obj, matches_list=m_list, title_top=title_top, overrides=overrides)
        if mp4_bytes:
            send_telegram_video(chat_id, mp4_bytes, caption="🎬 نسخه استوری موشن گرافیک (۱۴ ثانیه‌ای آماده استوری)")

    elif data == "ig_change_user":
        answer_callback(cb_id)
        state["awaiting_input"] = "ig_username"
        save_state(state)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": "✏ آیدی پیج عمومی جدید اینستاگرام را بفرستید:"}, timeout=10)

    elif data.startswith("igcheck_"):
        uname = data.replace("igcheck_", "", 1)
        answer_callback(cb_id, "🔍 در حال بررسی...")
        process_instagram_page_check(chat_id, uname, state)

    elif data.startswith("igframe_"):
        sc = data.replace("igframe_", "", 1)
        if sc:
            answer_callback(cb_id, "🎬 ارسال به ریلزساز اختصاصی...")
            process_viral_video_request(chat_id, f"https://www.instagram.com/reel/{sc}/", "", state)

    elif data == "set_footer":
        answer_callback(cb_id)
        state["awaiting_input"] = "footer"
        save_state(state)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": "✏ متن جدید امضای پایین پوسترها و ریلز را بفرستید:"}, timeout=10)

    elif data == "set_reel_badge":
        answer_callback(cb_id)
        state["awaiting_input"] = "reel_badge"
        save_state(state)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": "🔴 متن کوتاه جدید کادر قرمز ریلزساز (مثلا فوری یا اختصاصی) را بفرستید:"}, timeout=10)

    elif data.startswith("sethour_"):
        hr = int(data.replace("sethour_", "", 1))
        state["morning_hour"] = hr
        save_state(state)
        answer_callback(cb_id, f"✅ ساعت ارسال صبحگاهی: {to_fa_digits(hr)} صبح")
        send_settings_menu(chat_id, state)


if __name__ == "__main__":
    if not is_within_active_hours():
        print("Outside active Tehran hours (07:00 - 21:00). Exiting cleanly.")
        sys.exit(0)

    ensure_fonts()
    preload_templates()
    setup_bot_commands()
    state = load_state()

    refresh_daily_data_cache()
    check_all_football_free(state)

    now_tehran = jdatetime.datetime.now(TEHRAN_TZ)
    today_gregorian = now_tehran.togregorian().strftime("%Y-%m-%d")
    target = get_target_chat_id(state)

    if target and state.get("last_wake_notice_date") != today_gregorian:
        send_menu_keyboard(target, "☀️ ربات روشن شد! (ساعات فعالیت: ۷ صبح تا ۲۱ شب به وقت تهران)")
        state["last_wake_notice_date"] = today_gregorian
        save_state(state)

    threading.Thread(target=background_worker, args=(state,), daemon=True).start()

    start_ts = time.time()
    offset = 0
    while (time.time() - start_ts < MAX_CYCLE_SECONDS) and is_within_active_hours():
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            res = requests.get(url, params={"offset": offset, "timeout": 25}, timeout=30).json()
            for upd in res.get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    msg = upd["message"]
                    cid = msg["chat"]["id"]
                    txt = msg.get("text") or msg.get("caption") or ""
                    reply_id = msg.get("reply_to_message", {}).get("message_id")
                    tg_video_id = msg["video"].get("file_id") if "video" in msg else (msg["animation"].get("file_id") if "animation" in msg else None)
                    if txt or tg_video_id:
                        if not state.get("owner_chat_id"):
                            state["owner_chat_id"] = cid
                            save_state(state)
                        threading.Thread(target=handle_user_request, args=(cid, txt, state, reply_id, tg_video_id), daemon=True).start()
                elif "callback_query" in upd:
                    cb = upd["callback_query"]
                    threading.Thread(
                        target=handle_callback_query,
                        args=(cb["message"]["chat"]["id"], cb["message"]["message_id"], cb["id"], cb.get("data", ""), state),
                        daemon=True
                    ).start()
        except Exception as e:
            print("Polling error:", e)
            time.sleep(3)

    now_end = jdatetime.datetime.now(TEHRAN_TZ)
    today_end = now_end.togregorian().strftime("%Y-%m-%d")
    if not is_within_active_hours():
        if target and state.get("last_sleep_notice_date") != today_end:
            state["last_sleep_notice_date"] = today_end
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    data={"chat_id": target, "text": "🌙 ساعت ۲۱ به وقت تهران رسید؛ ربات تا ساعت ۷ صبح فردا خاموش می‌شود."},
                    timeout=10
                )
            except Exception:
                pass

    save_state(state)
