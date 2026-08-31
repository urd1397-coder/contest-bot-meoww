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

# --- البحث الشامل عبر الإنترنت في حال عدم توفر المعرف المباشر ---
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
            bio = desc_tag["content"] if desc_tag else "لا يوجد وصف متاح 🐾"
            
            return {
                "found": True,
                "name": name,
                "username": f"@{clean_un}",
                "bio": bio,
                "note": "✨ تم إحضار البيانات بنجاح من شبكة تيليجرام 🌐"
            }
    except Exception:
        pass
    return {"found": False}

# --- أزرار التنقل الثابتة تحت كل رسالة إجابة ---
def create_navigation_markup(back_callback="cmd_id_help"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

# --- أزرار القروب (زرين للمسابقات فقط) ---
def create_group_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية (قيد التطوير)", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية (قيد التطوير)", callback_data="cmd_end")
    )
    return markup

# --- القائمة الرئيسية (للخاص) ---
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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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

# --- تنسيق تقرير الحساب الاحترافي ---
def format_user_report(chat_info, source_chat_id=None):
    uname = f"@{chat_info.username}" if getattr(chat_info, 'username', None) else "لا يوجد يوزر عام"
    role_status = "عضو نشط 🐱"
    
    if source_chat_id:
        try:
            member = bot.get_chat_member(source_chat_id, chat_info.id)
            if member.status == 'creator':
                role_status = "👑 مالك القروب الملكي"
            elif member.status == 'administrator':
                role_status = "🛡️ مشرف الحماية"
            else:
                role_status = "👤 عضو أساسي"
        except Exception:
            role_status = "👤 عضو القروب"

    name = getattr(chat_info, 'first_name', None) or getattr(chat_info, 'title', None) or "مستخدم تيليجرام"

    return (
        f"🐾 <b>[ بطاقة حماية شركس الذكية ]</b> 🐱✨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>الاسم:</b> {name}\n"
        f"🔗 <b>المعرف:</b> {uname}\n"
        f"🆔 <b>الآيدي:</b> <code>{chat_info.id}</code>\n"
        f"📌 <b>الرتبة:</b> {role_status}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>نظام شركس السريع والمؤقت لخدمتكم!</i>"
    )

def format_chat_report(c):
    uname = f"@{c.username}" if getattr(c, 'username', None) else "بدون معرف عام"
    chat_type_ar = "📢 قناة عامة / إخبارية" if getattr(c, 'type', '') == "channel" else "👥 مجموعة تفاعلية نشطة"
    title = getattr(c, 'title', 'جهة تيليجرام')
    return (
        f"🐾 <b>[ بطاقة جهة شركس الخارجية ]</b> 🐱⚡\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>اسم الجهة:</b> {title}\n"
        f"🔗 <b>اليوزر:</b> {uname}\n"
        f"🆔 <b>آيدي الجهة:</b> <code>{c.id}</code>\n"
        f"📌 <b>التصنيف:</b> {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>جاري فحص وتأمين البيانات بنجاح!</i>"
    )

