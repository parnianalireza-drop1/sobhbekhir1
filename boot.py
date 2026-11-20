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
