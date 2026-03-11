#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests, os, sys, jwt, json, binascii, time, urllib3, xKEys, base64, datetime, re, socket, threading
import psutil
from protobuf_decoder.protobuf_decoder import Parser
from byte import *
from byte import xSendTeamMsg, xSEndMsg
from byte import Auth_Chat
from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
from black9 import openroom, spmroom
import telebot
from telebot import types
import logging
import io
import urllib.parse

# تحسينات لـ Render
os.environ['PYTHONUNBUFFERED'] = '1'
sys.dont_write_bytecode = True

# تعطيل تحذيرات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

# قراءة التوكن من متغيرات البيئة
TOKEN = os.environ.get('TOKEN', "8114634187:AAGE1c9THsRwbQKIAxmKD6aYeMoYlQzZlqA")
ADMIN_IDS = [6848455321, 7375963526]

# ==================== إعدادات البوت ====================
OWNERS = {
    "usernames": ["@ZikoB0SS", "@noseyrobot"],
    "ids": [7375963526, 6848455321]
}

# روابط الترويج
GROUP_LINK = "https://t.me/MTX_SX_CHAT_TEAM"
GROUP_USERNAME = "@MTX_SX_CHAT_TEAM"
DEV_CHANNEL = "https://t.me/Ziko_Tim"
DEV_USERNAME = "@Ziko_Tim"

ALLOWED_GROUPS = {}  # في الذاكرة
BLOCKED_USERS = set()

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

connected_clients = {}
connected_clients_lock = threading.Lock()

active_spam_targets = {}
active_room_spam_targets = {}
active_spam_lock = threading.Lock()

spam_initiators = {}
spam_initiators_lock = threading.Lock()

spam_start_times = {}
spam_start_times_lock = threading.Lock()

# إعدادات السرعة القصوى
MAX_WORKERS = 100
SPAM_DELAY = 0.01
BURST_SIZE = 50

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== دوال المساعدة ====================
def load_allowed_groups():
    global ALLOWED_GROUPS
    print(f"✅ تم تحميل {len(ALLOWED_GROUPS)} مجموعة مفعلة من الذاكرة")
    return

def save_allowed_groups():
    global ALLOWED_GROUPS
    print(f"✅ تم تحديث {len(ALLOWED_GROUPS)} مجموعة في الذاكرة")
    return

def load_blocked_users():
    global BLOCKED_USERS
    print(f"✅ تم تحميل {len(BLOCKED_USERS)} مستخدم محظور من الذاكرة")
    return

def save_blocked_users():
    global BLOCKED_USERS
    print(f"✅ تم تحديث {len(BLOCKED_USERS)} مستخدم محظور في الذاكرة")
    return

def is_group_allowed(chat_id):
    return str(chat_id) in ALLOWED_GROUPS

def is_user_blocked(user_id):
    return user_id in BLOCKED_USERS

def is_owner(user_id, username):
    if user_id in OWNERS["ids"]:
        return True
    if username and f"@{username}" in OWNERS["usernames"]:
        return True
    return False

def subscription_buttons(is_owner=False):
    """إنشاء أزرار الاشتراك"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # الزر الإجباري للمجموعة
    btn_group = types.InlineKeyboardButton("📢 اشترك في مجموعة البوتات", url=GROUP_LINK)
    markup.add(btn_group)
    
    # زر التحقق من الاشتراك
    btn_check = types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub")
    markup.add(btn_check)
    
    # إذا كان مستخدم يحاول تفعيل مجموعة (owner)، نضيف زر قناة المطور
    if is_owner:
        btn_dev = types.InlineKeyboardButton("👑 قناة المطور", url=DEV_CHANNEL)
        markup.add(btn_dev)
    
    return markup

def check_subscription(user_id):
    """التحقق من اشتراك المستخدم في المجموعة"""
    try:
        chat_member = bot.get_chat_member(GROUP_USERNAME, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"خطأ في التحقق من الاشتراك: {e}")
        return False

def check_user_access(message):
    user_id = message.from_user.id
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    if is_user_blocked(user_id):
        bot.reply_to(message, "❌ عذراً، تم حظرك من استخدام البوت")
        return False
    
    if chat_type in ['group', 'supergroup'] and not is_group_allowed(chat_id):
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"""
⚠️ محاولة استخدام في مجموعة غير مفعلة

👤 المستخدم: {message.from_user.first_name}
🆔 ID: <code>{user_id}</code>
👤 اليوزرنيم: @{message.from_user.username if message.from_user.username else 'لا يوجد'}

📌 المجموعة: {message.chat.title or 'بدون اسم'}
🆔 ID: <code>{chat_id}</code>

⏱️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                )
            except:
                pass
        
        bot.reply_to(message, "❌ هذه المجموعة غير مفعلة\nللتفعيل تواصل مع المطورين\n\n👥 @ZikoB0SS | @noseyrobot")
        return False
    
    return True

def check_user_access_with_subscription(message):
    """التحقق من وصول المستخدم مع الاشتراك الإجباري"""
    user_id = message.from_user.id
    
    if not check_user_access(message):
        return False
    
    # المطورين لا يحتاجون اشتراك
    if is_owner(user_id, message.from_user.username):
        return True
    
    # التحقق من الاشتراك
    if not check_subscription(user_id):
        bot.reply_to(
            message,
            f"🔒 <b>عذراً، يجب الاشتراك في مجموعة البوتات أولاً</b>\n\n"
            f"📢 المجموعة: {GROUP_USERNAME}\n\n"
            f"بعد الاشتراك اضغط على زر التحقق",
            reply_markup=subscription_buttons(is_owner=False)
        )
        return False
    
    return True

def get_player_full_info(uid):
    """
    جلب جميع معلومات اللاعب من API foubia-info-ff
    يعيد كل البيانات المتاحة
    """
    try:
        url = f"https://foubia-info-ff.vercel.app/{uid}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        data = response.json()
        
        # استخراج جميع المعلومات المتاحة
        result = {
            "success": True,
            "raw_data": data  # احتفظ بالبيانات الخام للتوسع مستقبلاً
        }
        
        # basicinfo - المعلومات الأساسية
        if "basicinfo" in data and len(data["basicinfo"]) > 0:
            basic = data["basicinfo"][0]
            result["username"] = basic.get('username', 'Unknown')
            result["uid"] = basic.get('uid', uid)
            result["region"] = basic.get('region', 'Unknown')
            result["level"] = basic.get('level', 'N/A')
            result["like"] = basic.get('like', '0')
            result["account_created"] = basic.get('account_created', 'Unknown')
            result["last_login"] = basic.get('last_login', 'Unknown')
            result["bio"] = basic.get('bio', '')
            result["login_method"] = basic.get('login_method', 'Unknown')
            result["gender"] = basic.get('gender', 'Unknown')
            result["age"] = basic.get('age', '0')
            result["br_rank_score"] = basic.get('br_rank_score', '0')
            result["br_rank_point"] = basic.get('br_rank_point', '0')
            result["cs_rank_score"] = basic.get('cs_rank_score', '0')
        
        # guildinfo - معلومات الطقم
        if "guildinfo" in data and len(data["guildinfo"]) > 0:
            guild = data["guildinfo"][0]
            result["guild_name"] = guild.get('guild_name', 'لا يوجد')
            result["guild_id"] = guild.get('guild_id', '0')
            result["guild_level"] = guild.get('guild_level', '0')
            result["guild_members"] = guild.get('guild_members', '0')
            result["guild_leader"] = guild.get('guild_leader_name', 'Unknown')
            result["guild_leader_uid"] = guild.get('guild_leader_uid', '0')
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Request error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def check_ban_simple(uid):
    """فحص الحظر المبسط - بدون صور ولا مدة"""
    try:
        # جلب معلومات اللاعب أولاً
        player_info = get_player_full_info(uid)
        
        if not player_info["success"]:
            return f"""
❌ فشل جلب معلومات اللاعب

خطأ: {player_info.get('error', 'Unknown')}

━━━━━━━━━━━━━━━━━━━━━━
🔹 /player_info [UID]
🔹 /check [UID]
🔹 /outfit [UID]
🔹 /visit [UID]

👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
        
        # فحص الحظر
        url = f"https://foubia-ban-check.vercel.app/bancheck?key=xTzPrO&uid={uid}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        ban_status = data.get('is_banned', False)
        
        if ban_status:
            status_text = "🚫 محظور"
        else:
            status_text = "✅ غير محظور"
        
        # بناء الرد المبسط
        info_text = f"""