@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
    bot.send_message(
        message.chat.id,
        "مياو أهلاً بك في عالم شركس! 🐱✨\n"
        "البوت الأنيق والسريع لإدارة وحماية مجموعاتك وقنواتك بكل احترافية.\n"
        "اختر ما يناسبك من الخيارات أدناه:",
        reply_markup=create_main_menu_markup()
    )

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
            bot.answer_callback_query(call.id, "هذه الميزة الرائعة قيد التطوير حالياً 🚧", show_alert=True)
        except Exception:
            pass
    elif call.data == "cmd_id_help":
        bot.edit_message_text(
            "⚡ <b>قسم البحث والاستخراج المتقدم</b> 🐾\n\n"
            "اختر الطريقة المناسبة لجلب البيانات بسرعة وسلاسة:",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        bot.send_message(
            chat_id,
            "👇 استخدم لوحة المفاتيح السفلية أدناه للاختيار السريع:",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif call.data == "method_username":
        bot.edit_message_text(
            "🌐 <b>[ وضع البحث اليدوي والروابط والقنوات ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر (مثل `@username`)، رابط القناة، أو معرفها وسأقوم بجلب تفاصيلها فوراً بقالب شركس الأنيق 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_navigation_markup("cmd_id_help")
        )
    elif call.data == "method_forward":
        bot.edit_message_text(
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة من أي شخص أو قناة لاستخراج بياناتها السرية فوراً!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_navigation_markup("cmd_id_help")
        )
    elif call.data == "cmd_home":
        bot.edit_message_text(
            "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:",
            chat_id,
            message_id,
            reply_markup=create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        bot.edit_message_text(
            "❌ تم إغلاق القائمة بنجاح. أرسل /start في أي وقت لإظهارها مجدداً.",
            chat_id,
            message_id,
            reply_markup=None
        )

@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    target_id = None

    if message.users_shared:
        target_id = message.users_shared.user_ids[0]
    elif message.chat_shared:
        target_id = message.chat_shared.chat_id

    if target_id:
        try:
            chat_info = bot.get_chat(target_id)
            if chat_info.type == "private":
                report_text = format_user_report(chat_info, message.chat.id)
            else:
                report_text = format_chat_report(chat_info)
            bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        except Exception:
            class TempObj:
                pass
            t = TempObj()
            t.id = target_id
            t.username = None
            t.first_name = "مستخدم مختار"
            report_text = format_user_report(t, message.chat.id)
            bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
    else:
        bot.send_message(message.chat.id, "⚠️ عذراً، لم يتم استلام أي معرف صالح.", reply_markup=create_navigation_markup("cmd_id_help"))

    bot.send_message(message.chat.id, "🔹 لوحة التحكم السريعة:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_private_messages(message):
    if message.forward_from:
        report_text = format_user_report(message.forward_from)
        bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        return
    elif message.forward_from_chat:
        report_text = format_chat_report(message.forward_from_chat)
        bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        return
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

        if len(clean_username) >= 2:
            try:
                target_query = "@" + clean_username if not text.startswith("@") and "t.me" not in text else text
                chat_info = bot.get_chat(target_query)
                if chat_info.type == "private":
                    report_text = format_user_report(chat_info)
                else:
                    report_text = format_chat_report(chat_info)
                bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
                return
            except Exception:
                adv_result = fetch_advanced_web_lookup(clean_username)
                if adv_result["found"]:
                    report_text = (
                        f"🐾 <b>[ بطاقة شركس للبحث الشامل ]</b> 🌐✨\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"📛 <b>الاسم / العنوان:</b> {adv_result['name']}\n"
                        f"🔗 <b>المعرف:</b> {adv_result['username']}\n"
                        f"📝 <b>الوصف:</b> {adv_result['bio']}\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"✨ {adv_result['note']}"
                    )
                    bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
                    return
                else:
                    bot.send_message(message.chat.id, f"❌ لم نتمكن من العثور على أي نتائج مطابقة لـ: <b>{text}</b> 🐾", parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))

@bot.message_handler(chat_types=["group", "supergroup"], content_types=["text"])
def handle_group_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id

    if "شركس" in text and not message.reply_to_message:
        bot.reply_to(
            message,
            "مياو! 🐱 أهلاً بك يا رئيس. إليك خيارات المسابقات المتاحة:",
            reply_markup=create_group_menu_markup()
        )
        return

    if message.reply_to_message:
        if "شركس" in text or "آيدي" in text or "id" in text.lower() or "معلومات" in text:
            if not is_user_admin(chat_id, user_id):
                bot.reply_to(message, "⚠️ عذراً صديقي، هذه الميزة مخصصة لمشرفي المجموعة فقط!")
                return

            target_user = message.reply_to_message.from_user
            if target_user:
                report_text = format_user_report(target_user, chat_id)
                bot.reply_to(message, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))

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
