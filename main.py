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

# --- [دالة احترافية]: البحث الشامل عبر الإنترنت للروابط واليوزرات ---
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

# --- [دالة احترافية]: لوحة المفاتيح السفلية (تظهر عند الطلب فقط) ---
def create_dynamic_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_user = types.KeyboardButton(
        text="👤 اختر مستخدم من الهاتف", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختر مجموعة أو قناة", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
    return markup

# --- [دالة احترافية]: القائمة الرئيسية الشفافة (مميزة ومزخرفة) ---
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث الشامل ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية جديدة", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

# --- [دالة احترافية]: قائمة خيارات البحث والتحكم ---
def create_id_help_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 فتح لوحة الاختيار السريع (أسفل الشاشة)", callback_data="show_keyboard"),
        types.InlineKeyboardButton("🌐 البحث اليدوي (يوزر / رابط مباشر)", callback_data="method_username"),
        types.InlineKeyboardButton("📥 البحث عبر إعادة توجيه الرسائل", callback_data="method_forward"),
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية 🏠", callback_data="cmd_home")
    )
    return markup

# --- [دالة احترافية]: زر العودة الثابت تحت التقارير ---
def create_home_return_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية 🏠", callback_data="cmd_home"))
    return markup

# --- [دالة احترافية]: تنسيق معلومات المستخدم الشخصي ---
def format_user_report(u):
    uname = f"@{u.username}" if u.username else "لا يوجد يوزر / No Username"
    return (
        f"🛡️ <b>[ تقرير حماية شركس - حساب شخصي ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{u.id}</code>\n"
        f"📛 اسم الحساب: {u.first_name}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 النوع: حساب شخصي موثق\n"
        f"━━━━━━━━━━━━━━━"
    )

