import time
import threading
import os
import telebot

from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot import types


# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)


# =========================================================
# تخزين حالة المستخدم مؤقتاً
# =========================================================

# user_states:
# {
#     user_id: "waiting_for_target"
# }
#
# نستخدمها لمعرفة أن المستخدم ضغط ID Help
# وأصبح البوت ينتظر منه Username أو رسالة مُعاد توجيهها.

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
# رسالة القائمة الرئيسية
# =========================================================

def send_main_menu(chat_id):
    bot.send_message(
        chat_id,
        "أهلاً بك في شركس 🐱\n"
        "إليك كافة الخيارات المتاحة:",
        reply_markup=main_menu()
    )


# =========================================================
# /start في الخاص
# =========================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    # تنظيف أي حالة قديمة
    user_states.pop(message.from_user.id, None)

    # في الخاص
    if message.chat.type == "private":

        bot.send_message(
            message.chat.id,
            "أهلاً بك في شركس 🐱\n"
            "أنا هنا لمساعدتك.",
            reply_markup=main_menu()
        )

    else:
        # إذا استُخدم /start في مجموعة
        send_main_menu(message.chat.id)


# =========================================================
# زر ID HELP
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_id_help")
def id_help_callback(call):

    bot.answer_callback_query(call.id)

    user_id = call.from_user.id

    # نضع المستخدم في حالة انتظار
    user_states[user_id] = "waiting_for_target"

    text = (
        "أهلاً بك، أنا شركس 🐱\n\n"
        "وأنا هنا لمساعدتك في جلب معلومات الحساب.\n\n"
        "إذا كان لدى الشخص Username، أرسله لي بهذا الشكل:\n"
        "@username\n\n"
        "وإذا لم يكن لديه Username، قم بإعادة توجيه "
        "أي رسالة من الحساب المطلوب إليّ.\n\n"
        "يمكن أن تكون الرسالة:\n"
        "• نص\n"
        "• صورة\n"
        "• فيديو\n"
        "• ملف\n"
        "• صوت\n"
        "• رسالة صوتية\n"
        "• Sticker\n"
        "• رابط\n"
        "• أو أي نوع رسالة آخر يصلني من الحساب."
    )

    bot.send_message(
        call.message.chat.id,
        text
    )


# =========================================================
# زر CREATE
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_create")
def create_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🎯 سيتم إضافة نظام إنشاء المسابقة هنا."
    )


# =========================================================
# زر END
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_end")
def end_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "⛔ سيتم إضافة نظام إنهاء المسابقة هنا."
    )


# =========================================================
# زر RESTART
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "cmd_restart")
def restart_callback(call):

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🔄 سيتم إضافة نظام إعادة البدء هنا."
    )


# =========================================================
# زر CANCEL
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
# استخراج معلومات المستخدم
# =========================================================

def get_user_info(user):

    if not user:
        return "❌ لم أتمكن من الحصول على معلومات المرسل."

    user_id = user.id

    first_name = user.first_name or "غير موجود"
    last_name = user.last_name or "غير موجود"

    if user.username:
        username = "@" + user.username
    else:
        username = "غير موجود"

    # رابط tg://user?id=
    user_link = f"tg://user?id={user_id}"

    result = (
        "👤 معلومات الحساب\n"
        "━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 الاسم: {first_name}\n"
        f"📝 الاسم الأخير: {last_name}\n"
        f"🔗 Username: {username}\n"
        f"🔐 رابط الحساب: <a href=\"{user_link}\">فتح الحساب</a>\n"
        "━━━━━━━━━━━━━━"
    )

    return result


