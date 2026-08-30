import os
import time
import threading
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

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
    )
    return markup

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="cmd_home"))
    return markup

def format_user(u):
    uname = f"@{u.username}" if u.username else "لا يوجد يوزر"
    return (
        f"🛡️ <b>تقرير حماية القروب - حساب شخصي</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{u.id}</code>\n"
        f"📛 اسم الحساب: {u.first_name}\n"
        f"🔗 اسم المستخدم: {uname}\n"
        f"📌 نوع الحساب: حساب شخصي\n"
        f"━━━━━━━━━━━━━━"
    )

def format_chat(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر"
    chat_type_ar = "قناة" if c.type == "channel" else ("مجموعة" if "group" in c.type else c.type)
    return (
        f"🛡️ <b>تقرير حماية القروب - جهة خارجية</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{c.id}</code>\n"
        f"📛 الاسم: {c.title}\n"
        f"🔗 اسم المستخدم: {uname}\n"
        f"📌 نوع الجهة: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━"
    )

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "مياو! 🐱\n"
        "أهلاً بك في بوت شركس للحماية.\n"
        "أنا قطك المطيع هيهي، جاهز لمساعدتك في جلب معلومات المخربين بدقة!\n\n"
        "إليك القائمة الرئيسية:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id

    if call.data == "cmd_id_help":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "مياو! 🐾 أهلاً أنا شركس قطك المطيع هيهي.\n\n"
            "قم بإرسال (اسم المستخدم / الـ Username) أو الرابط مباشرة، أو قم بإعادة توجيه (Forward) لأي رسالة من شخص أو قناة لأقوم بفك شفرتها وجلب الآيدي ومعلومات الحساب فوراً!",
            chat_id,
            call.message.message_id,
            reply_markup=back_menu()
        )
    elif call.data == "cmd_home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "مياو العودة للقرص! 🐱 تفضل القائمة الرئيسية:",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )
    elif call.data == "cmd_cancel":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "❌ تم إلغاء العملية بنجاح.",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ هذه الخاصية قيد البرمجة يا بطل.",
            chat_id,
            call.message.message_id,
            reply_markup=back_menu()
        )

@bot.message_handler(chat_types=["private"])
def process_id_help_target(message):
    response_text = ""

    # 1. فحص الطرق التقليدية والحديثة للرسائل المحولة (Forwarded Messages)
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
        elif getattr(origin, "sender_user_name", None):
            response_text = f"⚠️ مياو! الحساب يمتلك اسماً نصياً مخفياً: {origin.sender_user_name} ولا يمكن جلب الآيدي الثابت بسبب إعدادات الخصوصية الصارمة."
        else:
            response_text = "⚠️ مياو! عذراً، مصدر الرسالة المحولة مخفي تماماً بواسطة إعدادات الخصوصية."
    
    # 2. فحص إرسال اليوزر أو الرابط النصي مباشرة
    elif message.text:
        text = message.text.strip()
        if "t.me/" in text:
            clean_username = text.split("t.me/")[-1].split("/")[0].strip()
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
                response_text = (
                    f"❌ مياو! لم أتمكن من العثور على الحساب <b>{target_query}</b>.\n"
                    "تأكد من صحة اليوزر أو أن الحساب عام، أو جرب إرسال رسالة محولة (Forward) منه."
                )
        else:
            response_text = "⚠️ يرجى إرسال يوزر نيم صالح أو رابط صحيح."
    else:
        response_text = "⚠️ مياو! أرسل رسالة محولة أو يوزر نيم صالح من فضلك."

    bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=back_menu())

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
    
    time.sleep(3)

    while True:
        try:
            print("Starting bot polling safely...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
