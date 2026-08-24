import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 🛠️ قراءة توكن البوت والمنفذ السحابي من إعدادات خادم Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# 👑 تثبيت هويتك الموثقة كمطور ومالك رسمي ونهائي للبوت
OWNER_ID = 79636720007  
OWNER_USERNAME = "@z7xxq" 

bot = telebot.TeleBot(BOT_TOKEN)

# قواميس الذاكرة المؤقتة السحابية لشركس
user_states = {}
channel_contests = {}  # {channel_id: {msg_id: {user_id: {"mention": x, "votes": 0}}}}

# 🪐 دالة استقبال أمر /start بصيغة حيوية ومبهرة
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "انت من ايقظني 🙀 ؟\n\n"
        "يا أهلاً يا غالي! أنا **شركس** بوت المسابقات والفعاليات المتكاملة واللطيفة! 🐾🎈\n\n"
        "🚀 مهمتي زرع الحماس في الأجواء ومساعدتك على إشعال التحديات والتصويت، وأيضاً <b>أستطيع جلب وإحضار أرقام التعريف (الآيديات) الخاصة بالأشخاص والقنوات والجروبات تلقائياً!</b> 😎🪐\n\n"
        "👉 لطفاً أرسل أمر <b>/help</b> لعرض كافة الأكواد وسحري المتاح! 😸✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")


        "user_id": user_id,
        "mention": user_mention,
        "votes": 0
    }
    bot.answer_callback_query(call.id, text="🎉 تم تسجيل انضمامك بنجاح وبث رسالة تصويتك الفردية في القناة! انطلق! 🚀", show_alert=False)
