# ==========================================
# **بوتي شركس القط - الإصدار النهائي المحدث 2026**
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
DEV_ID = 7963720007  # آيدي المطور حصرياً

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# هاش قصير وفريد
hashids = Hashids(salt="sharx_secure_salt_2026", min_length=4)

last_panel_message = {}
contest_creation_state = {}
end_contest_state = {}

# ذاكرة ديناميكية لتخزين المجموعات والقنوات التي يخدمها البوت
served_chats = set()


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
# 2. دوال إنشاء الأزرار والقوائم (Keyboards)
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("💻 مطور البوت", callback_data="cmd_developer"),
        types.InlineKeyboardButton("⚙️ لوحة المطور السرية", callback_data="cmd_dev_panel"),
        types.InlineKeyboardButton("🧹 تنظيف شات البوت", callback_data="cmd_clean_chat"),
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
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup


# ==========================================
# 3. دوال التحقق من المطور والمشرفين
# ==========================================
def is_dev(user_id):
    return user_id == DEV_ID

def is_user_admin(chat_id, user_id):
    if is_dev(user_id):
        return True
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ["creator", "administrator"]:
            return True
    except Exception:
        pass
    return False


# ==========================================
# 4. التتبع التلقائي للمجموعات والقنوات
# ==========================================
@bot.my_chat_member_handler()
def track_chats(message):
    new_status = message.new_chat_member.status
    chat_id = message.chat.id
    if new_status in ['administrator', 'member']:
        served_chats.add(chat_id)
    elif new_status in ['left', 'kicked']:
        served_chats.discard(chat_id)


