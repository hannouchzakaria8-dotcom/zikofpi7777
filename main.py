#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests, os, sys, jwt, pickle, json, binascii, time, urllib3, base64, datetime, re, socket, threading, ssl, pytz, aiohttp
from protobuf_decoder.protobuf_decoder import Parser
from xC4 import *
from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from Pb2 import DEcwHisPErMsG_pb2, MajoRLoGinrEs_pb2, PorTs_pb2, MajoRLoGinrEq_pb2, sQ_pb2, Team_msg_pb2
from cfonts import render, say
from APIS import insta
from flask import Flask, jsonify, request
import asyncio
import signal
import sys
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Telegram Bot Imports
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------- الإعدادات الثابتة -------------------
ADMIN_UID = "8804135237"
server2 = "BD"
key2 = "mg24"
BYPASS_TOKEN = "your_bypass_token_here"

# ضع توكن البوت هنا مباشرة
BOT_TOKEN = "8248104861:AAEmzo4Bx2Ss6uiT3zma4CbCUnU717tRIEw"
ADMIN_TELEGRAM_ID = 6848455321
BASE_WEBHOOK_URL = "https://your-app-name.onrender.com"   # غيّره بعد النشر

# قنوات الاشتراك الإجباري
REQUIRED_CHANNEL = "@Ziko_Tim"
REQUIRED_GROUP = "@MTX_SX_CHAT_TEAM"

# ------------------- المتغيرات العامة -------------------
online_writer = None
whisper_writer = None
insquad = None
joining_team = False
lag_running = False
lag_task = None
telegram_bot_running = False
telegram_bot = None
telegram_dp = None

