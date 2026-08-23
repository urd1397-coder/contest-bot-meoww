import os
import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# قراءة المتغيرات السرية
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 8000))

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! البوت يعمل الآن بنجاح سحابياً ومستقر 100% على السيرفر المجاني.")

# خدعة برمجية لفتح منفذ وهمي يمنع الـ Timed Out
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is Live!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()

if __name__ == '__main__':
    print("جاري تشغيل المنفذ الوهمي لمنع الـ Timed Out...")
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("جاري تشغيل البوت سحابياً بنجاح...")
    bot.infinity_polling()
