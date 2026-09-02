# ==========================================
# **بوتي شركس - نظام المسابقات والتصويت الداخلي بالرسائل**
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

user_search_mode = {}
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
def create_navigation_markup(back_callback="cmd_id_help"):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث الشامل ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("🧹 تنظيف شات البوت", callback_data="cmd_clean_chat"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع للأعضاء والجهات", callback_data="show_keyboard"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة الذكي", callback_data="method_forward"),
        types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    btn_user = types.KeyboardButton(
        text="👤 اختر مستخدم", 
        request_users=types.KeyboardButtonRequestUsers(request_id=1, user_is_bot=False)
    )
    btn_group = types.KeyboardButton(
        text="👥 اختر مجموعة أو قناة", 
        request_chat=types.KeyboardButtonRequestChat(request_id=2, chat_is_channel=False)
    )
    markup.add(btn_user, btn_group)
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
    user_search_mode[message.chat.id] = False
    
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

    # **تفاعل التصويت في القناة (يمنع علامة التحميل المعلقة فوراً)**
    if data.startswith("part_cb_"):
        user_first_name = call.from_user.first_name or "المشارك"
        user_username = call.from_user.username
        current_text = call.message.text or call.message.caption or ""
        
        use_mention = "mention:yes" in call.message.reply_markup.inline_keyboard[0][0].callback_data if call.message.reply_markup else True
        
        if use_mention and user_username:
            user_identity = f"@{user_username}"
        else:
            user_identity = f"<a href='tg://user?id={user_id}'>{user_first_name}</a>"

        if f"id:{user_id}" in current_text or user_identity in current_text:
            try:
                bot.answer_callback_query(call.id, f"⚠️ عذراً يا {user_first_name}\nلقد قمت بالتصويت مسبقاً! 🚫", show_alert=True)
            except Exception:
                pass
            return

        try:
            if "👥 عدد الأصوات:" in current_text:
                parts = current_text.split("👥 عدد الأصوات:")
                count_part = parts[1].split("\n")[0].strip()
                clean_count = ''.join(filter(str.isdigit, count_part))
                current_count = int(clean_count) if clean_count else 0
            else:
                current_count = 0
        except Exception:
            current_count = 0

        new_count = current_count + 1

        voters_line = ""
        if "📋 قائمة المصوتين:" in current_text:
            try:
                old_voters = current_text.split("📋 قائمة المصوتين:")[1].split("<!-- v_data -->")[0].strip()
                if "لا يوجد أصوات حتى الآن" in old_voters:
                    voters_line = user_identity
                else:
                    voters_line = f"{old_voters}, {user_identity}"
            except Exception:
                voters_line = user_identity
        else:
            voters_line = user_identity

        try:
            base_question = current_text.split("👥 عدد الأصوات:")[0].strip()
        except Exception:
            base_question = current_text

        updated_text = (
            f"{base_question}\n\n"
            f"👥 عدد الأصوات: <b>{new_count}</b>\n"
            f"📋 قائمة المصوتين: {voters_line}\n"
            f"<!-- v_data id:{user_id} -->"
        )

        try:
            if call.message.photo:
                bot.edit_message_caption(
                    caption=updated_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="HTML",
                    reply_markup=call.message.reply_markup
                )
            else:
                bot.edit_message_text(
                    text=updated_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="HTML",
                    reply_markup=call.message.reply_markup
                )
        except Exception as e:
            print(f"Error updating message text directly: {e}")

        try:
            bot.answer_callback_query(call.id, f"✅ تم تسجيل صوتك بنجاح يا {user_first_name}!")
        except Exception:
            pass
        return

    # الرد السريع لجميع الأزرار الداخلية لمنع علامة التحميل المعلقة
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    try:
        if data == "cmd_create":
            if call.message.chat.type == "private":
                contest_creation_state[user_id] = {"step": 1}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
                text = (
                    "🐾 <b>[ إنشاء مسابقة / تصويت شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>معرف القناة أو القروب أو رابطهما الكامل</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
            else:
                contest_creation_state[user_id] = {"step": 2, "channel": chat_id}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="cmd_home"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة / تصويت شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص المسابقة أو سؤال التصويت</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_2":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 2
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة / تصويت شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص المسابقة أو سؤال التصويت</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "mention_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["mention_option"] = True
                proceed_to_prize_step(user_id, chat_id, message_id)

        elif data == "mention_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["mention_option"] = False
                proceed_to_prize_step(user_id, chat_id, message_id)

        elif data == "has_prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 6
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إدراج صورة المسابقة/التصويت ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>صورة الهدية أو الجائزة أو التصميم</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "has_prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_media"] = None
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "cmd_end":
            if call.message.chat.type != "private":
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
                bot.send_message(chat_id, "⛔ <b>تم إنهاء المسابقة وحذف منشورها!</b> 🐾", parse_mode="HTML")
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
                text = (
                    "⛔ <b>[ إنهاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي <b>معرف أو رابط القناة/القروب</b> المراد حذف مسابقتها:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "cmd_id_help" or data == "cmd_id_help_sub":
            if data == "cmd_id_help":
                user_search_mode[chat_id] = False
                help_text = (
                    "⚡ <b>قسم البحث والاستخراج المتقدم</b> 🐾\n\n"
                    "اختر الطريقة المناسبة لجلب البيانات بسرعة وسلاسة:"
                )
                markup = create_id_help_menu_markup()
            else:
                help_text = (
                    "💡 <b>طريقة جلب المعرف:</b>\n\n"
                    "قم بتحويل أي رسالة للبوت أو أرسل المعرف مباشرة."
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="cmd_home"))
            
            update_or_send_panel(chat_id, help_text, markup)

        elif data == "show_keyboard":
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "📂 <b>[ لوحة الاختيار السريع ]</b>\n\n"
                "👇 استخدم لوحة المفاتيح السفلية الظاهرة لديك الآن:",
                create_navigation_markup("cmd_id_help")
            )
            try:
                bot.send_message(chat_id, "👇 لوحة الاختيار السفلية:", reply_markup=create_dynamic_reply_keyboard())
            except Exception:
                pass

        elif data == "method_forward":
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "📥 <b>[ تحليل الرسائل المحولة ]</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "🐾 قم بإعادة توجيه أي رسالة هنا لاستخراج بياناتها بدقة!",
                create_navigation_markup("cmd_id_help")
            )

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
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:",
                create_main_menu_markup()
            )

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            try:
                bot.send_message(chat_id, "❌ تم إغلاق القائمة.", reply_markup=types.ReplyKeyboardRemove())
            except Exception:
                pass
            update_or_send_panel(
                chat_id,
                "❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.",
                None
            )

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


