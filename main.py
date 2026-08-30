import time
import threading
import os
import html

import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler


# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# حالات المستخدمين
# =========================================================

# عندما يضغط المستخدم ID Help في الخاص
# نخزن أنه ينتظر Username أو Forward
user_states = {}


# =========================================================
# القائمة الرئيسية
# =========================================================

def main_menu():

    markup = types.InlineKeyboardMarkup(row_width=1)

    markup.add(
        types.InlineKeyboardButton(
            "🔍😼 معرفة الآيدي (id_help)",
            callback_data="cmd_id_help"
        ),
        types.InlineKeyboardButton(
            "🎯😸 إنشاء مسابقة (create)",
            callback_data="cmd_create"
        ),
        types.InlineKeyboardButton(
            "⛔😺 إنهاء المسابقة (end)",
            callback_data="cmd_end"
        ),
        types.InlineKeyboardButton(
            "🔄😺 إعادة البدء (restart)",
            callback_data="cmd_restart"
        ),
        types.InlineKeyboardButton(
            "❌😺 إلغاء العملية (cancel)",
            callback_data="cmd_cancel"
        )
    )

    return markup


# =========================================================
# إرسال القائمة
# =========================================================

def send_main_menu(chat_id):

    bot.send_message(
        chat_id,
        "أهلاً بك في شركس 🐱\n"
        "إليك كافة الخيارات المتاحة:",
        reply_markup=main_menu()
    )


# =========================================================
# /start
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    user_states.pop(message.from_user.id, None)

    if message.chat.type == "private":

        bot.send_message(
            message.chat.id,
            "أهلاً بك في شركس 🐱\n"
            "أنا هنا لمساعدتك.",
            reply_markup=main_menu()
        )

    else:

        send_main_menu(message.chat.id)


# =========================================================
# ID HELP
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_id_help")
def id_help_callback(call):

    bot.answer_callback_query(call.id)

    user_states[call.from_user.id] = "waiting_for_target"

    bot.send_message(
        call.message.chat.id,
        "أهلاً، أنا شركس 🐱\n\n"
        "وأنا هنا لمساعدتك في جلب معلومات الحساب.\n\n"
        "إذا كان لديك Username للشخص أو القناة، أرسله لي:\n"
        "<code>@username</code>\n\n"
        "وإذا لم يكن لديه Username، قم بإعادة توجيه "
        "أي رسالة من الحساب أو القناة إليّ.\n\n"
        "يمكن أن تكون الرسالة:\n"
        "• نص\n"
        "• صورة\n"
        "• فيديو\n"
        "• ملف\n"
        "• صوت\n"
        "• Voice\n"
        "• Sticker\n"
        "• رابط\n"
        "• أو أي نوع رسالة آخر.",
        parse_mode="HTML"
    )


# =========================================================
# CREATE
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_create")
def create_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🎯 سيتم إضافة نظام إنشاء المسابقة هنا."
    )


# =========================================================
# END
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_end")
def end_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "⛔ سيتم إضافة نظام إنهاء المسابقة هنا."
    )


# =========================================================
# RESTART
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_restart")
def restart_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🔄 سيتم إضافة نظام إعادة البدء هنا."
    )


# =========================================================
# CANCEL
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_cancel")
def cancel_callback(call):

    bot.answer_callback_query(call.id)

    user_states.pop(call.from_user.id, None)

    bot.send_message(
        call.message.chat.id,
        "❌ تم إلغاء العملية.",
        reply_markup=main_menu()
    )


# =========================================================
# معلومات المستخدم
# =========================================================

def format_user_info(user):

    if not user:
        return None

    user_id = user.id

    first_name = html.escape(user.first_name or "غير موجود")
    last_name = html.escape(user.last_name or "غير موجود")

    if user.username:
        username = "@" + html.escape(user.username)
    else:
        username = "غير موجود"

    return (
        "👤 <b>معلومات الحساب</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 الاسم: {first_name}\n"
        f"📝 الاسم الأخير: {last_name}\n"
        f"🔗 Username: {username}\n"
        "━━━━━━━━━━━━━━"
    )


# =========================================================
# معلومات القناة
# =========================================================

