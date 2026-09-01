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

user_search_mode = {}
last_panel_message = {}

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

def create_navigation_markup(back_callback="cmd_id_help"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث الشامل ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية (قيد التطوير)", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية (قيد التطوير)", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع للأعضاء والجهات", callback_data="show_keyboard"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة الذكي", callback_data="method_forward"),
        types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    btn_user = types.KeyboardButton(
        text="👤 اختر مستخدم", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختر مجموعة أو قناة", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
    return markup

def format_unified_report(name, username, user_id, account_type):
    clean_name = name if name and name != "None" and str(name).strip() != "" else "جهة مختارة"
    
    username_line = ""
    if username and str(username).strip() != "" and str(username).lower() != "none":
        formatted_un = username if str(username).startswith("@") else f"@{username}"
        username_line = f"username: {formatted_un}\n"

    return (
        f"🐾 <b>[ بطاقة شركس الذكية ]</b> 🐱✨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{username_line}"
        f"👤 <b>الاسم:</b> {clean_name}\n"
        f"id: <code>{user_id}</code>\n"
        f"📌 <b>نوع الحساب:</b> {account_type}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>نظام شركس السريع لخدمتكم!</i>"
    )

def update_or_send_panel(chat_id, text, reply_markup):
    if chat_id in last_panel_message:
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=last_panel_message[chat_id],
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
    
    sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)
    last_panel_message[chat_id] = sent.message_id

@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
    user_search_mode[message.chat.id] = False
    
    text = (
        "مياو أهلاً بك في عالم شركس! 🐱✨\n"
        "البوت الأنيق والسريع لإدارة وحماية مجموعاتك وقنواتك بكل احترافية.\n"
        "اختر ما يناسبك من الخيارات أدناه:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=create_main_menu_markup())
    last_panel_message[message.chat.id] = sent.message_id

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "cmd_create" or call.data == "cmd_end":
        try:
            bot.answer_callback_query(call.id, "هذه الميزة الرائعة قيد التطوير حالياً 🚧", show_alert=True)
        except Exception:
            pass
    elif call.data == "cmd_id_help":
        user_search_mode[chat_id] = False
        update_or_send_panel(
            chat_id,
            "⚡ <b>قسم البحث والاستخراج المتقدم</b> 🐾\n\n"
            "اختر الطريقة المناسبة لجلب البيانات بسرعة وسلاسة:",
            create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        user_search_mode[chat_id] = False
        update_or_send_panel(
            chat_id,
            "📂 <b>[ لوحة الاختيار السريع للأعضاء والجهات ]</b>\n\n"
            "👇 استخدم لوحة المفاتيح السفلية الظاهرة لديك الآن لاختيار مستخدم أو مجموعة، وسأعرض لك بطاقته هنا فوراً 🚀",
            create_navigation_markup("cmd_id_help")
        )
        try:
            bot.send_message(
                chat_id, 
                "👇 لوحة الاختيار السفلية:", 
                reply_markup=create_dynamic_reply_keyboard()
            )
        except Exception:
            pass
    elif call.data == "method_username":
        user_search_mode[chat_id] = True
        update_or_send_panel(
            chat_id,
            "🌐 <b>[ وضع البحث اليدوي والروابط والقنوات ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر المطلوب (مثل `@username`)، رابط القناة، أو معرفها وسأقوم بجلب تفاصيلها فوراً 🚀",
            create_navigation_markup("cmd_id_help")
        )
    elif call.data == "method_forward":
        user_search_mode[chat_id] = False
        update_or_send_panel(
            chat_id,
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة من أي شخص أو قناة هنا لاستخراج بياناتها بدقة!",
            create_navigation_markup("cmd_id_help")
        )
    elif call.data == "cmd_home":
        user_search_mode[chat_id] = False
        update_or_send_panel(
            chat_id,
            "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:",
            create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        user_search_mode[chat_id] = False
        try:
            bot.send_message(chat_id, "❌ تم إغلاق القائمة.", reply_markup=types.ReplyKeyboardRemove())
        except Exception:
            pass
        update_or_send_panel(
            chat_id,
            "❌ تم إغلاق القائمة بنجاح. أرسل /start في أي وقت لإظهارها مجدداً.",
            None
        )

@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    chat_id = message.chat.id
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    target_id = None
    is_chat = False
    
    if message.users_shared:
        try:
            raw_target = message.users_shared.user_ids[0]
            if isinstance(raw_target, dict):
                target_id = raw_target.get("user_id")
            elif hasattr(raw_target, "user_id"):
                target_id = raw_target.user_id
            else:
                target_id = raw_target
        except Exception:
            target_id = message.users_shared.user_ids[0]
            
    elif message.chat_shared:
        target_id = message.chat_shared.chat_id
        is_chat = True

    if target_id:
        try:
            chat_info = bot.get_chat(target_id)
            uname = getattr(chat_info, 'username', None)
            
            if is_chat:
                name = getattr(chat_info, 'title', 'قناة أو مجموعة')
                acc_type = "قناة عامة" if chat_info.type == "channel" else "مجموعة تفاعلية"
            else:
                first = getattr(chat_info, 'first_name', '') or ''
                last = getattr(chat_info, 'last_name', '') or ''
                name = f"{first} {last}".strip() or "مستخدم تيليجرام"
                acc_type = "حساب بوت رسمي" if getattr(chat_info, 'is_bot', False) else "مستخدم شخصي"

            report_text = format_unified_report(name, uname, chat_info.id, acc_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        except Exception:
            fallback_type = "مجموعة أو قناة" if is_chat else "مستخدم شخصي"
            report_text = format_unified_report("جهة مختارة", None, target_id, fallback_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handler_private_messages(message):
    chat_id = message.chat.id

    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

    if message.forward_from:
        user = message.forward_from
        uname = user.username if user.username else None
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        acc_type = "حساب بوت رسمي" if user.is_bot else "مستخدم شخصي"
        report_text = format_unified_report(name, uname, user.id, acc_type)
        update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        return
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        uname = chat.username if chat.username else None
        acc_type = "قناة عامة" if chat.type == "channel" else "مجموعة تفاعلية"
        report_text = format_unified_report(chat.title, uname, chat.id, acc_type)
        update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        return
    elif message.forward_sender_name:
        report_text = format_unified_report(message.forward_sender_name, None, "غير متاح", "مستخدم شخصي (مخفي الهوية)")
        update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        return

    if message.text:
        text = message.text.strip()
        if text.startswith("/"):
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            return

        if not user_search_mode.get(chat_id, False):
            return

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port %s" % PORT)
    
    time.sleep(3)
    try:
        bot.remove_webhook()
        print("Old webhook removed successfully.")
    except Exception as e:
        print(f"Error removing webhook: %s" % e)

    while True:
        try:
            print("Starting bot polling safely...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: %s. Retrying in 5 seconds..." % e)
            time.sleep(5)
