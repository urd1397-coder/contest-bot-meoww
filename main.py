import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# قاموس لتخزين مسودات المسابقات مؤقتاً في الذاكرة
contest_drafts = {}

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Sharx Bot is active and running!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()

# --- دالة التحقق مما إذا كان المستخدم مشرفاً في القروب ---
def is_user_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# --- [دالة احترافية]: البحث الشامل عبر الإنترنت (للخاص) ---
def fetch_advanced_web_lookup(username):
    clean_un = username.replace("@", "").strip()
    if "t.me/" in clean_un:
        clean_un = clean_un.split("t.me/")[-1].split("/")[0].strip()
    elif "telegram.me/" in clean_un:
        clean_un = clean_un.split("telegram.me/")[-1].split("/")[0].strip()
        
    url = f"https://t.me/{clean_un}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find("meta", property="og:title")
            desc_tag = soup.find("meta", property="og:description")
            
            name = title_tag["content"] if title_tag else clean_un
            bio = desc_tag["content"] if desc_tag else "لايوجد وصف / No bio"
            
            return {
                "found": True,
                "name": name,
                "username": f"@{clean_un}",
                "bio": bio,
                "note": "✨ تم جلب البيانات بنجاح عبر البحث الشامل 🌐"
            }
    except Exception:
        pass
    return {"found": False}

# --- [قائمة القروب المخصصة]: زرين فقط (إنشاء مسابقة وإنهاء مسابقة) ---
def create_group_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end")
    )
    return markup