def format_chat_info(chat):

    if not chat:
        return None

    chat_id = chat.id

    title = html.escape(
        getattr(chat, "title", None) or
        getattr(chat, "first_name", None) or
        "غير موجود"
    )

    username_value = getattr(chat, "username", None)

    if username_value:
        username = "@" + html.escape(username_value)
    else:
        username = "غير موجود"

    chat_type = getattr(chat, "type", "غير معروف")

    return (
        "📢 <b>معلومات القناة / المجموعة</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{chat_id}</code>\n"
        f"📛 الاسم: {title}\n"
        f"🔗 Username: {username}\n"
        f"📌 النوع: {chat_type}\n"
        "━━━━━━━━━━━━━━"
    )


# =========================================================
# تحليل مصدر الـ Forward الحديث
# =========================================================

def analyze_forward(message):

    # -----------------------------------------------------
    # الطريقة القديمة
    # -----------------------------------------------------

    old_user = getattr(message, "forward_from", None)

    if old_user:

        return format_user_info(old_user)

    old_chat = getattr(message, "forward_from_chat", None)

    if old_chat:

        return format_chat_info(old_chat)

    # -----------------------------------------------------
    # الطريقة الحديثة
    # Telegram Bot API
    # forward_origin
    # -----------------------------------------------------

    origin = getattr(message, "forward_origin", None)

    if not origin:
        return None

    # -----------------------------------------------------
    # ForwardOriginUser
    # -----------------------------------------------------

    origin_user = getattr(origin, "sender_user", None)

    if origin_user:

        return format_user_info(origin_user)

    # -----------------------------------------------------
    # ForwardOriginChat
    # -----------------------------------------------------

    origin_chat = getattr(origin, "sender_chat", None)

    if origin_chat:

        return format_chat_info(origin_chat)

    # -----------------------------------------------------
    # ForwardOriginHiddenUser
    # -----------------------------------------------------

    sender_user_name = getattr(
        origin,
        "sender_user_name",
        None
    )

    if sender_user_name:

        safe_name = html.escape(sender_user_name)

        return (
            "⚠️ <b>معلومات محدودة عن المصدر</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"👤 الاسم الظاهر: {safe_name}\n\n"
            "🔒 Telegram أخفى هوية الحساب الأصلي "
            "عن البوت بسبب إعدادات خصوصية الـForward.\n"
            "لذلك لا يوجد User ID يمكن للبوت استخراجه "
            "من هذه الرسالة.\n"
            "━━━━━━━━━━━━━━"
        )

    # -----------------------------------------------------
    # ForwardOriginChannel
    # -----------------------------------------------------

    origin_chat = getattr(origin, "chat", None)

    if origin_chat:

        return format_chat_info(origin_chat)

    return None


# =========================================================
# معالجة Forward في الخاص
# =========================================================

def process_private_target(message):

    # أول شيء: هل الرسالة Forward؟
    result = analyze_forward(message)

    if result:

        user_states.pop(message.from_user.id, None)

        bot.send_message(
            message.chat.id,
            result,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        return True

    return False


# =========================================================
# ID HELP في الخاص
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.chat.type == "private"
        and user_states.get(message.from_user.id) == "waiting_for_target"
)
def private_id_help_handler(message):

    # -----------------------------------------------------
    # Forward
    # -----------------------------------------------------

    if process_private_target(message):

        return

    # -----------------------------------------------------
    # Username
    # -----------------------------------------------------

    if message.text:

        text = message.text.strip()

        if text.startswith("@"):

            username = text[1:].strip()

            if not username:

                bot.send_message(
                    message.chat.id,
                    "❌ Username غير صالح."
                )

                return

            try:

                chat = bot.get_chat("@" + username)

                result = format_chat_info(chat)

                if result:

                    bot.send_message(
                        message.chat.id,
                        result,
                        parse_mode="HTML"
                    )

                    user_states.pop(
                        message.from_user.id,
                        None
                    )

                    return

            except Exception as e:

                print(
                    f"Username lookup failed: {e}"
                )

            bot.send_message(
                message.chat.id,
                "⚠️ لم أتمكن من الوصول إلى هذا الـUsername "
                "عن طريق Bot API.\n\n"
                "إذا كان الحساب شخصًا وليس قناة أو مجموعة، "
                "قم بإعادة توجيه أي رسالة أرسلها هذا الحساب إليّ."
            )

            return

        bot.send_message(
            message.chat.id,
            "❌ لم أفهم الـUsername.\n\n"
            "أرسله بهذا الشكل:\n"
            "<code>@username</code>\n\n"
            "أو قم بإعادة توجيه رسالة من الحساب المطلوب.",
            parse_mode="HTML"
        )

        return

    # -----------------------------------------------------
    # أي نوع رسالة آخر بدون Forward
    # -----------------------------------------------------

    bot.send_message(
        message.chat.id,
        "⚠️ وصلتني الرسالة، لكن لا تحتوي على معلومات "
        "مصدر Forward يمكنني استخدامها.\n\n"
        "قم باستخدام <b>إعادة توجيه / Forward</b> "
        "لرسالة من الحساب المطلوب.",
        parse_mode="HTML"
    )