def proceed_to_prize_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 5
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
        )
        markup.row(
            types.InlineKeyboardButton("✅ نعم (إرفاق صورة)", callback_data="has_prize_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="has_prize_no")
        )
        text = (
            "🐾 <b>[ سؤال 4: إرفاق جائزة أو صورة ]</b> 🐱✨\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "هل تريد إدراج <b>صورة أو وسائط</b> مع رسالة المسابقة/التصويت في القناة؟"
        )
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


# ==========================================
# **دالة نشر المسابقة في القناة أو القروب مع التثبيت**
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
        
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    button_text = state_data.get("button_text", "تصويت / مشاركة 🏆")
    mention_option = state_data.get("mention_option", False)
    prize_media = state_data.get("prize_media")
    
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID in publish: {e}")

    final_text = (
        f"🎉 <b>مسابقة / تصويت شركس التفاعلي!</b> 🐾\n\n"
        f"❓ <b>السؤال / النص:</b>\n{announcement}\n\n"
        f"👥 عدد الأصوات: <b>0</b>\n"
        f"📋 قائمة المصوتين: <i>لا يوجد أصوات حتى الآن</i>"
    )

    cb_data_str = f"part_cb_active"

    channel_markup = types.InlineKeyboardMarkup()
    channel_markup.add(types.InlineKeyboardButton(button_text, callback_data=cb_data_str))

    try:
        if prize_media:
            sent_msg = bot_instance.send_photo(target_chat_id, prize_media, caption=final_text, parse_mode="HTML", reply_markup=channel_markup)
        else:
            sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="HTML", reply_markup=channel_markup)
        
        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception as pin_err:
            print(f"Pin message error (make sure bot is admin): {pin_err}")

        bot_instance.edit_message_text("✅ <b>تم نشر المسابقة وتثبيتها في الوجهة المحددة بنجاح تام!</b> 🐾", chat_id, message_id, parse_mode="HTML")
    except Exception as e:
        bot_instance.edit_message_text(f"⚠️ تعذر النشر، تأكد من صلاحيات البوت في القناة أو القروب: {e}", chat_id, message_id, parse_mode="HTML")


# ==========================================
# **معالجة خطوات إنشاء المسابقة والأسئلة**
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
        resolved_channel_id = text_content
        if "t.me/" in text_content:
            parts = text_content.split("t.me/")[-1].split("?")[0].strip("/")
            if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                resolved_channel_id = f"@{parts}"

        try:
            chat_obj = bot.get_chat(resolved_channel_id)
            resolved_channel_id = chat_obj.id
        except Exception as e:
            print(f"Could not resolve channel for ending: {e}")

        end_contest_state.pop(user_id, None)
        update_or_send_panel(
            chat_id,
            f"⛔ <b>تم إيقاف معالجة إنهاء المسابقة للقناة المحددة.</b> 🐾",
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
                chat_obj = bot.get_chat(resolved_channel_id)
                resolved_channel_id = chat_obj.id
            except Exception as e:
                print(f"Could not resolve chat from link: {e}")

            state_data["channel"] = resolved_channel_id
            state_data["step"] = 2

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
            text = (
                "🐾 <b>[ سؤال 1: نص المسابقة أو التصويت ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>نص المسابقة أو السؤال المراد نشره</b>:"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
            text = (
                "🐾 <b>[ سؤال 2: اسم زر المشاركة / التصويت ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "ما هو النص الذي تريد أن يظهر على <b>الزر الشفاف</b>؟ (مثال: تصويت 🗳️ أو مشاركة 🏆):"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 3:
            state_data["button_text"] = text_content
            state_data["step"] = 4
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم (إرفاق منشن للمشارك)", callback_data="mention_yes"),
                types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_no")
            )
            text = (
                "🐾 <b>[ سؤال 3: خيار المنشن ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تريد إرفاق <b>منشن لاسم الشخص</b> في رسالة القناة عندما يضغط على زر التصويت/المشاركة؟"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, parse_mode="HTML", reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 6:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = None
            finalize_and_publish_contest(bot, chat_id, target_message_id, user_id)
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
