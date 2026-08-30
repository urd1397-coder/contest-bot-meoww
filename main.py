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

# --- القوائم الرئيسية ---
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
        types.InlineKeyboardButton("🎯 من خلال اليوزر نيم / By Username", callback_data="method_username"),
        types.InlineKeyboardButton("📥 من خلال الرسائل المحولة / By Forwarded Msg", callback_data="method_forward"),
        types.InlineKeyboardButton("🔍 البحث السريع / Inline Search", callback_data="method_inline_search"),
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
        f"🛡️ <b>تقرير حماية القروب - حساب شخصي / User Report</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت / ID: <code>{u.id}</code>\n"
        f"📛 اسم الحساب / Name: {u.first_name}\n"
        f"🔗 اسم المستخدم / Username: {uname}\n"
        f"📌 نوع الحساب / Type: حساب شخصي / Personal Account\n"
        f"━━━━━━━━━━━━━━"
    )

def format_chat(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر / No Username"
    chat_type_ar = "قناة" if c.type == "channel" else ("مجموعة" if "group" in c.type else c.type)
    return (
        f"🛡️ <b>تقرير حماية القروب - جهة خارجية / Chat Report</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت / ID: <code>{c.id}</code>\n"
        f"📛 الاسم / Name: {c.title}\n"
        f"🔗 اسم المستخدم / Username: {uname}\n"
        f"📌 نوع الجهة / Type: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━"
    )

@bot.message_handler(commands=["start"])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "مياو! 🐱\n"
        "أهلاً بك في بوت شركس للحماية.\n"
        "أنا قطك المطيع هيهي، جاهز لمساعدتك في جلب معلومات المخربين بدقة وتجاوز كل القيود!\n\n"
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
            "اختر الطريقة التي تفضلها لاستخراج الآيدي والمعلومات بدقة:\n"
            "Choose the method you prefer to extract ID and info accurately:",
            chat_id,
            message_id,
            reply_markup=id_help_menu()
        )
    elif call.data == "method_username":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🎯 <b>هاتِ اليوزر يا بطل! / Send the Username!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "✍️ اكتب اسم المستخدم أو الرابط مباشرة (مثل: `@username` أو الرابط)، وسأجيبك بتقريره الكامل قبل أن ترمش عيونك!\n"
            "Type the username or direct link, and I'll fetch its report instantly! 👀✨",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=back_menu()
        )
    elif call.data == "method_forward":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "📥 <b>حوّل الرسالة ودع الباقي عليّ! / Forward the Message!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة هنا (نص، صورة، فيديو...) وسأستخرج لك الآيدي والمعلومات فوراً!\n"
            "Forward any message here and I'll extract the ID and info instantly! 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=back_menu()
        )
    elif call.data == "method_inline_search":
        bot.answer_callback_query(call.id)
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton("🔍 ابحث الآن / Search Now", switch_inline_query_current_chat=""))
        inline_markup.add(types.InlineKeyboardButton("🔙 العودة لقائمة الآيدي / Back", callback_data="cmd_id_help"))
        
        bot.edit_message_text(
            "🔍 <b>البحث السريع / Quick Search</b>\n"
            "━━━━━━━━━━━━━━\n"
            "🐾 اضغط على الزر بالأسفل للبحث عن أي شخص ومشاركته معنا مباشرة!\n"
            "Tap the button below to search for anyone and share it directly! 🚀✨",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=inline_markup
        )
    elif call.data == "cmd_home":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "مياو العودة للقرص! 🐱 تفضل القائمة الرئيسية:\nBack to main menu:",
            chat_id,
            message_id,
            reply_markup=main_menu()
        )
    elif call.data == "cmd_cancel":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "❌ تم إلغاء العملية بنجاح.\nOperation cancelled successfully.",
            chat_id,
            message_id,
            reply_markup=main_menu()
        )
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ هذه الخاصية قيد البرمجة يا بطل.\nThis feature is under development.",
            chat_id,
            message_id,
            reply_markup=back_menu()
        )

@bot.message_handler(chat_types=["private"], content_types=["contact"])
def process_contact_target(message):
    contact = message.contact
    if contact.user_id:
        response_text = (
            f"🛡️ <b>تقرير حماية القروب - جهة اتصال مستخرجة / Contact Report</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 المعرف الثابت / ID: <code>{contact.user_id}</code>\n"
            f"📛 الاسم / Name: {contact.first_name}\n"
            f"📞 الهاتف / Phone: {contact.phone_number}\n"
            f"📌 الحالة / Status: تم استخراج الآيدي بنجاح متجاوزاً الخصوصية! / Extracted successfully!\n"
            f"━━━━━━━━━━━━━━"
        )
    else:
        response_text = "⚠️ مياو! جهة الاتصال هذه غير مرتبطة بحساب تيليغرام مباشر.\nNot linked to a direct Telegram account."
    
    bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=back_menu())

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def process_id_help_target(message):
    response_text = ""

    # 1. معالجة الرسائل المحولة (Forward)
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
            name = origin.sender_user_name
            response_text = (
                f"⚠️ <b>مياو! تنبيه حماية هام / Security Alert</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📛 الاسم الظاهر / Name: {name}\n"
                f"📌 الحالة / Status: <b>حساب مخفي تماماً / Hidden Account</b>\n"
                f"💡 هذا المستخدم قام بتفعيل إعدادات الخصوصية القصوى. استخدم البحث السريع أو اطلب منه مراسلتك.\n"
                f"━━━━━━━━━━━━━━"
            )
        else:
            response_text = "⚠️ مياو! عذراً، مصدر الرسالة مخفي تماماً.\nSorry, the message source is hidden."
    
    # 2. معالجة اليوزرات والروابط النصية
    elif message.text:
        text = message.text.strip()
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
                response_text = (
                    f"❌ مياو! لم أتمكن من جلب معلومات الحساب <b>{target_query}</b>.\n\n"
                    f"🔍 <b>السبب / Reason:</b> يمنع تيليغرام البوتات من البحث العشوائي إلا إذا تفاعل الشخص مسبقاً.\n"
                    f"💡 <b>الحل / Solution:</b> اطلب منه إرسال رسالة للبوت أولاً."
                )
        else:
            response_text = "⚠️ يرجى إرسال يوزر نيم صالح أو رابط صحيح.\nPlease send a valid username or link."
    
    else:
        response_text = "⚠️ مياو! يرجى إرسال رسالة محولة، يوزر نيم، أو جهة اتصال.\nPlease send a forwarded message, username, or contact."

    bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=back_menu())

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
    
    time.sleep(3)

    # إزالة الويب هوك القديم لمنع خطأ 409 Conflict نهائياً
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