# --- [دالة احترافية]: تنسيق معلومات المجموعات والقنوات ---
def format_chat_report(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر / No Username"
    chat_type_ar = "قناة عامة" if c.type == "channel" else ("مجموعة تفاعلية" if "group" in c.type else c.type)
    return (
        f"🛡️ <b>[ تقرير حماية شركس - جهة خارجية ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{c.id}</code>\n"
        f"📛 اسم الجهة: {c.title}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 التصنيف: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━━"
    )

# --- معالج أمر البداية /start ---
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    bot.send_message(
        message.chat.id,
        "مياو! 🐱✨\n"
        "أهلاً بك في النسخة المطورّة من بوت حماية شركس.\n"
        "أرسل أي يوزر أو رابط مباشر، أو استخدم القائمة أدناه للتحكم الكامل:",
        reply_markup=create_main_menu_markup()
    )

# --- معالج الأزرار الشفافة (Inline Callbacks) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "cmd_id_help":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🐾 أهلاً بك في قسم البحث الذكي والتحكم المتقدم.\n\n"
            "اختر الطريقة المناسبة للبحث أدناه:",
            chat_id,
            message_id,
            reply_markup=create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        bot.answer_callback_query(call.id, "تم فتح لوحة الاختيار السريع بنجاح!")
        bot.send_message(
            chat_id,
            "👇 استخدم الأزرار الظاهرة أسفل الشاشة للاختيار المباشر:",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif call.data == "method_username":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🎯 <b>[ وضع البحث اليدوي المباشر ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر (مثل `@username`) أو الرابط (مثل `t.me/...`) وسأقوم بجلبه فوراً بروابط بحث صاروخية 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "method_forward":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة من أي قروب أو شخص هنا وسأستخرج كافة بياناته السرية!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "cmd_home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🏠 عودة موفقة لقرص العمليات الرئيسي 🐱 تفضل:",
            chat_id,
            message_id,
            reply_markup=create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "❌ تم إغلاق القائمة بنجاح. أرسل /start للإعادة.",
            chat_id,
            message_id,
            reply_markup=None
        )
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ هذه الخاصية تحت التطوير والصيانة المستمرة.",
            chat_id,
            message_id,
            reply_markup=create_home_return_markup()
        )

# --- [دالة احترافية معدلة]: معالجة الاختيارات من نافذة تيليجرام الداخلية دون أخطاء No Result ---
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
                response_text = format_user_report(chat_info)
            else:
                response_text = format_chat_report(chat_info)
        except Exception:
            response_text = (
                f"🛡️ <b>[ تقرير حماية شركس - الاختيار المباشر ]</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 المعرف الثابت: <code>{target_id}</code>\n"
                f"✨ تم استلام المعرف بنجاح من نافذة الاختيار الداخلية.\n"
                f"━━━━━━━━━━━━━━━"
            )
    else:
        response_text = "⚠️ لم يتم استلام أي معرف صالح من القائمة، حاول مرة أخرى."

    # إخفاء الكيبورد السفلي فوراً وإرسال النتيجة بوضوح
    bot.send_message(
        message.chat.id, 
        response_text, 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    # إرسال زر العودة للرئيسية برسالة منفصلة ومرتبة
    bot.send_message(
        message.chat.id, 
        "🔹 هل تريد عملية بحث أو استعلام آخر؟", 
        reply_markup=create_home_return_markup()
    )

# --- معالج النصوص والرسائل المحولة والبحث الشامل ---
@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_text_and_forwards_lookup(message):
    response_text = ""
    
    if message.forward_from:
        response_text = format_user_report(message.forward_from)
    elif message.forward_from_chat:
        response_text = format_chat_report(message.forward_from_chat)
    elif hasattr(message, "forward_origin") and message.forward_origin:
        origin = message.forward_origin
        if getattr(origin, "sender_user", None):
            response_text = format_user_report(origin.sender_user)
        elif getattr(origin, "chat", None):
            response_text = format_chat_report(origin.chat)
        else:
            sender_name = getattr(origin, "sender_user_name", "مخفي تماماً")
            response_text = (
                f"🛡️ <b>[ تقرير حماية شركس - خصوصية مفعلة ]</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📛 الاسم الظاهر: {sender_name}\n"
                f"━━━━━━━━━━━━━━━"
            )
    elif message.text:
        text = message.text.strip()
        
        if text.startswith("/") or len(text) < 3 or (" " in text and "t.me/" not in text and "telegram.me/" not in text):
            return

        clean_username = text
        if "t.me/" in text:
            clean_username = text.split("t.me/")[-1].split("/")[0].strip()
        elif "telegram.me/" in text:
            clean_username = text.split("telegram.me/")[-1].split("/")[0].strip()
        else:
            clean_username = text.replace("@", "").strip()

        if clean_username:
            target_query = "@" + clean_username
            try:
                chat_info = bot.get_chat(target_query)
                if chat_info.type == "private":
                    response_text = format_user_report(chat_info)
                else:
                    response_text = format_chat_report(chat_info)
            except Exception:
                adv_result = fetch_advanced_web_lookup(clean_username)
                if adv_result["found"]:
                    response_text = (
                        f"🛡️ <b>[ تقرير البحث الشامل المفتوح - شركس بوت ]</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📛 الاسم: {adv_result['name']}\n"
                        f"🔗 اليوزر: {adv_result['username']}\n"
                        f"📝 الوصف: {adv_result['bio']}\n"
                        f"📌 ملاحظة: {adv_result['note']}\n"
                        f"━━━━━━━━━━━━━━━"
                    )
                else:
                    response_text = f"❌ مياو! عذراً، لم أتمكن من العثور على أي نتائج مطابقة لـ: <b>{text}</b>."
        else:
            return
    else:
        return

    if response_text:
        bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=create_home_return_markup())

# --- معالج تفاعلات المجموعات حصراً ---
@bot.message_handler(chat_types=["group", "supergroup"], content_types=["text"])
def handle_group_exclusive_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id

    if text == "قائمة":
        bot.send_message(
            chat_id,
            "📋 <b>[ القائمة المتميزة الخاصة بالمجموعة ]</b>\n"
            "اضغط على الزر أدناه لاختيار أعضاء المجموعة حصراً:",
            parse_mode="HTML",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif "شركس" in text:
        bot.send_message(
            chat_id,
            "مياو! 🐱 ناديتني؟ تفضل القائمة الرئيسية الخاصة بي:",
            reply_markup=create_main_menu_markup()
        )

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
