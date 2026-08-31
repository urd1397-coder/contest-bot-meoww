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

# تخزين حالة البحث اليدوي النصي
user_search_mode = {}

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

# --- التحقق من الإشراف ---
def is_user_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# --- البحث الويب الدقيق ---
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
            bio = desc_tag["content"] if desc_tag else ""
            
            account_type = "قناة عامة على تيليجرام"
            if bio and ("is telegram" in bio.lower() or "chat group" in bio.lower() or "group" in bio.lower()):
                account_type = "مجموعة عامة على تيليجرام"
            elif not bio or "fast secure powerful" in bio.lower() or "telegram - a new era" in bio.lower():
                account_type = "حساب شخصي أو قناة عامة"

            return {
                "found": True,
                "name": name,
                "username": f"@{clean_un}",
                "type": account_type
            }
    except Exception:
        pass
    return {"found": False}

# --- أزرار التنقل الثابتة ---
def create_navigation_markup(back_callback="cmd_id_help"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_group_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية (قيد التطوير)", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية (قيد التطوير)", callback_data="cmd_end")
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

# --- تنسيق التقرير الدقيق الموحد ---
def format_unified_report(name, username, user_id, account_type):
    formatted_username = username if username and username != "None" else "لا يوجد يوزر"
    
    return (
        f"🐾 <b>[ بطاقة شركس الذكية ]</b> 🐱✨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"<b>username:</b> {formatted_username}\n"
        f"👤 <b>الاسم:</b> {name}\n"
        f"🆔 <b>الآيدي:</b> <code>{user_id}</code>\n"
        f"📌 <b>نوع الحساب:</b> {account_type}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>نظام شركس السريع لخدمتكم!</i>"
    )

