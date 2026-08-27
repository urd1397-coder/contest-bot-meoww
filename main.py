import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PicklePersistence

# إعدادات تسجيل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TEXTS = {
    "ar": {
        "welcome": "👋 أهلاً بك في بوت شركس للمسابقات!\n\nللبدء، يرجى الانضمام إلى قناتنا أولاً لمتابعة كل جديد، ثم أجب على الاستطلاع أدناه بالضغط على الزر المزين! ✨",
        "poll_question": "🎭 جاهز لبدء المسابقة؟ اضغط على الزر أدناه:",
        "poll_option": "✨🚀 اِبدأ الآن | START NOW 🚀✨"
    },
    "en": {
        "welcome": "👋 Welcome to Sharkas Quiz Bot!\n\nTo start, please join our channel first, then answer the poll below by clicking the decorated button! ✨",
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

def main():
    # جلب التوكن بناءً على التسمية الظاهرة في صورتك BOT_TOKEN
    TOKEN = os.getenv("BOT_TOKEN")
    # جلب المنفذ (Port) المخصص من Render، وإذا لم يوجد نستخدم 8000 كافتراضي
    PORT = int(os.getenv("PORT", 8000))
    # جلب رابط موقعك الخاص على ريندر (ستجده أعلى لوحة تحكم Render وينتهي بـ .onrender.com)
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    
    if not TOKEN:
        logger.error("خطأ: لم يتم العثور على BOT_TOKEN في إعدادات البيئة!")
        return

    bot_persistence = PicklePersistence(filepath="sharkas_data.pickle")
    application = Application.builder().token(TOKEN).persistence(bot_persistence).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Text(["بدء", "start", "البدء", "Start"]), start_command))

    # التشغيل بنظام Webhook المتوافق مع خطة Web Service المجانية في Render
    if RENDER_EXTERNAL_URL:
        logger.info(f"جاري تشغيل البوت بنظام Webhook على المنفذ: {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
    else:
        # في حال كنت تجربه محلياً على جهازك سيعمل تلقائياً بنظام Polling
        logger.info("لم يتم العثور على رابط ريندر الخارجي، جاري التشغيل بنظام Polling محلياً...")
        application.run_polling()

if __name__ == '__main__':
    main()
