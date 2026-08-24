import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# قراءة المتغيرات الإعدادية المحمية من ريندر
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # معرف حسابك الشخصي لاستلام أرباح النجوم
PORT = int(os.getenv("PORT", 8000))

bot = telebot.TeleBot(BOT_TOKEN)

# قواميس تتبع البيانات
user_states = {}
channel_contests = {}  # لحفظ أصوات المشتركين {channel_id: {msg_id: {user_id: {"name": x, "votes": 0}}}}
paid_users = set()     # المستخدمين الذين اشتروا الخدمة

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    # رسالة الترحيب والاستيقاظ المزدوجة لشركس
    if user_id not in user_states:
        user_states[user_id] = "awakened"
        welcome_text = "انت من ايقظني 🙀 ؟\n\nاهلا بك انا شركس هيهي 😸\nبوت لمسابقات وفعاليات وكثير أيضًا 🎯✨️♠️\n\nاضغط على /start مرة ثانية لترى الكوماندز المتاحة! ✨"
        bot.reply_to(message, welcome_text)
    else:
        commands_text = (
            "😸 **مرحباً بك مجدداً! إليك أوامر شركس لإدارة قنواتك:**\n\n"
            "💳 /buy ➔ شراء رخصة استخدام البوت لقناتك بـ 50 نجمة ⭐️\n"
            "➕ /create ➔ لبدء إنشاء مسابقة جديدة (للآدمنز فقط) 🎯\n"
            "🏁 /end ➔ إنهاء المسابقة الحالية واحتساب الأصوات وإعلان الفائزين 🏆\n"
            "❌ /cancel ➔ لإلغاء أي عملية جارية 🫧"
        )
        bot.reply_to(message, commands_text, parse_mode="Markdown")

# 💳 نظام الدفع والاشتراك بنجوم تليجرام
@bot.message_handler(commands=['buy'])
def cmd_buy(message):
    user_id = message.from_user.id
    if user_id in paid_users or user_id == OWNER_ID:
        bot.reply_to(message, "😸 أنت تملك رخصة تفعيل البوت بالفعل!")
        return

    prices = [LabeledPrice(label="رخصة تفعيل شركس للمسابقات", amount=50)]
    bot.send_invoice(
        chat_id=message.chat.id,
        title="✨ تفعيل بوت شركس ✨",
        description="اشترِ رخصة تشغيل البوت في قناتك للأبد بمبلغ زهيد ودع الحماس يبدأ! 😸🐾",
        provider_token="",
        currency="XTR",  # كود نجوم تليجرام
        prices=prices,
        start_parameter="activate-cherkes",
        payload="cherkes_license"
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    paid_users.add(user_id)
    bot.reply_to(message, "🎉 كفووو! تم الدفع بنجاح وتحويل 50 نجمة لحساب المطور. يمكنك الآن استخدام شركس بحرية كاملة في قناتك! 🥳🐾")

# ➕ أمر بدء مسابقة جديدة للآدمنز فقط
@bot.message_handler(commands=['create'])
def start_contest(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in paid_users:
        bot.reply_to(message, "⚠️ عذراً يا غالي، يجب تفعيل رخصة البوت أولاً عبر أمر /buy بـ 50 نجمة! 💳")
        return
        
    user_states[user_id] = {"step": "get_channel"}
    bot.reply_to(message, "📢 أرسل لي معرف قناتك أولاً (مثال: `@my_channel`) لنتأكد من صلاحياتك:")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "get_channel")
def check_admin_and_channel(message):
    user_id = message.from_user.id
    channel_user = message.text.strip()
    
    try:
        member = bot.get_chat_member(channel_user, user_id)
        if member.status in ['creator', 'administrator']:
            user_states[user_id] = {"step": "contest_text", "channel": channel_user}
            bot.reply_to(message, f"✅ تم التحقق بنجاح! أنت آدمن في {channel_user}.\n\n📝 أرسل لي الآن نص وعنوان المسابقة الفخم:")
        else:
            bot.reply_to(message, "❌ عذراً! الكود كشف أنك لست مسؤولاً (Admin) في هذه القناة.")
            user_states.pop(user_id, None)
    except Exception:
        bot.reply_to(message, "⚠️ تأكد من كتابة معرف القناة بشكل صحيح، وأن البوت مضاف فيها كمسؤول (Admin) أولاً!")
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "contest_text")
def get_contest_text(message):
    user_id = message.from_user.id
    state = user_states[user_id]
    channel_id = state["channel"]
    contest_text = message.text
    
    channel_contests[channel_id] = {}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎯 إشتراك 🎯", callback_data=f"join_{channel_id}"))
    
    bot.send_message(chat_id=channel_id, text=f"🏆 **مسابقة جديدة من شركس!** 🏆\n\n{contest_text}", reply_markup=markup, parse_mode="Markdown")
    bot.reply_to(message, f"🚀 طييرااان! تم نشر المسابقة بنجاح في القناة {channel_id}!")
    user_states.pop(user_id, None)