# ------------------- تعيينات الإيموجيات (اختصار – يمكنك إكمالها لاحقاً) -------------------
# القائمة الكاملة للإيموجيات العادية (1-414) طويلة جداً، نكتفي بالجزء الذي يظهر في الملفات.
# أنصحك بنسخ القواميس كاملة من ملف main.py الذي أرسلته سابقاً إذا احتجت 414 إيموجي.
# هنا سأضع نموذجاً مختصراً للتوضيح، لكن في مشروعك الحقيقي يجب أن تكون القواميس كاملة.
ALL_EMOTE = {
    1: 909000001,
    2: 909000002,
    3: 909000003,
    4: 909000004,
    5: 909000005,
    6: 909000006,
    7: 909000007,
    8: 909000008,
    9: 909000009,
    10: 909000010,
    11: 909000011,
    12: 909000012,
    13: 909000013,
    14: 909000014,
    15: 909000015,
    16: 909000016,
    17: 909000017,
    18: 909000018,
    19: 909000019,
    20: 909000020,
    21: 909000021,
    22: 909000022,
    23: 909000023,
    24: 909000024,
    25: 909000025,
    26: 909000026,
    27: 909000027,
    28: 909000028,
    29: 909000029,
    30: 909000031,
    31: 909000032,
    32: 909000033,
    33: 909000034,
    34: 909000035,
    35: 909000036,
    36: 909000037,
    37: 909000038,
    38: 909000039,
    39: 909000040,
    40: 909000041,
    41: 909000042,
    42: 909000043,
    43: 909000044,
    44: 909000045,
    45: 909000046,
    46: 909000047,
    47: 909000048,
    48: 909000049,
    49: 909000051,
    50: 909000052,
    51: 909000053,
    52: 909000054,
    53: 909000055,
    54: 909000056,
    55: 909000057,
    56: 909000058,
    57: 909000059,
    58: 909000060,
    59: 909000061,
    60: 909000062,
    61: 909000063,
    62: 909000064,
    63: 909000065,
    64: 909000066,
    65: 909000067,
    66: 909000068,
    67: 909000069,
    68: 909000070,
    69: 909000071,
    70: 909000072,
    71: 909000073,
    72: 909000074,
    73: 909000075,
    74: 909000076,
    75: 909000077,
    76: 909000078,
    77: 909000079,
    78: 909000080,
    79: 909000081,
    80: 909000082,
    81: 909000083,
    82: 909000084,
    83: 909000085,
    84: 909000086,
    85: 909000087,
    86: 909000088,
    87: 909000089,
    88: 909000090,
    89: 909000091,
    90: 909000092,
    91: 909000093,
    92: 909000094,
    93: 909000095,
    94: 909000096,
    95: 909000097,
    96: 909000098,
    97: 909000099,
    98: 909000100,
    99: 909000101,
    100: 909000102,
    101: 909000103,
    102: 909000104,
    103: 909000105,
    104: 909000106,
    105: 909000107,
    106: 909000108,
    107: 909000109,
    108: 909000110,
    109: 909000111,
    110: 909000112,
    111: 909000113,
    112: 909000114,
    113: 909000115,
    114: 909000116,
    115: 909000117,
    116: 909000118,
    117: 909000119,
    118: 909000120,
    119: 909000121,
    120: 909000122,
    121: 909000123,
    122: 909000124,
    123: 909000125,
    124: 909000126,
    125: 909000127,
    126: 909000128,
    127: 909000129,
    128: 909000130,
    129: 909000131,
    130: 909000132,
    131: 909000133,
    132: 909000134,
    133: 909000135,
    134: 909000136,
    135: 909000137,
    136: 909000138,
    137: 909000139,
    138: 909000140,
    139: 909000141,
    140: 909000142,
    141: 909000143,
    142: 909000144,
    143: 909000145,
    144: 909000150,
    145: 909033001,
    146: 909033002,
    147: 909033003,
    148: 909033004,
    149: 909033005,
    150: 909033006,
    151: 909033007,
    152: 909033008,
    153: 909033009,
    154: 909033010,
    155: 909034001,
    156: 909034002,
    157: 909034003,
    158: 909034004,
    159: 909034005,
    160: 909034006,
    161: 909034007,
    162: 909034008,
    163: 909034009,
    164: 909034010,
    165: 909034011,
    166: 909034012,
    167: 909034013,
    168: 909034014,
    169: 909035001,
    170: 909035002,
    171: 909035003,
    172: 909035004,
    173: 909035005,
    174: 909035006,
    175: 909035007,
    176: 909035008,
    177: 909035009,
    178: 909035010,
    179: 909035011,
    180: 909035012,
    181: 909035013,
    182: 909035014,
    183: 909035015,
    184: 909036001,
    185: 909036002,
    186: 909036003,
    187: 909036004,
    188: 909036005,
    189: 909036006,
    190: 909036008,
    191: 909036009,
    192: 909036010,
    193: 909036011,
    194: 909036012,
    195: 909036014,
    196: 909037001,
    197: 909037002,
    198: 909037003,
    199: 909037004,
    200: 909037005,
    201: 909037006,
    202: 909037007,
    203: 909037008,
    204: 909037009,
    205: 909037010,
    206: 909037011,
    207: 909037012,
    208: 909038001,
    209: 909038002,
    210: 909038003,
    211: 909038004,
    212: 909038005,
    213: 909038006,
    214: 909038008,
    215: 909038009,
    216: 909038010,
    217: 909038011,
    218: 909038012,
    219: 909038013,
    220: 909039001,
    221: 909039002,
    222: 909039003,
    223: 909039004,
    224: 909039005,
    225: 909039006,
    226: 909039007,
    227: 909039008,
    228: 909039009,
    229: 909039010,
    230: 909039011,
    231: 909039012,
    232: 909039013,
    233: 909039014,
    234: 909040001,
    235: 909040002,
    236: 909040003,
    237: 909040004,
    238: 909040005,
    239: 909040006,
    240: 909040008,
    241: 909040009,
    242: 909040010,
    243: 909040011,
    244: 909040012,
    245: 909040013,
    246: 909040014,
    247: 909041001,
    248: 909041002,
    249: 909041003,
    250: 909041004,
    251: 909041005,
    252: 909041006,
    253: 909041007,
    254: 909041008,
    255: 909041009,
    256: 909041010,
    257: 909041011,
    258: 909041012,
    259: 909041013,
    260: 909041014,
    261: 909041015,
    262: 909042001,
    263: 909042002,
    264: 909042003,
    265: 909042004,
    266: 909042005,
    267: 909042006,
    268: 909042007,
    269: 909042008,
    270: 909042009,
    271: 909042011,
    272: 909042012,
    273: 909042013,
    274: 909042016,
    275: 909042017,
    276: 909042018,
    277: 909043001,
    278: 909043002,
    279: 909043003,
    280: 909043004,
    281: 909043005,
    282: 909043006,
    283: 909043007,
    284: 909043008,
    285: 909043009,
    286: 909043010,
    287: 909043013,
    288: 909044001,
    289: 909044002,
    290: 909044003,
    291: 909044004,
    292: 909044005,
    293: 909044006,
    294: 909044007,
    295: 909044008,
    296: 909044009,
    297: 909044010,
    298: 909044011,
    299: 909044012,
    300: 909044015,
    301: 909044016,
    302: 909045001,
    303: 909045002,
    304: 909045003,
    305: 909045004,
    306: 909045005,
    307: 909045006,
    308: 909045007,
    309: 909045008,
    310: 909045009,
    311: 909045010,
    312: 909045011,
    313: 909045012,
    314: 909045015,
    315: 909045016,
    316: 909045017,
    317: 909046001,
    318: 909046002,
    319: 909046003,
    320: 909046004,
    321: 909046005,
    322: 909046006,
    323: 909046007,
    324: 909046008,
    325: 909046009,
    326: 909046010,
    327: 909046011,
    328: 909046012,
    329: 909046013,
    330: 909046014,
    331: 909046015,
    332: 909046016,
    333: 909046017,
    334: 909047001,
    335: 909047002,
    336: 909047003,
    337: 909047004,
    338: 909047005,
    339: 909047006,
    340: 909047007,
    341: 909047008,
    342: 909047009,
    343: 909047010,
    344: 909047011,
    345: 909047012,
    346: 909047013,
    347: 909047015,
    348: 909047016,
    349: 909047017,
    350: 909047018,
    351: 909047019,
    352: 909048001,
    353: 909048002,
    354: 909048003,
    355: 909048004,
    356: 909048005,
    357: 909048006,
    358: 909048007,
    359: 909048008,
    360: 909048009,
    361: 909048010,
    362: 909048011,
    363: 909048012,
    364: 909048013,
    365: 909048014,
    366: 909048015,
    367: 909048016,
    368: 909048017,
    369: 909048018,
    370: 909049001,
    371: 909049002,
    372: 909049003,
    373: 909049004,
    374: 909049005,
    375: 909049006,
    376: 909049007,
    377: 909049008,
    378: 909049009,
    379: 909049010,
    380: 909049011,
    381: 909049012,
    382: 909049013,
    383: 909049014,
    384: 909049015,
    385: 909049016,
    386: 909049017,
    387: 909049018,
    388: 909049019,
    389: 909049020,
    390: 909049021,
    391: 909050002,
    392: 909050003,
    393: 909050004,
    394: 909050005,
    395: 909050006,
    396: 909050008,
    397: 909050009,
    398: 909050010,
    399: 909050011,
    400: 909050012,
    401: 909050013,
    402: 909050014,
    403: 909050015,
    404: 909050016,
    405: 909050017,
    406: 909050018,
    407: 909050019,
    408: 909050020,
    409: 909050021,
    410: 909050026,
    411: 909050027,
    412: 909050028,
    413: 909547001,
    414: 909550001
    # ... (يمكنك إكمال البقية حسب الملف الأصلي)
}

