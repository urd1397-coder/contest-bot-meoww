# ==========================================
# **بوتي شركس - نظام المسابقات والتصويت الداخلي الذكي**
# ==========================================
import os
import time
import threading
import random
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

active_contests = {}
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
# **لوحات الأزرار والقوائم**
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


# ==========================================
# **أمر البداية (Start)**
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
     
    if data.startswith("join_contest_") or data == "contest_vote_action":
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

            # استرجاع النص المخصص الذي أدخله المستخدم أو استخدام النص الافتراضي
            parts_data = active_contests.get(data.replace("join_contest_", ""))
            custom_text = parts_data.get("join_msg_text", "انضم إلى المسابقة بنجاح! 🔥") if parts_data else "انضم إلى المسابقة بنجاح! 🔥"

            announcement_to_send = f"\u200f{user_identity} {custom_text}"
             
            try:
                sent_notif = bot.send_message(
                    chat_id, 
                    announcement_to_send, 
                    parse_mode="HTML"
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
                markup = get_cancel_and_home_markup("cmd_home")
                text = (
                    "🐾 <b>[ إنشاء مسابقة / تصويت شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>معرف القناة أو القروب أو رابطهما</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
            else:
                contest_creation_state[user_id] = {"step": 2, "is_private": False, "channel": chat_id}
                markup = get_cancel_and_home_markup("cmd_home")
                text = (
                    "🐾 <b>[ إنشاء مسابقة في هذا القروب ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص اعلان المسابقة أو السؤال</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 4
                markup = get_cancel_and_home_markup("cmd_create")
                text = "🎁 أرسل لي الآن **صورة الهدية** أو رابطها:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_media"] = None
                ask_button_naming_step(user_id, chat_id, message_id)

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
                text = (
                    "⛔ <b>[ إنهاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي <b>معرف أو رابط القناة/القروب</b> المراد إنهاء مسابقتها:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "cmd_clean_chat":
            for m_id in range(message_id, max(0, message_id - 50), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            sent = bot.send_message(chat_id, "🧹 <b>تم تنظيف الشات بنجاح!</b> 🐱✨", parse_mode="HTML", reply_markup=create_main_menu_markup())
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


def ask_button_naming_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 6
        markup = get_cancel_and_home_markup("cmd_create")
        text = "🔤 أرسل لي الآن **تسمية زر التسجيل/الانضمام** المرادة في رسالة المسابقة (مثال: اشترك الآن 🎁):"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


def ask_join_text_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 7
        markup = get_cancel_and_home_markup("cmd_create")
        text = "💬 أرسل لي الآن **النص الذي سيتم نشره عند انضمام المستخدم** (مثال: انضم إلى المسابقة بنجاح! 🔥):"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.get(user_id)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    button_text = state_data.get("button_text", "تسجيل / انضمام 🏆")
    prize_media = state_data.get("prize_media") 
    join_msg_text = state_data.get("join_msg_text", "انضم إلى المسابقة بنجاح! 🔥")
     
    contest_short_id = random.randint(1000, 9999)
    
    # حفظ النص المرتبط بهذه المسابقة تحديداً
    active_contests[str(contest_short_id)] = {"join_msg_text": join_msg_text}
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID in publish: {e}")

    if prize_media:
        final_text = (
            f"🎉 <b>مسابقة جديدة! (رقم #{contest_short_id})</b>\n\n"
            f"❓ <b>السؤال:</b>\n{announcement}\n\n"
            f"🎁 <b>الهدية:</b> <a href='{prize_media}'>{prize_media}</a>\n\n"
            f"👥 عدد المسجلين: <b>0</b>\n"
            f"📋 قائمة المشاركين: <i>لا يوجد مشاركين حتى الآن</i>"
        )
    else:
        final_text = (
            f"🎉 <b>مسابقة جديدة! (رقم #{contest_short_id})</b>\n\n"
            f"❓ <b>السؤال:</b>\n{announcement}\n\n"
            f"👥 عدد المسجلين: <b>0</b>\n"
            f"📋 قائمة المشاركين: <i>لا يوجد مشاركين حتى الآن</i>"
        )

    channel_markup = types.InlineKeyboardMarkup()
    channel_markup.add(types.InlineKeyboardButton(button_text, callback_data=f"join_contest_{contest_short_id}"))

    try:
        sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=channel_markup)

        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception as pin_err:
            print(f"Pin message error: {pin_err}")

        bot_instance.edit_message_text(
            "✅ <b>تم نشر المسابقة وتثبيتها بنجاح تام!</b> 🐾",
            chat_id, message_id, parse_mode="HTML", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        bot_instance.edit_message_text(
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت في القناة أو القروب: {e}",
            chat_id, message_id, parse_mode="HTML", reply_markup=create_main_menu_markup()
        )


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
            f"⛔ <b>تم إنهاء معالجة الطلب للقناة المحددة.</b> 🐾",
            create_main_menu_markup()
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
            except Exception:
                markup = get_back_and_home_markup("cmd_create")
                bot.edit_message_text(
                    "⚠️ **خطأ في الصلاحيات أو المعرف!**\nتأكد أن البوت مشرف في القناة/القروب وأنك أرسلت المعرف الصحيح.",
                    chat_id, target_message_id, parse_mode="HTML", reply_markup=markup
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
                "🐾 <b>[ سؤال 2: نص اعلان المسابقة ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>نص المسابقة أو السؤال المراد نشره</b>:"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("✅ نعم (إرفاق صورة/رابط هدية)", callback_data="prize_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="prize_no")
            )
            text = (
                "🐾 <b>[ سؤال 3: إرفاق هدية أو صورة ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق <b>رابط لهدية أو صورة للهدية</b> لعرضها في الإعلان؟"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 4:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            ask_button_naming_step(user_id, chat_id, target_message_id)
            return

        elif step == 6:
            state_data["button_text"] = text_content
            # الانتقال لخطوة سؤال نص الانضمام
            ask_join_text_step(user_id, chat_id, target_message_id)
            return

        elif step == 7:
            state_data["join_msg_text"] = text_content
            # النشر النهائي بعد اكتمال سؤال النص
            finalize_and_publish_contest(bot, chat_id, target_message_id, user_id)
            return


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