# =========================================================
# تحليل رسالة الهدف في المجموعة
# =========================================================

def process_group_target(message):

    replied = getattr(message, "reply_to_message", None)

    if not replied:
        return False

    # -----------------------------------------------------
    # صاحب الرسالة كمستخدم
    # -----------------------------------------------------

    user = getattr(replied, "from_user", None)

    if user:

        result = format_user_info(user)

        if result:

            bot.reply_to(
                message,
                result,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            return True

    # -----------------------------------------------------
    # الرسالة مرسلة باسم قناة/مجموعة
    # -----------------------------------------------------

    sender_chat = getattr(
        replied,
        "sender_chat",
        None
    )

    if sender_chat:

        result = format_chat_info(sender_chat)

        if result:

            bot.reply_to(
                message,
                result,
                parse_mode="HTML"
            )

            return True

    # -----------------------------------------------------
    # إذا كانت الرسالة نفسها Forward
    # -----------------------------------------------------

    result = analyze_forward(replied)

    if result:

        bot.reply_to(
            message,
            result,
            parse_mode="HTML"
        )

        return True

    return False


# =========================================================
# كلمة "شركس" في المجموعات
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.chat.type in ["group", "supergroup"]
        and message.text
        and "شركس" in message.text
)
def handle_groups_full(message):

    print(
        f"Group Message Received in chat ID: "
        f"{message.chat.id}"
    )

    # -----------------------------------------------------
    # إذا كانت الرسالة Reply
    # -----------------------------------------------------

    if message.reply_to_message:

        processed = process_group_target(message)

        if processed:

            return

    # -----------------------------------------------------
    # إذا كتب شركس بدون Reply
    # تظهر القائمة
    # -----------------------------------------------------

    bot.reply_to(
        message,
        "أهلاً بك في المجموعة! "
        "معك شركس 🐱، إليك كافة الخيارات المتاحة:",
        reply_markup=main_menu()
    )


# =========================================================
# /id_help داخل المجموعة
# =========================================================

@bot.message_handler(
    commands=["id_help"],
    func=lambda message:
        message.chat.type in ["group", "supergroup"]
)
def id_help_group_command(message):

    if message.reply_to_message:

        processed = process_group_target(message)

        if processed:

            return

    bot.reply_to(
        message,
        "🔍 قم بعمل Reply على رسالة الشخص ثم اكتب:\n"
        "/id_help"
    )


# =========================================================
# Web Server - Render
# =========================================================

class SimpleHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"Sharx Bot is active and running!"
        )

    def do_HEAD(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain"
        )

        self.end_headers()


def run_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        SimpleHandler
    )

    server.serve_forever()


# =========================================================
# تشغيل البوت
# =========================================================

if __name__ == "__main__":

    server_thread = threading.Thread(
        target=run_server
    )

    server_thread.daemon = True
    server_thread.start()

    print(
        f"HTTP Server started on port {PORT}"
    )

    time.sleep(5)

    bot.remove_webhook()

    print(
        "Starting TeleBot polling safely..."
    )

    while True:

        try:

            bot.infinity_polling(
                skip_pending=True,
                timeout=20,
                long_polling_timeout=20
            )

        except Exception as e:

            print(
                f"Polling warning: {e}. "
                f"Retrying in 5 seconds..."
            )

            time.sleep(5)
