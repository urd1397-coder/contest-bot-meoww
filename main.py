import time
import threading
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# جلب توكن البورت والبوت من البيئة بأمان
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)

# تخزين المستخدمين الذين قاموا بتفعيل أداة معرفة الآيدي في المحادثة الخاصة
active_id_help_users = set()

# دالة الترحيب والأزرار الأساسية في الخاص
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔍😼 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        telebot.types.InlineKeyboardButton("🎯😸 إنشاء مسابقة (create)", callback_data="cmd_create"),
        telebot.types.InlineKeyboardButton("⛔😺 إنهاء المسابقة (end)", callback_data="cmd_end"),
        telebot.types.InlineKeyboardButton("❌😺 إلغاء العملية (cancel)", callback_data="cmd_cancel")
    )
    bot.reply_to(
        message,
        "مرحباً! معك شركس 🐱\nجاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اختر الأمر المطلوب بالضغط على الزر أدناه:",
        reply_markup=markup
    )

# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def callback_home(call):
    user_id = call.from_user.id
    active_id_help_users.discard(user_id)  # إلغاء تفعيل وضع الآيدي عند العودة للقائمة
    bot.answer_callback_query(call.id, "عادت الأمور للبداية 🐱")
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔍😼 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        telebot.types.InlineKeyboardButton("🎯😸 إنشاء مسابقة (create)", callback_data="cmd_create"),
        telebot.types.InlineKeyboardButton("⛔😺 إنهاء المسابقة (end)", callback_data="cmd_end"),
        telebot.types.InlineKeyboardButton("❌😺 إلغاء العملية (cancel)", callback_data="cmd_cancel")
    )
    bot.edit_message_text(
        "مرحباً! معك شركس 🐱، جاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اختر الأمر المطلوب بالضغط على الزر:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# تفعيل أداة معرفة الآيدي عند الضغط على الزر الشفاف
@bot.callback_query_handler(func=lambda call: call.data == "cmd_id_help")
def activate_id_help(call):
    user_id = call.from_user.id
    active_id_help_users.add(user_id)
    bot.answer_callback_query(call.id, "🔍 تم تفعيل أداة معرفة الآيدي")
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
    
    bot.send_message(
        call.message.chat.id,
        "🎯 **تم تفعيل أداة (id_help) بنجاح!**\n\n"
        "الآن يمكنك إرسال:\n"
        "• **إعادة توجيه (Forward)** لأي رسالة (ملف، صورة، ملصق، فيديو).\n"
        "• **يوزرنيم** (@username).\n"
        "• **رابط** لشخص، قناة، أو مجموعة.\n\n"
        "وسأستخرج معلوماته لك فوراً.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# معالجة رسائل التوجيه (Forward) بغض النظر عن نوعها في الخاصة
@bot.message_handler(func=lambda message: message.chat.type == 'private' and getattr(message, 'forward_date', None) is not None)
def handle_forwarded_content(message):
    user_id = message.from_user.id
    if user_id not in active_id_help_users:
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))

    if message.forward_from:
        target = message.forward_from
        t_type = "شخص (حساب خاص)"
        name = f"{target.first_name} {target.last_name or ''}".strip()
        username = f"@{target.username}" if target.username else "غير متوفر"
        t_id = target.id
    elif message.forward_from_chat:
        target = message.forward_from_chat
        t_type = "قناة أو مجموعة"
        name = target.title or "غير معروف"
        username = f"@{target.username}" if target.username else "غير متوفر"
        t_id = target.id
    elif message.forward_sender_name:
        t_type = "شخص (حساب مخفي)"
        name = message.forward_sender_name
        username = "محمي بواسطة إعدادات الخصوصية"
        t_id = "مخفي"
    else:
        bot.reply_to(message, "⚠️ لم نتمكن من قراءة مصدر التوجيه.", reply_markup=markup)
        return

    result_text = (
        f"🔍 **معلومات الكيان المستخرج (عبر التوجيه):**\n\n"
        f"• **النوع:** {t_type}\n"
        f"• **الاسم:** {name}\n"
        f"• **المعرف:** {username}\n"
        f"• **الآيدي الثابت:** `{t_id}`"
    )
    bot.reply_to(message, result_text, parse_mode="Markdown", reply_markup=markup)

# معالجة الروابط أو اليوزرنيمات المرسلة نصياً في الخاصة بعد تفعيل الأداة
@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text and not message.text.startswith('/'))
def handle_text_target_query(message):
    user_id = message.from_user.id
    if user_id not in active_id_help_users:
        return

    text = message.text.strip()
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))

    if '@' in text or 't.me/' in text:
        clean_target = text.replace("https://t.me/", "").replace("http://t.me/", "").strip("@/")
        try:
            query_target = f"@{clean_target}" if not text.startswith('http') and not text.startswith('@') else (text if text.startswith('@') else f"@{clean_target}")
            chat_info = bot.get_chat(query_target)
            
            chat_type_str = "قناة / مجموعة" if chat_info.type in ['channel', 'supergroup', 'group'] else "مستخدم"
            name = chat_info.title if chat_info.title else f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
            username = f"@{chat_info.username}" if chat_info.username else "غير متوفر"
            
            result_text = (
                f"🔍 **معلومات الكيان المستهدف (عبر الرابط/اليوزرنيم):**\n\n"
                f"• **النوع:** {chat_type_str}\n"
                f"• **الاسم:** {name}\n"
                f"• **المعرف:** {username}\n"
                f"• **الآيدي الثابت:** `{chat_info.id}`"
            )
            bot.reply_to(message, result_text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            bot.reply_to(message, f"⚠️ عذراً، لم أستطع العثور على معلومات لـ ({text}). تأكد من صحة الرابط أو المعرف.", reply_markup=markup)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال **إعادة توجيه (Forward)** أو **يوزرنيم** أو **رابط** صحيح للاستعلام عنه.", reply_markup=markup)

# [ دالة الرد بلمجموعات ]
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text and 'شركس' in message.text)
def handle_groups_full(message):
    print(f"Group Message Received in chat ID: {message.chat.id}")
    
    # القائمة الكاملة بجميع الأزرار والخيارات للمجموعات
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔍😼 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        telebot.types.InlineKeyboardButton("🎯😸 إنشاء مسابقة (create)", callback_data="cmd_create"),
        telebot.types.InlineKeyboardButton("⛔😺 إنهاء المسابقة (end)", callback_data="cmd_end"),
        telebot.types.InlineKeyboardButton("🔄😺 إعادة البدء (restart)", callback_data="cmd_restart"),
        telebot.types.InlineKeyboardButton("❌😺 إلغاء العملية (cancel)", callback_data="cmd_cancel")
    )
    
    bot.reply_to(
        message,
        "أهلاً بك في المجموعة! معك شركس 🐱، إليك كافة الخيارات المتاحة:",
        reply_markup=markup
    )
    
# تجاوز فحص المنفذ بسيط جداً Render لفتح البورت المطلوب على HTTP سيرفر #
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
    server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    # تشغيل سيرفر الويب في خلفية مستقلة لفتح البورت
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")

    # انتظار 5 ثوانٍ لضمان إغلاق النسخة القديمة تماماً
    time.sleep(5)

    bot.remove_webhook()
    print("Starting TeleBot polling safely...")

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling warning: {e}. Retrying in 5 seconds...")
            time.sleep(5)