EMOTE_MAP = {
    1: 909000063, 2: 909000081, 3: 909000075, 4: 909000085, 5: 909000134,
    6: 909000098, 7: 909035007, 8: 909051012, 9: 909000141, 10: 909034008,
    11: 909041002, 12: 909039004, 13: 909042008, 14: 909051014, 15: 909039012,
    16: 909040010, 17: 909035010, 18: 909041005, 19: 909051003, 20: 909034001
}

# ------------------- دوال التحقق من الاشتراك -------------------
async def check_subscription(user_id: int) -> bool:
    try:
        channel_member = await telegram_bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        group_member = await telegram_bot.get_chat_member(REQUIRED_GROUP, user_id)
        return (channel_member.status not in ["left", "kicked"] and
                group_member.status not in ["left", "kicked"])
    except Exception as e:
        print(f"خطأ في التحقق من الاشتراك: {e}")
        return False

async def require_subscription(message: Message):
    if message.from_user.id == ADMIN_TELEGRAM_ID:
        return True
    if await check_subscription(message.from_user.id):
        return True
    else:
        await message.reply(
            f"⚠️ **عذراً، يجب عليك الاشتراك في القناة والمجموعة التاليتين لاستخدام البوت:**\n\n"
            f"📢 **القناة:** {REQUIRED_CHANNEL}\n"
            f"💬 **المجموعة:** {REQUIRED_GROUP}\n\n"
            f"بعد الاشتراك، أرسل الأمر مرة أخرى."
        )
        return False

