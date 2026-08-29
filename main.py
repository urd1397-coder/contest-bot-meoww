import os
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)

# دالة الترحيب والأوامر الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔹 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        telebot.types.InlineKeyboardButton("🔸 إنشاء مسابقة (create)", callback_data="cmd_create"),
        telebot.types.InlineKeyboardButton("🔺 إنهاء المسابقة (end)", callback_data="cmd_end"),
        telebot.types.InlineKeyboardButton("❌ إلغاء العملية (cancel)", callback_data="cmd_cancel")
    )
    bot.send_message(
        message.chat.id,
        "مرحباً! معك شركس 🐱\nجاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اختر الأمر المطلوب بالضغط على الزر:",
        reply_markup=markup
    )

# معالجة الضغط على زر المساعدة أو الأوامر
@bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
def callback_commands(call):
    action = call.data.split("_")[1]
    
    if action == "id_help":
        bot.answer_callback_query(call.id, "جاري إحضار معلومات الآيدي...")
        # ضع هنا الكود أو الرد الخاص بأمر id_help
        bot.send_message(call.message.chat.id, "📋 معلومات الآيدي الخاصة بك أو بالقروب...")
        
    elif action == "create":
        bot.answer_callback_query(call.id, "تم بدء إنشاء المسابقة!")
        # ضع هنا الكود أو الرد الخاص بأمر create
        bot.send_message(call.message.chat.id, "✨ تم بدء عملية إنشاء مسابقة جديدة...")
        
    elif action == "end":
        bot.answer_callback_query(call.id, "تم إنهاء المسابقة الحالية.")
        # ضع هنا الكود أو الرد الخاص بأمر end
        bot.send_message(call.message.chat.id, "🛑 تم إنهاء المسابقة الحالية بنجاح.")
        
    elif action == "cancel":
        bot.answer_callback_query(call.id, "تم إلغاء العملية.")
        # ضع هنا الكود أو الرد الخاص بأمر cancel
        bot.send_message(call.message.chat.id, "↩️ تم تصفير وإلغاء أي عملية جارية.")

# زر العودة للقائمة الرئيسية
@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def callback_home(call):
    bot.answer_callback_query(call.id, "عادت الأمور للبداية 🐾")
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🔹 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        telebot.types.InlineKeyboardButton("🔸 إنشاء مسابقة (create)", callback_data="cmd_create"),
        telebot.types.InlineKeyboardButton("🔺 إنهاء المسابقة (end)", callback_data="cmd_end"),
        telebot.types.InlineKeyboardButton("❌ إلغاء العملية (cancel)", callback_data="cmd_cancel")
    )
    bot.edit_message_text(
        "مرحباً! معك شركس 🐱\nجاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اختر الأمر المطلوب بالضغط على الزر:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# سيرفر HTTP بسيط جداً لفتح البورت المطلوب على Render وتجاوز فحص المنفذ
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sharx Bot is active and running!")

    def do_HEAD(self):
        self.send_response(200)
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

    # تصفير أي ويب هوك قديم والبدء بالبولينغ مباشرة
    bot.remove_webhook()
    print("Starting TeleBot polling...")
    bot.infinity_polling(skip_pending=True)