📊 فحص الحظر

👤 الاسم: {player_info.get('username', 'Unknown')}
🆔 UID: <code>{uid}</code>
🌍 المنطقة: {player_info.get('region', 'Unknown')}
📊 المستوى: {player_info.get('level', 'N/A')}
📌 الحالة: {status_text}

━━━━━━━━━━━━━━━━━━━━━━
🔹 /player_info [UID]
🔹 /check [UID]
🔹 /outfit [UID]
🔹 /visit [UID]

👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
        
        return info_text
        
    except Exception as e:
        return f"""
❌ خطأ في فحص الحظر

خطأ: {str(e)}

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""

def get_outfit(uid):
    """جلب صورة الأوتفيت"""
    try:
        player_info = get_player_full_info(uid)
        player_name = player_info.get('username', 'Unknown') if player_info.get('success') else 'Unknown'
        player_region = player_info.get('region', 'Unknown') if player_info.get('success') else 'Unknown'
        
        region = "me"
        outfit_url = f"https://ffoutfitapis.vercel.app/outfit-image?uid={uid}&region={region}&key=99day"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        response = requests.get(outfit_url, headers=headers, timeout=30)
        
        if response.status_code == 200 and len(response.content) > 1000:
            caption = f"""
👕 صورة الأوتفيت

👤 الاسم: {player_name}
🆔 UID: <code>{uid}</code>
🌍 المنطقة: {player_region}

━━━━━━━━━━━━━━━━━━━━━━
🔹 /player_info [UID]
🔹 /check [UID]
🔹 /outfit [UID]
🔹 /visit [UID]

👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            return response.content, caption
        else:
            return None, f"""
❌ فشل جلب الأوتفيت

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            
    except Exception as e:
        return None, f"""
❌ خطأ في جلب الأوتفيت

خطأ: {str(e)}

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""

def send_visits_background(uid, chat_id, wait_msg_id):
    """إرسال الزيارات في الخلفية"""
    try:
        player_info = get_player_full_info(uid)
        player_name = player_info.get('username', uid) if player_info.get('success') else uid
        
        url = f"https://zikovisit.onrender.com/visit?region=BD&uid={uid}"
        requests.get(url, timeout=5)
        
    except Exception as e:
        print(f"⚠️ خطأ في إرسال الزيارات: {e}")
    
    time.sleep(15)
    try:
        bot.edit_message_text(
            f"""
✅ تم إرسال الزيارات

👤 الاسم: {player_name}
🆔 UID: <code>{uid}</code>
🌍 المنطقة: ME
📊 العدد: 1000 زيارة

━━━━━━━━━━━━━━━━━━━━━━
🔹 /player_info [UID]
🔹 /check [UID]
🔹 /outfit [UID]
🔹 /visit [UID]

👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
""",
            chat_id, wait_msg_id
        )
    except:
        pass

