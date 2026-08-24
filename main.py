import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 🛠️ قراءة توكن البوت والمنفذ السحابي من بيئة خادم Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# 👑 تثبيت هويتك كمطور ومالك رسمي ونهائي للبوت لمنع أي تضارب
OWNER_ID = 79636720007  
OWNER_USERNAME = "@z7xxq" 

# 🚀 إنشاء كائن البوت للبدء بالاستماع للأوامر
bot = telebot.TeleBot(BOT_TOKEN)

# 💾 القواميس السحابية لتخزين خطوات المستخدمين، بيانات المسابقات، والمشتركين
user_states = {}
channel_contests = {}  # لحفظ أصوات المسابقات {channel_id: {msg_id: {user_id: {"name": x, "votes": 0}}}}
paid_users = set()     # المستخدمين الذين اشتروا الخدمة بـ 50 نجمة

# 🪐 استقبال حماسي وحيوي عند إرسال /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "انت من ايقظني 🙀 ؟\n\n"
        "يا أهلاً يا غالي! أنا **شركس** بوت المسابقات والفعاليات المتكاملة واللطيفة! 🐾🎈\n\n"
        "🚀 مهمتي زرع الحماس في الأجواء ومساعدتك على إشعال التحديات والتصويت، وأيضاً **أستطيع جلب وإحضار أرقام التعريف (الآيديات) الخاصة بالأشخاص والقنوات والجروبات تلقائياً!** 😎🪐\n\n"
        "👉 لطفاً أرسل أمر **/help** لعرض كافة الأكواد وسحري المتاح! 😸✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 📋 قائمة المساعدة لعرض الأكواد المتاحة للمستخدم عند إرسال /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    commands_text = (
        "😸 **إليك قائمة أوامر شركس السحرية المتاحة حالياً:**\n\n"
        "💳 /buy ➔ شراء رخصة استخدام البوت لقناتك بـ 50 نجمة ⭐️\n"
        "🎫 /redeem ➔ لإدخال كود ترويجي أو تجريبي مجاني 🎁\n"
        "➕ /create ➔ لبدء إنشاء مسابقة جديدة داخل قناتك 🎯\n"
        "🔍 /id_help ➔ لتحصيل وقشط آيدي أي قناة أو شخص تلقائياً بالتوجيه مجاناً 📡\n"
        "🏁 /end ➔ إنهاء المسابقة الحالية واحتساب الأصوات وإعلان الفائزين 🏆\n"
        "❌ /cancel ➔ لإلغاء أي عملية جارية وتصفير الخطوات 🫧"
    )
    bot.reply_to(message, commands_text, parse_mode="Markdown")
