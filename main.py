 import os
import logging
import pickle
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
    
    # تحديد اللغة وحفظها في "ذاكرة المستخدم السحابية" التابعة لتليجرام
    lang = "ar" if (user_lang == "ar" or "بدء" in user_text) else "en"
    context.user_data["lang"] = lang  # هنا تم حفظ لغة المستخدم سحابياً!
    
    await update.message.reply_text(TEXTS[lang]["welcome"])
    
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=TEXTS[lang]["poll_question"],
        options=[TEXTS[lang]["poll_option"]],
        is_anonymous=False,
        allows_multiple_answers=False
    )

def main():
    TOKEN = os.getenv("TOKEN", "ضع_توكن_البوت_هنا")
    
    if TOKEN == "ضع_توكن_البوت_هنا":
        logger.error("الرجاء إضافة توكن البوت الصحيح!")
        return

    # تفعيل ميزة الحفظ المستمر السحابي (Persistence)
    # مكتبة python-telegram-bot ستقوم بحفظ أي بيانات نضعها في context.user_data أو context.bot_data تلقائياً
    bot_persistence = PicklePersistence(filepath="sharkas_data.pickle")

    # بناء التطبيق مع ربطه بالذاكرة المستمرة
    application = Application.builder().token(TOKEN).persistence(bot_persistence).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Text(["بدء", "start", "البدء", "Start"]), start_command))

    application.run_polling()

if __name__ == '__main__':
    main()