# ==================== معالج الأزرار ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "check_sub":
        user_id = call.from_user.id
        
        if check_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح! يمكنك استخدام البوت الآن")
            bot.edit_message_text(
                "✅ تم التحقق بنجاح!\nأرسل /start أو /help لبدء استخدام البوت",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد! اشترك ثم حاول مرة أخرى")

# ==================== أوامر البوت ====================

@bot.message_handler(commands=['start', 'help'])
def start_help_command(message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    if chat_type != 'private':
        if is_group_allowed(chat_id):
            # التحقق من الاشتراك في المجموعات
            if not check_subscription(user_id) and not is_admin:
                bot.reply_to(
                    message,
                    f"🔒 <b>عذراً، يجب الاشتراك في مجموعة البوتات أولاً</b>\n\n"
                    f"📢 المجموعة: {GROUP_USERNAME}\n\n"
                    f"بعد الاشتراك اضغط على زر التحقق",
                    reply_markup=subscription_buttons(is_owner=False)
                )
                return
            
            msg = f"""
⚡ 𝑭𝑷𝑰 𝑺𝑿 𝑻𝑬𝑨𝑴 – 𝑪𝒐𝒎𝒎𝒂𝒏𝒅 𝑳𝒊𝒔𝒕 ⚡

📋 الأوامر المتاحة:

• خدمات السبام:
  /spam [UID] - بدء سبام (30 دقيقة)
  /room [UID] - بدء سبام روم (30 دقيقة)
  /status [UID] - عرض حالة السبام
  /stop_spam [UID] - إيقاف السبام
  /stop_room [UID] - إيقاف سبام الروم

• خدمات الاستعلام:
  /player_info [UID] - جميع معلومات اللاعب
  /check [UID] - فحص الحظر (مبسط)
  /outfit [UID] - صورة الأوتفيت
  /visit [UID] - إرسال 1000 زيارة

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
        else:
            msg = f"❌ هذه المجموعة غير مفعلة\nللتفعيل تواصل مع المطورين\n\n👥 @ZikoB0SS | @noseyrobot\n📢 {GROUP_USERNAME}"
    else:
        if is_admin:
            msg = f"""
⚡ 𝑭𝑷𝑰 𝑺𝑿 𝑻𝑬𝑨𝑴 – 𝑪𝒐𝒎𝒎𝒂𝒏𝒅 𝑳𝒊𝒔𝒕 ⚡

📋 قائمة أوامر التحكم:

• خدمات السبام:
  /spam [UID] - بدء سبام (30 دقيقة)
  /room [UID] - بدء سبام روم (30 دقيقة)
  /status [UID] - عرض حالة السبام
  /stop_spam [UID] - إيقاف السبام
  /stop_room [UID] - إيقاف سبام الروم

• خدمات الاستعلام:
  /player_info [UID] - جميع معلومات اللاعب
  /check [UID] - فحص الحظر (مبسط)
  /outfit [UID] - صورة الأوتفيت
  /visit [UID] - إرسال 1000 زيارة

• أوامر النظام:
  /restart - إعادة تشغيل الحسابات
  /addgroup - تفعيل المجموعة
  /removegroup - تعطيل المجموعة
  /groups - عرض المجموعات المفعلة
  /reply [user_id] [رسالة] - رد على مستخدم
  /block_user [user_id] - حظر مستخدم
  /addgroup_confirm [chat_id] - تأكيد تفعيل مجموعة

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
👑 {DEV_USERNAME}
"""
        else:
            msg = f"""
🗿 ACCESS

❌ عذراً، هذا البوت مخصص للمطورين فقط

للتواصل مع المطورين:
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
    
    bot.reply_to(message, msg)

@bot.message_handler(commands=['player_info'])
def player_info_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"❌ استخدم: /player_info 123456789\n\n📢 {GROUP_USERNAME}")
        return
    
    uid = args[1]
    wait_msg = bot.reply_to(message, f"🔍 جلب جميع معلومات اللاعب {uid}...")
    
    player_info = get_player_full_info(uid)
    
    if player_info["success"]:
        # تحويل التواريخ
        create_date = format_timestamp(player_info.get('createat', 0))
        last_login = format_timestamp(player_info.get('lastlogin', 0))
        
        # بناء الرد الأساسي
        info_text = f"""
📊 جميع معلومات اللاعب

👤 <b>الاسم:</b> {player_info['username']}
🆔 <b>UID:</b> <code>{uid}</code>
🌍 <b>المنطقة:</b> {player_info['region']}
📊 <b>المستوى:</b> {player_info['level']}
❤️ <b>الإعجابات:</b> {player_info['likes']}
🏅 <b>الشارات:</b> {player_info['badge_count']}
✨ <b>الخبرة:</b> {player_info['exp']}
📝 <b>الحالة:</b> {player_info['bio']}
📅 <b>تاريخ الإنشاء:</b> {create_date}
⏱️ <b>آخر دخول:</b> {last_login}

🎯 <b>BR رانك:</b> النقاط {player_info['br_point']} | النتيجة {player_info['br_score']}
🎯 <b>CS رانك:</b> النقاط {player_info['cs_point']} | النتيجة {player_info['cs_score']}
"""
        
        # إضافة معلومات الكلان إذا وجد
        if player_info.get('has_clan'):
            info_text += f"""
━━━━━━━━━━━━━━━━━━━━━━
👥 <b>الكلان:</b> {player_info['clan_name']}
🆔 <b>ID الكلان:</b> <code>{player_info['clan_id']}</code>
📊 <b>مستوى الكلان:</b> {player_info['clan_level']}
👥 <b>عدد الأعضاء:</b> {player_info['clan_members']}
"""
        
        # إضافة مدراء الكلان إذا وجدوا
        if player_info.get('clan_admins'):
            info_text += f"\n👑 <b>مدراء الكلان:</b>\n"
            for admin in player_info['clan_admins']:
                info_text += f"  • {admin['name']} (ID: <code>{admin['id']}</code>) - مستوى {admin['level']}\n"
        
        info_text += f"""
━━━━━━━━━━━━━━━━━━━━━━
🔹 /player_info [UID]
🔹 /check [UID]
🔹 /outfit [UID]
🔹 /visit [UID]

👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
        
        bot.edit_message_text(info_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text(
            f"❌ فشل جلب معلومات اللاعب\n\nخطأ: {player_info.get('error', 'Unknown')}\n\n👥 @ZikoB0SS | @noseyrobot\n📢 {GROUP_USERNAME}",
            chat_id=message.chat.id,
            message_id=wait_msg.message_id
        )

@bot.message_handler(commands=['check'])
def check_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"❌ استخدم: /check 123456789\n\n📢 {GROUP_USERNAME}")
        return
    
    uid = args[1]
    wait_msg = bot.reply_to(message, f"🔍 جاري فحص الحظر للـ UID: {uid}...")
    
    info_text = check_ban_simple(uid)
    
    bot.edit_message_text(info_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML")

@bot.message_handler(commands=['outfit'])
def outfit_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"❌ استخدم: /outfit 123456789\n\n📢 {GROUP_USERNAME}")
        return
    
    uid = args[1]
    wait_msg = bot.reply_to(message, f"🔍 جاري جلب الأوتفيت للـ UID: {uid}...")
    
    try:
        outfit_image, caption = get_outfit(uid)
        
        if outfit_image:
            photo = io.BytesIO(outfit_image)
            photo.name = f"outfit_{uid}.jpg"
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_photo(message.chat.id, photo, caption=caption, parse_mode="HTML")
        else:
            bot.edit_message_text(caption, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="HTML")
            
    except Exception as e:
        bot.edit_message_text(
            f"❌ خطأ في جلب الأوتفيت\n\n👥 @ZikoB0SS | @noseyrobot\n📢 {GROUP_USERNAME}",
            chat_id=message.chat.id,
            message_id=wait_msg.message_id
        )

@bot.message_handler(commands=['visit'])
def visit_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, f"❌ استخدم: /visit 123456789\n\n📢 {GROUP_USERNAME}")
        return
    
    uid = args[1]
    
    wait_msg = bot.reply_to(
        message, 
        f"""
📤 جاري إرسال الزيارات

🆔 UID: <code>{uid}</code>
🌍 المنطقة: ME
⏱️ الوقت: 15 ثانية...
━━━━━━━━━━━━━━━━━━━━━━
📢 {GROUP_USERNAME}
"""
    )
    
    thread = threading.Thread(
        target=send_visits_background,
        args=(uid, message.chat.id, wait_msg.message_id)
    )
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=['spam'])
def spam_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    
    try:
        if len(args) != 2:
            bot.reply_to(message, f"❌ صيغة خاطئة\nالاستخدام: /spam [UID]\nالمدة: 30 دقيقة ثابتة\n\n📢 {GROUP_USERNAME}")
            return
        
        target_id = args[1]
        hours = 0.5  # 30 دقيقة
        
        if not ChEck_Commande(target_id):
            bot.reply_to(message, f"❌ خطأ\nمعرف المستخدم غير صالح\n\n📢 {GROUP_USERNAME}")
            return
        
        with active_spam_lock:
            if target_id in active_spam_targets:
                bot.reply_to(message, f"⚠️ هذا الحساب في حالة سبام بالفعل\n\n📢 {GROUP_USERNAME}")
                return
            
            active_spam_targets[target_id] = {
                'active': True,
                'start_time': datetime.now(),
                'duration': hours,
                'type': 'normal',
                'initiator': message.from_user.id
            }
            
            with spam_start_times_lock:
                spam_start_times[target_id] = datetime.now()
            
            with spam_initiators_lock:
                spam_initiators[target_id] = message.from_user.id
            
            threading.Thread(target=normal_spam_worker, args=(target_id, hours), daemon=True).start()
            
            bot.reply_to(
                message, 
                f"""
✅ تم بدء السبام بنجاح

🎯 الهدف: <code>{target_id}</code>
⏱️ المدة: 30 دقيقة
⚡ السرعة: قصوى
👥 الحسابات: {len(connected_clients)}

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}\n\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['room'])
def room_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    
    try:
        if len(args) != 2:
            bot.reply_to(message, f"❌ صيغة خاطئة\nالاستخدام: /room [UID]\nالمدة: 30 دقيقة ثابتة\n\n📢 {GROUP_USERNAME}")
            return
        
        target_id = args[1]
        hours = 0.5  # 30 دقيقة
        
        if not ChEck_Commande(target_id):
            bot.reply_to(message, f"❌ خطأ\nمعرف المستخدم غير صالح\n\n📢 {GROUP_USERNAME}")
            return
        
        with active_spam_lock:
            if target_id in active_room_spam_targets:
                bot.reply_to(message, f"⚠️ هذا الحساب في حالة سبام روم بالفعل\n\n📢 {GROUP_USERNAME}")
                return
            
            active_room_spam_targets[target_id] = {
                'active': True,
                'start_time': datetime.now(),
                'duration': hours,
                'type': 'room',
                'initiator': message.from_user.id
            }
            
            with spam_start_times_lock:
                spam_start_times[f"room_{target_id}"] = datetime.now()
            
            with spam_initiators_lock:
                spam_initiators[f"room_{target_id}"] = message.from_user.id
            
            threading.Thread(target=room_spam_worker, args=(target_id, hours), daemon=True).start()
            
            bot.reply_to(
                message, 
                f"""
✅ تم بدء سبام الروم بنجاح

🎯 الهدف: <code>{target_id}</code>
⏱️ المدة: 30 دقيقة
⚡ السرعة: قصوى
👥 الحسابات: {len(connected_clients)}

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}\n\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['status'])
def status_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    
    try:
        if len(args) != 2:
            bot.reply_to(message, f"❌ صيغة خاطئة\nالاستخدام: /status [UID]\n\n📢 {GROUP_USERNAME}")
            return
        
        target_id = args[1]
        found = False
        
        with active_spam_lock:
            if target_id in active_spam_targets:
                with spam_start_times_lock:
                    if target_id in spam_start_times:
                        start_time = spam_start_times[target_id]
                        elapsed = datetime.now() - start_time
                        total_seconds = int(elapsed.total_seconds())
                        duration = active_spam_targets[target_id]['duration'] * 3600
                        remaining = duration - total_seconds
                        
                        if remaining > 0:
                            minutes = int(remaining // 60)
                            seconds = int(remaining % 60)
                            
                            bot.reply_to(
                                message,
                                f"""
📊 حالة السبام

🎯 الهدف: <code>{target_id}</code>
📌 النوع: سبام عادي
👥 الحسابات: {len(connected_clients)}
⏱️ الوقت المتبقي: {minutes} دقيقة {seconds} ثانية
👤 المنشئ: <code>{active_spam_targets[target_id]['initiator']}</code>

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
                            )
                            found = True
        
        if not found:
            with active_spam_lock:
                if target_id in active_room_spam_targets:
                    with spam_start_times_lock:
                        room_key = f"room_{target_id}"
                        if room_key in spam_start_times:
                            start_time = spam_start_times[room_key]
                            elapsed = datetime.now() - start_time
                            total_seconds = int(elapsed.total_seconds())
                            duration = active_room_spam_targets[target_id]['duration'] * 3600
                            remaining = duration - total_seconds
                            
                            if remaining > 0:
                                minutes = int(remaining // 60)
                                seconds = int(remaining % 60)
                                
                                bot.reply_to(
                                    message,
                                    f"""
📊 حالة السبام

🎯 الهدف: <code>{target_id}</code>
📌 النوع: سبام روم
👥 الحسابات: {len(connected_clients)}
⏱️ الوقت المتبقي: {minutes} دقيقة {seconds} ثانية
👤 المنشئ: <code>{active_room_spam_targets[target_id]['initiator']}</code>

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
                                )
                                found = True
        
        if not found:
            bot.reply_to(message, f"❌ لا يوجد سبام نشط للمعرف <code>{target_id}</code>\n\n📢 {GROUP_USERNAME}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}\n\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['stop_spam'])
def stop_spam_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    
    try:
        if len(args) != 2:
            bot.reply_to(message, f"❌ صيغة خاطئة\nالاستخدام: /stop_spam [UID]\n\n📢 {GROUP_USERNAME}")
            return
        
        target_id = args[1]
        
        with active_spam_lock:
            if target_id not in active_spam_targets:
                bot.reply_to(message, f"❌ لا يوجد سبام نشط للمعرف <code>{target_id}</code>\n\n📢 {GROUP_USERNAME}")
                return
            
            with spam_initiators_lock:
                initiator = spam_initiators.get(target_id)
                if initiator != message.from_user.id and message.from_user.id not in ADMIN_IDS:
                    bot.reply_to(
                        message, 
                        f"⛔ عذراً، لا يمكنك إيقاف هذا السبام. فقط من قام بإضافته يمكنه إيقافه.\n\n📢 {GROUP_USERNAME}"
                    )
                    return
                
                if target_id in spam_initiators:
                    del spam_initiators[target_id]
            
            with spam_start_times_lock:
                if target_id in spam_start_times:
                    del spam_start_times[target_id]
            
            del active_spam_targets[target_id]
            
            bot.reply_to(
                message, 
                f"""
✅ تم إيقاف السبام

🎯 الهدف: <code>{target_id}</code>

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}\n\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['stop_room'])
def stop_room_command(message):
    if not check_user_access_with_subscription(message):
        return
    
    args = message.text.split()
    
    try:
        if len(args) != 2:
            bot.reply_to(message, f"❌ صيغة خاطئة\nالاستخدام: /stop_room [UID]\n\n📢 {GROUP_USERNAME}")
            return
        
        target_id = args[1]
        room_key = f"room_{target_id}"
        
        with active_spam_lock:
            if target_id not in active_room_spam_targets:
                bot.reply_to(message, f"❌ لا يوجد سبام روم نشط للمعرف <code>{target_id}</code>\n\n📢 {GROUP_USERNAME}")
                return
            
            with spam_initiators_lock:
                initiator = spam_initiators.get(room_key)
                if initiator != message.from_user.id and message.from_user.id not in ADMIN_IDS:
                    bot.reply_to(
                        message, 
                        f"⛔ عذراً، لا يمكنك إيقاف هذا السبام. فقط من قام بإضافته يمكنه إيقافه.\n\n📢 {GROUP_USERNAME}"
                    )
                    return
                
                if room_key in spam_initiators:
                    del spam_initiators[room_key]
            
            with spam_start_times_lock:
                if room_key in spam_start_times:
                    del spam_start_times[room_key]
            
            del active_room_spam_targets[target_id]
            
            bot.reply_to(
                message, 
                f"""
✅ تم إيقاف سبام الروم

🎯 الهدف: <code>{target_id}</code>

━━━━━━━━━━━━━━━━━━━━━━
👥 @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}\n\n📢 {GROUP_USERNAME}")

# ==================== أوامر المالكين (مع أزرار الترويج) ====================

@bot.message_handler(commands=['addgroup'])
def add_group_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_type = message.chat.type
    chat_id = message.chat.id
    chat_title = message.chat.title or "مجموعة بدون اسم"
    
    if chat_type in ['group', 'supergroup'] and not is_owner(user_id, username):
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"""
🔔 طلب تفعيل مجموعة جديد

👤 المستخدم: {message.from_user.first_name}
🆔 ID: <code>{user_id}</code>
👤 اليوزرنيم: @{username if username else 'لا يوجد'}

📌 المجموعة: {chat_title}
🆔 ID: <code>{chat_id}</code>

⏱️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━
للرد على المستخدم: /reply {user_id} [الرسالة]
لتفعيل المجموعة: /addgroup_confirm {chat_id}
لحظر المستخدم: /block_user {user_id}
"""
                )
            except:
                pass
        
        # إرسال رد مع أزرار الترويج
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_group = types.InlineKeyboardButton("📢 مجموعة البوتات", url=GROUP_LINK)
        btn_dev = types.InlineKeyboardButton("👑 قناة المطور", url=DEV_CHANNEL)
        markup.add(btn_group, btn_dev)
        
        bot.reply_to(
            message, 
            f"""
📨 تم إرسال طلبك للمطورين

سيتم مراجعة طلبك والرد عليك قريباً
للتواصل المباشر: @ZikoB0SS | @noseyrobot

اشترك في قنواتنا:
""",
            reply_markup=markup
        )
        return
    
    if is_owner(user_id, username):
        if chat_type not in ['group', 'supergroup']:
            bot.send_message(chat_id, "❌ هذا الأمر يعمل فقط في المجموعات!")
            return
        
        ALLOWED_GROUPS[str(chat_id)] = {
            "added_by": user_id,
            "added_at": time.time(),
            "group_title": chat_title,
            "added_by_username": username
        }
        save_allowed_groups()
        
        for admin_id in ADMIN_IDS:
            if admin_id != user_id:
                try:
                    bot.send_message(
                        admin_id,
                        f"""
✅ تم تفعيل مجموعة جديدة

📌 المجموعة: {chat_title}
🆔 ID: <code>{chat_id}</code>
👤 بواسطة: @{username}

⏱️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                    )
                except:
                    pass
        
        bot.send_message(chat_id, f"✅ تم تفعيل البوت في هذه المجموعة!\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['removegroup'])
def remove_group_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_owner(user_id, username):
        return
    
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    if chat_type not in ['group', 'supergroup']:
        bot.send_message(chat_id, "❌ هذا الأمر يعمل فقط في المجموعات!")
        return
    
    if str(chat_id) in ALLOWED_GROUPS:
        del ALLOWED_GROUPS[str(chat_id)]
        save_allowed_groups()
        bot.send_message(chat_id, f"✅ تم تعطيل البوت في هذه المجموعة!\n📢 {GROUP_USERNAME}")

@bot.message_handler(commands=['groups'])
def list_groups_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not is_owner(user_id, username):
        return
    
    if not ALLOWED_GROUPS:
        bot.send_message(message.chat.id, f"📋 لا توجد مجموعات مفعلة.\n\n👥 @ZikoB0SS | @noseyrobot\n📢 {GROUP_USERNAME}")
        return
    
    text = "📋 المجموعات المفعلة\n\n"
    for group_id, group_info in ALLOWED_GROUPS.items():
        text += f"📌 {group_info['group_title']}\n🆔 <code>{group_id}</code>\n\n"
    
    text += f"━━━━━━━━━━━━━━━━━━━━━━\n👥 @ZikoB0SS | @noseyrobot\n📢 {GROUP_USERNAME}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['reply'])
def reply_to_user(message):
    user_id = message.from_user.id
    if not is_owner(user_id, message.from_user.username):
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "❌ استخدم: /reply [user_id] [الرسالة]")
        return
    
    target_user = int(args[1])
    reply_text = args[2]
    
    try:
        bot.send_message(
            target_user,
            f"""
📬 رد من المطورين

{reply_text}

━━━━━━━━━━━━━━━━━━━━━━
للتواصل: @ZikoB0SS | @noseyrobot
📢 {GROUP_USERNAME}
"""
        )
        bot.reply_to(message, f"✅ تم إرسال الرد إلى {target_user}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الإرسال: {e}")

