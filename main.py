import time
import threading
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = telebot.TeleBot(BOT_TOKEN)

# [ دالة الرد بالمجموعات ]
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and message.text and 'شركس' in message.text)
def handle_groups_full(message):
    print(f"Group Message Received in chat ID: {message.chat.id}")
    
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

# سيرفر الويب الخاص بـ Render
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
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")

    time.sleep(5)

    bot.remove_webhook()
    print("Starting TeleBot polling safely...")

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling warning: {e}. Retrying in 5 seconds...")
            time.sleep(5)
