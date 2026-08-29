import time
import threading
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# جلب توكن البورت والبوت من البيئة بأمان
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)

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
# 1. معالج عام لقراءة الروابط أو اليوزرنيمات في المجموعات والخاصة مباشرة
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and ('t.me/' in message.text or '@' in message.text))
def handle_group_or_private_links(message):
    text = message.text.strip()
    # استخراج اليوزرنيم أو الرابط بدقة
    match = re.search(r'(@[a-zA-Z0-9_]{5,}|https?://t\.me/[a-zA-Z0-9_+/]+)', text)
    if not match:
        return
        
    target_query = match.group(0)
    clean_target = target_query.replace("https://t.me/", "").replace("http://t.me/", "").strip("@/")
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
    
    try:
        query_target = f"@{clean_target}" if not target_query.startswith('http') and not target_query.startswith('@') else (target_query if target_query.startswith('@') else f"@{clean_target}")
        chat_info = bot.get_chat(query_target)
        
        chat_type_str = "قناة / مجموعة" if chat_info.type in ['channel', 'supergroup', 'group'] else "مستخدم"
        name = chat_info.title if chat_info.title else f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
        username = f"@{chat_info.username}" if chat_info.username else "غير متوفر"
        
        response_text = (
            f"😾 **معلومات الكيان المستهدف:**\n\n"
            f"• **النوع:** {chat_type_str}\n"
            f"• **الاسم:** {name}\n"
            f"• **المعرف:** {username}\n"
            f"• **الآيدي الثابت:** `{chat_info.id}`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

# 2. معالج الرد (Reply) في المجموعات (يعمل الآن بأي رد عادي بدون الحاجة لكتابة كلمة شركس)
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.reply_to_message is not None)
def handle_group_reply_extraction(message):
    reply_msg = message.reply_to_message
    markup_reply = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup_reply.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
    
    # إذا كانت الرسالة المُردود عليها تخص قناة أو مجموعة
    if reply_msg.sender_chat:
        target_chat = reply_msg.sender_chat
        response_text = (
            f"😾 **تفاصيل الكيان المستهدف (قناة/مجموعة):**\n\n"
            f"• **الاسم:** {target_chat.title}\n"
            f"• **المعرف:** @{target_chat.username if target_chat.username else 'غير متوفر'}\n"
            f"• **الآيدي الثابت:** `{target_chat.id}`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup_reply)
        return

    # إذا كانت الرسالة المُردود عليها تخص شخص (حتى لو كانت ملفاً، صورة، ملصقاً، إلخ)
    if reply_msg.from_user:
        target_user = reply_msg.from_user
        name = f"{target_user.first_name} {target_user.last_name or ''}".strip()
        username = f"@{target_user.username}" if target_user.username else "غير متوفر"
        
        response_text = (
            f"😾 **تفاصيل الحساب المستهدف (تخطي الفلترة):**\n\n"
            f"• **الاسم:** {name}\n"
            f"• **المعرف:** {username}\n"
            f"• **الآيدي الثابت:** `{target_user.id}`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup_reply)

# 3. معالج كلمة "شركس" وحدها في المجموعات لإظهار قائمة الأزرار والمسابقات
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text is not None and message.text.strip().lower() in ['شركس', 'sharكس', 'شاركس'])
def handle_group_menu_command(message):
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