@bot.message_handler(commands=['block_user'])
def block_user(message):
    user_id = message.from_user.id
    if not is_owner(user_id, message.from_user.username):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ استخدم: /block_user [user_id]")
        return
    
    target_user = int(args[1])
    BLOCKED_USERS.add(target_user)
    save_blocked_users()
    bot.reply_to(message, f"✅ تم حظر المستخدم {target_user}")

@bot.message_handler(commands=['addgroup_confirm'])
def addgroup_confirm(message):
    user_id = message.from_user.id
    if not is_owner(user_id, message.from_user.username):
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❌ استخدم: /addgroup_confirm [chat_id]")
        return
    
    chat_id = int(args[1])
    
    try:
        chat = bot.get_chat(chat_id)
        chat_title = chat.title or "مجموعة بدون اسم"
        
        ALLOWED_GROUPS[str(chat_id)] = {
            "added_by": user_id,
            "added_at": time.time(),
            "group_title": chat_title,
            "added_by_username": message.from_user.username
        }
        save_allowed_groups()
        
        bot.reply_to(message, f"✅ تم تفعيل المجموعة {chat_title}")
        
        try:
            bot.send_message(
                chat_id,
                f"✅ تم تفعيل البوت في هذه المجموعة!\nأهلاً بكم في بوت الخدمات\n📢 {GROUP_USERNAME}"
            )
        except:
            pass
            
    except Exception as e:
        bot.reply_to(message, f"❌ فشل التفعيل: {e}")

