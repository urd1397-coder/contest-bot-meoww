import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# قراءة المتغيرات الإعدادية المحمية من ريندر
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_ID = os.getenv("GROUP_ID")  # معرف القروب الجديد الذي سنضيفه
PORT = int(os.getenv("PORT", 8000))

bot = telebot.TeleBot(BOT_TOKEN)

# قاموس لتتبع حالة المستخدمين (الترحيب المزدوج)
user_states = {}

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
    bot.reply_to(message, "📝 أرسل لي الآن نص المسابقة الفخم والكيوت:")

@bot.message_handler(func=lambda msg: user_states.get(f"contest_{msg.from_user.id}", {}).get("step") == "text")
def get_contest_text(message):
    user_id = message.from_user.id
    contest_text = message.text
    
    # إنشاء زر الاشتراك التفاعلي تحت رسالة المسابقة في القناة
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎯 إشتراك 🎯", callback_data="join_contest"))
    
    # إرسال المسابقة إلى القناة
    bot.send_message(chat_id=CHANNEL_ID, text=f"🏆 **مسابقة جديدة من شركس!** 🏆\n\n{contest_text}", reply_markup=markup, parse_mode="Markdown")
    
    bot.reply_to(message, "🚀 طييرااان! تم نشر المسابقة بنجاح في القناة مع زر الاشتراك! 🎉")
    user_states.pop(f"contest_{user_id}")

# التعامل مع ضغطة زر "اشتراك" في القناة
@bot.callback_query_handler(func=lambda call: call.data == "join_contest")
def handle_join(call):
    username = call.from_user.username
    first_name = call.from_user.first_name
    
    # تجهيز صيغة المناداة باليوزر نيم أو الاسم الأول إذا لم يكن لديه يوزر
    user_mention = f"@{username}" if username else first_name
    
    # إرسال الرسالة التفاعلية مباشرة إلى القروب
    group_msg = bot.send_message(
        chat_id=GROUP_ID,
        text=f"🔥 {user_mention} انضم! هل يستحق؟\n\nصوتوا له الآن بالـ Reactions! 👇\n⭐ = صوتان\nأي تفاعل آخر = صوت واحد"
    )
    
    # إشعار سريع للمستخدم الذي ضغط على الزر
    bot.answer_callback_query(call.id, text="😸 تم تسجيل انضمامك وإرساله للقروب للتصويت!", show_alert=False)

# تتبع ومراقبة الريأكشنز في القروب لحساب الأصوات تلقائياً
@bot.message_reaction_handler()
def handle_reaction(message_reaction):
    chat_id = message_reaction.chat.id
    message_id = message_reaction.message_id
    
    # نتأكد أن التفاعل يحدث داخل القروب المخصص
    if str(chat_id) == str(GROUP_ID):
        total_votes = 0
        
        # حساب الأصوات بناءً على نوع الريأكشن
        for react in message_reaction.new_reaction:
            # إذا كان الريأكشن رمز تعبيري (Emoji)
            if react.type == 'emoji':
                if react.emoji == '⭐':
                    total_votes += 2  # النجمة تساوي صوتين
                else:
                    total_votes += 1  # أي ريأكشن آخر يساوي صوتاً واحداً
                    
        # تحديث النتيجة أو طباعتها في سجل السيرفر (ويمكنك تطويرها لإرسال رسالة بالنتيجة عند انتهاء الوقت)
        print(f"📊 رسالة المسابقة رقم {message_id} حصلت حالياً على مجموع أصوات: {total_votes}")

# خادم وهمي لمنع توقف السيرفر المجاني (Timed Out)
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Cherkes Bot is Live and Coding!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري تشغيل شركس الكيوت سحابياً...")
    bot.infinity_polling()
