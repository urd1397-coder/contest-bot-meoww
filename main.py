import os
import telebot
from telebot 
import types

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# حالات المستخدمين في الخاص
user_states = {}

# =========================================================
# القوائم والأزرار
# =========================================================

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

# التحقق مما إذا كان المستخدم مشرفاً في المجموعة
def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# تنسيق معلومات المستخدم
def format_user(user):
    return (
        f"👤 <b>معلومات الحساب:</b>\n"
        f"🆔 الآيدي: <code>{user.id}</code>\n"
        f"📛 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: @{user.username}" if user.username else f"👤 الاسم: {user.first_name}\n🔗 اليوزر: لا يوجد"
    )

# تنسيق معلومات القناة/المجموعة
def format_chat(chat):
    return (
        f"📢 <b>معلومات القناة / المجموعة:</b>\n"
        f"🆔 الآيدي: <code>{chat.id}</code>\n"
        f"📛 الاسم: {chat.title}\n"
        f"🔗 اليوزر: @{chat.username}" if chat.username else f"📛 الاسم: {chat.title}\n🔗 اليوزر: لا يوجد"
    )

# =========================================================
# الأوامر والرسائل (الخاص)
# =========================================================

@bot.message_handler(commands=["start"], chat_types=["private"])
def start_private(message):
    user_states.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "أهلاً بك في بوت شركس 🐱\nاختر ما تحتاجه من القائمة أدناه:",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == "cmd_id_help":
        user_states[user_id] = "waiting_target"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "أرسل الآن (يوزر نيم)، أو رابط الحساب، أو قم بإعادة توجيه (Forward) أي رسالة أو ملف لجلب معلوماته:",
            chat_id,
            call.message.message_id,
            reply_markup=back_menu()
        )

    elif call.data == "cmd_home":
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "أهلاً بك مجدداً في القائمة الرئيسية:",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )

    elif call.data == "cmd_cancel":
        user_states.pop(user_id, None)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "❌ تم الإلغاء.",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )
    
    elif call.data in ["cmd_create", "cmd_end"]:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "⚙️ هذه الميزة قيد التطوير.",
            chat_id,
            call.message.message_id,
            reply_markup=back_menu()
        )

# استقبال الرسائل في الخاص عند تفعيل زر id_help
@bot.message_handler(chat_types=["private"], func=lambda m: user_states.get(m.from_user.id) == "waiting_target")
def process_private_target(message):
    user_id = message.from_user.id
    
    # 1. التحقق إذا كانت رسالة محولة (Forward)
    if message.forward_from:
        res = format_user(message.forward_from)
    elif message.forward_from_chat:
        res = format_chat(message.forward_from_chat)
    elif hasattr(message, "forward_origin") and message.forward_origin:
        origin = message.forward_origin
        if getattr(origin, "sender_user", None):
            res = format_user(origin.sender_user)
        elif getattr(origin, "chat", None):
            res = format_chat(origin.chat)
        else:
            res = "⚠️ الحساب مخفي أو لا يمكن قراءة تفاصيله بسبب الخصوصية."
    # 2. التحقق إذا أرسل يوزر نيم أو رابط
    elif message.text:
        text = message.text.strip()
        if text.startswith("@") or "t.me/" in text:
            username = text.split("/")[-1].replace("@", "")
            try:
                chat_info = bot.get_chat("@" + username)
                res = format_chat(chat_info) if chat_info.type != "private" else format_user(chat_info)
            except Exception:
                res = "❌ لم يتم العثور على الحساب. تأكد من صحة اليوزر أو الرابط."
        else:
            res = "⚠️ يرجى إرسال يوزر نيم صحيح، رابط، أو إعادة توجيه (Forward) رسالة."
    else:
        res = "⚠️ أرسل رسالة محولة (Forward) أو يوزر نيم صحيح."

    bot.send_message(message.chat.id, res, parse_mode="HTML", reply_markup=back_menu())
    user_states.pop(user_id, None)

# =========================================================
# العمليات داخل المجموعات
# =========================================================

@bot.message_handler(chat_types=["group", "supergroup"], func=lambda m: m.text and "شركس" in m.text)
def group_mentions(message):
    # السيناريو الثالث: إذا تم عمل Reply على شخص وكتب اسم البوت
    if message.reply_to_message:
        replied = message.reply_to_message
        if replied.from_user:
            res = format_user(replied.from_user)
        elif replied.sender_chat:
            res = format_chat(replied.sender_chat)
        else:
            res = "⚠️ لا يمكن جلب المعلومات من هذه الرسالة."
        bot.reply_to(message, res, parse_mode="HTML")
        return

    # إذا تم مناداة البوت فقط (حصرياً للمشرفين)
    if not is_admin(message.chat.id, message.from_user.id):
        return  # تجاهل إذا لم يكن مشرفاً

    bot.reply_to(message, "أهلاً بك! إليك القائمة الرئيسية:", reply_markup=main_menu())

# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