# التعامل مع زر الاشتراك المانع للتكرار في نفس القناة
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def handle_join(call):
    channel_id = call.data.replace("join_", "")
    user_id = call.from_user.id
    username = call.from_user.username
    first_name = call.from_user.first_name
    
    if channel_id not in channel_contests:
        channel_contests[channel_id] = {}
        
    if any(user_id in msg_data for msg_data in channel_contests[channel_id].values()):
        bot.answer_callback_query(call.id, text="عذراً، أنت مسجل في المسابقة بالفعل! 😸🐾", show_alert=True)
        return
        
    registered_users_count = len(channel_contests[channel_id]) + 1
    user_mention = f"@{username}" if username else first_name
    
    vote_msg = bot.send_message(
        chat_id=channel_id,
        text=f"🔥 المتسابق رقم {registered_users_count}: {user_mention} انضم للمسابقة!\n\nصوتوا له بالـ Reactions أسفل هذه الرسالة! 👇\n⭐ = صوتان | أي تفاعل آخر = صوت واحد"
    )
    
    channel_contests[channel_id][vote_msg.message_id] = {
        "user_id": user_id,
        "mention": user_mention,
        "votes": 0
    }
    bot.answer_callback_query(call.id, text="😸 تم تسجيل انضمامك بنجاح وبدء التصويت علناً!", show_alert=False)

# تتبع التفاعلات وحساب الأصوات آلياً
@bot.message_reaction_handler()
def handle_reaction(message_reaction):
    chat_id = str(message_reaction.chat.id)
    message_id = message_reaction.message_id
    
    for ch_id, msgs in channel_contests.items():
        if ch_id in [str(message_reaction.chat.id), f"@{message_reaction.chat.username}"]:
            if message_id in msgs:
                total_votes = 0
                for react in message_reaction.new_reaction:
                    if react.type == 'emoji':
                        if react.emoji == '⭐':
                            total_votes += 2
                        else:
                            total_votes += 1
                channel_contests[ch_id][message_id]["votes"] = total_votes

# 🏁 أمر إنهاء المسابقة وإعلان الفائزين بصور بروفايلاتهم
@bot.message_handler(commands=['end'])
def end_contest(message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "end_get_channel"}
    bot.reply_to(message, "🏁 أرسل لي معرف القناة المراد إنهاء مسابقتها وحساب نتائجها:")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "end_get_channel")
def end_get_winners_count(message):
    user_id = message.from_user.id
    channel_id = message.text.strip()
    
    if channel_id not in channel_contests or not channel_contests[channel_id]:
        bot.reply_to(message, "❌ لا توجد مسابقة نشطة مسجلة في ذاكرة شركس لهذه القناة!")
        user_states.pop(user_id, None)
        return
        
    user_states[user_id] = {"step": "get_prizes", "channel": channel_id}
    bot.reply_to(message, "🔢 كم عدد المراكز الفائزة المطلوبة؟ (مثال اكتب: 3 واضغط إرسال):")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "get_prizes")
def end_calculate_and_announce(message):
    user_id = message.from_user.id
    state = user_states[user_id]
    channel_id = state["channel"]
    
    try:
        winners_count = int(message.text)
        contest_data = channel_contests[channel_id]
        
        sorted_competitors = sorted(contest_data.values(), key=lambda x: x["votes"], reverse=True)
        actual_winners = sorted_competitors[:winners_count]
        
        if not actual_winners:
            bot.reply_to(message, "🛑 لم يقم أحد بالاشتراك في المسابقة ليتم حساب النتائج!")
            user_states.pop(user_id, None)
            return
            
        top_winner = actual_winners[0]
        medals = ["🥇 الأول", "🥈 الثاني", "🥉 الثالث"]
        
        result_text = f"🥳 **شركس يعلن نتائج المسابقة الرسمية لـ {channel_id}** 🥳\n\n"
        for i, winner in enumerate(actual_winners):
            medal = medals[i] if i < 3 else f"🔹 المركز {i+1}"
            result_text += f"{medal}: {winner['mention']} بـ ({winner['votes']} صوت) ✨\n"
            
        result_text += "\n🎁 **تهانينا الحارة لجميع الأبطال الفائزين!** 🎉\n👉 *يُرجى من الفائزين التواصل مع الإدارة لاستلام الجوائز الفخمة فوراً!* 🐾"
        
        try:
            photos = bot.get_user_profile_photos(top_winner["user_id"], limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][0].file_id
                bot.send_photo(chat_id=channel_id, photo=file_id, caption=result_text, parse_mode="Markdown")
            else:
                bot.send_message(chat_id=channel_id, text=result_text, parse_mode="Markdown")
        except Exception:
            bot.send_message(chat_id=channel_id, text=result_text, parse_mode="Markdown")
            
        bot.reply_to(message, "🏆 تم إنهاء المسابقة وحساب الأصوات التفاعلية وضخ لوحة الصدارة بنجاح في القناة!")
        channel_contests.pop(channel_id, None)
        user_states.pop(user_id, None)
        
    except ValueError:
        bot.reply_to(message, "⚠️ لطفاً أرسل رقماً صحيحاً لعدد الفائزين:")

# خادم وهمي لإبقاء البوت مستيقظاً ومستقراً مجاناً في ريندر
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Cherkes Commercial Bot is Live!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري إقلاع شركس التجاري السحابي المطور...")
    bot.infinity_polling()