# ------------------- دوال التلغرام الأساسية -------------------
async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}/webhook")
    print(f"✅ Webhook set to {BASE_WEBHOOK_URL}/webhook")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    await bot.delete_webhook()
    print("❌ Webhook deleted")

async def telegram_startup():
    global telegram_bot, telegram_dp, telegram_bot_running
    logging.basicConfig(level=logging.INFO)
    telegram_bot = Bot(token=BOT_TOKEN)
    telegram_dp = Dispatcher()
    await register_handlers(telegram_dp)
    telegram_dp.startup.register(on_startup)
    telegram_dp.shutdown.register(on_shutdown)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=telegram_dp, bot=telegram_bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, telegram_dp, bot=telegram_bot)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🤖 بوت التلغرام يعمل على المنفذ {port} مع webhook")
    telegram_bot_running = True
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await runner.cleanup()

async def register_handlers(dp: Dispatcher):
    """تسجيل معالجات الأوامر المطلوبة فقط (المجموعة، الدعوة، الرقص، الإيموجي التطوري، الـ lag)"""

    @dp.message(Command("help"))
    async def help_cmd(message: Message):
        if not await require_subscription(message):
            return
        help_text = """
🤖 **بوت ZAKARIA - أوامر التلغرام**

**أوامر المجموعة:**
/3 [UID] - إنشاء مجموعة 3 لاعبين للمعرف المحدد
/5 [UID] - إنشاء مجموعة 5 لاعبين
/6 [UID] - إنشاء مجموعة 6 لاعبين
/inv [UID] - إرسال دعوة للاعب

**أوامر الرقص والإيموجي:**
/dance [team_code] [UID] [رقم_الرقصة 1-414] - انضمام، رقصة عادية، مغادرة
/evo [team_code] [UID] [رقم_الرقصة 1-20] - انضمام، رقصة تطورية، مغادرة

**أوامر متقدمة:**
/lag [team_code] - هجوم تأخير (انضمام/مغادرة سريع)
/stop_lag - إيقاف هجوم التأخير
"""
        await message.reply(help_text)

    # أوامر المجموعة (3، 5، 6)
    @dp.message(Command("3", "5", "6"))
    async def squad_size_cmd(message: Message):
        if not await require_subscription(message):
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply(f"❌ الاستخدام: /{message.text[1]} [UID]")
            return
        target_uid = parts[1]
        if not target_uid.isdigit():
            await message.reply("❌ الرجاء إدخال معرف صحيح!")
            return
        size = int(message.text[1])  # الرقم بعد الشرطة
        await message.reply(f"🚀 جاري إنشاء مجموعة {size} لاعبين للمعرف {target_uid}...")
        try:
            global online_writer, whisper_writer, key, iv, region
            uid = target_uid
            PAc = await OpEnSq(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
            C = await cHSq(size, uid, key, iv, region)
            await asyncio.sleep(0.3)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
            V = await SEnd_InV(size, uid, key, iv, region)
            await asyncio.sleep(0.3)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
            E = await ExiT(None, key, iv)
            await asyncio.sleep(3.5)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
            await message.reply(f"✅ تم إنشاء مجموعة {size} لاعبين وإرسال الدعوة إلى {target_uid}!")
        except Exception as e:
            await message.reply(f"❌ خطأ: {str(e)}")

    @dp.message(Command("inv"))
    async def invite_cmd(message: Message):
        if not await require_subscription(message):
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ الاستخدام: /inv [UID]")
            return
        target_uid = parts[1]
        if not target_uid.isdigit():
            await message.reply("❌ الرجاء إدخال معرف صحيح!")
            return
        await message.reply(f"🚀 جاري إرسال دعوة إلى {target_uid}...")
        try:
            V = await SEnd_InV(4, int(target_uid), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
            await message.reply(f"✅ تم إرسال الدعوة إلى {target_uid}!")
        except Exception as e:
            await message.reply(f"❌ خطأ: {str(e)}")

    @dp.message(Command("dance"))
    async def dance_cmd(message: Message):
        if not await require_subscription(message):
            return
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("❌ الاستخدام: /dance [team_code] [UID] [رقم_الرقصة 1-414]")
            return
        team_code = parts[1]
        target_uid = parts[2]
        try:
            emote_number = int(parts[3])
            if emote_number < 1 or emote_number > 414:
                await message.reply("❌ رقم الرقصة يجب أن يكون بين 1 و 414")
                return
        except ValueError:
            await message.reply("❌ رقم الرقصة غير صالح")
            return

        await message.reply(f"🚀 بدء أمر الرقص: الفريق {team_code}, الهدف {target_uid}, الرقصة {emote_number}")
        try:
            emote_id = ALL_EMOTE.get(emote_number)
            if not emote_id:
                await message.reply("❌ معرف الرقصة غير صالح!")
                return

            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            await asyncio.sleep(1.5)
            H = await Emote_k(int(target_uid), emote_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            await asyncio.sleep(0.5)
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)

            await message.reply(f"✅ تم إرسال الرقصة {emote_number} إلى {target_uid} والمغادرة.")
        except Exception as e:
            await message.reply(f"❌ خطأ: {str(e)}")

    @dp.message(Command("evo"))
    async def evo_cmd(message: Message):
        if not await require_subscription(message):
            return
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("❌ الاستخدام: /evo [team_code] [UID] [رقم_الرقصة 1-20]")
            return
        team_code = parts[1]
        target_uid = parts[2]
        try:
            emote_number = int(parts[3])
            if emote_number < 1 or emote_number > 20:
                await message.reply("❌ رقم الرقصة يجب أن يكون بين 1 و 20")
                return
        except ValueError:
            await message.reply("❌ رقم الرقصة غير صالح")
            return

        await message.reply(f"🚀 بدء أمر الرقص التطوري: الفريق {team_code}, الهدف {target_uid}, الرقصة {emote_number}")
        try:
            emote_id = EMOTE_MAP.get(emote_number)
            if not emote_id:
                await message.reply("❌ معرف الرقصة التطورية غير صالح!")
                return

            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            await asyncio.sleep(1.5)
            H = await Emote_k(int(target_uid), emote_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            await asyncio.sleep(0.5)
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)

            await message.reply(f"✅ تم إرسال الرقصة التطورية {emote_number} إلى {target_uid} والمغادرة.")
        except Exception as e:
            await message.reply(f"❌ خطأ: {str(e)}")

    @dp.message(Command("lag"))
    async def lag_cmd(message: Message):
        if not await require_subscription(message):
            return
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ الاستخدام: /lag [team_code]")
            return
        team_code = parts[1]
        await message.reply(f"🚀 بدء هجوم التأخير على الفريق {team_code}...")
        try:
            global lag_running, lag_task
            if lag_task and not lag_task.done():
                lag_running = False
                lag_task.cancel()
                await asyncio.sleep(0.1)
            lag_running = True
            lag_task = asyncio.create_task(lag_team_loop(team_code, key, iv, region))
            await message.reply(f"✅ بدأ هجوم التأخير. للإيقاف: /stop_lag")
        except Exception as e:
            await message.reply(f"❌ خطأ: {str(e)}")

    @dp.message(Command("stop_lag"))
    async def stop_lag_cmd(message: Message):
        if not await require_subscription(message):
            return
        global lag_running, lag_task
        if lag_task and not lag_task.done():
            lag_running = False
            lag_task.cancel()
            await message.reply("✅ تم إيقاف هجوم التأخير.")
        else:
            await message.reply("❌ لا يوجد هجوم تأخير نشط.")

# ------------------- دوال اللعبة الأساسية (موجودة في xC4 و xHeaders) -------------------
# لضمان عدم فقدان أي دالة، نعتمد على أن xC4 و xHeaders تم استيرادهما في الأعلى.
# الدالة lag_team_loop معرفة في xC4، لكن إن لم تكن موجودة نضيفها هنا:
async def lag_team_loop(team_code, key, iv, region):
    global lag_running
    count = 0
    while lag_running:
        try:
            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            await asyncio.sleep(0.01)
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
            count += 1
            print(f"دورة التأخير #{count} للفريق {team_code}")
            await asyncio.sleep(0.01)
        except Exception as e:
            print(f"خطأ في حلقة التأخير: {e}")
            await asyncio.sleep(0.1)

# ------------------- الدالة الرئيسية -------------------
async def MaiiiinE():
    # بيانات الحساب (يفضل وضعها في متغيرات بيئة لأمان أكثر، لكن حسب طلبك وضعناها ثابتة)
    Uid, Pw = '4378068850', '8C583277F6A0221993BAC8FBBD712BC25B171A445A34FB1DD0966609CB74729D'

    open_id, access_token = await GeNeRaTeAccEss(Uid, Pw)
    if not open_id or not access_token:
        print("خطأ - حساب غير صالح")
        return None

    PyL = await EncRypTMajoRLoGin(open_id, access_token)
    MajoRLoGinResPonsE = await MajorLogin(PyL)
    if not MajoRLoGinResPonsE:
        print("الحساب المستهدف => محظور / غير مسجل!")
        return None

    MajoRLoGinauTh = await DecRypTMajoRLoGin(MajoRLoGinResPonsE)
    UrL = MajoRLoGinauTh.url
    region = MajoRLoGinauTh.region
    ToKen = MajoRLoGinauTh.token
    TarGeT = MajoRLoGinauTh.account_uid
    key = MajoRLoGinauTh.key
    iv = MajoRLoGinauTh.iv
    timestamp = MajoRLoGinauTh.timestamp

    LoGinDaTa = await GetLoginData(UrL, PyL, ToKen)
    if not LoGinDaTa:
        print("خطأ في الحصول على المنافذ من بيانات الدخول!")
        return None
    LoGinDaTaUncRypTinG = await DecRypTLoGinDaTa(LoGinDaTa)

    OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
    ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port

    OnLine_parts = OnLinePorTs.split(":")
    OnLineiP = OnLine_parts[0]
    OnLineporT = OnLine_parts[1] if len(OnLine_parts) > 1 else "80"

    Chat_parts = ChaTPorTs.split(":")
    ChaTiP = Chat_parts[0]
    ChaTporT = Chat_parts[1] if len(Chat_parts) > 1 else "80"

    acc_name = LoGinDaTaUncRypTinG.AccountName

    equie_emote(ToKen, UrL)
    AutHToKen = await xAuThSTarTuP(int(TarGeT), ToKen, int(timestamp), key, iv)
    ready_event = asyncio.Event()

    # تشغيل بوت التلغرام كمهمة خلفية
    telegram_task = asyncio.create_task(telegram_startup())

    task1 = asyncio.create_task(TcPChaT(ChaTiP, ChaTporT, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region))
    task2 = asyncio.create_task(TcPOnLine(OnLineiP, OnLineporT, key, iv, AutHToKen))

    print("🤖 بوت ZAKARIA - متصل")
    print(f"🔹 المعرف: {TarGeT}")
    print(f"🔹 الاسم: {acc_name}")
    print("🔹 الحالة: 🟢 جاهز")
    print("🤖 بوت التلغرام يعمل مع webhook")

    await asyncio.gather(task1, task2, telegram_task)

def handle_keyboard_interrupt(signum, frame):
    print("\n\n🛑 طلب إيقاف البوت...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_keyboard_interrupt)

async def StarTinG():
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(), timeout=7 * 60 * 60)
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
            break
        except asyncio.TimeoutError:
            print("انتهت صلاحية الرمز! إعادة التشغيل")
        except Exception as e:
            print(f"خطأ في TCP - {e} => إعادة التشغيل ...")

if __name__ == '__main__':
    threading.Thread(target=start_insta_api, daemon=True).start()
    asyncio.run(StarTinG())