@bot.message_handler(commands=['restart'])
def restart_command(message):
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.reply_to(message, "❌ هذا الأمر للمشرفين فقط")
        return
    
    bot.reply_to(message, "🔄 جاري إعادة تشغيل الحسابات...")
    threading.Thread(target=restart_accounts, daemon=True).start()

# ==================== دوال السبام (بدون تغيير) ====================

def restart_accounts():
    time.sleep(2)
    ResTarT_BoT()

def AuTo_ResTartinG():
    time.sleep(6 * 60 * 60)
    print(' - AuTo ResTartinG The BoT ... ! ')
    p = psutil.Process(os.getpid())
    for handler in p.open_files():
        try:
            os.close(handler.fd)
        except Exception as e:
            print(f" - Error CLose Files : {e}")
    for conn in p.net_connections():
        try:
            if hasattr(conn, 'fd'):
                os.close(conn.fd)
        except Exception as e:
            print(f" - Error CLose Connection : {e}")
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    python = sys.executable
    os.execl(python, python, *sys.argv)
       
def ResTarT_BoT():
    print(' - ResTartinG The BoT ... ! ')
    p = psutil.Process(os.getpid())
    open_files = p.open_files()
    connections = p.net_connections()
    for handler in open_files:
        try:
            os.close(handler.fd)
        except Exception:
            pass           
    for conn in connections:
        try:
            conn.close()
        except Exception:
            pass
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    python = sys.executable
    os.execl(python, python, *sys.argv)

