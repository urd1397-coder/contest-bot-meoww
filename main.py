# ==========================================
# **بوتي شركس القط - الإصدار النهائي المعدل 2026**
# ==========================================
import os
import time
import threading
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler
from hashids import Hashids

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

hashids = Hashids(salt="sharx_secure_salt_2026", min_length=4)

last_panel_message = {}
contest_creation_state = {}
end_contest_state = {}


# ==========================================
# 1. خادم الويب المصغر (Keep-Alive Server)
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Sharx Bot Clean Mode is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# ==========================================
# 2. الأزرار والقوائم
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("💻 مطور البوت", callback_data="cmd_developer"),
        types.InlineKeyboardButton("🧹 تنظيف شات البوت", callback_data="cmd_clean_chat"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def get_cancel_and_home_markup(back_callback="cmd_home"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup


# ==========================================
# 3. التحقق من المشرفين
# ==========================================
def is_user_admin(chat_id, user_id):
    if user_id in [1087968824, 777000]:  # حسابات الخدمات والدعم
        return True
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id == user_id:
                return True
    except Exception:
        pass
    return False


# ==========================================
# 4. معالج أمر البدء (Start)
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    chat_id = message.chat.id
    if message.chat.type != "private":
        if not is_user_admin(chat_id, message.from_user.id):
            return
    
    text = (
        "مياو أهلاً بك في عالم شركس القط! 🐱✨\n"
        "البوت الذكي لإدارة المسابقات بكل احترافية وبدون عشوائية.\n"
        "اختر ما يناسبك من القائمة أدناه:"
    )
    try:
        sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
        last_panel_message[chat_id] = sent.message_id
    except Exception as e:
        print(f"Error in start command: {e}")


# ==========================================
# 5. معالج رسائل القروبات (معالجة مستقلة للردود وجلب المعلومات)
# ==========================================
@bot.message_handler(chat_types=["supergroup", "group"], content_types=["text", "photo"])
def handle_group_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    # (الحل 3): فحص الرد على الرسائل لجلب معلومات العضو فوراً ودون قيود
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_id = target_user.id
        target_first = target_user.first_name or "غير معروف"
        target_username = f"@{target_user.username}" if target_user.username else "لا يوجد"
        account_type = "🤖 بوت" if target_user.is_bot else "👤 شخص حقيقي (مستخدم)"

        info_text = (
            "🐱 **بطاقة معلومات الحساب - شركس القط** 🐾\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** [{target_first}](tg://user?id={target_id})\n"
            f"🏷️ **المعرف (Username):** {target_username}\n"
            f"🆔 **الآيدي (Account ID):** `{target_id}`\n"
            f"📊 **نوع الحساب:** {account_type}\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        try:
            bot.reply_to(message, info_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Error sending user info: {e}")
        return

    # إظهار القائمة عند ذكر اسم البوت
    if not user_id in contest_creation_state and text_content and any(name in text_content for name in ["شركس", "Sharx", "شاركس"]):
        if not is_user_admin(chat_id, user_id):
            return
        try:
            sent = bot.send_message(chat_id, "مياو! أهلاً بك يا مشرفنا العزيز 🐱✨\nإليك قائمة التحكم الخاصة بالمسابقات:", reply_markup=create_main_menu_markup())
            last_panel_message[chat_id] = sent.message_id
        except Exception:
            pass
        return

    # متابعة خطوات إنشاء المسابقة داخل القروب
    if user_id in contest_creation_state:
        if not is_user_admin(chat_id, user_id):
            return

        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 2)
        target_message_id = last_panel_message.get(chat_id)

        # (الحل 2): حذف رسالة المستخدم بشكل آمن لمنع تكدس الـ Stack
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        if step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("🎁 نعم (إرفاق صورة/رابط)", callback_data="prize_yes"),
                types.InlineKeyboardButton("⏭️ تخطي", callback_data="prize_no")
            )
            text = (
                "🐾 [ السؤال الثالث: إرفاق هدية أو صورة ] 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق صورة أو رابط هدية لتميز مسابقتك؟ (اضغط تخطي للانتقال مباشرة)."
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 3:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            ask_join_button_step(user_id, chat_id, target_message_id)
            return

        elif step == 5:
            state_data["button_text"] = text_content
            state_data["step"] = 6
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(types.InlineKeyboardButton("⏭️ تخطي واستخدام الرد التلقائي", callback_data="join_msg_skip"))
            text = (
                "🐾 [ السؤال الخامس: رسالة الرد المميزة ] 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن نص الرد المخصص عند ضغط المستخدم على الزر (أو اضغط تخطي):"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 6:
            state_data["join_msg_text"] = text_content
            ask_mention_step(user_id, chat_id, target_message_id)
            return


# ==========================================
# 6. معالج الأزرار والتصويت (معالجة الردود الطويلة بدون إرسال رسائل مزعجة)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id 
    user_id = call.from_user.id
    data = call.data
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id

    if call.message.chat.type != "private" and not data.startswith("vote_"):
        if not is_user_admin(chat_id, user_id):
            try:
                bot.answer_callback_query(call.id, "⚠️ هذه الأزرار مخصصة للمشرفين فقط يا صديقي! 🐾", show_alert=True)
            except Exception:
                pass
            return
     
    # (الحل 4): معالجة الضغط وتحديث المشاركين بصمت عبر الإشعار المنبثق دون إرسال رسائل طويلة متكررة بالقروب
    if data.startswith("vote_"):
        try:
            parts = data.split("_", 3)
            use_mention = (parts[2] == "1")
            custom_join_msg = parts[3].replace("__", " ") if len(parts) > 3 else "انضم إلى المسابقة بنجاح! 🔥"

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
                elif "قائمة المشاركين:" in line:
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
                bot.edit_message_caption(caption=updated_full_text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=call.message.reply_markup)
            else:
                bot.edit_message_text(text=updated_full_text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=call.message.reply_markup)

            # إرسال رسالة تنبيه منبثقة قصيرة وخاصة بالمستخدم فقط لتفادي إزعاج المجموعة بالرسائل الطويلة المتكررة
            alert_text = f"✅ تم تسجيل مشاركتك بنجاح يا {user_first_name}!\n{custom_join_msg}"
            try:
                bot.answer_callback_query(call.id, alert_text, show_alert=True)
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
            if call.message.chat.type == "private":
                contest_creation_state[user_id] = {"step": 1, "is_private": True}
                markup = get_cancel_and_home_markup("cmd_home")
                text = (
                    "🐾 *[ السؤال الأول: معرف القناة أو القروب المستهدف ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **معرف القناة أو القروب أو الرابط** المراد النشر فيه:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            else:
                if not is_user_admin(chat_id, user_id):
                    return
                contest_creation_state[user_id] = {"step": 2, "is_private": False, "channel": chat_id}
                markup = get_cancel_and_home_markup("cmd_home")
                text = (
                    "🐾 *[ السؤال الثاني: نص المسابقة ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **نص المسابقة أو السؤال** المراد نشره:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 3
                markup = get_cancel_and_home_markup("cmd_create")
                text = "🎁 *[ السؤال الثالث ]*\nأرسل لي الآن **صورة الهدية أو رابطها** لتميز مسابقتك:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_media"] = None
                ask_join_button_step(user_id, chat_id, message_id)

        elif data == "btn_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 5
                markup = get_cancel_and_home_markup("cmd_create")
                text = "🔤 *[ السؤال الخامس ]*\nأرسل لي الآن **نص الرد المميز** الذي يظهر عند ضغط المستخدم على الزر:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "btn_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["button_text"] = None
                contest_creation_state[user_id]["join_msg_text"] = "انضم إلى المسابقة بنجاح! 🔥"
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "join_msg_skip":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["join_msg_text"] = "انضم إلى المسابقة بنجاح! 🔥"
                ask_mention_step(user_id, chat_id, message_id)

        elif data == "mention_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = False
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "cmd_developer":
            bot.edit_message_text("💻 **المطور:** [@z7xxq](https://t.me/z7xxq)", chat_id, message_id, parse_mode="Markdown", reply_markup=get_cancel_and_home_markup("cmd_home"))

        elif data == "cmd_end":
            if call.message.chat.type != "private":
                if not is_user_admin(chat_id, user_id):
                    return
                msg_txt = call.message.text or call.message.caption or ""
                count_val = "0"
                if "عدد المسجلين:" in msg_txt:
                    import re
                    nums = re.findall(r'\d+', msg_txt.split("عدد المسجلين:")[1].split("\n")[0])
                    if nums:
                        count_val = nums[0]
                 
                bot.send_message(chat_id, f"⛔ *تم إنهاء المسابقة بنجاح!*\n📊 إجمالي المشاركين: *{count_val}*", parse_mode="Markdown", reply_markup=create_main_menu_markup())
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
            else:
                end_contest_state[user_id] = {"step": 1}
                bot.edit_message_text("⛔ *[ إنهاء مسابقة شركس ]*\nأرسل لي *معرف أو رابط القناة/القروب* المراد إنهاء مسابقتها:", chat_id, message_id, parse_mode="Markdown", reply_markup=get_cancel_and_home_markup("cmd_home"))

        elif data == "cmd_clean_chat":
            for m_id in range(message_id, max(0, message_id - 20), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            sent = bot.send_message(chat_id, "🧹 *تم تنظيف الشات بنجاح!* 🐱✨", parse_mode="Markdown", reply_markup=create_main_menu_markup())
            last_panel_message[chat_id] = sent.message_id

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            try:
                bot.edit_message_text("🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:", chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup())
            except Exception:
                pass

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            try:
                bot.edit_message_text("❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.", chat_id, message_id, parse_mode="Markdown")
            except Exception:
                pass

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# 7. خطوات إعداد وإنشاء المسابقة
# ==========================================
def ask_join_button_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 4
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(types.InlineKeyboardButton("✅ نعم", callback_data="btn_join_yes"), types.InlineKeyboardButton("❌ لا", callback_data="btn_join_no"))
        text = "🎯 *[ السؤال الرابع ]*\nهل تود إضافة زر اشتراك/تسجيل أسفل الرسالة؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass

def ask_mention_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 7
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(types.InlineKeyboardButton("✅ نعم (مع منشن)", callback_data="mention_join_yes"), types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_join_no"))
        text = "🏷️ *[ السؤال الأخير ]*\nهل تود عمل تاغ أو منشن للشخص الضاغط على الزر عند الانضمام؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass


# ==========================================
# 8. (الحل 1): دالة النشر النهائية المحدثة بدقة لضمان النشر بالقروبات
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    button_text = state_data.get("button_text", "تسجيل / انضمام 🏆")
    prize_media = state_data.get("prize_media") 
    join_msg_text = state_data.get("join_msg_text", "انضم إلى المسابقة بنجاح! 🔥")
    msg_mention_bool = state_data.get("msg_mention", True)
    
    unique_hash = hashids.encode(int(time.time()))
     
    try:
        target_chat = bot_instance.get_chat(raw_channel)
        target_chat_id = target_chat.id
    except Exception as e:
        print(f"Error resolving target chat: {e}")
        target_chat_id = raw_channel

    if prize_media:
        final_text = (
            f"🎉 *مسابقة شركس القط الجديدة* (كود: `{unique_hash}`)\n\n"
            f"❓ *السؤال:*\n{announcement}\n\n"
            f"🎁 *الهدية:* {prize_media}\n\n"
            f"👥 عدد المسجلين: *0*\n"
            f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
        )
    else:
        final_text = (
            f"🎉 *مسابقة شركس القط الجديدة* (كود: `{unique_hash}`)\n\n"
            f"❓ *السؤال:*\n{announcement}\n\n"
            f"👥 عدد المسجلين: *0*\n"
            f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
        )

    mention_flag = "1" if msg_mention_bool else "0"
    sanitized_msg = join_msg_text.replace(" ", "__")
    callback_payload = f"vote_{unique_hash}_{mention_flag}_{sanitized_msg}"

    channel_markup = types.InlineKeyboardMarkup()
    if button_text:
        channel_markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_payload))

    try:
        sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=channel_markup)
        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception:
            pass

        bot_instance.edit_message_text(
            f"✅ *تم نشر المسابقة وتثبيتها بنجاح تام يا بطل!* 🐾\n🔑 كود الهاش: `{unique_hash}`",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        print(f"Publishing Error: {e}")
        try:
            bot_instance.edit_message_text(
                f"⚠️ تعذر النشر، تأكد من صلاحيات البوت كمسؤول بالقروب: {e}",
                chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
            )
        except Exception:
            pass


# ==========================================
# 9. معالج المحادثات الخاصة (Private Chat)
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
        update_or_send_panel(chat_id, f"⛔ *تم إنهاء معالجة الطلب بنجاح.* 🐾", create_main_menu_markup())
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
                admins = bot.get_chat_administrators(resolved_channel_id)
                is_admin = any(admin.user.id == user_id for admin in admins)
                if not is_admin:
                    raise Exception("User is not admin")
                
                bot_member = bot.get_chat_member(resolved_channel_id, bot.get_me().id)
                if bot_member.status not in ["administrator", "creator"]:
                    raise Exception("Bot is not admin")
            except Exception:
                markup = get_back_and_home_markup("cmd_create")
                bot.edit_message_text(
                    "⚠️ **فشل التحقق من الصلاحيات!**\nتأكد أنك أنت (المستخدم) والبوت مشرفين.",
                    chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup
                )
                contest_creation_state.pop(user_id, None)
                return

            try:
                resolved_channel_id = bot.get_chat(resolved_channel_id).id
            except Exception:
                pass

            state_data["channel"] = resolved_channel_id
            state_data["step"] = 2
            markup = get_cancel_and_home_markup("cmd_create")
            bot.edit_message_text("🐾 *[ السؤال الثاني: نص المسابقة ]*\nأرسل لي الآن نص المسابقة:", chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(types.InlineKeyboardButton("🎁 نعم", callback_data="prize_yes"), types.InlineKeyboardButton("⏭️ تخطي", callback_data="prize_no"))
            bot.edit_message_text("🐾 *[ السؤال الثالث ]*\nهل تود إرفاق صورة أو رابط هدية؟", chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 3:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            ask_join_button_step(user_id, chat_id, target_message_id)
            return

        elif step == 5:
            state_data["button_text"] = text_content
            state_data["step"] = 6
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(types.InlineKeyboardButton("⏭️ تخطي", callback_data="join_msg_skip"))
            bot.edit_message_text("🐾 *[ السؤال الخامس ]*\nأرسل لي الآن **نص الرد المخصص**:", chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 6:
            state_data["join_msg_text"] = text_content
            ask_mention_step(user_id, chat_id, target_message_id)
            return

def update_or_send_panel(chat_id, text, reply_markup):
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
# 10. التشغيل الرئيسي (Main Execution)
# ==========================================
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port {PORT}")
     
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
