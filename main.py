# ==========================================
# **بوتي شركس - نظام المسابقات والتصويت الداخلي الذكي**
# ==========================================
import os
import time
import threading
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler
from hashids import Hashids
import base64

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# إعداد مكتبة Hashids لهاش قصير وفريد لتشفير الرسائل المخصصة
hashids = Hashids(salt="sharx_secure_salt_2026", min_length=4)

last_panel_message = {}
contest_creation_state = {}
end_contest_state = {}

# ==========================================
# **خادم الويب للحفاظ على نشاط البوت**
# ==========================================
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


# ==========================================
# **لوحات الأزرار والقوائم الموحدة**
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("🧹 تنظيف شات البوت", callback_data="cmd_clean_chat"),
        types.InlineKeyboardButton("🐾 مطور البوت", callback_data="cmd_developer"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def get_back_and_home_markup(back_callback="cmd_home"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def get_cancel_and_home_markup(back_callback="cmd_home"):
    return get_back_and_home_markup(back_callback)

def update_or_send_panel(chat_id, text, reply_markup, message_id=None):
    if message_id:
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            last_panel_message[chat_id] = message_id
            return
        except Exception:
            pass

    if chat_id in last_panel_message:
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=last_panel_message[chat_id],
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
     
    sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=reply_markup)
    last_panel_message[chat_id] = sent.message_id


# ==========================================
# **أمر البداية (Start) ومناداة البوت**
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
     
    text = (
        "مياو أهلاً بك في عالم شركس! 🐱✨\n"
        "البوت الأنيق والسريع لإدارة مسابقاتك وتصويتك بكل احترافية.\n"
        "اختر ما يناسبك من الخيارات أدناه:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
    last_panel_message[message.chat.id] = sent.message_id


@bot.message_handler(func=lambda message: message.text and "شركس" in message.text)
def handle_bot_mention(message):
    if message.chat.type in ["group", "supergroup"]:
        text = (
        "🐾 *مياو! شركس هنا بخدمتكم في القروب* 🐱✨\n"
        "البوت الجاهز لإدارة مسابقاتكم بحماس وسرعة.\n"
        "اختر ما يناسبك لإدارتها هنا:"
    )
        sent = bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
        last_panel_message[message.chat.id] = sent.message_id


# ==========================================
# **مساعدات لترميز وفك ترميز النصوص المخصصة بالهاش**
# ==========================================
def encode_custom_text(text):
    if not text:
        return "DEFAULT"
    encoded_bytes = base64.urlsafe_b64encode(text.encode("utf-8"))
    return encoded_bytes.decode("utf-8").rstrip("=")

def decode_custom_text(code):
    if not code or code == "DEFAULT":
        return "انضم إلى المسابقة بنجاح! 🔥"
    try:
        padding = '=' * (-len(code) % 4)
        decoded_bytes = base64.urlsafe_b64decode((code + padding).encode("utf-8"))
        return decoded_bytes.decode("utf-8")
    except Exception:
        return "انضم إلى المسابقة بنجاح! 🔥"


# ==========================================
# **معالجة الأزرار التفاعلية (Callbacks)**
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id 
    user_id = call.from_user.id
    data = call.data
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id
     
    if data.startswith("contest_vote_"):
        try:
            # استخراج الهاش والبيانات من زر الـ callback مباشرة وبكل أمان ودون اعتماد على الذاكرة
            payload = data.replace("contest_vote_", "")
            parts = payload.split("_", 1)
            custom_code = parts[0]
            use_mention = True if len(parts) > 1 and parts[1] == "1" else False

            custom_join_msg = decode_custom_text(custom_code)
            
            message_text = call.message.text or call.message.caption or ""
            user_first_name = call.from_user.first_name or "المشارك"
            user_username = call.from_user.username
             
            if user_username:
                user_identity = f"@{user_username}"
            else:
                user_identity = f"[{user_first_name}](tg://user?id={user_id})"

            if user_identity in message_text:
                try:
                    bot.answer_callback_query(call.id, f"⚠️ عذراً يا {user_first_name}\nلقد قمت بالتسجيل مسبقاً ولا يمكنك التكرار! 🚫", show_alert=True)
                except Exception:
                    pass
                return

            lines = message_text.split("\n")
            new_lines = []
            current_count = 0
            participants_line_idx = -1
             
            for i, line in enumerate(lines):
                if "عدد المسجلين:" in line:
                    import re
                    nums = re.findall(r'\d+', line)
                    if nums:
                        current_count = int(nums[0])
                    current_count += 1
                    new_lines.append(f"👥 عدد المسجلين: *{current_count}*")
                elif "📋 قائمة المشاركين:" in line:
                    participants_line_idx = i
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if participants_line_idx != -1:
                old_participants_text = lines[participants_line_idx].replace("📋 قائمة المشاركين:", "").strip()
                if "لا يوجد مشاركين" in old_participants_text or not old_participants_text:
                    updated_participants = f"{user_identity}"
                else:
                    updated_participants = f"{old_participants_text}, {user_identity}"
                 
                new_lines[participants_line_idx] = f"📋 قائمة المشاركين: {updated_participants}"

            updated_full_text = "\n".join(new_lines)

            if call.message.photo:
                bot.edit_message_caption(
                    caption=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=call.message.reply_markup
                )
            else:
                bot.edit_message_text(
                    text=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=call.message.reply_markup
                )

            if use_mention:
                announcement_to_send = f"{user_identity} {custom_join_msg}"
            else:
                announcement_to_send = f"{custom_join_msg}"
             
            try:
                sent_notif = bot.send_message(
                    chat_id, 
                    announcement_to_send, 
                    parse_mode="Markdown"
                )
                try:
                    bot.pin_chat_message(chat_id, sent_notif.message_id)
                except Exception:
                    pass
            except Exception as e:
                print(f"Error sending independent join notification: {e}")

            try:
                bot.answer_callback_query(call.id, f"✅ تم تسجيل مشاركتك بنجاح يا {user_first_name}!", show_alert=True)
            except Exception:
                pass

        except Exception as e:
            print(f"Error handling contest vote: {e}")
        return

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
         
    try:
        if data == "cmd_create":
            contest_creation_state[user_id] = {"step": 1}
            markup = get_cancel_and_home_markup("cmd_home")
            text = (
                "🐾 *[ السؤال 1: تحديد القناة أو القروب ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن *معرف القناة أو القروب المستهدف أو رابطهما*:"
            )
            update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "step_back_q1":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 2
                markup = get_cancel_and_home_markup("cmd_create")
                text = (
                    "🐾 *[ السؤال 2: نص المسابقة أو السؤال ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن *نص اعلان المسابقة أو السؤال*:"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "step_back_q2":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 2
                markup = get_cancel_and_home_markup("cmd_create")
                text = (
                    "🐾 *[ السؤال 2: نص المسابقة أو السؤال ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن *نص اعلان المسابقة أو السؤال*:"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "step_back_q3":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 3
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(types.InlineKeyboardButton("⏩ تخطي هذه الخطوة", callback_data="skip_image"))
                text = (
                    "🐾 *[ السؤال 3: إرفاق صورة مميزة ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود إرفاق صورة في أعلى منشور المسابقة للتميز؟\n"
                    "أرسل الصورة الآن أو اضغط على (تخطي)."
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "step_back_q4":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 4
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(types.InlineKeyboardButton("⏩ تخطي هذه الخطوة", callback_data="skip_comments"))
                text = (
                    "🐾 *[ السؤال 4: خانة التعليقات ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود إضافة خانة أو مساحة تعليقات للمنشور؟\n"
                    "اكتب تفاصيلها أو اضغط على (تخطي)."
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "skip_image":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_media"] = None
                contest_creation_state[user_id]["step"] = 4
                markup = get_cancel_and_home_markup("step_back_q3")
                markup.row(types.InlineKeyboardButton("⏩ تخطي هذه الخطوة", callback_data="skip_comments"))
                text = (
                    "🐾 *[ السؤال 4: خانة التعليقات ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود إضافة خانة أو مساحة تعليقات للمنشور؟\n"
                    "اكتب تفاصيلها أو اضغط على (تخطي)."
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "skip_comments":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["comments_box"] = None
                contest_creation_state[user_id]["step"] = 5
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="btn_join_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="btn_join_no")
                )
                text = (
                    "🐾 *[ السؤال 5: زر الاشتراك ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود إضافة زر اشتراك/انضمام أسفل الرسالة؟"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "btn_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["has_join_btn"] = True
                contest_creation_state[user_id]["step"] = 6
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(types.InlineKeyboardButton("⏩ تخطي (استخدام الرد الافتراضي)", callback_data="skip_custom_msg"))
                text = (
                    "🐾 *[ السؤال 6: نص مخصص للانضمام ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن نص الرد المخصص عند انضمام العضو (أو اضغط تخطي لاستخدام الرد الافتراضي: انضم [المستخدم] بنجاح! 🔥):"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "skip_custom_msg":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["custom_join_text"] = "انضم إلى المسابقة بنجاح! 🔥"
                contest_creation_state[user_id]["step"] = 7
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="mention_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="mention_no")
                )
                text = (
                    "🐾 *[ السؤال 7: منشن العضو ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود عمل منشن (تاغ) للضاغط على الزر في الرسالة؟"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "btn_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["has_join_btn"] = False
                contest_creation_state[user_id]["step"] = 7
                markup = get_cancel_and_home_markup("cmd_create")
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="mention_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="mention_no")
                )
                text = (
                    "🐾 *[ السؤال 7: منشن العضو ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود عمل منشن (تاغ) للضاغط على الزر في الرسالة؟"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "mention_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = False
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "cmd_end":
            if call.message.chat.type != "private":
                msg_txt = call.message.text or call.message.caption or ""
                count_val = "0"
                if "عدد المسجلين:" in msg_txt:
                    import re
                    nums = re.findall(r'\d+', msg_txt.split("عدد المسجلين:")[1].split("\n")[0])
                    if nums:
                        count_val = nums[0]
                 
                report = f"⛔ *تم إنهاء المسابقة بنجاح!*\n📊 إجمالي المشاركين: *{count_val}*"
                bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=create_main_menu_markup())
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = get_cancel_and_home_markup("cmd_home")
                text = (
                    "⛔ *[ إنهاء مسابقة شركس ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي *معرف أو رابط القناة/القروب* المراد إنهاء مسابقتها:"
                )
                update_or_send_panel(chat_id, text, markup, message_id)

        elif data == "cmd_clean_chat":
            for m_id in range(message_id, max(0, message_id - 50), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            sent = bot.send_message(chat_id, "🧹 *تم تنظيف الشات بنجاح!* 🐱✨", parse_mode="Markdown", reply_markup=create_main_menu_markup())
            last_panel_message[chat_id] = sent.message_id

        elif data == "cmd_developer":
            markup = get_back_and_home_markup("cmd_home")
            card_text = (
                "🐾 *[ بطاقة مطور البوت - شركس القط ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "• **اسم المطور:** صانع ومبتكر نظام شركس الذكي.\n"
                "• **نبذة:** قط عبقري يهوى البرمجة، هندسة البوتات، وتأليف الأنظمة التفاعلية الملساء دون أخطاء أو تعقيد!\n"
                "• **الحساب الشخصي:** يمكنك التواصل عبر معرف المطور أو القناة الرسمية.\n"
                "🐾 *مبرمج خصيصاً لإدارة مسابقاتكم بحب واحترافية!*"
            )
            update_or_send_panel(chat_id, card_text, markup, message_id)

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            update_or_send_panel(chat_id, "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:", create_main_menu_markup(), message_id)

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            update_or_send_panel(chat_id, "❌ تم إغلاق القائمة بنجاح. أرسل /start أو اكتب اسم البوت لإظهارها مجدداً.", create_main_menu_markup(), message_id)

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# **دالة نشر المسابقة مع تضمين الهاش المعالج ذاتياً في الإعلان**
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    prize_media = state_data.get("prize_media") 
    comments_box = state_data.get("comments_box")
    has_join_btn = state_data.get("has_join_btn", True)
    custom_join_text = state_data.get("custom_join_text", "انضم إلى المسابقة بنجاح! 🔥")
    msg_mention_bool = state_data.get("msg_mention", True)
    
    # ترجمة النص المخصص إلى كود هاش قصير وآمن يُحفظ في الإعلان مباشرة
    encoded_custom = encode_custom_text(custom_join_text if custom_join_text else "انضم إلى المسابقة بنجاح! 🔥")
    mention_flag = "1" if msg_mention_bool else "0"
    unique_hash = f"{encoded_custom}_{mention_flag}"
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID in publish: {e}")

    # بناء نص الإعلان مع إخفاء أو تضمين الكود بدقة
    text_parts = [f"🎉 *مسابقة جديدة* `(كود: {encoded_custom})`\n", f"❓ *السؤال:*\n{announcement}"]
    
    if prize_media:
        text_parts.append(f"🎁 *الهدية/الصورة:* مرفقة")
    if comments_box:
        text_parts.append(f"💬 *خانة التعليقات:* {comments_box}")
        
    text_parts.extend([
        f"👥 عدد المسجلين: *0*",
        f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
    ])
    
    final_text = "\n\n".join(text_parts)

    channel_markup = types.InlineKeyboardMarkup()
    if has_join_btn:
        channel_markup.add(types.InlineKeyboardButton("تسجيل / انضمام 🏆", callback_data=f"contest_vote_{unique_hash}"))

    try:
        if prize_media and message_has_photo_id(prize_media):
            sent_msg = bot_instance.send_photo(target_chat_id, prize_media, caption=final_text, parse_mode="Markdown", reply_markup=channel_markup)
        else:
            sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=channel_markup)

        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception as pin_err:
            print(f"Pin message error: {pin_err}")

        update_or_send_panel(
            chat_id,
            "✅ *تم نشر المسابقة وتثبيتها بنجاح تام وبدون أي اعتماد على الذاكرة!* 🐾",
            create_main_menu_markup(),
            message_id
        )
    except Exception as e:
        update_or_send_panel(
            chat_id,
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت في القناة أو القروب: {e}",
            create_main_menu_markup(),
            message_id
        )

def message_has_photo_id(media_val):
    return isinstance(media_val, str) and len(media_val) > 20 and not media_val.startswith("http")


# ==========================================
# **معالجة خطوات الأسئلة السبعة في المحادثة الخاصة**
# ==========================================
@bot.message_handler(chat_types=["private"], content_types=["text", "photo"])
def handler_private_contest_steps(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    target_message_id = last_panel_message.get(chat_id)

    if user_id in end_contest_state:
        end_contest_state.pop(user_id, None)
        update_or_send_panel(
            chat_id,
            f"⛔ *تم إنهاء معالجة الطلب للقناة المحددة بنجاح.* 🐾",
            create_main_menu_markup(),
            target_message_id
        )
        return

    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)

        if step == 1:
            resolved_channel_id = text_content
            if "t.me/" in text_content:
                parts = text_content.split("t.me/")[-1].split("?")[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved_channel_id = f"@{parts}"

            try:
                chat_member = bot.get_chat_member(resolved_channel_id, bot.get_me().id)
                if chat_member.status not in ["administrator", "creator"]:
                    raise Exception("Bot is not admin")
            except Exception as e:
                markup = get_back_and_home_markup("cmd_create")
                update_or_send_panel(
                    chat_id,
                    "⚠️ **خطأ في الصلاحيات أو المعرف!**\nتأكد أن البوت مشرف في القناة/القروب ولديه صلاحيات النشر والتثبيت.",
                    markup,
                    target_message_id
                )
                contest_creation_state.pop(user_id, None)
                return

            try:
                chat_obj = bot.get_chat(resolved_channel_id)
                resolved_channel_id = chat_obj.id
            except Exception:
                pass

            state_data["channel"] = resolved_channel_id
            state_data["step"] = 2

            markup = get_cancel_and_home_markup("step_back_q1")
            text = (
                "🐾 *[ السؤال 2: نص المسابقة أو السؤال ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن *نص المسابقة أو سؤال التصويت المراد نشره*:"
            )
            update_or_send_panel(chat_id, text, markup, target_message_id)
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("step_back_q2")
            markup.row(types.InlineKeyboardButton("⏩ تخطي هذه الخطوة", callback_data="skip_image"))
            text = (
                "🐾 *[ السؤال 3: إرفاق صورة مميزة (اختياري) ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق صورة في أعلى منشور المسابقة للتميز؟\n"
                "أرسل الصورة الآن أو اضغط على (تخطي)."
            )
            update_or_send_panel(chat_id, text, markup, target_message_id)
            return

        elif step == 3:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            
            state_data["step"] = 4
            markup = get_cancel_and_home_markup("step_back_q3")
            markup.row(types.InlineKeyboardButton("⏩ تخطي هذه الخطوة", callback_data="skip_comments"))
            text = (
                "🐾 *[ السؤال 4: خانة التعليقات (اختياري) ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إضافة خانة أو مساحة تعليقات للمنشور؟\n"
                "اكتب تفاصيلها أو اضغط على (تخطي)."
            )
            update_or_send_panel(chat_id, text, markup, target_message_id)
            return

        elif step == 4:
            state_data["comments_box"] = text_content
            state_data["step"] = 5
            markup = get_cancel_and_home_markup("step_back_q4")
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="btn_join_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="btn_join_no")
            )
            text = (
                "🐾 *[ السؤال 5: زر الاشتراك ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إضافة زر اشتراك/انضمام أسفل الرسالة؟"
            )
            update_or_send_panel(chat_id, text, markup, target_message_id)
            return

        elif step == 6:
            state_data["custom_join_text"] = text_content
            state_data["step"] = 7
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="mention_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="mention_no")
            )
            text = (
                "🐾 *[ السؤال 7: منشن العضو ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود عمل منشن (تاغ) للضاغط على الزر في الرسالة؟"
            )
            update_or_send_panel(chat_id, text, markup, target_message_id)
            return
         
# ==========================================
# **التشغيل الأساسي للبوت والخادم**
# ==========================================
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port %s" % PORT)
     
    time.sleep(2)
     
    try:
        bot.remove_webhook()
        bot.set_webhook(url="")
    except Exception as e:
        print(f"Webhook reset error: {e}")

    while True:
        try:
            print("Starting bot polling safely...")
            bot.infinity_polling(skip_pending=True, timeout=15, long_polling_timeout=15)
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