def GeT_Time(timestamp):
    last_login = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - last_login   
    d = diff.days
    h , rem = divmod(diff.seconds, 3600)
    m , s = divmod(rem, 60)    
    return d, h, m, s

def Time_En_Ar(t): 
    return ' '.join(t.replace("Day","Day").replace("Hour","Hour").replace("Min","Min").replace("Sec","Sec").split(" - "))
    
Thread(target = AuTo_ResTartinG , daemon = True).start()

ACCOUNTS = []

def load_accounts_from_file(filename="accs.json"):
    accounts = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            
            if isinstance(data, list):
                for account in data:
                    if isinstance(account, dict):
                        account_id = account.get('uid', '')
                        password = account.get('password', '')
                        
                        if account_id:
                            accounts.append({
                                'id': str(account_id),
                                'password': password
                            })
            
            print(f"Loaded {len(accounts)} accounts from {filename}")
            
    except FileNotFoundError:
        print(f"File {filename} not found!")
    except json.JSONDecodeError:
        print(f"JSON format error in file {filename}!")
    except Exception as e:
        print(f"Error reading file: {e}")
    
    return accounts

ACCOUNTS = load_accounts_from_file()

def normal_spam_worker(target_id, duration_hours=None):
    print(f"🔥 Starting NORMAL SPAM on target: {target_id} at MAX SPEED")
    
    start_time = datetime.now()
    
    while True:
        with active_spam_lock:
            if target_id not in active_spam_targets:
                print(f"Normal spam stopped on target: {target_id}")
                break
                
            if duration_hours:
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() >= duration_hours * 3600:
                    print(f"Normal spam duration ended for target: {target_id}")
                    with spam_initiators_lock:
                        if target_id in spam_initiators:
                            del spam_initiators[target_id]
                    with spam_start_times_lock:
                        if target_id in spam_start_times:
                            del spam_start_times[target_id]
                    del active_spam_targets[target_id]
                    break
        
        try:
            send_normal_spam_max_speed(target_id)
        except Exception as e:
            print(f"Error in normal spam on {target_id}: {e}")
            time.sleep(0.5)

def room_spam_worker(target_id, duration_hours=None):
    print(f"🔥 Starting ROOM SPAM on target: {target_id} at MAX SPEED")
    
    start_time = datetime.now()
    
    while True:
        with active_spam_lock:
            if target_id not in active_room_spam_targets:
                print(f"Room spam stopped on target: {target_id}")
                break
                
            if duration_hours:
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() >= duration_hours * 3600:
                    print(f"Room spam duration ended for target: {target_id}")
                    with spam_initiators_lock:
                        room_key = f"room_{target_id}"
                        if room_key in spam_initiators:
                            del spam_initiators[room_key]
                    with spam_start_times_lock:
                        if room_key in spam_start_times:
                            del spam_start_times[room_key]
                    del active_room_spam_targets[target_id]
                    break
        
        try:
            send_room_spam_max_speed(target_id)
        except Exception as e:
            print(f"Error in room spam on {target_id}: {e}")
            time.sleep(0.5)

def send_normal_spam_max_speed(target_id):
    active_accounts = []
    with connected_clients_lock:
        for account_id, client in connected_clients.items():
            if (hasattr(client, 'CliEnts2') and client.CliEnts2 and 
                hasattr(client, 'key') and client.key and 
                hasattr(client, 'iv') and client.iv):
                active_accounts.append((account_id, client))
    
    if not active_accounts:
        return
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for account_id, client in active_accounts:
            for burst in range(BURST_SIZE):
                future = executor.submit(send_normal_spam_burst, client, account_id, target_id)
                futures.append(future)
        
        for future in as_completed(futures, timeout=0.5):
            try:
                future.result()
            except Exception as e:
                pass

def send_normal_spam_burst(client, account_id, target_id):
    try:
        for i in range(5):
            client.CliEnts2.send(SEnd_InV(1, target_id, client.key, client.iv))
            client.CliEnts2.send(OpEnSq(client.key, client.iv))
            client.CliEnts2.send(SPamSq(target_id, client.key, client.iv))
    except Exception as e:
        pass

def send_room_spam_max_speed(target_id):
    active_accounts = []
    with connected_clients_lock:
        for account_id, client in connected_clients.items():
            if (hasattr(client, 'CliEnts2') and client.CliEnts2 and 
                hasattr(client, 'key') and client.key and 
                hasattr(client, 'iv') and client.iv):
                active_accounts.append((account_id, client))
    
    if not active_accounts:
        return
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for account_id, client in active_accounts:
            try:
                client.CliEnts2.send(openroom(client.key, client.iv))
            except:
                pass
            
            for burst in range(BURST_SIZE):
                future = executor.submit(send_room_spam_burst, client, account_id, target_id)
                futures.append(future)
        
        for future in as_completed(futures, timeout=0.5):
            try:
                future.result()
            except Exception as e:
                pass

def send_room_spam_burst(client, account_id, target_id):
    try:
        for i in range(5):
            client.CliEnts2.send(spmroom(client.key, client.iv, target_id))
    except Exception as e:
        pass