# --- القائمة الرئيسية الكاملة (للخاص) ---
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث / ID & Search ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة / Close", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع / Quick Selection", callback_data="show_keyboard"),
        types.InlineKeyboardButton("🌐 البحث اليدوي المباشر / Manual Search", callback_data="method_username"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة / Forward Analysis", callback_data="method_forward"),
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية / Home 🏠", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_user = types.KeyboardButton(
        text="👤 اختر مستخدم / Select User", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختر مجموعة أو قناة / Select Chat", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
    return markup

def create_home_return_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية / Home 🏠", callback_data="cmd_home"))
    return markup

def format_user_report(u, chat_id=None):
    uname = f"@{u.username}" if u.username else "لا يوجد يوزر / No Username"
    role_status = "عضو عادي (Member)"
    
    if chat_id:
        try:
            member = bot.get_chat_member(chat_id, u.id)
            if member.status == 'creator':
                role_status = "👑 مالك القروب (Creator)"
            elif member.status == 'administrator':
                role_status = "🛡️ مشرف في القروب (Admin)"
            else:
                role_status = "👤 عضو أساسي في القروب (Member)"
        except Exception:
            role_status = "👤 عضو"

    return (
        f"🛡️ <b>[ تقرير حماية شركس - سجل الحساب ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{u.id}</code>\n"
        f"📛 اسم الحساب: {u.first_name}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 الصلاحية: {role_status}\n"
        f"━━━━━━━━━━━━━━━"
    )

def format_chat_report(c):
    uname = f"@{c.username}" if c.username else "لا يوجد يوزر / No Username"
    chat_type_ar = "قناة عامة" if c.type == "channel" else "مجموعة تفاعلية"
    return (
        f"🛡️ <b>[ تقرير حماية شركس - جهة خارجية ]</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 المعرف الثابت: <code>{c.id}</code>\n"
        f"📛 اسم الجهة: {c.title}\n"
        f"🔗 اليوزر: {uname}\n"
        f"📌 التصنيف: {chat_type_ar}\n"
        f"━━━━━━━━━━━━━━━"
    )

# --- معالج أمر البداية /start (للخاص) ---
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
    bot.send_message(
        message.chat.id,
        "مياو! 🐱✨\n"
        "أهلاً بك في النسخة المطورّة من بوت حماية شركس.\n"
        "اختر ما يناسبك من القائمة أدناه:",
        reply_markup=create_main_menu_markup()
    )

# --- معالج الأزرار الشفافة (Inline Callbacks) ---
@bot.callback_query_handler(func=lambda call: call.data in ["cmd_end", "cmd_id_help", "show_keyboard", "method_username", "method_forward", "cmd_home", "cmd_cancel"])
def handle_inline_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "cmd_end":
        try:
            bot.answer_callback_query(call.id, "هذه الميزة قيد التطوير حالياً 🚧", show_alert=True)
        except Exception:
            pass
    elif call.data == "cmd_id_help":
        bot.edit_message_text(
            "🐾 أهلاً بك في قسم البحث والتحكم المتقدم.\n"
            "Welcome to ID & Advanced Search Section.\n\n"
            "اختر الطريقة / Choose method:",
            chat_id,
            message_id,
            reply_markup=create_id_help_menu_markup()
        )
    elif call.data == "show_keyboard":
        bot.send_message(
            chat_id,
            "👇 استخدم الأزرار الظاهرة أسفل الشاشة للاختيار المباشر:",
            reply_markup=create_dynamic_reply_keyboard()
        )
    elif call.data == "method_username":
        bot.edit_message_text(
            "🎯 <b>[ وضع البحث اليدوي المباشر ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "✍️ أرسل الآن اليوزر (مثل `@username`) أو الرابط لجلب نتائجه فوراً 🚀",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "method_forward":
        bot.edit_message_text(
            "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
            "━━━━━━━━━━━━━━━\n"
            "🐾 قم بإعادة توجيه أي رسالة لاستخراج بيانات صاحبها السرية!",
            chat_id,
            message_id,
            parse_mode="HTML",
            reply_markup=create_home_return_markup()
        )
    elif call.data == "cmd_home":
        bot.edit_message_text(
            "🏠 عودة للقائمة الرئيسية / Main Menu 🐱:",
            chat_id,
            message_id,
            reply_markup=create_main_menu_markup()
        )
    elif call.data == "cmd_cancel":
        bot.edit_message_text(
            "❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.",
            chat_id,
            message_id,
            reply_markup=None
        )

# --- معالج الاختيارات السفلية ---
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    response_text = ""
    target_id = None

    if message.users_shared:
        target_id = message.users_shared.user_ids[0]
    elif message.chat_shared:
        target_id = message.chat_shared.chat_id

    if target_id:
        try:
            chat_info = bot.get_chat(target_id)
            if chat_info.type == "private":
                response_text = format_user_report(chat_info, message.chat.id)
            else:
                response_text = format_chat_report(chat_info)
        except Exception:
            response_text = (
                f"🛡️ <b>[ تقرير حماية شركس - الاختيار المباشر ]</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 المعرف الثابت: <code>{target_id}</code>\n"
                f"✨ تم استلام المعرف بنجاح.\n"
                f"━━━━━━━━━━━━━━━"
            )
    else:
        response_text = "⚠️ لم يتم استلام أي معرف صالح."

    bot.send_message(
        message.chat.id, 
        response_text, 
        parse_mode="HTML", 
        reply_markup=types.ReplyKeyboardRemove()
    )

# --- معالج الدردشة الخاصة (Private) بالكامل ---
@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handle_private_messages(message):
    response_text = ""
    
    if message.forward_from:
        response_text = format_user_report(message.forward_from)
    elif message.forward_from_chat:
        response_text = format_chat_report(message.forward_from_chat)
    elif message.text:
        text = message.text.strip()
        if text.startswith("/"):
            return

        clean_username = text
        if "t.me/" in text:
            clean_username = text.split("t.me/")[-1].split("/")[0].strip()
        elif "telegram.me/" in text:
            clean_username = text.split("telegram.me/")[-1].split("/")[0].strip()
        else:
            clean_username = text.replace("@", "").strip()

        if len(clean_username) >= 3:
            try:
                chat_info = bot.get_chat("@" + clean_username)
                if chat_info.type == "private":
                    response_text = format_user_report(chat_info)
                else:
                    response_text = format_chat_report(chat_info)
            except Exception:
                adv_result = fetch_advanced_web_lookup(clean_username)
                if adv_result["found"]:
                    response_text = (
                        f"🛡️ <b>[ تقرير البحث الشامل - شركس بوت ]</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📛 الاسم: {adv_result['name']}\n"
                        f"🔗 اليوزر: {adv_result['username']}\n"
                        f"📝 الوصف: {adv_result['bio']}\n"
                        f"━━━━━━━━━━━━━━━"
                    )
                else:
                    response_text = f"❌ لم يتم العثور على نتائج مطابقة لـ: <b>{text}</b>"

    if response_text:
        bot.send_message(message.chat.id, response_text, parse_mode="HTML", reply_markup=create_home_return_markup())

# --- معالج المجموعات (القروبات حصراً) ---
@bot.message_handler(chat_types=["group", "supergroup"], content_types=["text"])
def handle_group_messages(message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id

    if "شركس" in text and not message.reply_to_message:
        bot.reply_to(
            message,
            "مياو! 🐱 أهلاً بك. إليك خيارات المسابقات:",
            reply_markup=create_group_menu_markup()
        )
        return

    if message.reply_to_message:
        if "شركس" in text or "آيدي" in text or "id" in text.lower() or "معلومات" in text:
            if not is_user_admin(chat_id, user_id):
                bot.reply_to(message, "⚠️ عذراً، هذه الميزة مخصصة لمشرفي المجموعة فقط!")
                return

            target_user = message.reply_to_message.from_user
            if target_user:
                report = format_user_report(target_user, chat_id)
                bot.reply_to(message, report, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "cmd_create")
def start_contest_flow(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    chat_id = call.message.chat.id
    
    contest_drafts[chat_id] = {}
    
    bot.send_message(
        chat_id,
        "🐾  تبي تسوي مسابقة؟ يا سلام سلم!\n\n"
        "أرسل لي الآن نص إعلان المسابقة مع الشرح والقوانين في رسالة واحدة."
    )
    bot.register_next_step_handler(call.message, step_receive_text)

def step_receive_text(message):
    chat_id = message.chat.id
    
    try: 
        bot.delete_message(chat_id, message.message_id)
    except: 
        pass
    
    contest_drafts[chat_id]['text'] = message.text
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 معرفة الأيدي (id_help)", callback_data="cmd_id_help"))
    
    msg = bot.send_message(
        chat_id,
        "تمام! الحين أرسل لي معرف القناة/القروب أو رابطها.\n"
        "وإذا ما تعرف، ببساطة حوّل (Forward) أي رسالة منها هنا وأنا بتكفل بالباقي.\n\n"
        "💡 (يمكنك الاستعانة بزر معرفة الأيدي أدناه عند الحاجة):",
        reply_markup=markup
    )
    
    bot.register_next_step_handler(msg, step_receive_channel_or_group)

def step_receive_channel_or_group(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try: 
        bot.delete_message(chat_id, message.message_id)
    except: 
        pass
    
    target_identifier = None
    
    if message.forward_from_chat:
        target_identifier = message.forward_from_chat.id
    else:
        target_identifier = message.text.strip()
        
    contest_drafts[chat_id]['target_chat'] = target_identifier

    if not is_user_admin(target_identifier, user_id):
        bot.send_message(
            chat_id, 
            "❌ عذراً، يبدو أنك لست مشرفاً (Admin) في هذه القناة أو المجموعة! لا يمكنني إتمام إنشاء المسابقة."
        )
        contest_drafts.pop(chat_id, None)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("نعم ✅", callback_data="reg_yes"),
        types.InlineKeyboardButton("لا ❌", callback_data="reg_no")
    )
    bot.send_message(
        chat_id, 
        "✅ تم التحقق من صلاحيات الإشراف بنجاح!\n\n"
        "هل تريد إرفاق زر للتسجيل بالمسابقة؟", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["reg_yes", "reg_no"])
def step_reg_decision(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    chat_id = call.message.chat.id
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    if call.data == "reg_yes":
        contest_drafts[chat_id]['has_reg_btn'] = True
        msg = bot.send_message(chat_id, "وش حاب يكون مكتوب على الزر؟ (مثال: اشترك الآن 🐾)")
        bot.register_next_step_handler(msg, step_save_reg_btn_text)
    else:
        contest_drafts[chat_id]['has_reg_btn'] = False
        contest_drafts[chat_id]['reg_btn_text'] = None
        ask_prize_type_flow(chat_id)

def step_save_reg_btn_text(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    contest_drafts[chat_id]['reg_btn_text'] = message.text
    ask_prize_type_flow(chat_id)

def ask_prize_type_flow(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("صورة 🖼️", callback_data="prize_img"),
        types.InlineKeyboardButton("رابط مقتنى 💎", callback_data="prize_col"),
        types.InlineKeyboardButton("تخطي ➡️", callback_data="prize_skip")
    )
    bot.send_message(chat_id, "هل تريد إرفاق صورة أو رابط جائزة/مقتنى تيليجرام مع النشر؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["prize_img", "prize_col", "prize_skip"])
def step_prize_choice(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    chat_id = call.message.chat.id
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    if call.data == "prize_img":
        contest_drafts[chat_id]['prize_type'] = 'image'
        msg = bot.send_message(chat_id, "أرسل لي صورة الجائزة الآن 📸")
        bot.register_next_step_handler(msg, step_save_prize_media)
    elif call.data == "prize_col":
        contest_drafts[chat_id]['prize_type'] = 'collectible'
        msg = bot.send_message(chat_id, "أرسل رابط المقتنى (مثل رابط هدية أو Fragment) 🔗\n(ملاحظة: سيتم إرفاقه كنص آمن بدون فتحه)")
        bot.register_next_step_handler(msg, step_save_prize_media)
    else:
        contest_drafts[chat_id]['prize_type'] = None
        contest_drafts[chat_id]['prize_value'] = None
        ask_entry_message_flow(chat_id)

def step_save_prize_media(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    if message.photo:
        contest_drafts[chat_id]['prize_value'] = message.photo[-1].file_id
    else:
        contest_drafts[chat_id]['prize_value'] = message.text.strip()
        
    ask_entry_message_flow(chat_id)

def ask_entry_message_flow(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("نعم ✅", callback_data="entry_yes"),
        types.InlineKeyboardButton("لا ❌", callback_data="entry_no")
    )
    bot.send_message(chat_id, "هل تريد إرسال رسالة خاصة في القناة أو المجموعة كلما دخل أحد المسابقة؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["entry_yes", "entry_no"])
def step_entry_decision(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    chat_id = call.message.chat.id
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    if call.data == "entry_yes":
        contest_drafts[chat_id]['has_entry_msg'] = True
        msg = bot.send_message(chat_id, "أرسل لي نص رسالة الدخول التي ستظهر عند تفاعل المشارك:")
        bot.register_next_step_handler(msg, step_save_entry_text)
    else:
        contest_drafts[chat_id]['has_entry_msg'] = False
        contest_drafts[chat_id]['entry_msg_text'] = None
        ask_username_inclusion_flow(chat_id)

def step_save_entry_text(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    contest_drafts[chat_id]['entry_msg_text'] = message.text.strip()
    ask_username_inclusion_flow(chat_id)

def ask_username_inclusion_flow(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("نعم ✅", callback_data="uname_yes"),
        types.InlineKeyboardButton("لا ❌", callback_data="uname_no")
    )
    bot.send_message(chat_id, "هل تريد تضمين معرف المشارك (Username) عند تسجيل دخوله؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["uname_yes", "uname_no"])
def step_username_decision(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    chat_id = call.message.chat.id
    try: bot.delete_message(chat_id, call.message.message_id)
    except: pass
    
    contest_drafts[chat_id]['include_username'] = (call.data == "uname_yes")
    publish_contest(chat_id)

def publish_contest(chat_id):
    draft = contest_drafts.get(chat_id)
    if not draft:
        bot.send_message(chat_id, "❌ حدث خطأ، انتهت مسودة المسابقة. حاول مرة أخرى.")
        return
        
    target_chat = draft['target_chat']
    text = draft['text']
    
    markup = types.InlineKeyboardMarkup()
    if draft.get('has_reg_btn') and draft.get('reg_btn_text'):
        markup.add(types.InlineKeyboardButton(draft['reg_btn_text'], callback_data="contest_join_action"))
        
    try:
        if draft.get('prize_type') == 'image' and draft.get('prize_value'):
            bot.send_photo(target_chat, draft['prize_value'], caption=text, reply_markup=markup)
        else:
            final_text = text
            if draft.get('prize_type') == 'collectible' and draft.get('prize_value'):
                final_text += f"\n\n💎 الجائزة/المقتنى: {draft['prize_value']}"
            bot.send_message(target_chat, final_text, reply_markup=markup)
            
        bot.send_message(chat_id, "🎉 يا سلام سلم! تم نشر المسابقة بنجاح في القناة/المجموعة المطلوبة بطابع قططي نظيف وآمن!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء النشر: تأكد أن البوت مشرف في القناة/المجموعة.\nالتفاصيل: {e}")
    
    clear_contest_draft(chat_id)

def clear_contest_draft(chat_id):
    if chat_id in contest_drafts:
        contest_drafts.pop(chat_id, None)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
    
    time.sleep(3)
    try:
        bot.remove_webhook()
        print("Old webhook removed successfully.")
    except Exception as e:
        print(f"Error removing webhook: {e}")

    while True:
        try:
            print("Starting bot polling safely...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
