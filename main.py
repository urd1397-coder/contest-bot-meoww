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
    
# مجموعة لتخزين آيدي المشرفين المفعلين في الجلسة المؤقتة للمجموعات
id_help_sessions = set()

# 1. أمر id_help في المحادثة الخاصة (كتابة أو عبر الزر)
@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text is not None and message.text.strip() in ['id_help', '/id_help'])
def private_id_help_prompt(message):
    print("DEBUG: Private id_help triggered.")
    user_id = message.from_user.id
    id_help_sessions.add(user_id)
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
    bot.reply_to(
        message,
        "😾 أرسل لي الآن إعادة توجيه (Forward)، أو يوزرنيم، أو أي رسالة مهما كان نوعها للحصول على تفاصيلها.",
        reply_markup=markup
    )

# 2. معالجة الضغط على زر "معرفة الأيدي" من القائمة الشفافة بالخاص
@bot.callback_query_handler(func=lambda call: call.data == "cmd_id_help")
def callback_id_help(call):
    print("DEBUG: Callback id_help triggered.")
    user_id = call.from_user.id
    id_help_sessions.add(user_id)
    
    bot.answer_callback_query(call.id, "😾 وضع كشف المعرفات مفعّل")
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
    bot.send_message(
        call.message.chat.id,
        "😾 أرسل لي الآن أي رسالة، توجيه، أو يوزرنيم للحصول على تفاصيلها الكاملة.",
        reply_markup=markup
    )

# 3. تفعيل أمر id_help في المجموعة (كتابة الأمر مع الرد على الرسالة المطلوبة)
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text is not None and message.text.strip() in ['id_help', '/id_help'])
def group_id_help_trigger(message):
    print("DEBUG: Group id_help session activated by admin.")
    user_id = message.from_user.id
    
    # التحقق إن كان المستخدم قام بالرد على رسالة مباشرة مع كتابة الأمر
    if message.reply_to_message:
        # تنفيذ الفحص مباشرة لأن المشرف حدد الرسالة بالرد وأمر معا
        process_id_action(message, message.reply_to_message)
    else:
        # تسجيل الجلسة إذا أرسل الأمر وحده لكي ينتظر ردّه أو توجيهه القادم
        id_help_sessions.add(user_id)
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))
        bot.reply_to(message, "😾 تم تفعيل وضع كشف المعرفات. قم بالرد (Reply) أو التوجيه (Forward) على الرسالة المطلوبة الآن.", reply_markup=markup)

# 4. المعالج الشامل والآمن (يعمل في الخاصة لأي رسالة، وفي المجموعة حصراً للمشرف المفعل)
@bot.message_handler(func=lambda message: message.chat.type == 'private' or message.from_user.id in id_help_sessions)
def universal_secure_handler(message):
    user_id = message.from_user.id
    if message.chat.type in ['group', 'supergroup']:
        id_help_sessions.discard(user_id) # إنهاء الجلسة فور الاستجابة بالمجموعة للأمان
    
    process_id_action(message, message.reply_to_message)