# =========================================================
# معالجة رسالة مرسلة مباشرة في الخاص بعد ID HELP
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.chat.type == "private"
        and user_states.get(message.from_user.id) == "waiting_for_target"
)
def private_id_help_handler(message):

    # إذا كان المستخدم أرسل Username
    if message.text:

        text = message.text.strip()

        # نتأكد أنه يبدو كـ Username
        if text.startswith("@"):

            username = text[1:].strip()

            if username:

                # ملاحظة:
                # Bot API لا يوفر طريقة عامة للحصول على User
                # عشوائي بواسطة Username.
                #
                # نحاول get_chat، وهذا يفيد خصوصاً مع القنوات
                # والمجموعات العامة.

                try:

                    chat = bot.get_chat("@" + username)

                    # إذا كانت قناة أو مجموعة
                    if chat.type in ["channel", "supergroup", "group"]:

                        result = (
                            "📢 معلومات الوجهة\n"
                            "━━━━━━━━━━━━━━\n"
                            f"🆔 ID: <code>{chat.id}</code>\n"
                            f"👤 الاسم: {chat.title or 'غير موجود'}\n"
                            f"🔗 Username: @{username}\n"
                            f"📌 النوع: {chat.type}\n"
                            "━━━━━━━━━━━━━━"
                        )

                        bot.send_message(
                            message.chat.id,
                            result,
                            parse_mode="HTML"
                        )

                        user_states.pop(message.from_user.id, None)
                        return

                    else:

                        bot.send_message(
                            message.chat.id,
                            "⚠️ هذا الـUsername يشير إلى حساب مستخدم.\n\n"
                            "لا يستطيع Bot API الاعتماد على Username "
                            "للعثور على User ID لشخص لم يتفاعل مع البوت.\n\n"
                            "للحصول على معلومات الحساب، قم بإعادة توجيه "
                            "أي رسالة من هذا الحساب إليّ."
                        )

                        return

                except Exception:

                    bot.send_message(
                        message.chat.id,
                        "⚠️ لم أتمكن من الوصول إلى هذا الـUsername.\n\n"
                        "إذا لم يكن الحساب قناة/مجموعة عامة، "
                        "قم بإعادة توجيه أي رسالة منه إليّ."
                    )

                    return

        # إذا أرسل نصاً عادياً
        bot.send_message(
            message.chat.id,
            "أرسل Username بهذا الشكل:\n"
            "@username\n\n"
            "أو قم بإعادة توجيه رسالة من الحساب المطلوب."
        )

        return

    # =====================================================
    # إذا كانت الرسالة Forwarded
    # =====================================================

    # بعض أنواع الرسائل قد تحتوي على معلومات Forward
    if getattr(message, "forward_from", None):

        user = message.forward_from

        result = get_user_info(user)

        bot.send_message(
            message.chat.id,
            result,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        user_states.pop(message.from_user.id, None)

        return

    # =====================================================
    # إذا كانت الرسالة Forwarded من قناة
    # =====================================================

    if getattr(message, "forward_from_chat", None):

        chat = message.forward_from_chat

        if chat.type == "channel":

            username = (
                "@" + chat.username
                if getattr(chat, "username", None)
                else "غير موجود"
            )

            title = chat.title or "غير موجود"

            result = (
                "📢 معلومات القناة\n"
                "━━━━━━━━━━━━━━\n"
                f"🆔 ID: <code>{chat.id}</code>\n"
                f"📛 الاسم: {title}\n"
                f"🔗 Username: {username}\n"
                "━━━━━━━━━━━━━━"
            )

            bot.send_message(
                message.chat.id,
                result,
                parse_mode="HTML"
            )

            user_states.pop(message.from_user.id, None)

            return

    # =====================================================
    # إذا أرسل رسالة عادية وليس Forward
    # =====================================================

    bot.send_message(
        message.chat.id,
        "⚠️ هذه الرسالة وصلتني منك أنت.\n\n"
        "للحصول على معلومات حساب شخص آخر، "
        "قم باستخدام خيار **إعادة توجيه / Forward** "
        "لرسالة أرسلها الحساب المطلوب."
    )


# =========================================================
# وظيفة عرض معلومات صاحب رسالة في المجموعة
# =========================================================

def process_group_target(message):

    # الرسالة التي قام المستخدم بالرد عليها
    replied = message.reply_to_message

    if not replied:
        return False

    # نحاول الحصول على صاحب الرسالة
    user = getattr(replied, "from_user", None)

    if user:

        result = get_user_info(user)

        bot.reply_to(
            message,
            result,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        return True

    # إذا كانت الرسالة من قناة / مرسلة باسم قناة
    sender_chat = getattr(replied, "sender_chat", None)

    if sender_chat:

        username = (
            "@" + sender_chat.username
            if getattr(sender_chat, "username", None)
            else "غير موجود"
        )

        title = (
            sender_chat.title
            or "غير موجود"
        )

        result = (
            "📢 معلومات الحساب/القناة\n"
            "━━━━━━━━━━━━━━\n"
            f"🆔 ID: <code>{sender_chat.id}</code>\n"
            f"📛 الاسم: {title}\n"
            f"🔗 Username: {username}\n"
            "━━━━━━━━━━━━━━"
        )

        bot.reply_to(
            message,
            result,
            parse_mode="HTML"
        )

        return True

    return False


# =========================================================
# التعامل مع كلمة "شركس" في المجموعات
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

    # =====================================================
    # إذا كانت الرسالة Reply على رسالة شخص
    # =====================================================

    if message.reply_to_message:

        # نحاول مباشرة معرفة صاحب الرسالة
        processed = process_group_target(message)

        if processed:
            return

    # =====================================================
    # إذا كتب "شركس" بدون Reply
    # =====================================================

    bot.reply_to(
        message,
        "أهلاً بك في المجموعة! "
        "معك شركس 🐱، إليك كافة الخيارات المتاحة:",
        reply_markup=main_menu()
    )


# =========================================================
# أوامر إضافية اختيارية
# /id_help داخل المجموعة مع Reply
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
# سيرفر الويب الخاص بـ Render
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
