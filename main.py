import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Sharx Bot is active and running!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()

# --- دالة التحقق مما إذا كان المستخدم مشرفاً في القروب ---
def is_user_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# --- [دالة احترافية]: البحث الشامل عبر الإنترنت (للخاص) ---
def fetch_advanced_web_lookup(username):
    clean_un = username.replace("@", "").strip()
    if "t.me/" in clean_un:
        clean_un = clean_un.split("t.me/")[-1].split("/")[0].strip()
    elif "telegram.me/" in clean_un:
        clean_un = clean_un.split("telegram.me/")[-1].split("/")[0].strip()
        
    url = f"https://t.me/{clean_un}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("meta", property="og:title")
            desc_tag = soup.find("meta", property="og:description")
            
            name = title_tag["content"] if title_tag else clean_un
            bio = desc_tag["content"] if desc_tag else "لايوجد وصف / No bio"
            
            return {
                "found": True,
                "name": name,
                "username": f"@{clean_un}",
                "bio": bio,
                "note": "✨ تم جلب البيانات بنجاح عبر البحث الشامل 🌐"
            }
    except Exception:
        pass
    return {"found": False}

# --- [قائمة القروب المخصصة]: زرين فقط (إنشاء مسابقة وإنهاء مسابقة) ---
def create_group_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية (قيد التطوير)", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية (قيد التطوير)", callback_data="cmd_end")
    )
    return markup

