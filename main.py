import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PicklePersistence

# إعدادات تسجيل الأخطاء لرؤيتها على منصة Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# نصوص الترحيب باللغتين العربية والإنجليزية
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

# دالة الترحيب والبدء عند إرسال /start أو كلمة بدء
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower() if update.message.text else ""
    user_lang = update.effective_user.language_code
    
    # تحديد اللغة وحفظها في ذاكرة تليجرام السحابية للمستخدم
    lang = "ar" if (user_lang == "ar" or "بدء" in user_text) else "en"
    context.user_data["lang"] = lang
    
    # 1. إرسال رسالة الترحيب
    await update.message.reply_text(TEXTS[lang]["welcome"])
    
    # 2. إرسال الاستطلاع المنبثق المزين
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=TEXTS[lang]["poll_question"],
        options=[TEXTS[lang]["poll_option"]],
        is_anonymous=False,
        allows_multiple_answers=False
    )

def main():
    # جلب التوكن من إعدادات البيئة (Environment Variables) في Render باسم TOKEN
    TOKEN = os.getenv("TOKEN", "ضع_توكن_البوت_هنا")
    
    if TOKEN == "ضع_توكن_البوت_هنا":
        logger.error("الرجاء إضافة توكن البوت الصحيح في إعدادات ريندر!")
        return

    # تفعيل الذاكرة السحابية المستمرة لتخزين بيانات المسابقات واللغات تلقائياً
    bot_persistence = PicklePersistence(filepath="sharkas_data.pickle")

    # بناء وتجهيز تطبيق البوت
    application = Application.builder().token(TOKEN).persistence(bot_persistence).build()

    # إضافة الأوامر والمستقبلات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Text(["بدء", "start", "البدء", "Start"]), start_command))

    # تشغيل البوت بنظام استقبال التحديثات المستمر (Polling)
    application.run_polling()

if __name__ == '__main__':
    main()
