# ==========================================
# **بوتي شركس - نظام المسابقات والتصويت الذكي**
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

# إعداد مكتبة Hashids لهاش قصير وفريد[cite: 3]
hashids = Hashids(salt="sharx_secure_salt_2026", min_length=4)

# خزان داخلي لتخزين إعدادات المسابقات المرتبطة بالـ Hashid[cite: 3]
contest_storage = {}

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
# **لوحات الأزرار والقوائم (بطابع قططي ظريف)**
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
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

def get_skip_and_home_markup(skip_callback, back_callback="cmd_home"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⏭️ تخطي", callback_data=skip_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data=back_callback)
    )
    return markup

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
# **أمر البداية (Start)**
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
     
    text = (
        "مياو! أهلاً بك في عالم شركس 🐱✨\n"
        "البوت الأنيق والسريع لإدارة مسابقاتك وتصويتك بكل احترافية ودون أي عشوائية.\n"
        "اختر ما يناسبك من الخيارات أدناه:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
    last_panel_message[message.chat.id] = sent.message_id


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
            h_id = data.replace("contest_vote_", "")
            contest_info = contest_storage.get(h_id, {"join_msg": "انضم إلى المسابقة بنجاح! 🔥", "mention": True})[cite: 3]
            
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

            custom_join_msg = contest_info.get("join_msg", "انضم إلى المسابقة بنجاح! 🔥")
            use_mention = contest_info.get("mention", True)

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
            if call.message.chat.type == "private":
                contest_creation_state[user_id] = {"step": 1, "is_private": True}
                markup = get_back_and_home_markup("cmd_home")
                text = (
                    "🐾 *[ السؤال 1: معرف القناة أو القروب ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **معرف القناة أو القروب المستهدف أو رابطهما**:\n"
                    "_(سيتم التحقق من هويتك كأدمن ووجود البوت بصلاحياته لتجنب العشوائية)_"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            else:
                contest_creation_state[user_id] = {"step": 2, "is_private": False, "channel": chat_id}
                markup = get_back_and_home_markup("cmd_home")
                text = (
                    "🐾 *[ السؤال 2: نص المسابقة أو السؤال ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **نص اعلان المسابقة أو السؤال**:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        # -- تخطي السؤال 3 (الصورة) --
        elif data == "skip_step3":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["image_media"] = None
                go_to_step4(user_id, chat_id, message_id)

        # -- تخطي السؤال 4 (التعليقات) --
        elif data == "skip_step4":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["comments_enabled"] = False
                go_to_step5(user_id, chat_id, message_id)

        elif data == "comments_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["comments_enabled"] = True
                go_to_step5(user_id, chat_id, message_id)

        # -- السؤال 5: زر الاشتراك --
        elif data == "sub_btn_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["has_sub_button"] = True
                contest_creation_state[user_id]["step"] = 6
                
                markup = get_skip_and_home_markup("skip_step6", "cmd_create")
                text = (
                    "🐾 *[ السؤال 6: الرد المميز عند الضغط ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **الرد المميز** من اختيارك (أو اضغط **تخطي** لاستخدام الرد التلقائي):"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "sub_btn_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["has_sub_button"] = False
                contest_creation_state[user_id]["custom_join_msg"] = "انضم إلى المسابقة بنجاح! 🔥"
                go_to_step7(user_id, chat_id, message_id)

        elif data == "skip_step6":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["custom_join_msg"] = "انضم إلى المسابقة بنجاح! 🔥"
                go_to_step7(user_id, chat_id, message_id)

        # -- السؤال 7 والأخير: المنشن --
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
                markup = get_back_and_home_markup("cmd_home")
                text = (
                    "🐾 *[ إنهاء مسابقة شركس ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي *معرف أو رابط القناة/القروب* المراد إنهاء مسابقتها:"
                )
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
# **دوال التنقل السلس بين خطوات الأسئلة**
# ==========================================
def go_to_step4(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 4
        markup = get_skip_and_home_markup("skip_step4", "cmd_create")
        markup.row(types.InlineKeyboardButton("✅ نعم، أضف خانة تعليقات", callback_data="comments_yes"))
        text = (
            "🐾 *[ السؤال 4: خانة التعليقات للمنشور ]* 🐱✨\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "هل تود إضافة خانة تعليقات للمنشور؟\n"
            "يمكنك النقر على زر **تخطي** أدناه إذا لم تكن بحاجة إليها."
        )
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id

def go_to_step5(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 5
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ نعم", callback_data="sub_btn_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="sub_btn_no")
        )
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home"))
        text = (
            "🐾 *[ السؤال 5: زر الاشتراك ]* 🐱✨\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "هل تود إضافة زر اشتراك أسفل رسالة المسابقة؟"
        )
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id

def go_to_step7(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 7
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ نعم", callback_data="mention_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="mention_no")
        )
        markup.add(types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home"))
        text = (
            "🐾 *[ السؤال 7 والأخير: تاغ أو منشن للضاغط على الزر ]* 🐱✨\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "هل تود عمل تاغ أو منشن للشخص عند الضغط على زر الاشتراك وإرسال الإشعار؟"
        )
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


# ==========================================
# **دالة النشر النهائي مع الهاش (Hashid) والجمالية**
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    image_media = state_data.get("image_media")
    has_sub_button = state_data.get("has_sub_button", True)
    custom_join_msg = state_data.get("custom_join_msg", "انضم إلى المسابقة بنجاح! 🔥")
    msg_mention_bool = state_data.get("msg_mention", True)
    
    unique_hash = hashids.encode(int(time.time()))[cite: 3]
    
    contest_storage[unique_hash] = {
        "join_msg": custom_join_msg,
        "mention": msg_mention_bool
    }[cite: 3]
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID in publish: {e}")

    final_text = (
        f"🎉 *مسابقة جديدة* (كود الهاش: `{unique_hash}`)\n\n"
        f"❓ *السؤال:*\n{announcement}\n\n"
        f"👥 عدد المسجلين: *0*\n"
        f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
    )

    channel_markup = types.InlineKeyboardMarkup()
    if has_sub_button:
        channel_markup.add(types.InlineKeyboardButton("اشترك الآن 🏆", callback_data=f"contest_vote_{unique_hash}"))

    try:
        if image_media:
            sent_msg = bot_instance.send_photo(target_chat_id, image_media, caption=final_text, parse_mode="Markdown", reply_markup=channel_markup)
        else:
            sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=channel_markup)

        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception as pin_err:
            print(f"Pin message error: {pin_err}")

        bot_instance.edit_message_text(
            "✅ *تم نشر المسابقة وتثبيتها بنجاح تام مع كود الهاش الجميل!* 🐾🐱",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        bot_instance.edit_message_text(
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت الإدارية في القناة أو القروب: {e}",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )


# ==========================================
# **معالجة المدخلات والخطوات بدون أي تعليق**
# ==========================================
@bot.message_handler(chat_types=["private"], content_types=["text", "photo"])
def handler_private_contest_steps(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    target_message_id = last_panel_message.get(chat_id)

    if user_id in end_contest_state:
        end_contest_state.pop(user_id, None)
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
        update_or_send_panel(
            chat_id,
            f"⛔ *تم إنهاء معالجة الطلب للقناة المحددة.* 🐾",
            create_main_menu_markup()
        )
        return

    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)

        # -- معالجة الخطوة الأولى بأمان تام لتجنب أي تعليق --
        if step == 1:
            resolved_channel_id = text_content
            if "t.me/" in text_content:
                parts = text_content.split("t.me/")[-1].split("?")[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved_channel_id = f"@{parts}"

            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass

            try:
                chat_member = bot.get_chat_member(resolved_channel_id, bot.get_me().id)
                if chat_member.status not in ["administrator", "creator"]:
                    raise Exception("Bot is not admin")
            except Exception:
                markup = get_back_and_home_markup("cmd_create")
                if target_message_id:
                    try:
                        bot.edit_message_text(
                            "⚠️ **خطأ في الصلاحيات أو المعرف!**\nتأكد أن البوت مشرف ولديه الصلاحيات، وأنك أرسلت المعرف الصحيح لتجنب العشوائية.",
                            chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup
                        )
                    except Exception:
                        pass
                contest_creation_state.pop(user_id, None)
                return

            try:
                chat_obj = bot.get_chat(resolved_channel_id)
                resolved_channel_id = chat_obj.id
            except Exception:
                pass

            state_data["channel"] = resolved_channel_id
            state_data["step"] = 2

            markup = get_back_and_home_markup("cmd_create")
            text = (
                "🐾 *[ السؤال 2: نص المسابقة أو السؤال ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **نص اعلان المسابقة أو السؤال** المراد نشره:"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
                except Exception:
                    pass
            return

        # حذف الرسالة المكتوبة في باقي الخطوات لتنظيف الشات
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        # -- السؤال 2: حفظ النص والانتقال للسؤال 3 (الصورة) --
        if step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            
            markup = get_skip_and_home_markup("skip_step3", "cmd_create")
            text = (
                "🐾 *[ السؤال 3: إرفاق صورة (اختياري) ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق **صورة** في أعلى منشور المسابقة للتميز؟\n"
                "أرسل الصورة مباشرة أو انقر على زر **تخطي** أدناه."
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
                except Exception:
                    pass
            return

        # -- استقبال الصورة والانتقال للسؤال 4 --
        elif step == 3:
            if message.photo:
                state_data["image_media"] = message.photo[-1].file_id
            else:
                state_data["image_media"] = text_content
            if target_message_id:
                go_to_step4(user_id, chat_id, target_message_id)
            return

        # -- السؤال 6: استلام الرد المميز --
        elif step == 6:
            state_data["custom_join_msg"] = text_content
            if target_message_id:
                go_to_step7(user_id, chat_id, target_message_id)
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
