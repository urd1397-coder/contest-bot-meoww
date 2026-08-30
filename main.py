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
        types.InlineKeyboardButton("🎯 من خلال اليوزر نيم", callback_data="method_username"),
        types.InlineKeyboardButton("📥 من خلال الرسائل الموجهة", callback_data="method_forward"),
        types.InlineKeyboardButton("🔍 البحث السريع وتجاوز الخصوصية", callback_data="method_inline_search"),
        types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="cmd_home")
    )
    return markup

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة لقائمة الآيدي", callback_data="cmd_id_help"))
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
            "اختر الطريقة التي تفضلها لاستخراج الآيدي والمعلومات بدقة:",
            chat_id,
            message_id,
            reply_markup=id_help_menu()
        )
    elif call.data == "method_username":
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🎯 <b>هاتِ اليوزر يا بطل!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "✍️ اكتب اسم المستخدم أو الرابط مباشرة (مثل: `@username` أو الرابط)، وسأجيبك بتقريره الكامل قبل أن ترمش عيونك! 👀✨",
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
            "🐾 قم بإعادة توجيه (Forward) أي رسالة هنا—سواء كانت نصاً، صورة، فيديو، أو من أي قناة عامة أو خاصة—وسأستخرج لك الآيدي والمعلومات فوراً! 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=back_menu()
        )
    elif call.data == "method_inline_search":
        bot.answer_callback_query(call.id)
        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton("🔍 اضغط للبحث عن مستخدم", switch_inline_query_current_chat=""))
        inline_markup.add(types.InlineKeyboardButton("🔙 العودة لقائمة الآيدي", callback_data="cmd_id_help"))
        
        bot.edit_message_text(
            "🔍 <b>ابحث واكشفه فوراً!</b>\n"
            "━━━━━━━━━━━━━━\n"
            "🐾 اضغط على الزر بالأسفل للبحث عن أي شخص في التيليغرام واختياره لمشاركته معنا—حتى لو لم يكن مسجلاً في جهات اتصالك! 🚀✨",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=inline_markup
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

@bot.message_handler(chat_types=["private"], content_types=["contact"])
def process_contact_target(message):
    contact = message.contact
    if contact.user_id:
        response_text = (
            f"🛡️ <b>تقرير حماية القروب - جهة اتصال مستخرجة</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🆔 المعرف الثابت: <code>{contact.user_id}</code>\n"
            f"📛 الاسم: {contact.first_name}\n"
            f"📞 الهاتف / رقم التواصل: {contact.phone_number}\n"
            f"📌 الحالة: تم استخراج الآيدي بنجاح متجاوزاً الخصوصية!\n"
            f"━━━━━━━━━━━━━━"
        )
    else:
        response_text = "⚠️ مياو! جهة الاتصال هذه غير مرتبطة بحساب تيليغرام مباشر."
    
    bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=back_menu())

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
        elif getattr(origin, "sender_user_name", None):
            name = origin.sender_user_name
            response_text = (
                f"⚠️ <b>مياو! تنبيه حماية هام</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📛 الاسم الظاهر: {name}\n"
                f"📌 الحالة: <b>حساب مخفي تماماً</b>\n"
                f"💡 هذا المستخدم قام بتفعيل إعدادات الخصوصية القصوى. لتجاوز ذلك والحصول على آيديه، قم بمشاركة <b>جهة الاتصال (Contact)</b> الخاصة به أو استخدم البحث السريع.\n"
                f"━━━━━━━━━━━━━━"
            )
        else:
            response_text = "⚠️ مياو! عذراً، مصدر الرسالة مخفي تماماً بواسطة إعدادات الخصوصية."
    
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
                    f"❌ مياو! لم أتمكن من جلب معلومات الحساب <b>{target_query}</b>.\n\n"
                    f"🔍 <b>السبب:</b> يمنع تيليغرام البوتات من البحث العشوائي عن الحسابات عبر اليوزر إلا إذا تفاعل الشخص مسبقاً مع البوت أو كانا في قروب مشترك.\n"
                    f"💡 <b>الحل البديل:</b> اطلب منه إرسال رسالة مباشرة للبوت أو شارك جهة اتصاله."
                )
        else:
            response_text = "⚠️ يرجى إرسال يوزر نيم صالح أو رابط صحيح."
    else:
        response_text = "⚠️ مياو! يرجى إرسال رسالة محولة، يوزر نيم، أو جهة اتصال."

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
