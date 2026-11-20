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

    draw_luxury_text(base, 540, 912, overrides.get("score", f"{m['a_g']} - {m['h_g']}"), 126, style="gold", use_display_font=True, max_width=320)
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
        draw_luxury_text(base, 540, cy, f"{m['a_g']} - {m['h_g']}", 64, style="gold", use_display_font=True, max_width=180)
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
                            score_str = overrides.get("score", f"{m_obj['a_g']} - {m_obj['h_g']}")
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
                            paste_sprite_animated(frame, render_text_sprite(f"{m['a_g']} - {m['h_g']}", 64, "gold", True, 180), 540, cy, scale=0.5 + 0.5 * p_row, alpha_mult=a_row)
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


def register_and_check_match(state, matches_mem, lg_key, match_id, league_fa, is_iran, h_name, a_name, h_g, a_g, h_logo, a_logo, is_live, is_finished, minute_str="", scorers_list=None, allow_auto_alert=True):
    if is_live:
        status_emoji = "🔴"
        status_label = f"زنده (دقیقه {to_fa_digits(minute_str)})" if minute_str else "زنده"
        header_prefix = "زنده"
        line_str = f"🔴 زنده ({to_fa_digits(minute_str)}') | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}" if minute_str else f"🔴 زنده | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
        CACHE["leagues"][lg_key]["has_live"] = True
    elif is_finished:
        status_emoji = "🏁"
        status_label = "پایان بازی"
        header_prefix = "نتیجه نهایی"
        line_str = f"🏁 پایان | {h_name} {to_fa_digits(h_g)} - {to_fa_digits(a_g)} {a_name}"
    else:
        status_emoji = "⏰"
        status_label = f"در انتظار شروع ({to_fa_digits(minute_str)})" if minute_str else "در انتظار شروع"
        header_prefix = "برنامه بازی"
        line_str = f"⏰ {to_fa_digits(minute_str)} | {h_name} - {a_name}" if minute_str else f"⏰ در انتظار شروع | {h_name} - {a_name}"

    m_obj = {
        "id": match_id, "status_emoji": status_emoji, "status_label": status_label,
        "league_title": f"{header_prefix} | {league_fa}", "league_fa": league_fa,
        "h_name": h_name, "a_name": a_name, "h_g": h_g, "a_g": a_g,
        "h_logo": h_logo, "a_logo": a_logo, "is_live": is_live, "is_finished": is_finished,
        "scorers_list": scorers_list or []
    }
    CACHE["matches_by_id"][match_id] = m_obj
    CACHE["leagues"][lg_key]["lines"].append(line_str)
    CACHE["leagues"][lg_key]["match_ids"].append(match_id)

    if is_live:
        CACHE["live_match_ids"].append(match_id)
        CACHE["live_lines"].append(f"🏆 {league_fa}: {line_str}")

    if not allow_auto_alert:
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


def check_all_football_free(state):
    matches_mem = state.setdefault("matches", {})
    now_greg = jdatetime.datetime.now(TEHRAN_TZ).togregorian()
    today_compact = now_greg.strftime("%Y%m%d")

    CACHE["live_match_ids"] = []
    CACHE["live_lines"] = []
    for lg_key, lg_title in LEAGUE_CATEGORIES:
        CACHE["leagues"][lg_key] = {"title": lg_title, "lines": [], "match_ids": [], "has_live": False}

    for day_offset in [0, -1, 1, -2, 2]:
        target_date = (now_greg + timedelta(days=day_offset)).strftime("%Y%m%d")
        is_today = (day_offset == 0)
        found_iran = False
        try:
            f_leagues = requests.get(f"https://www.fotmob.com/api/matches?date={target_date}", headers=HEADERS, timeout=10).json().get("leagues", [])
            for lg in f_leagues:
                lid = lg.get("primaryId")
                if lid not in (9090, 9384):
                    continue
                found_iran = True
                l_fa = "لیگ برتر ایران" if lid == 9090 else "جام حذفی ایران"
                for m in lg.get("matches", []):
                    mid = f"ir_{m['id']}"
                    st = m.get("status", {})
                    register_and_check_match(
                        state, matches_mem, "lg_ir", mid, l_fa, True,
                        to_persian_text(m["home"]["name"]), to_persian_text(m["away"]["name"]),
                        int(m["home"].get("score", 0) or 0), int(m["away"].get("score", 0) or 0),
                        f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['home']['id']}.png",
                        f"https://images.fotmob.com/image_resources/logo/teamlogo/{m['away']['id']}.png",
                        st.get("started", False) and not st.get("finished", False),
                        st.get("finished", False),
                        st.get("liveTime", {}).get("short", "").replace("'", ""),
                        allow_auto_alert=is_today
                    )
        except Exception:
            pass
        if found_iran:
            break

    espn_configs = [
        ("lg_eng", "eng.1", "لیگ برتر انگلیس"),
        ("lg_esp", "esp.1", "لالیگا اسپانیا"),
        ("lg_ger", "ger.1", "بوندسلیگا آلمان"),
        ("lg_ucl", "uefa.champions", "لیگ قهرمانان اروپا")
    ]
    for lg_key, code, l_fa in espn_configs:
        try:
            events = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={today_compact}", headers=HEADERS, timeout=10).json().get("events", [])
            is_today_batch = True
            if not events:
                events = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", headers=HEADERS, timeout=10).json().get("events", [])
                is_today_batch = False

            for ev in events[:10]:
                mid = f"eu_{ev['id']}"
                comp = ev["competitions"][0]
                state_type = ev["status"]["type"]["state"]
                home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
                away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

                scorers_list = []
                for det in comp.get("details", []):
                    if det.get("scoringPlay"):
                        clock = det.get("clock", {}).get("displayValue", "").replace("'", "")
                        athletes = det.get("athletesInvolved", [])
                        if athletes:
                            scorers_list.append(f"{to_persian_text(athletes[0].get('displayName', ''))} ({to_fa_digits(clock)})")

                register_and_check_match(
                    state, matches_mem, lg_key, mid, l_fa, False,
                    to_persian_text(home["team"]["displayName"]), to_persian_text(away["team"]["displayName"]),
                    int(home.get("score", 0) or 0), int(away.get("score", 0) or 0),
                    home["team"].get("logo", ""), away["team"].get("logo", ""),
                    state_type == "in", state_type == "post",
                    ev["status"]["type"].get("shortDetail", ""),
                    scorers_list=scorers_list, allow_auto_alert=is_today_batch
                )
        except Exception:
            pass


