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
        types.InlineKeyboardButton("🌐 البحث اليدوي المباشر (يوزر / رابط / قناة)", callback_data="method_username"),
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
    
    # تنسيق اليوزرنيم في سطر مستقل إذا وجد
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
            # جلب تفاصيل الحساب الكاملة من تيليجرام لاستخراج الاسم واليوزر الحقيقي
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

        clean_target = text
        if "t.me/" in text:
            clean_target = "@" + text.split("t.me/")[-1].split("/")[0].strip()
        elif "telegram.me/" in text:
            clean_target = "@" + text.split("telegram.me/")[-1].split("/")[0].strip()
        elif not text.startswith("@"):
            clean_target = "@" + text

        user_search_mode[chat_id] = False
        try:
            chat_info = bot.get_chat(clean_target)
            uname = getattr(chat_info, 'username', None)
            
            if chat_info.type == "private":
                first = getattr(chat_info, 'first_name', '') or ''
                last = getattr(chat_info, 'last_name', '') or ''
                name = f"{first} {last}".strip() or "مستخدم تيليجرام"
                acc_type = "حساب بوت رسمي" if getattr(chat_info, 'is_bot', False) else "مستخدم شخصي"
            elif chat_info.type == "channel":
                name = getattr(chat_info, 'title', 'قناة تيليجرام')
                acc_type = "قناة عامة"
            else:
                name = getattr(chat_info, 'title', 'مجموعة تيليجرام')
                acc_type = "مجموعة تفاعلية"
            
            report_text = format_unified_report(name, uname, chat_info.id, acc_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        except Exception as e:
            err_text = f"❌ عذراً، لم أتمكن من جلب البيانات لـ: <b>{text}</b>\n\nتأكد أن اليوزر صحيح أو جرب إعادة توجيه رسالة منه مباشرة 🐾"
            update_or_send_panel(chat_id, err_text, create_navigation_markup("cmd_id_help"))

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
