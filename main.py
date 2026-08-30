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

# --- دالة البحث الشامل والمتقدم لأي حساب أو قناة عامة عبر الرابط أو اليوزر ---
def advanced_lookup_by_username(username):
    clean_un = username.replace("@", "").strip()
    # إزالة روابط تليجرام الشائعة للحصول على المعرف النقي
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
                "note": "تم جلب البيانات بنجاح عبر البحث الشامل للرابط 🌐"
            }
    except Exception:
        pass
    return {"found": False}

# --- لوحة المفاتيح السفلية المتاحة عند الحاجة ---
def request_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_user = types.KeyboardButton(
        text="👤 اختيار مستخدم من الهاتف", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختيار مجموعة/قناة", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
    return markup

# --- القوائم الشفافة (Inline) ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
    )
    return markup

def id_help_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📋 إظهار أزرار الاختيار السريع أسفل الشاشة", callback_data="show_keyboard"),
        types.InlineKeyboardButton("🎯 البحث الشامل باليوزر أو الرابط", callback_data="method_username"),
        types.InlineKeyboardButton("📥 من خلال الرسائل المحولة / By Forwarded Msg", callback_data="method_forward"),
        types.InlineKeyboardButton("🔙 العودة للرئيسية / Main Menu", callback_data="cmd_home")
    )
    return markup

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة لقائمة الآيدي / Back", callback_data="cmd_id_help"))
    return markup

def format_user(u):
    uname = f"@{u.username}" if u.username else "لا يوجد يوزر / No Username"
    return (
        f"🛡️ <b>تقرير حماية القروب - حساب شخصي</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت / ID: <code>{u.id}</code>\n"
        f"📛 اسم الحساب / Name: {u.first_name}\n"
        f"🔗 اسم المستخدم / Username: {uname}\n"
        f"📌 نوع الحساب: حساب شخصي\n"
        f"━━━━━━━━━━━━━━"
    )

def format_chat(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر / No Username"
    chat_type_ar = "قناة" if c.type == "channel" else ("مجموعة" if "group" in c.type else c.type)
    return (
        f"🛡️ <b>تقرير حماية القروب - جهة خارجية</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت / ID: <code>{c.id}</code>\n"
        f"📛 الاسم / Name: {c.title}\n"
        f"🔗 اسم المستخدم / Username: {uname}\n"
        f"📌 نوع الجهة: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━"
    )

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "مياو! 🐱\n"
        "أهلاً بك في بوت شركس للحماية المطور.\n"
        "أرسل أي يوزر أو رابط لأي قناة، مجموعة، أو شخص، وسأقوم بجلبه لك فوراً!\n\n"
        "إليك القائمة الرئيسية:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "cmd_id_help":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "مياو! 🐾 أهلاً أنا شركس قطك المطيع هيهي.\n\n"
            "اختر الطريقة لاستخراج المعلومات أو أرسل الرابط مباشرة:",
            chat_id,
            message_id,
            reply_markup=id_help_menu()
        )
    elif call.data == "show_keyboard":
        bot.answer_callback_query(call.id, "تم إظهار أزرار الاختيار أسفل الشاشة بنجاح!")
        bot.send_message(
            chat_id,
            "👇 اضغط على الزر أدناه لاختيار مستخدم أو مجموعة مباشرة:",
            reply_markup=request_keyboard()
        )
    elif call.data == "method_username":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🎯 <b>البحث الشامل المفتوح!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن أي رابط (مثل `t.me/username`) أو يوزر (`@username`) لأي شخص أو قناة أو مجموعة وسأقوم بجلبه فوراً! 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=back_menu()
        )
    elif call.data == "method_forward":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "📥 <b>حوّل الرسالة ودع الباقي عليّ!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة هنا وسأستخرج لك الآيدي والمعلومات فوراً!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=back_menu()
        )
    elif call.data == "cmd_home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "مياو العودة للقرص! 🐱 تفضل القائمة الرئيسية:",
            chat_id,
            message_id,
            reply_markup=main_menu()
        )
    elif call.data == "cmd_cancel":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "❌ تم إلغاء العملية بنجاح.",
            chat_id,
            message_id,
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ هذه الخاصية قيد البرمجة يا بطل.",
            chat_id,
            message_id,
            reply_markup=back_menu()
        )

@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_targets(message):
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
                response_text = format_user(chat_info)
            else:
                response_text = format_chat(chat_info)
        except Exception:
            response_text = (
                f"🛡️ <b>تقرير الحماية - مشاركة مباشرة</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"🆔 المعرف الثابت / ID: <code>{target_id}</code>\n"
                f"━━━━━━━━━━━━━━"
            )
    else:
        response_text = "⚠️ لم يتم استلام أي معرف صالح."

    bot.send_message(message.chat.id, response_text, parse_mode="HTML")

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def process_id_help_target(message):
    response_text = ""
    
    if message.forward_from:
        response_text = format_user(message.forward_from)
    elif message.forward_from_chat:
        response_text = format_chat(message.forward_from_chat)
    elif hasattr(message, "forward_origin") and message.forward_origin:
        origin = message.forward_origin
        if getattr(origin, "sender_user", None):
            response_text = format_user(origin.sender_user)
        elif getattr(origin, "chat", None):
            response_text = format_chat(origin.chat)
        else:
            sender_name = getattr(origin, "sender_user_name", "مخفي")
            response_text = (
                f"🛡️ <b>تقرير حماية القروب - حساب بخصوصية مفعلة</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📛 الاسم الظاهر: {sender_name}\n"
                f"━━━━━━━━━━━━━━"
            )
    elif message.text:
        text = message.text.strip()
        
        if text.startswith("/"):
            return

        # تنظيف النص واستخراج اليوزر أو الرابط بأي شكل تم إرساله
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
                    response_text = format_user(chat_info)
                else:
                    response_text = format_chat(chat_info)
            except Exception:
                adv_result = advanced_lookup_by_username(clean_username)
                if adv_result["found"]:
                    response_text = (
                        f"🛡️ <b>تقرير البحث الشامل المفتوح - شركس بوت</b>\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📛 الاسم / Name: {adv_result['name']}\n"
                        f"🔗 اسم المستخدم / Username: {adv_result['username']}\n"
                        f"📝 الوصف / Bio: {adv_result['bio']}\n"
                        f"📌 ملاحظة: {adv_result['note']}\n"
                        f"━━━━━━━━━━━━━━"
                    )
                else:
                    response_text = f"❌ مياو! لم أتمكن من العثور على الحساب أو الرابط <b>{text}</b>."
        else:
            response_text = "⚠️ يرجى إرسال رابط صحيح أو يوزر نيم."
    else:
        response_text = "⚠️ مياو! أرسل رسالة نصية أو رابط صالح."

    bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=id_help_menu())

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
