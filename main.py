import os
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)

# دالة الترحيب والأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🐾 الأوامر والمساعدة", callback_data="show_help"))
    bot.send_message(
        message.chat.id,
        "مرحباً! معك شركس 🐱\nجاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اضغط على الزر أدناه لنلقي نظرة على الأوامر.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "show_help")
def callback_help(call):
    bot.answer_callback_query(call.id, "تم فتح الأوامر بنجاح 📋")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_home"))
    
    help_text = (
        "📋 **قائمة خيارات وأوامر شركس:**\n\n"
        "🔹 `/id_help` : إحضار معرفات القنوات والقروبات والحسابات.\n"
        "🔹 `/create` : لبدء وإنشاء مسابقة جديدة.\n"
        "🔹 `/end` : لإنهاء المسابقة الحالية.\n"
        "🔹 `/cancel` : لتلغيم أي عملية جارية وتصفير الحالة."
    )
    bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def callback_home(call):
    bot.answer_callback_query(call.id, "عادت الأمور للبداية 🐾")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🐾 الأوامر والمساعدة", callback_data="show_help"))
    bot.edit_message_text(
        "مرحباً! معك شركس 🐱\nجاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اضغط على الزر أدناه لنلقي نظرة على الأوامر.",
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
