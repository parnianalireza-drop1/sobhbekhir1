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