# ==========================================
# 5. دوال إدارة واجهة التحكم والتحديث
# ==========================================
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
# 6. استقبال أمر البدء (Start Command)
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        if not is_user_admin(message.chat.id, message.from_user.id):
            return
    
    text = (
        "مياو أهلاً بك في عالم شركس القط! 🐱✨\n"
        "البوت الذكي لإدارة المسابقات بكل احترافية وبدون عشوائية.\n"
        "اختر ما يناسبك من القائمة أدناه:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
    last_panel_message[message.chat.id] = sent.message_id


# ==========================================
# 7. أوامر المطور الاحترازية (كتم وقفل الجميع / إلغاء الكتم)
# ==========================================
@bot.message_handler(commands=['mute_all'])
def mute_all_command(message):
    if not is_dev(message.from_user.id):
        return
    
    chat_id = message.chat.id
    try:
        permissions = types.ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.set_chat_permissions(chat_id, permissions)
        bot.send_message(chat_id, "⚠️ **إجراء احترازي قاطع:** تم قفل الشات وكتم الجميع بالكامل! لا يمكن لأحد الكتابة باستثناء المطور 🐾")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تنفيذ الكتم العام: {e}")

@bot.message_handler(commands=['unmute_all'])
def unmute_all_command(message):
    if not is_dev(message.from_user.id):
        return
    
    chat_id = message.chat.id
    try:
        permissions = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.set_chat_permissions(chat_id, permissions)
        bot.send_message(chat_id, "✅ تم إلغاء الكتم العام وإعادة فتح الشات للجميع بنجاح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء فتح الشات: {e}")


# ==========================================
# 8. معالج الرسائل في القروبات (استجابة شركس الكلمة المجردة + الكاشف + الخطوات)
# ==========================================
@bot.message_handler(chat_types=["supergroup", "group"], content_types=["text", "photo"])
def handle_group_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    # 1. الاستجابة لمناداة "شركس" (الكلمة مجردة تماماً + للمشرفين والمطور فقط)
    if not user_id in contest_creation_state and text_content in ["شركس", "Sharx", "شاركس"]:
        if not is_user_admin(chat_id, user_id):
            return

        # جلب معلومات الحساب عند الرد على رسالة أو توجيه رسالة
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_id = target_user.id
            target_first = target_user.first_name or "غير معروف"
            target_username = f"@{target_user.username}" if target_user.username else "لا يوجد"
            account_type = "🤖 بوت" if target_user.is_bot else "👤 مستخدم حقيقي"

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

        sent = bot.send_message(chat_id, "مياو! أهلاً بك يا مشرفنا العزيز 🐱✨\nإليك قائمة التحكم الخاصة بالمسابقات:", reply_markup=create_main_menu_markup())
        last_panel_message[chat_id] = sent.message_id
        return

    # 2. متابعة خطوات إنشاء المسابقة مباشرة داخل القروب
    if user_id in contest_creation_state:
        if not is_user_admin(chat_id, user_id):
            return

        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 2)
        target_message_id = last_panel_message.get(chat_id)

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
            markup.row(
                types.InlineKeyboardButton("⏭️ تخطي واستخدام الرد التلقائي", callback_data="join_msg_skip")
            )
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
# 9. معالج الأزرار الشفافة والأوامر (Callback Handler)
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

    # معالجة تفاعل التصويت وتسجيل المشاركين
    if data.startswith("vote_"):
        try:
            parts = data.split("_", 3)
            h_id = parts[1]
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
                sent_notif = bot.send_message(chat_id, announcement_to_send, parse_mode="Markdown")
                try:
                    bot.pin_chat_message(chat_id, sent_notif.message_id)
                except Exception:
                    pass
            except Exception as e:
                print(f"Error sending join notification: {e}")

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
                    bot.answer_callback_query(call.id, "⚠️ عذراً، هذه الميزة للمشرفين فقط!", show_alert=True)
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
                text = "🎁 *[ السؤال الثالث ]*\nأرسل لي الآن **صورة الهدية أو رابطها** لتميز مسابقتك (أو اضغط رجوع للتخطي):"
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
            try:
                dev_user = bot.get_chat(DEV_ID)
                dev_name = dev_user.first_name or "المطور"
                dev_bio = dev_user.bio or "لا توجد نبذة تعريفية مضافة."
                dev_username = f"@{dev_user.username}" if dev_user.username else "لا يوجد"
                
                dev_info_text = (
                    "💻 **معلومات مطور بوت شركس القط** 🐾\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **الاسم:** [{dev_name}](tg://user?id={DEV_ID})\n"
                    f"🏷️ **المعرف:** {dev_username}\n"
                    f"🆔 **الآيدي:** `{DEV_ID}`\n"
                    f"📝 **البايو:** {dev_bio}\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "✨ مطور بوتات تليجرام الذكية والأنظمة التفاعلية."
                )
                
                markup = get_back_and_home_markup("cmd_home")
                if dev_user.username:
                    markup.row(types.InlineKeyboardButton("💬 تواصل مع المطور", url=f"https://t.me/{dev_user.username}"))
                
                bot.edit_message_text(dev_info_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                fallback_text = (
                    "💻 **معلومات مطور بوت شركس القط** 🐾\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "👤 **المطور:** [@z7xxq](https://t.me/z7xxq)\n"
                    f"🆔 **الآيدي:** `{DEV_ID}`\n"
                    "✨ المبرمج والمسؤول عن تطوير أنظمة شركس الذكية."
                )
                bot.edit_message_text(fallback_text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_and_home_markup("cmd_home"), disable_web_page_preview=True)

        elif data == "cmd_dev_panel":
            if not is_dev(user_id):
                bot.answer_callback_query(call.id, "⚠️ غير مصرح لك بالوصول لقائمة المطور السرية!", show_alert=True)
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("📊 المجموعات والقنوات التي يخدمها البوت", callback_data="dev_chats"),
                types.InlineKeyboardButton("❌ إلغاء العملية والعودة", callback_data="cmd_home")
            )
            bot.edit_message_text("⚙️ **أهلاً بك في لوحة تحكم المطور السرية** 🛠️", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "dev_chats":
            if not is_dev(user_id):
                return
            
            count = len(served_chats)
            msg = f"📊 **المجموعات والقنوات النشطة حالياً ({count}):**\n\n"
            for cid in served_chats:
                try:
                    c_info = bot.get_chat(cid)
                    msg += f"• **{c_info.title}** (`{cid}`)\n"
                except Exception:
                    msg += f"• المحادثة: `{cid}`\n"
            
            bot.edit_message_text(msg, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_and_home_markup("cmd_dev_panel"))

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
                 
                report = f"⛔ *تم إنهاء المسابقة بنجاح!*\n📊 إجمالي المشاركين: *{count_val}*"
                bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=create_main_menu_markup())
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = get_cancel_and_home_markup("cmd_home")
                text = "⛔ *[ إنهاء مسابقة شركس ]*\nأرسل لي *معرف أو رابط القناة/القروب* المراد إنهاء مسابقتها:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "cmd_clean_chat":
            for m_id in range(message_id, max(0, message_id - 50), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            sent = bot.send_message(chat_id, "🧹 *تم تنظيف الشات بنجاح!* 🐱✨", parse_mode="Markdown", reply_markup=create_main_menu_markup())
            last_panel_message[chat_id] = sent.message_id

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            update_or_send_panel(chat_id, "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:", create_main_menu_markup())

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            try:
                bot.send_message(chat_id, "❌ تم إغلاق القائمة.", reply_markup=types.ReplyKeyboardRemove())
            except Exception:
                pass
            update_or_send_panel(chat_id, "❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.", create_main_menu_markup())

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# 10. خطوات إعداد وإنشاء المسابقة (Steps Functions)
# ==========================================
def ask_join_button_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 4
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(
            types.InlineKeyboardButton("✅ نعم", callback_data="btn_join_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="btn_join_no")
        )
        text = "🎯 *[ السؤال الرابع ]*\nهل تود إضافة زر اشتراك/تسجيل أسفل الرسالة؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id

def ask_mention_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 7
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(
            types.InlineKeyboardButton("✅ نعم (مع منشن)", callback_data="mention_join_yes"),
            types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_join_no")
        )
        text = "🏷️ *[ السؤال الأخير ]*\nهل تود عمل تاغ أو منشن للشخص الضاغط على الزر عند الانضمام؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


# ==========================================
# 11. دالة نشر المسابقة النهائية (Finalize & Publish)
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
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID: {e}")

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
        except Exception as pin_err:
            print(f"Pin message error: {pin_err}")

        bot_instance.edit_message_text(
            f"✅ *تم نشر المسابقة وتثبيتها بنجاح تام يا بطل!* 🐾\n🔑 كود الهاش: `{unique_hash}`",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        bot_instance.edit_message_text(
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت كمسؤول في المكان المستهدف: {e}",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )


# ==========================================
# 12. معالج المحادثات الخاصة والخطوات (Private Messages Handler)
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

            # التحقق الدقيق: هل المستخدم مشرف في المكان المحدّد وهل البوت مشرف أيضاً؟
            try:
                # 1. فحص هل المستخدم الحالي مشرف في تلك القناة/القروب
                user_member = bot.get_chat_member(resolved_channel_id, user_id)
                if user_member.status not in ["creator", "administrator"] and not is_dev(user_id):
                    raise Exception("User is not admin")

                # 2. فحص هل البوت مشرف ولديه الصلاحيات
                bot_member = bot.get_chat_member(resolved_channel_id, bot.get_me().id)
                if bot_member.status not in ["administrator", "creator"]:
                    raise Exception("Bot is not admin")
            except Exception as e:
                markup = get_back_and_home_markup("cmd_create")
                bot.edit_message_text(
                    "⚠️ **عذراً، فشل التحقق من الصلاحيات!**\n"
                    "1. تأكد أنك أنت (المستخدم) مشرف فعلي في القناة/القروب المستهدف.\n"
                    "2. تأكد أن البوت مشرف ولديه صلاحيات النشر والتثبيت.\n"
                    "ثم أرسل المعرف أو الرابط الصحيح مجدداً:",
                    chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup
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

            markup = get_cancel_and_home_markup("cmd_create")
            text = (
                "🐾 *[ السؤال الثاني: نص المسابقة ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **نص المسابقة أو سؤال التصويت** المراد نشره:"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("🎁 نعم (إرفاق صورة/رابط)", callback_data="prize_yes"),
                types.InlineKeyboardButton("⏭️ تخطي", callback_data="prize_no")
            )
            text = (
                "🐾 *[ السؤال الثالث: إرفاق هدية أو صورة ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق صورة أو رابط هدية لتميز مسابقتك؟ (اضغط تخطي للانتقال مباشرة)."
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
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
            markup.row(
                types.InlineKeyboardButton("⏭️ تخطي واستخدام الرد التلقائي", callback_data="join_msg_skip")
            )
            text = (
                "🐾 *[ السؤال الخامس: رسالة الرد المميزة ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **نص الرد المخصص** عند ضغط المستخدم على الزر (أو اضغط تخطي):"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 6:
            state_data["join_msg_text"] = text_content
            ask_mention_step(user_id, chat_id, target_message_id)
            return


# ==========================================
# 13. نقطة تشغيل البوت الأساسية (Main Execution)
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
            bot.infinity_polling(
                skip_pending=True, 
                timeout=15, 
                long_polling_timeout=15, 
                allowed_updates=['message', 'edited_message', 'channel_post', 'my_chat_member', 'chat_member', 'callback_query']
            )
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