# --- القائمة الرئيسية الكاملة (للخاص) ---
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث / ID & Search ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية (قيد التطوير)", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية (قيد التطوير)", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة / Close", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع / Quick Selection", callback_data="show_keyboard"),
        types.InlineKeyboardButton("🌐 البحث اليدوي المباشر / Manual Search", callback_data="method_username"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة / Forward Analysis", callback_data="method_forward"),
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية / Home 🏠", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_user = types.KeyboardButton(
        text="👤 اختر مستخدم / Select User", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختر مجموعة أو قناة / Select Chat", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
    return markup

def create_home_return_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية / Home 🏠", callback_data="cmd_home"))
    return markup

def format_user_report(u, chat_id=None):
    uname = f"@{u.username}" if u.username else "لا يوجد يوزر / No Username"
    role_status = "عضو عادي (Member)"
    
    if chat_id:
        try:
            member = bot.get_chat_member(chat_id, u.id)
            if member.status == 'creator':
                role_status = "👑 مالك القروب (Creator)"
            elif member.status == 'administrator':
                role_status = "🛡️ مشرف في القروب (Admin)"
            else:
                role_status = "👤 عضو أساسي في القروب (Member)"
        except Exception:
            role_status = "👤 عضو"

    return (
        f"🛡️ <b>[ تقرير حماية شركس - سجل الحساب ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{u.id}</code>\n"
        f"📛 اسم الحساب: {u.first_name}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 الصلاحية: {role_status}\n"
        f"━━━━━━━━━━━━━━━"
    )

def format_chat_report(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر / No Username"
    chat_type_ar = "قناة عامة" if c.type == "channel" else "مجموعة تفاعلية"
    return (
        f"🛡️ <b>[ تقرير حماية شركس - جهة خارجية ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{c.id}</code>\n"
        f"📛 اسم الجهة: {c.title}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 التصنيف: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━━"
    )

# --- معالج أمر البداية /start (للخاص) ---
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
    bot.send_message(
        message.chat.id,
        "مياو! 🐱✨\n"
        "أهلاً بك في النسخة المطورّة من بوت حماية شركس.\n"
        "اختر ما يناسبك من القائمة أدناه:",
        reply_markup=create_main_menu_markup()
    )

# --- معالج الأزرار الشفافة (Inline Callbacks) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "cmd_create" or call.data == "cmd_end":
        try:
            bot.answer_callback_query(call.id, "هذه الميزة قيد التطوير حالياً 🚧", show_alert=True)
        except Exception:
            pass
    elif call.data == "cmd_id_help":
        bot.edit_message_text(
            "🐾 أهلاً بك في قسم البحث والتحكم المتقدم.\n"
            "Welcome to ID & Advanced Search Section.\n\n"
            "اختر الطريقة / Choose method:",
            chat_id,
            message_id,
            reply_markup=create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        bot.send_message(
            chat_id,
            "👇 استخدم الأزرار الظاهرة أسفل الشاشة للاختيار المباشر:",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif call.data == "method_username":
        bot.edit_message_text(
            "🎯 <b>[ وضع البحث اليدوي المباشر ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر (مثل `@username`) أو الرابط لجلب نتائجه فوراً 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "method_forward":
        bot.edit_message_text(
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة لاستخراج بيانات صاحبها السرية!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "cmd_home":
        bot.edit_message_text(
            "🏠 عودة للقائمة الرئيسية / Main Menu 🐱:",
            chat_id,
            message_id,
            reply_markup=create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        bot.edit_message_text(
            "❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.",
            chat_id,
            message_id,
            reply_markup=None
        )

# --- معالج الاختيارات السفلية ---
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    response_text = ""
    target_id = None

    if message.users_shared:
        target_id = message.users_shared.user_ids[0]
    elif message.chat_shared:
        target_id = message.chat_shared.chat_id

    if target_id:
        try:
            chat_info = bot.get_chat(target_id)
            if chat_info.type == "private":
                response_text = format_user_report(chat_info, message.chat.id)
            else:
                response_text = format_chat_report(chat_info)
        except Exception:
            response_text = (
                f"🛡️ <b>[ تقرير حماية شركس - الاختيار المباشر ]</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 المعرف الثابت: <code>{target_id}</code>\n"
                f"✨ تم استلام المعرف بنجاح.\n"
                f"━━━━━━━━━━━━━━━"
            )
    else:
        response_text = "⚠️ لم يتم استلام أي معرف صالح."

    bot.send_message(
        message.chat.id, 
        response_text, 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )

# --- معالج الدردشة الخاصة (Private) بالكامل ---
@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_private_messages(message):
    response_text = ""
    
    if message.forward_from:
        response_text = format_user_report(message.forward_from)
    elif message.forward_from_chat:
        response_text = format_chat_report(message.forward_from_chat)
    elif message.text:
        text = message.text.strip()
        if text.startswith("/"):
            return

        clean_username = text
        if "t.me/" in text:
            clean_username = text.split("t.me/")[-1].split("/")[0].strip()
        elif "telegram.me/" in text:
            clean_username = text.split("telegram.me/")[-1].split("/")[0].strip()
        else:
            clean_username = text.replace("@", "").strip()

        if len(clean_username) >= 3:
            try:
                chat_info = bot.get_chat("@" + clean_username)
                if chat_info.type == "private":
                    response_text = format_user_report(chat_info)
                else:
                    response_text = format_chat_report(chat_info)
            except Exception:
                adv_result = fetch_advanced_web_lookup(clean_username)
                if adv_result["found"]:
                    response_text = (
                        f"🛡️ <b>[ تقرير البحث الشامل - شركس بوت ]</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📛 الاسم: {adv_result['name']}\n"
                        f"🔗 اليوزر: {adv_result['username']}\n"
                        f"📝 الوصف: {adv_result['bio']}\n"
                        f"━━━━━━━━━━━━━━━"
                    )
                else:
                    response_text = f"❌ لم يتم العثور على نتائج مطابقة لـ: <b>{text}</b>"

    if response_text:
        bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=create_home_return_markup())

# --- معالج المجموعات (القروبات حصراً: زرين للمسابقات + ظهور القائمة بمناداة "شركس" + كشف الرد للمشرفين) ---
@bot.message_handler(chat_types=["group", "supergroup"], content_types=["text"])
def handle_group_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id

    # 1. إذا نادى البوت بكلمة "شركس" ولم يكن رد (Reply) -> يظهر زرين المسابقات فقط
    if "شركس" in text and not message.reply_to_message:
        bot.reply_to(
            message,
            "مياو! 🐱 أهلاً بك. إليك خيارات المسابقات:",
            reply_markup=create_group_menu_markup()
        )
        return

    # 2. ميزة الرد (Reply) مع مناداة البوت (مثل "شركس" أو "آيدي") لجلب معلومات الشخص المردود عليه (للمشرفين حصراً)
    if message.reply_to_message:
        if "شركس" in text or "آيدي" in text or "id" in text.lower() or "معلومات" in text:
            if not is_user_admin(chat_id, user_id):
                bot.reply_to(message, "⚠️ عذراً، هذه الميزة مخصصة لمشرفي المجموعة فقط!")
                return

            target_user = message.reply_to_message.from_user
            if target_user:
                report = format_user_report(target_user, chat_id)
                bot.reply_to(message, report, parse_mode="HTML")

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
    
    time.sleep(3)
    try:
        bot.remove_webhook()
        print("Old webhook removed successfully.")
    except Exception as e:
        print(f"Error removing webhook: {e}")

    while True:
        try:
            print("Starting bot polling safely...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
