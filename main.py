import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# قراءة المتغيرات الإعدادية المحمية من ريندر
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 8000))

bot = telebot.TeleBot(BOT_TOKEN)

# قواميس تتبع الحالات وقائمة المسجلين بالمسابقة
user_states = {}
registered_users = set()  # خزانة سرية لحفظ المتسابقين ومنع التكرار

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    # المرة الأولى: رسالة الاستيقاظ الكيوت
    if user_id not in user_states:
        user_states[user_id] = "awakened"
        welcome_text = "انت من ايقظني 🙀 ؟\n\nاهلا بك انا شركس هيهي 😸\nبوت لمسابقات وفعاليات وكثير أيضًا 🎯✨️♠️\n\nاضغط على /start مرة ثانية لترى قدراتي وسحري! ✨"
        bot.reply_to(message, welcome_text)
    
    # المرة الثانية: عرض الكوماندز والقدرات
    else:
        commands_text = (
            "😸 **مرحباً بك مجدداً! إليك قدرات شركس السحرية:**\n\n"
            "➕ /create ➔ لصنع مسابقة جديدة وإرسالها إلى القناة 🎯\n"
            "❌ /cancel ➔ لإلغاء عملية إنشاء المسابقة الحالية 🫧"
        )
        bot.reply_to(message, commands_text, parse_mode="Markdown")

@bot.message_handler(commands=['create'])
def start_contest(message):
    user_id = message.from_user.id
    user_states[f"contest_{user_id}"] = {"step": "text"}
    bot.reply_to(message, "📝 أرسل لي الآن نص المسابقة الفخم لإنشائه في القناة:")

@bot.message_handler(func=lambda msg: user_states.get(f"contest_{msg.from_user.id}", {}).get("step") == "text")
def get_contest_text(message):
    user_id = message.from_user.id
    contest_text = message.text
    
    # تنظيف قائمة المسجلين القديمة عند بدء مسابقة جديدة تماماً
    registered_users.clear()
    
    # إنشاء زر الاشتراك التفاعلي تحت رسالة المسابقة في القناة
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎯 إشتراك 🎯", callback_data="join_contest"))
    
    # إرسال المسابقة إلى القناة
    bot.send_message(chat_id=CHANNEL_ID, text=f"🏆 **مسابقة جديدة من شركس!** 🏆\n\n{contest_text}", reply_markup=markup, parse_mode="Markdown")
    
    bot.reply_to(message, "🚀 طييرااان! تم نشر المسابقة بنجاح في قناتك مع زر الاشتراك الحصري! 🎉")
    user_states.pop(f"contest_{user_id}")

# التعامل مع ضغطة زر "اشتراك" والحماية من التكرار
@bot.callback_query_handler(func=lambda call: call.data == "join_contest")
def handle_join(call):
    user_id = call.from_user.id
    username = call.from_user.username
    first_name = call.from_user.first_name
    
    # 🚫 خطوة الحماية: إذا كان المستخدم مسجلاً مسبقاً في القائمة
    if user_id in registered_users:
        bot.answer_callback_query(call.id, text="عذراً، أنت مسجل في المسابقة بالفعل! 😸🐾", show_alert=True)
        return
        
    # 📝 إذا كان أول مرة يضغط: نقوم بإضافته فوراً للقائمة لمنعه مستقبلاً
    registered_users.add(user_id)
    
    # تجهيز صيغة المناداة باليوزر نيم أو الاسم الأول
    user_mention = f"@{username}" if username else first_name
    
    # إرسال الرسالة التفاعلية مباشرة إلى نفس القناة ليصوت عليها المتابعون
    bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"🔥 {user_mention} انضم للمسابقة! هل يستحق الفوز؟ 🤔✨\n\nصوتوا له بالـ Reactions أسفل هذه الرسالة! 👇\n⭐ = صوتان\nأي تفاعل آخر = صوت واحد"
    )
    
    # إشعار منبثق لطيف يؤكد نجاح أول تسجيل
    bot.answer_callback_query(call.id, text="😸 تم تسجيل انضمامك بنجاح ونشره للتصويت!", show_alert=False)

# تتبع ومراقبة الريأكشنز في القناة لحساب الأصوات تلقائياً لشركس
@bot.message_reaction_handler()
def handle_reaction(message_reaction):
    chat_id = message_reaction.chat.id
    message_id = message_reaction.message_id
    
    if str(chat_id) == str(CHANNEL_ID):
        total_votes = 0
        for react in message_reaction.new_reaction:
            if react.type == 'emoji':
                if react.emoji == '⭐':
                    total_votes += 2
                else:
                    total_votes += 1
                    
        print(f"📊 الرسالة رقم {message_id} حصلت حالياً على مجموع أصوات: {total_votes}")

# خادم وهمي لإبقاء البوت مستيقظاً ومستقراً مجاناً في ريندر
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Cherkes Anti-Duplicate Bot is Live!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري تشغيل شركس المحمي من التكرار سحابياً...")
    bot.infinity_polling()