@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
    user_search_mode[message.chat.id] = False
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
        user_search_mode[chat_id] = False
        bot.edit_message_text(
            "⚡ <b>قسم البحث والاستخراج المتقدم</b> 🐾\n\n"
            "اختر الطريقة المناسبة لجلب البيانات بسرعة وسلاسة:",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        user_search_mode[chat_id] = False
        bot.send_message(
            chat_id,
            "👇 استخدم لوحة المفاتيح السفلية أدناه للاختيار السريع:",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif call.data == "method_username":
        user_search_mode[chat_id] = True
        bot.edit_message_text(
            "🌐 <b>[ وضع البحث اليدوي والروابط والقنوات ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر المطلوب (مثل `@username`)، رابط القناة، أو معرفها وسأقوم بجلب تفاصيلها فوراً 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_navigation_markup("cmd_id_help")
        )
    elif call.data == "method_forward":
        user_search_mode[chat_id] = False
        bot.edit_message_text(
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة من أي شخص أو قناة هنا لاستخراج بياناتها بدقة!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_navigation_markup("cmd_id_help")
        )
    elif call.data == "cmd_home":
        user_search_mode[chat_id] = False
        bot.edit_message_text(
            "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:",
            chat_id,
            message_id,
            reply_markup=create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        user_search_mode[chat_id] = False
        bot.edit_message_text(
            "❌ تم إغلاق القائمة بنجاح. أرسل /start في أي وقت لإظهارها مجدداً.",
            chat_id,
            message_id,
            reply_markup=None
        )

# --- معالج الاختيارات السفلية (مُصلح بالكامل لجلب البيانات وعرضها بالبطاقة) ---
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
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
            uname = f"@{chat_info.username}" if getattr(chat_info, 'username', None) else "لا يوجد يوزر"
            name = getattr(chat_info, 'first_name', None) or getattr(chat_info, 'title', 'جهة تيليجرام')
            
            if is_chat:
                acc_type = "قناة عامة على تيليجرام" if chat_info.type == "channel" else "مجموعة تفاعلية على تيليجرام"
            else:
                acc_type = "حساب بوت رسمي" if getattr(chat_info, 'is_bot', False) else "مستخدم شخصي"

            report_text = format_unified_report(name, uname, chat_info.id, acc_type)
            bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        except Exception:
            # احتياطي في حال لم يتمكن البوت من جلب معلومات مباشرة
            fallback_type = "مجموعة أو قناة تيليجرام" if is_chat else "مستخدم شخصي"
            report_text = format_unified_report("جهة مختارة", "لا يوجد يوزر", target_id, fallback_type)
            bot.send_message(message.chat.id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
    else:
        bot.send_message(message.chat.id, "⚠️ عذراً، لم يتم استلام أي معرف صالح.", reply_markup=create_navigation_markup("cmd_id_help"))

    # إزالة لوحة المفاتيح السفلية بعد الاستخدام لمنع التشويش
    bot.send_message(message.chat.id, "🔹 تم إتمام الاستخراج بنجاح:", reply_markup=types.ReplyKeyboardRemove())

# --- معالج الرسائل الخاصة ---
@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_private_messages(message):
    chat_id = message.chat.id

    # 1. معالجة التحويل (Forward)
    if message.forward_from:
        user = message.forward_from
        uname = f"@{user.username}" if user.username else "لا يوجد يوزر"
        acc_type = "حساب بوت رسمي" if user.is_bot else "مستخدم شخصي"
        report_text = format_unified_report(user.first_name, uname, user.id, acc_type)
        bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        return
    elif message.forward_from_chat:
        chat = message.forward_from_chat
        uname = f"@{chat.username}" if chat.username else "قناة/مجموعة خاصة"
        acc_type = "قناة تيليجرام" if chat.type == "channel" else "مجموعة تيليجرام"
        report_text = format_unified_report(chat.title, uname, chat.id, acc_type)
        bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        return
    elif message.forward_sender_name:
        report_text = format_unified_report(message.forward_sender_name, "حساب مخفي الإعدادات", "غير متاح", "حساب شخصي مخفي الهوية")
        bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
        return

    # 2. معالجة البحث اليدوي النصي (يعمل فقط عند تفعيل وضع البحث من الزر)
    if message.text:
        text = message.text.strip()
        if text.startswith("/"):
            return

        if not user_search_mode.get(chat_id, False):
            return

        clean_username = text
        if "t.me/" in text:
            clean_username = text.split("t.me/")[-1].split("/")[0].strip()
        elif "telegram.me/" in text:
            clean_username = text.split("telegram.me/")[-1].split("/")[0].strip()
        else:
            clean_username = text.replace("@", "").strip()

        if len(clean_username) >= 2:
            user_search_mode[chat_id] = False
            try:
                target_query = "@" + clean_username if not text.startswith("@") and "t.me" not in text else text
                chat_info = bot.get_chat(target_query)
                uname = f"@{chat_info.username}" if getattr(chat_info, 'username', None) else "لا يوجد يوزر"
                name = getattr(chat_info, 'first_name', None) or getattr(chat_info, 'title', 'جهة تيليجرام')
                
                acc_type = "مستخدم شخصي" if chat_info.type == "private" else ("قناة عامة" if chat_info.type == "channel" else "مجموعة تفاعلية")
                
                report_text = format_unified_report(name, uname, chat_info.id, acc_type)
                bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
                return
            except Exception:
                adv_result = fetch_advanced_web_lookup(clean_username)
                if adv_result["found"]:
                    report_text = format_unified_report(adv_result['name'], adv_result['username'], "رابط خارجي / عام", adv_result['type'])
                    bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))
                    return
                else:
                    bot.send_message(chat_id, f"❌ ملاحظة: بالنسبة للقنوات أو المجموعات <b>الخاصة</b>، لا يمكن للبوت جلب بياناتها إلا إذا كان مشرفاً فيها.\n\nلم يتم العثور على نتائج مطابقة لـ: <b>{text}</b> 🐾", parse_mode="HTML", reply_markup=create_navigation_markup("cmd_id_help"))

# --- معالج القروبات ---
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
                uname = f"@{target_user.username}" if target_user.username else "لا يوجد يوزر"
                acc_type = "حساب بوت رسمي" if target_user.is_bot else "عضو في المجموعة"
                report_text = format_unified_report(target_user.first_name, uname, target_user.id, acc_type)
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