class FF_CLient():
    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.key = None
        self.iv = None
        self.connection_active = True
        self.max_retries = 5
        self.retry_delay = 10
        self.Get_FiNal_ToKen_0115()     
            
    def Connect_SerVer_OnLine(self , Token , tok , host , port , key , iv , host2 , port2):
        try:
            self.AutH_ToKen_0115 = tok    
            self.CliEnts2 = socket.create_connection((host2 , int(port2)))
            self.CliEnts2.send(bytes.fromhex(self.AutH_ToKen_0115))                  
        except Exception as e:
            print(f"Error in Connect_SerVer_OnLine: {e}")
            return
        
        while self.connection_active:
            try:
                self.DaTa2 = self.CliEnts2.recv(99999)
                if '0500' in self.DaTa2.hex()[0:4] and len(self.DaTa2.hex()) > 30:	         	    	    
                    self.packet = json.loads(DeCode_PackEt(f'08{self.DaTa2.hex().split("08", 1)[1]}'))
                    self.AutH = self.packet['5']['data']['7']['data']
            except Exception as e:
                print(f"Error in Connect_SerVer_OnLine receive: {e}")
                time.sleep(1)
                                                            
    def Connect_SerVer(self , Token , tok , host , port , key , iv , host2 , port2):
        try:
            self.AutH_ToKen_0115 = tok    
            self.CliEnts = socket.create_connection((host , int(port)))
            self.CliEnts.send(bytes.fromhex(self.AutH_ToKen_0115))  
            self.DaTa = self.CliEnts.recv(1024)          	        
            threading.Thread(target=self.Connect_SerVer_OnLine, args=(Token , tok , host , port , key , iv , host2 , port2)).start()
            self.Exemple = xMsGFixinG('12345678')
            
            self.key = key
            self.iv = iv
            
            with connected_clients_lock:
                connected_clients[self.id] = self
                print(f"Account {self.id} registered, total accounts: {len(connected_clients)}")
            
            while True:      
                try:
                    self.DaTa = self.CliEnts.recv(1024)   
                    if len(self.DaTa) == 0 or (hasattr(self, 'DaTa2') and len(self.DaTa2) == 0):	            		
                        print(f"Connection lost for account {self.id}, reconnecting...")
                        try:            		    
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            
                            time.sleep(3)
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)                    		                    
                        except:
                            print(f"Failed to reconnect account {self.id}")
                            with connected_clients_lock:
                                if self.id in connected_clients:
                                    del connected_clients[self.id]
                            break	            
                                      
                    if '/pp/' in self.input_msg[:4]:
                        self.target_id = self.input_msg[4:]	 
                        self.Zx = ChEck_Commande(self.target_id)
                        if True == self.Zx:	            		     
                            threading.Thread(target=send_normal_spam_max_speed, args=(self.target_id,)).start()
                            time.sleep(2.5)    			         
                            self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] SuccEss Spam To {xMsGFixinG(self.target_id)} From All Accounts\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))
                            time.sleep(1.3)
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		      	
                        elif False == self.Zx: 
                            self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] - PLease Use /pp/<id>\n - Ex : /pp/{self.Exemple}\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))	
                            time.sleep(1.1)
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		

                except Exception as e:
                    print(f"Error in Connect_SerVer: {e}")
                    try:
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                    except:
                        pass
                    time.sleep(5)
                    try:
                        self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)
                    except:
                        print(f"Final reconnection failed for account {self.id}")
                        with connected_clients_lock:
                            if self.id in connected_clients:
                                del connected_clients[self.id]
                        break
        except Exception as e:
            print(f"Error in Connect_SerVer initial connection: {e}")
            time.sleep(self.retry_delay)
                                    
    def GeT_Key_Iv(self , serialized_data):
        my_message = xKEys.MyMessage()
        my_message.ParseFromString(serialized_data)
        timestamp , key , iv = my_message.field21 , my_message.field22 , my_message.field23
        timestamp_obj = Timestamp()
        timestamp_obj.FromNanoseconds(timestamp)
        timestamp_seconds = timestamp_obj.seconds
        timestamp_nanos = timestamp_obj.nanos
        combined_timestamp = timestamp_seconds * 1_000_000_000 + timestamp_nanos
        return combined_timestamp , key , iv    

    def Guest_GeneRaTe(self, uid, password):
        urls = [
            "https://100067.connect.garena.com/oauth/guest/token/grant",
            "https://100067.connect.garena.com/api/oauth/guest/token/grant",
            "https://account.garena.com/api/oauth/guest/token/grant",
            "https://accounts.garena.com/oauth/guest/token/grant",
            "https://connect.garena.com/oauth/guest/token/grant",
            "https://api.garena.com/oauth/guest/token/grant"
        ]
        
        self.headers = {
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        self.dataa = {
            "uid": f"{uid}",
            "password": f"{password}",
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        }
        
        for url in urls:
            try:
                print(f"Trying URL: {url}")
                response = requests.post(
                    url, 
                    headers=self.headers, 
                    data=self.dataa,
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    try:
                        response_json = response.json()
                        if 'access_token' in response_json and 'open_id' in response_json:
                            print(f"Success with URL: {url}")
                            self.Access_ToKen = response_json['access_token']
                            self.Access_Uid = response_json['open_id']
                            time.sleep(0.2)
                            return self.ToKen_GeneRaTe(self.Access_ToKen, self.Access_Uid)
                        else:
                            print(f"Response missing required fields from {url}")
                    except json.JSONDecodeError:
                        print(f"Invalid JSON response from {url}")
                else:
                    print(f"HTTP {response.status_code} from {url}")
                    
            except requests.exceptions.SSLError as e:
                print(f"SSL Error with {url}: {e}")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"Connection Error with {url}: {e}")
                continue
            except requests.exceptions.Timeout as e:
                print(f"Timeout with {url}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error with {url}: {e}")
                continue
        
        print(f"All URLs failed for account {uid}, retrying in {self.retry_delay} seconds...")
        time.sleep(self.retry_delay)
        return self.Guest_GeneRaTe(uid, password)
                                        
    def GeT_LoGin_PorTs(self , JwT_ToKen , PayLoad):
        self.UrL = 'https://clientbp.ggwhitehawk.com/GetLoginData'
        self.HeadErs = {
            'Expect': '100-continue',
            'Authorization': f'Bearer {JwT_ToKen}',
            'X-Unity-Version': '2022.3.47f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': 'OB52',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Accept-Encoding': 'deflate, gzip',
        }        
        
        try:
            self.Res = requests.post(self.UrL , headers=self.HeadErs , data=PayLoad , verify=False , timeout=10)
            
            if self.Res.status_code == 200:
                try:
                    self.BesTo_data = json.loads(DeCode_PackEt(self.Res.content.hex()))  
                    address , address2 = self.BesTo_data['32']['data'] , self.BesTo_data['14']['data'] 
                    ip , ip2 = address[:len(address) - 6] , address2[:len(address2) - 6]
                    port , port2 = address[len(address) - 5:] , address2[len(address2) - 5:]             
                    return ip , port , ip2 , port2
                except Exception as e:
                    print(f"Error parsing GetLoginData response: {e}")
            else:
                print(f"GetLoginData returned status code: {self.Res.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error in GeT_LoGin_PorTs: {e}")
        except Exception as e:
            print(f"Unexpected error in GeT_LoGin_PorTs: {e}")
            
        print(" - Failed To Get Ports!")
        return None, None, None, None
        
    def ToKen_GeneRaTe(self , Access_ToKen , Access_Uid):
        self.UrL = "https://loginbp.ggwhitehawk.com/MajorLogin"
        self.HeadErs = {
            'X-Unity-Version': '2022.3.47f1',
            'ReleaseVersion': 'OB52',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-GA': 'v1 1',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Accept-Encoding': 'deflate, gzip',
        }   
        
        self.dT = bytes.fromhex('1a13323032362d30312d31342031323a31393a3032220966726565206669726528013a07312e3132302e324232416e64726f6964204f532039202f204150492d3238202850492f72656c2e636a772e32303232303531382e313134313333294a0848616e6468656c64520c4d544e2f537061636574656c5a045749464960800a68d00572033234307a2d7838362d3634205353453320535345342e3120535345342e32204156582041565832207c2032343030207c20348001e61e8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e329a012b476f6f676c657c36323566373136662d393161372d343935622d396631362d303866653964336336353333a2010d3137362e32382e3134352e3239aa01026172b201203931333263366662373263616363666463383132306439656332636330366238ba010134c2010848616e6468656c64ca010d4f6e65506c7573204135303130d201025347ea014033646661396162396432353237306661663433326637623532383536346265396563343739306263373434613465626137303232353230373432376430633430f00101ca020c4d544e2f537061636574656cd2020457494649ca03203161633462383065636630343738613434323033626638666163363132306635e003b5ee02e803c28302f003af13f80384078004cf92028804b5ee029004cf92029804b5ee02b00404c80403d2043d2f646174612f6170702f636f6d2e6474732e667265656669726574682d49316855713474347641365f516f34432d58676165513d3d2f6c69622f61726de00401ea045f65363261623933353464386662356662303831646233333861636233333439317c2f646174612f6170702f636f6d2e6474732e667265656669726574682d49316855713474347641365f516f34432d58676165513d3d2f626173652e61706bf00406f804018a050233329a050a32303139313139363234b205094f70656e474c455332b805ff01c00504e005edb402ea05093372645f7061727479f2055c4b7173485438512b6c73302b4464496c2f4f617652726f7670795a596377676e51485151636d57776a476d587642514b4f4d63747870796f7054515754487653354a714d6967476b534c434c423651387839544161764d666c6a6f3d8806019006019a060134a2060134b206224006474f56540a011a5d0e115e00170d4b6e085709510a685a02586800096f000161')
        
        self.dT = self.dT.replace(b'2026-01-14 12:19:02' , str(datetime.now())[:-7].encode())        
        self.dT = self.dT.replace(b'3dfa9ab9d25270faf432f7b528564be9ec4790bc744a4eba70225207427d0c40' , Access_ToKen.encode())
        self.dT = self.dT.replace(b'9132c6fb72caccfdc8120d9ec2cc06b8' , Access_Uid.encode())
        
        try:
            hex_data = self.dT.hex()
            encoded_data = EnC_AEs(hex_data)
            
            if not all(c in '0123456789abcdefABCDEF' for c in encoded_data):
                print("Invalid hex output from EnC_AEs, using alternative encoding")
                encoded_data = hex_data
            
            self.PaYload = bytes.fromhex(encoded_data)
        except Exception as e:
            print(f"Error in encoding: {e}")
            self.PaYload = self.dT
        
        try:
            self.ResPonse = requests.post(self.UrL, headers=self.HeadErs, data=self.PaYload, verify=False, timeout=10)        
            
            if self.ResPonse.status_code == 200 and len(self.ResPonse.text) > 10:
                try:
                    self.BesTo_data = json.loads(DeCode_PackEt(self.ResPonse.content.hex()))
                    self.JwT_ToKen = self.BesTo_data['8']['data']           
                    self.combined_timestamp , self.key , self.iv = self.GeT_Key_Iv(self.ResPonse.content)
                    ip , port , ip2 , port2 = self.GeT_LoGin_PorTs(self.JwT_ToKen , self.PaYload)            
                    return self.JwT_ToKen , self.key , self.iv, self.combined_timestamp , ip , port , ip2 , port2
                except Exception as e:
                    print(f"Error parsing MajorLogin response: {e}")
            else:
                print(f"MajorLogin failed with status code: {self.ResPonse.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error in ToKen_GeneRaTe: {e}")
        except Exception as e:
            print(f"Unexpected error in ToKen_GeneRaTe: {e}")
            
        print("Retrying ToKen_GeneRaTe...")
        time.sleep(self.retry_delay)
        return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
      
    def Get_FiNal_ToKen_0115(self):
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                result = self.Guest_GeneRaTe(self.id , self.password)
                
                if not result:
                    print(f"Failed to get tokens for account {self.id}, retrying... ({retry_count + 1}/{self.max_retries})")
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue
                    
                token , key , iv , Timestamp , ip , port , ip2 , port2 = result
                
                if not all([ip, port, ip2, port2]):
                    print(f"Failed to get ports for account {self.id}, retrying... ({retry_count + 1}/{self.max_retries})")
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue
                    
                self.JwT_ToKen = token        
                try:
                    self.AfTer_DeC_JwT = jwt.decode(token, options={"verify_signature": False})
                    self.AccounT_Uid = self.AfTer_DeC_JwT.get('account_id')
                    self.EncoDed_AccounT = hex(self.AccounT_Uid)[2:]
                    self.HeX_VaLue = DecodE_HeX(Timestamp)
                    self.TimE_HEx = self.HeX_VaLue
                    self.JwT_ToKen_ = token.encode().hex()
                    print(f'✅ Account connected: {self.AccounT_Uid}')
                except Exception as e:
                    print(f"Error decoding JWT: {e}")
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue
                    
                try:
                    self.Header = hex(len(EnC_PacKeT(self.JwT_ToKen_, key, iv)) // 2)[2:]
                    length = len(self.EncoDed_AccounT)
                    self.__ = '00000000'
                    if length == 9: self.__ = '0000000'
                    elif length == 8: self.__ = '00000000'
                    elif length == 10: self.__ = '000000'
                    elif length == 7: self.__ = '000000000'
                    else:
                        print(f'Unexpected length: {length}')
                        self.__ = '00000000'            
                    
                    self.Header = f'0115{self.__}{self.EncoDed_AccounT}{self.TimE_HEx}00000{self.Header}'
                    self.FiNal_ToKen_0115 = self.Header + EnC_PacKeT(self.JwT_ToKen_ , key , iv)
                except Exception as e:
                    print(f"Error creating final token: {e}")
                    retry_count += 1
                    time.sleep(self.retry_delay)
                    continue
                    
                self.AutH_ToKen = self.FiNal_ToKen_0115
                self.Connect_SerVer(self.JwT_ToKen , self.AutH_ToKen , ip , port , key , iv , ip2 , port2)        
                return self.AutH_ToKen , key , iv
                
            except Exception as e:
                print(f"Error in Get_FiNal_ToKen_0115 for account {self.id}: {e}")
                retry_count += 1
                time.sleep(self.retry_delay)
        
        print(f"❌ Failed to connect account {self.id} after {self.max_retries} attempts")
        return None, None, None

def start_account(account):
    try:
        print(f"Starting account: {account['id']}")
        client = FF_CLient(account['id'], account['password'])
        if client.key and client.iv:
            print(f"✅ Account {account['id']} connected successfully")
        else:
            print(f"⚠️ Account {account['id']} connection incomplete")
    except Exception as e:
        print(f"Error starting account {account['id']}: {e}")
        time.sleep(5)
        start_account(account)

def run_bot():
    print("🤖 Bot started...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot polling error: {e}")
        time.sleep(5)
        run_bot()

def StarT_SerVer():
    threads = []
    
    for account in ACCOUNTS:
        thread = threading.Thread(target=start_account, args=(account,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(1)
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting FPI SX TEAM BOT on RENDER...")
    print(f"📅 Time: {datetime.now()}")
    print(f"📊 Total accounts: {len(ACCOUNTS)}")
    print("⚡ MAX SPEED MODE ENABLED")
    print(f"⚡ Workers: {MAX_WORKERS}, Burst: {BURST_SIZE}")
    print("=" * 50)
    print("🤖 Services Bot Loaded")
    load_allowed_groups()
    load_blocked_users()
    print(f"👑 Owners: @ZikoB0SS, @noseyrobot")
    print(f"📢 Group: {GROUP_USERNAME}")
    print(f"👑 Channel: {DEV_USERNAME}")
    print("=" * 50)
    print("✅ Bot ready for Render - All data stored in memory")
    print("=" * 50)
    
    # تشغيل حسابات اللعبة في خيط منفصل
    game_thread = threading.Thread(target=StarT_SerVer, daemon=True)
    game_thread.start()
    
    # تشغيل البوت في الخيط الرئيسي
    print("🤖 Starting Telegram bot...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)