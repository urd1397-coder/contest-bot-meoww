import os
import time
import telebot
from telebot import types

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
user_states = {}

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 معرفة الآيدي (id_help)", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
    )
    return markup

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="cmd_home"))
    return markup

def is_admin(chat_id, user_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['creator', 'administrator']
    except:
        return False

def format_user(u):
    uname = f"@{u.username}" if u.username else "لا يوجد"
    return f"👤 <b>معلومات الحساب:</b>\n🆔 الآيدي: <code>{u.id}</code>\n📛 الاسم: {u.first_name}\n🔗 اليوزر: {uname}"

def format_chat(c):
    uname = f"@{c.username}" if c.username else "لا يوجد"
    return f"📢 <b>معلومات القناة / المجموعة:</b>\n🆔 الآيدي: <code>{c.id}</code>\n📛 الاسم: {c.title}\n🔗 اليوزر: {uname}"

@bot.message_handler(commands=["start"], chat_types=["private"])
def start_private(m):
    user_states.pop(m.from_user.id, None)
    bot.send_message(m.chat.id, "أهلاً بك في بوت شركس 🐱\nاختر ما تحتاجه:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id
    if call.data == "cmd_id_help":
        user_states[user_id] = "waiting_target"
        bot.answer_callback_query(call.id)
        bot.edit_message_text("أرسل يوزر نيم، رابط، أو قم بإعادة توجيه رسالة:", chat_id, call.message.message_id, reply_markup=back_menu())
    elif call.data == "cmd_home":
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)
        bot.edit_message_text("القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=main_menu())
    elif call.data == "cmd_cancel":
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)
        bot.edit_message_text("❌ تم الإلغاء.", chat_id, call.message.message_id, reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id)
        bot.edit_message_text("⚙️ قيد التطوير.", chat_id, call.message.message_id, reply_markup=back_menu())

@bot.message_handler(chat_types=["private"], func=lambda m: user_states.get(m.from_user.id) == "waiting_target")
def process_target(m):
    if m.forward_from: 
        res = format_user(m.forward_from)
    elif m.forward_from_chat: 
        res = format_chat(m.forward_from_chat)
    elif m.text and (m.text.startswith("@") or "t.me/" in m.text):
        try:
            c = bot.get_chat("@" + m.text.split("/")[-1].replace("@", ""))
            res = format_chat(c) if c.type != "private" else format_user(c)
        except: 
            res = "❌ لم يتم العثور على الحساب."
    else: 
        res = "⚠️ يرجى إرسال يوزر صحيح أو رسالة محولة (Forward)."
    
    # إرسال النتيجة مع زر العودة للرئيسية إجباريًا مع كل رد
    bot.send_message(m.chat.id, res, parse_mode="HTML", reply_markup=back_menu())
    user_states.pop(m.from_user.id, None)

@bot.message_handler(chat_types=["group", "supergroup"], func=lambda m: m.text and "شركس" in m.text)
def group_handler(m):
    if m.reply_to_message:
        r = m.reply_to_message
        res = format_user(r.from_user) if r.from_user else (format_chat(r.sender_chat) if r.sender_chat else "⚠️ لا يمكن جلب المعلومات.")
        bot.reply_to(m, res, parse_mode="HTML")
        return
    if is_admin(m.chat.id, m.from_user.id):
        bot.reply_to(m, "القائمة الرئيسية:", reply_markup=main_menu())

if __name__ == "__main__":
    print("Bot is running...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
