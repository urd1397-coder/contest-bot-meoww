import os
import sys
import logging
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# تثبيت المكتبة لضمان استقرار البيئة
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PicklePersistence
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.8"])
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PicklePersistence

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TEXTS = {
    "ar": {
        "welcome": "👋 أهلاً بك في بوت شركس للمسابقات والفعاليات المفتوحة!\n\nأجب على الاستطلاع أدناه بالضغط على الزر المزين لنبدأ معاً! ✨",
        "poll_question": "🎭 جاهز لبدء المسابقة؟ اضغط على الزر أدناه:",
        "poll_option": "✨🚀 اِبدأ الآن | START NOW 🚀✨"
    },
    "en": {
        "welcome": "👋 Welcome to Sharkas Open Contest Bot!\n\nAnswer the poll below by clicking the decorated button to start! ✨",
        "poll_question": "🎭 Ready to start the quiz? Click the button below:",
        "poll_option": "✨🚀 START NOW | اِبدأ الآن 🚀✨"
    }
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower() if update.message.text else ""
    user_lang = update.effective_user.language_code
    
    lang = "ar" if (user_lang == "ar" or "بدء" in user_text) else "en"
    context.user_data["lang"] = lang
    
    await update.message.reply_text(TEXTS[lang]["welcome"])
    
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=TEXTS[lang]["poll_question"],
        options=[TEXTS[lang]["poll_option"]],
        is_anonymous=False,
        allows_multiple_answers=False
    )

# 🌐 خادم ويب مصغر وخفيف جداً لمنع توقف السيرفر المجاني في Render
class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sharkas Bot is Active")

def run_web_server(port):
    server = HTTPServer(('0.0.0.0', port), WebHandler)
    server.serve_forever()

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    PORT = int(os.getenv("PORT", 8000))
    
    if not TOKEN:
        logger.error("خطأ: لم يتم العثور على BOT_TOKEN!")
        return

    # تشغيل خادم الويب في خلفية النظام لإرضاء Render ومنع خطأ الـ Port
    threading.Thread(target=run_web_server, args=(PORT,), daemon=True).start()

    # التخزين السحابي المستمر لبيانات شركس لضمان عدم ضياع المسابقات
    bot_persistence = PicklePersistence(filepath="sharkas_data.pickle")
    application = Application.builder().token(TOKEN).persistence(bot_persistence).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Text(["بدء", "start", "البدء", "Start"]), start_command))

    logger.info("🚀 جاري تشغيل شركس وتصفية الرسائل القديمة المتراكمة...")
    
    # تشغيل مستقر وتجاهل كامل للرسائل المعلقة القديمة لمنع التكرار والتعليق
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
