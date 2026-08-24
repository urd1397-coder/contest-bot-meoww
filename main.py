import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 🛠️ قراءة توكن البوت والمنفذ السحابي من إعدادات خادم Render (الداشبورد)
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# 👑 تثبيت هويتك الموثقة كمطور ومالك رسمي ونهائي للبوت
OWNER_ID = 79636720007  
OWNER_USERNAME = "@z7xxq" 

# 🚀 إيقاظ محرك البوت للبدء بالاستماع الصاروخي للأوامر
bot = telebot.TeleBot(BOT_TOKEN)

# 💾 القواميس السحابية (الخزنات المؤقتة) لتتبع الفعاليات وخطوات الآدمنز
user_states = {}
channel_contests = {}

# 🪐 دالة استقبال أمر /start بصيغة حيوية ومبهرة تناسب طلبك
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "مياوو😾!/n/n"
        "انت من ايقظني 🙀 ؟\n\n"
        "يا أهلاً يا غالي! أنا **شركس** بوت المسابقات والفعاليات المتكاملة واللطيفة! 🐾🎈\n\n"
        "🚀 مهمتي زرع الحماس في الأجواء ومساعدتك على إشعال التحديات والتصويت، وأيضاً **أستطيع جلب وإحضار أرقام التعريف (الآيديات) الخاصة بالأشخاص والقنوات والجروبات تلقائياً!** 😎🪐\n\n"
        "👉 لطفاً أرسل أمر **/help** لعرض كافة الأكواد وسحري المتاح! 😸✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# 📋 دالة قائمة المساعدة المنسقة بالرموز عند إرسال /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    commands_text = (
        "😸 **إليك قائمة أوامر شركس السحرية المتاحة حالياً:**\n\n"
        "➕ /create ➔ لبدء إنشاء مسابقة جديدة داخل قناتك 🎯\n"
        "🔍 /id_help ➔ لتحصيل وقشط آيدي أي قناة أو شخص تلقائياً بالتوجيه مجاناً 📡\n"
        "🏁 /end ➔ إنهاء المسابقة الحالية واحتساب الأصوات وإعلان الفائزين 🏆\n"
        "❌ /cancel ➔ لإلغاء أي عملية جارية وتصفير الخطوات 🫧"
    )
    bot.reply_to(message, commands_text, parse_mode="Markdown")

# =========================================================================
# 🌐 خادم الويب (Web Server) مخصص لاستقبال نبضات UptimeRobot ليبقى البوت حياً 24 ساعة
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        # إرجاع رمز الاستجابة الناجحة 200 إلى UptimeRobot لتوثيق استقرار الاتصال
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # النص المقروء عند فتح الرابط السحابي
        self.wfile.write(b"Cherkes Bot is Live, Up, and Responding to UptimeRobot!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()

# 🏁 جذع التشغيل الحتمي وإطلاق البوت والخادم بمسارات متوازية لمنع التجمد
if __name__ == '__main__':
    # إطلاق خادم الويب في مسار خلفي صامت لكي لا يتعطل معالج رسائل تليجرام
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري تشغيل شركس السحابي وتفعيل موانئ استقبال نبضات الـ Uptime...")
    # إدخال البوت في وضع المراقبة والاستماع الدائم واللانهائي للأوامر
    bot.infinity_polling()