# دالة مركزية معالجة لاستخراج الأيدي لضمان عدم تكرار الكود ودعم كافة الأنواع
def process_id_action(message, reply_msg):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("🏠 العودة للبداية", callback_data="back_home"))

    # أ. إذا كانت رسالة معاد توجيهها (Forward) - مهما كان نوعها
    if getattr(message, 'forward_date', None) is not None:
        if message.forward_from:
            target = message.forward_from
            target_type = "شخص (محادثة خاصة)"
            name = f"{target.first_name} {target.last_name or ''}".strip()
            username = f"@{target.username}" if target.username else "غير متوفر"
            target_id = target.id
        elif message.forward_from_chat:
            target = message.forward_from_chat
            target_type = "قناة أو مجموعة"
            name = target.title or "غير معروف"
            username = f"@{target.username}" if target.username else "غير متوفر"
            target_id = target.id
        elif message.forward_sender_name:
            target_type = "شخص (حساب مخفي الإعدادات)"
            name = message.forward_sender_name
            username = "غير متوفر (محمي بواسطة الخصوصية)"
            target_id = "مخفي من قِبل تيليجرام"
        else:
            bot.reply_to(message, "😾 لم يتم التعرف على مصدر التوجيه.", reply_markup=markup)
            return

        response_text = (
            f"😾 **معلومات الكيان المستهدف:**\n\n"
            f"• **النوع:** {target_type}\n"
            f"• **الاسم:** {name}\n"
            f"• **المعرف:** {username}\n"
            f"• **الآيدي الثابت:** `{target_id}`"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup)
        return

    # ب. إذا كانت رسالة تم الرد عليها (Reply) - تدعم الملصقات والصور وكل الأنواع
    if reply_msg is not None:
        target_user = None
        if reply_msg.from_user:
            target_user = reply_msg.from_user
        elif reply_msg.sender_chat:
            target_chat = reply_msg.sender_chat
            response_text = (
                f"😾 **تفاصيل الكيان (قناة/مجموعة):**\n\n"
                f"• **الاسم:** {target_chat.title}\n"
                f"• **المعرف:** @{target_chat.username if target_chat.username else 'غير متوفر'}\n"
                f"• **الآيدي الثابت:** `{target_chat.id}`"
            )
            bot.reply_to(reply_msg, response_text, parse_mode="Markdown", reply_markup=markup)
            return

        if not target_user:
            bot.reply_to(reply_msg, "😾 عذراً، لا يمكن استخراج آيدي هذا العنصر.", reply_markup=markup)
            return

        name = f"{target_user.first_name} {target_user.last_name or ''}".strip()
        username = f"@{target_user.username}" if target_user.username else "غير متوفر"
        user_id_fixed = target_user.id

        response_text = (
            f"😾 **تفاصيل الحساب المستهدف:**\n\n"
            f"• **الاسم:** {name}\n"
            f"• **المعرف:** {username}\n"
            f"• **الآيدي الثابت:** `{user_id_fixed}`"
        )
        bot.reply_to(reply_msg, response_text, parse_mode="Markdown", reply_markup=markup)
        return

    # ج. إذا أرسل يوزرنيم مباشرة (يبدأ بـ @)
    if message.text is not None and message.text.strip().startswith('@'):
        username_input = message.text.strip()
        try:
            chat_info = bot.get_chat(username_input)
            name = chat_info.title if chat_info.type in ['channel', 'supergroup', 'group'] else f"{chat_info.first_name} {chat_info.last_name or ''}".strip()
            target_type = "قناة / مجموعة" if chat_info.type in ['channel', 'supergroup', 'group'] else "حساب شخصي"
            
            response_text = (
                f"😾 **تفاصيل المعرف المطلوب:**\n\n"
                f"• **النوع:** {target_type}\n"
                f"• **الاسم:** {name}\n"
                f"• **المعرف:** @{chat_info.username if chat_info.username else username_input.replace('@', '')}\n"
                f"• **الآيدي الثابت:** `{chat_info.id}`"
            )
            bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            bot.reply_to(message, f"😾 عذراً، لم أتمكن من العثور على `{username_input}`.", parse_mode="Markdown", reply_markup=markup)
        return

    # د. أي رسالة أخرى (صورة مرسلة مباشرة، ملف، ملصق، إلخ)
    target_user = message.from_user
    name = f"{target_user.first_name} {target_user.last_name or ''}".strip()
    username = f"@{target_user.username}" if target_user.username else "غير متوفر"
    
    response_text = (
        f"😾 **تفاصيل مرسل الرسالة:**\n\n"
        f"• **الاسم:** {name}\n"
        f"• **المعرف:** {username}\n"
        f"• **الآيدي الثابت:** `{target_user.id}`"
    )
    bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=markup)

# 5. زر العودة لإلغاء الجلسة
@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home_handler(call):
    user_id = call.from_user.id
    id_help_sessions.discard(user_id)
    bot.answer_callback_query(call.id, "🏠 تم إلغاء الطلب والعودة للبداية")
    # ضع هنا منطق العودة للقائمة الرئيسية للبوت الخاص بك


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
