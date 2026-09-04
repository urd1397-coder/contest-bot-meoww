# ==========================================
# **بوتي شركس - نظام مسابقات القطط الفخمة**
# ==========================================
import os
import time
import threading
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

last_panel_message = {}
contest_creation_state = {}
end_contest_state = {}
contest_text_cache = {}

# ==========================================
# **خادم الويب للحفاظ على نشاط البوت**
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Sharx Cat Bot is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# ==========================================
# **لوحات الأزرار والقوائم**
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة بقطة ترويسية 😎", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
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

def update_or_send_panel(chat_id, text, reply_markup):
    if chat_id in last_panel_message:
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=last_panel_message[chat_id],
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
     
    sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup)
    last_panel_message[chat_id] = sent.message_id


@bot.message_handler(commands=["start"])
def handle_start_command(message):
    if message.chat.type != "private":
        return
     
    text = (
        "مياو أهلاً بك في مقر قطط شركس الفخمة! 🐱🕶️✨\n"
        "البوت جاهز لإدارة مسابقاتك مع أروع صور القطط الترويسية:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=create_main_menu_markup())
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
            message_text = call.message.text or call.message.caption or ""
            user_first_name = call.from_user.first_name or "المشارك"
            user_username = call.from_user.username
             
            if user_username:
                user_identity = f"@{user_username}"
            else:
                user_identity = f"<a href='tg://user?id={user_id}'>{user_first_name}</a>"

            if str(user_id) in message_text or (user_username and f"@{user_username}" in message_text):
                try:
                    bot.answer_callback_query(call.id, f"⚠️ عذراً يا {user_first_name}\nلقد قمت بالتسجيل مسبقاً ولا يمكنك التكرار! 🚫", show_alert=True)
                except Exception:
                    pass
                return

            cache_key = f"{chat_id}_{message_id}"
            cached_data = contest_text_cache.get(cache_key, {"msg": "انضم إلى مسابقة القطط بنجاح! 🐾", "mention": True})
            
            custom_join_msg = cached_data["msg"]
            use_mention = cached_data["mention"]

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
                    new_lines.append(f"👥 عدد المسجلين: <b>{current_count}</b>")
                elif "قائمة المشاركين:" in line:
                    participants_line_idx = i
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if participants_line_idx != -1:
                old_participants_text = lines[participants_line_idx].replace("📋 قائمة المشاركين:", "").strip()
                if "لا يوجد مشاركين" in old_participants_text or not old_participants_text:
                    updated_participants = f"{user_identity} (ID:{user_id})"
                else:
                    updated_participants = f"{old_participants_text}, {user_identity} (ID:{user_id})"
                 
                new_lines[participants_line_idx] = f"📋 قائمة المشاركين: {updated_participants}"

            updated_full_text = "\n".join(new_lines)

            if call.message.photo:
                bot.edit_message_caption(
                    caption=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="HTML",
                    reply_markup=call.message.reply_markup
                )
            else:
                bot.edit_message_text(
                    text=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="HTML",
                    reply_markup=call.message.reply_markup
                )

            if use_mention:
                announcement_to_send = f"{user_identity}\n{custom_join_msg}"
            else:
                announcement_to_send = f"{custom_join_msg}"
             
            try:
                sent_notif = bot.send_message(chat_id, announcement_to_send, parse_mode="HTML")
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
                    "🐾 <b>[ الخطوة 1: معرف القناة/القروب ]</b> 🐱🕶️\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>معرف القناة أو القروب أو رابطهما</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
            else:
                contest_creation_state[user_id] = {"step": 2, "is_private": False, "channel": chat_id}
                markup = get_cancel_and_home_markup("cmd_home")
                text = "📸 أرسل لي الآن **صورة الـ Header (القطة الكشخة)** التي تريد وضعها في رأس المسابقة:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "join_msg_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 6
                markup = get_cancel_and_home_markup("cmd_create")
                text = "💬 أرسل لي الآن **النص المخصص** ليرسله البوت عند دخول الشخص:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "join_msg_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["send_join_msg"] = False
                contest_creation_state[user_id]["msg_mention"] = False
                contest_creation_state[user_id]["join_msg_text"] = "انضم إلى مسابقة القطط بنجاح! 🐾"
                finalize_and_publish_cat_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_cat_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = False
                finalize_and_publish_cat_contest(bot, chat_id, message_id, user_id)

        elif data == "cmd_end":
            if call.message.chat.type != "private":
                msg_txt = call.message.text or call.message.caption or ""
                count_val = "0"
                if "عدد المسجلين:" in msg_txt:
                    import re
                    nums = re.findall(r'\d+', msg_txt.split("عدد المسجلين:")[1].split("\n")[0])
                    if nums:
                        count_val = nums[0]
                 
                report = f"⛔ <b>تم إنهاء المسابقة بنجاح!</b>\n📊 إجمالي المشاركين: <b>{count_val}</b>"
                bot.send_message(chat_id, report, parse_mode="HTML", reply_markup=create_main_menu_markup())
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = get_cancel_and_home_markup("cmd_home")
                text = "⛔ أرسل لي <b>معرف أو رابط القناة/القروب</b> المراد إنهاء مسابقتها:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "cmd_clean_chat":
            for m_id in range(message_id, max(0, message_id - 50), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            sent = bot.send_message(chat_id, "🧹 <b>تم تنظيف الشات بنجاح!</b> 🐾", parse_mode="HTML", reply_markup=create_main_menu_markup())
            last_panel_message[chat_id] = sent.message_id

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            update_or_send_panel(chat_id, "🏠 القائمة الرئيسية لقطط شركس 🐱:", create_main_menu_markup())

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            update_or_send_panel(chat_id, "❌ تم إغلاق القائمة. أرسل /start لإظهارها مجدداً.", create_main_menu_markup())

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# **دالة نشر المسابقة بصورة القطـة الحقيقية**
# ==========================================
def finalize_and_publish_cat_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة القطط الكشخة!")
    header_photo = state_data.get("header_photo")
     
    join_msg_text = state_data.get("join_msg_text", "انضم إلى المسابقة بنجاح! 🐾")
    msg_mention = state_data.get("msg_mention", True)
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID: {e}")

    final_text = (
        f"🎉 <b>مسابقة جديدة برعاية قطط شركس الفخمة</b> 😎\n\n"
        f"❓ <b>السؤال:</b>\n{announcement}\n\n"
        f"👥 عدد المسجلين: <b>0</b>\n"
        f"📋 قائمة المشاركين: <i>لا يوجد مشاركين حتى الآن</i>"
    )

    channel_markup = types.InlineKeyboardMarkup()
    channel_markup.add(types.InlineKeyboardButton("اشترك الآن 😎 🏆", callback_data="contest_vote_action"))

    try:
        if header_photo:
            sent_msg = bot_instance.send_photo(
                target_chat_id, 
                photo=header_photo, 
                caption=final_text, 
                parse_mode="HTML", 
                reply_markup=channel_markup
            )
        else:
            sent_msg = bot_instance.send_message(
                target_chat_id, 
                text=final_text, 
                parse_mode="HTML", 
                reply_markup=channel_markup,
                disable_web_page_preview=True
            )
        
        cache_key = f"{target_chat_id}_{sent_msg.message_id}"
        contest_text_cache[cache_key] = {
            "msg": join_msg_text,
            "mention": msg_mention
        }

        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception:
            pass

        bot_instance.edit_message_text(
            "✅ <b>تم نشر المسابقة بصورة القطة الترويسية بنجاح تام!</b> 🐾",
            chat_id, message_id, parse_mode="HTML", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        bot_instance.edit_message_text(
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت في القناة: {e}",
            chat_id, message_id, parse_mode="HTML", reply_markup=create_main_menu_markup()
        )


# ==========================================
# **معالجة خطوات المحادثة الخاصة**
# ==========================================
@bot.message_handler(chat_types=["private"], content_types=["text", "photo"])
def handler_private_contest_steps(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    target_message_id = last_panel_message.get(chat_id)

    if user_id in end_contest_state:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
        end_contest_state.pop(user_id, None)
        update_or_send_panel(chat_id, "⛔ <b>تم إنهاء مسابقة القناة المحددة.</b> 🐾", create_main_menu_markup())
        return

    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        if step == 1:
            resolved_channel_id = text_content
            if "t.me/" in text_content:
                parts = text_content.split("t.me/")[-1].split("?")[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved_channel_id = f"@{parts}"

            try:
                chat_obj = bot.get_chat(resolved_channel_id)
                state_data["channel"] = chat_obj.id
            except Exception:
                state_data["channel"] = resolved_channel_id

            state_data["step"] = 2
            markup = get_cancel_and_home_markup("cmd_create")
            text = "📸 أرسل لي الآن **صورة الـ Header (القطة الكشخة)** التي تريد وضعها برأس المسابقة:"
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 2:
            if message.photo:
                state_data["header_photo"] = message.photo[-1].file_id
            else:
                state_data["header_photo"] = None
            
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            text = "❓ ممتاز! أرسل لي الآن **نص سؤال أو إعلان المسابقة**:"
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 3:
            state_data["announcement"] = text_content
            state_data["step"] = 4
            
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="join_msg_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="join_msg_no")
            )
            text = "💬 هل تود أن يرسل البوت **نصاً مخصصاً** عند دخول الشخص للمسابقة؟"
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
            return

    if user_id in contest_creation_state and contest_creation_state[user_id].get("step") == 6:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass
            
        state_data["join_msg_text"] = text_content
        state_data["step"] = 7
         
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(
            types.InlineKeyboardButton("✅ نعم (مع منشن)", callback_data="mention_join_yes"),
            types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_join_no")
        )
        text = "👤 هل تود إرفاق **منشن** لاسم المشارك مع رسالة الترحيب؟"
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
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
