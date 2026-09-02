# ==========================================
# **بوتي شركس - النسخة الكاملة والمستقرة (بدون أي نقص)**
# ==========================================
import os
import time
import threading
import uuid
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
active_contest_messages = {}  # {chat_id: message_id}


# ==========================================
# **خادم الويب للحفاظ على نشاط البوت على Render**
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
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية", callback_data="cmd_create"),
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

def format_unified_report(name, username, user_id, account_type):
    clean_name = name if name and name != "None" and str(name).strip() != "" else "جهة مختارة"
    username_line = ""
    if username and str(username).strip() != "" and str(username).lower() != "none":
        formatted_un = username if str(username).startswith("@") else f"@{username}"
        username_line = f"username: {formatted_un}\n"

    return (
        f"🐾 <b>[ بطاقة شركس الذكية ]</b> 🐱✨\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{username_line}"
        f"👤 <b>الاسم:</b> {clean_name}\n"
        f"id: <code>{user_id}</code>\n"
        f"📌 <b>نوع الحساب:</b> {account_type}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>نظام شركس السريع لخدمتكم!</i>"
    )

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
        "البوت الأنيق والسريع لإدارة وحماية مجموعاتك وقنواتك بكل احترافية.\n"
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

    # **نظام تسجيل المشاركة المستقر داخل رسالة القناة/القروب**
    if data.startswith("part_cb_"):
        user_first_name = call.from_user.first_name or "المشارك"
        user_username = call.from_user.username
        
        if user_username:
            user_mention = f"@{user_username}"
        else:
            user_mention = f"<a href='tg://user?id={user_id}'>{user_first_name}</a>"
        
        current_text = call.message.text or call.message.caption or ""
        
        # منع تكرار المشاركة بفحص الآيدي أو المنشن داخل نص الرسالة المنشورة
        user_tag_identifier = f"id:{user_id}"
        if user_tag_identifier in current_text or user_mention in current_text:
            try:
                bot.answer_callback_query(call.id, f"⚠️ عذراً يا {user_first_name}\nلقد شاركت في هذه المسابقة مسبقاً! 🚫", show_alert=True)
            except Exception:
                pass
            return

        # إضافة المشارك الجديد مباشرة لكي يثبت في نص الرسالة ولا يضيع بنوم البوت
        new_participant_line = f"\n▫️ {user_mention} (<code>id:{user_id}</code>)"
        
        updated_text = current_text
        if "<b>قائمة المشاركين:</b>" in updated_text:
            updated_text = updated_text.replace("<b>قائمة المشاركين:</b>", f"<b>قائمة المشاركين:</b>{new_participant_line}")
        else:
            updated_text += f"\n\n<b>قائمة المشاركين:</b>{new_participant_line}"

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
            
            bot.answer_callback_query(call.id, f"✅ تم تسجيل مشاركتك بنجاح يا {user_first_name}!", show_alert=True)
        except Exception as e:
            print(f"Error updating channel/group message: {e}")
            try:
                bot.answer_callback_query(call.id, "✅ تم تسجيل مشاركتك بنجاح!", show_alert=True)
            except Exception:
                pass
        return

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    try:
        # خطوات إنشاء المسابقة الكاملة
        if data == "cmd_create":
            if call.message.chat.type == "private":
                contest_creation_state[user_id] = {"step": 1}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس ]</b> 🐱✨\n"
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
                    "🐾 <b>[ إنشاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>سؤال أو نص المسابقة</b>:"
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
                    "🐾 <b>[ إنشاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>سؤال أو نص المسابقة</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "has_prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 3.5
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إدراج الجائزة ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>تفاصيل الهدية أو الجائزة</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "has_prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize"] = None
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        # إنهاء المسابقة
        elif data == "cmd_end":
            if call.message.chat.type != "private":
                target_chat = chat_id
                if target_chat in active_contest_messages:
                    try:
                        m_id = active_contest_messages[target_chat]
                        bot.delete_message(target_chat, m_id)
                        active_contest_messages.pop(target_chat, None)
                    except Exception as e:
                        print(f"Error deleting contest message: {e}")
                
                bot.edit_message_text(
                    "⛔ <b>تم إنهاء المسابقة وحذف منشورها بنجاح!</b> 🐾",
                    chat_id, message_id, parse_mode="HTML"
                )
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
                text = (
                    "⛔ <b>[ إنهاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي <b>معرف أو رابط القناة/القروب</b> المراد إنهاء مسابقتها:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "calc_results_yes" or data == "calc_results_no":
            if user_id in end_contest_state:
                state_end = end_contest_state.get(user_id, {})
                channel_target = state_end.get("channel")
                
                if channel_target and channel_target in active_contest_messages:
                    try:
                        m_id = active_contest_messages[channel_target]
                        bot.delete_message(channel_target, m_id)
                        active_contest_messages.pop(channel_target, None)
                    except Exception as e:
                        print(f"Error deleting contest message: {e}")

                end_contest_state.pop(user_id, None)
                update_or_send_panel(
                    chat_id,
                    "⛔ <b>تم إنهاء المسابقة وحذف منشورها بنجاح تام!</b> 🐾",
                    create_main_menu_markup()
                )

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


# ==========================================
# **دالة نشر المسابقة في القناة أو القروب**
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
        
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    prize = state_data.get("prize")
    
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID in publish: {e}")

    final_text = f"🎉 <b>مسابقة شركس التفاعلية!</b> 🐾\n\n❓ <b>السؤال / النص:</b>\n{announcement}"
    if prize:
        final_text += f"\n\n🎁 <b>الجائزة:</b> {prize}"
    
    final_text += "\n\n<b>قائمة المشاركين:</b>\n<i>(لم يبدأ أحد بالمشاركة بعد)</i>"

    unique_key = str(uuid.uuid4())[:8]
    channel_markup = types.InlineKeyboardMarkup()
    channel_markup.add(types.InlineKeyboardButton("مشاركة بالمسابقة 🏆", callback_data=f"part_cb_{unique_key}"))

    try:
        sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="HTML", reply_markup=channel_markup)
        active_contest_messages[target_chat_id] = sent_msg.message_id
        bot_instance.edit_message_text("✅ <b>تم نشر المسابقة وزر الاشتراك في الوجهة المحددة بنجاح تام!</b> 🐾", chat_id, message_id, parse_mode="HTML")
    except Exception as e:
        bot_instance.edit_message_text(f"⚠️ تعذر النشر، تأكد من صلاحيات البوت في القناة أو القروب: {e}", chat_id, message_id, parse_mode="HTML")


# ==========================================
# **معالجة الرسائل والخطوات النصية الكاملة**
# ==========================================
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    chat_id = message.chat.id
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    target_id = None
    is_chat = False
    
    if message.users_shared:
        try:
            raw_target = message.users_shared.user_ids[0]
            target_id = raw_target.user_id if hasattr(raw_target, "user_id") else raw_target
        except Exception:
            target_id = message.users_shared.user_ids[0]
    elif message.chat_shared:
        target_id = message.chat_shared.chat_id
        is_chat = True

    if target_id:
        try:
            chat_info = bot.get_chat(target_id)
            uname = getattr(chat_info, 'username', None)
            if is_chat:
                name = getattr(chat_info, 'title', 'قناة أو مجموعة')
                acc_type = "قناة عامة" if chat_info.type == "channel" else "مجموعة تفاعلية"
            else:
                first = getattr(chat_info, 'first_name', '') or ''
                last = getattr(chat_info, 'last_name', '') or ''
                name = f"{first} {last}".strip() or "مستخدم تيليجرام"
                acc_type = "حساب بوت رسمي" if getattr(chat_info, 'is_bot', False) else "مستخدم شخصي"

            report_text = format_unified_report(name, uname, chat_info.id, acc_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
        except Exception:
            fallback_type = "مجموعة أو قناة" if is_chat else "مستخدم شخصي"
            report_text = format_unified_report("جهة مختارة", None, target_id, fallback_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))

@bot.message_handler(chat_types=["private", "supergroup", "group"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handler_private_and_group_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_group = message.chat.type in ["supergroup", "group"]
    text_content = message.text.strip() if message.text else ""

    if is_group:
        if text_content in ["إنشاء مسابقة", "إنهاء المسابقة"]:
            try:
                member_status = bot.get_chat_member(chat_id, user_id)
                if member_status.status not in ["creator", "administrator"]:
                    return
            except Exception:
                return

            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass

            if text_content == "إنشاء مسابقة":
                contest_creation_state[user_id] = {"step": 2, "channel": chat_id}
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="cmd_home"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>سؤال أو نص المسابقة</b>:"
                )
                sent = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
                last_panel_message[chat_id] = sent.message_id
                return
            elif text_content == "إنهاء المسابقة":
                if chat_id in active_contest_messages:
                    try:
                        m_id = active_contest_messages[chat_id]
                        bot.delete_message(chat_id, m_id)
                        active_contest_messages.pop(chat_id, None)
                    except Exception as e:
                        print(f"Error deleting contest message: {e}")
                
                sent = bot.send_message(chat_id, "⛔ <b>تم إنهاء المسابقة وحذف منشورها بنجاح!</b> 🐾", parse_mode="HTML")
                last_panel_message[chat_id] = sent.message_id
                return
        return

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    target_message_id = last_panel_message.get(chat_id)

    # معالجة خطوات إنهاء المسابقة من الخاص
    if user_id in end_contest_state:
        state = end_contest_state[user_id]
        step = state.get("step", 1)

        if step == 1:
            raw_input_text = text_content
            resolved_channel_id = raw_input_text
            
            if "t.me/" in raw_input_text:
                parts = raw_input_text.split("t.me/")[-1].split("?")[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved_channel_id = f"@{parts}"

            try:
                chat_obj = bot.get_chat(resolved_channel_id)
                resolved_channel_id = chat_obj.id
            except Exception as e:
                print(f"Could not resolve channel for ending: {e}")

            state["channel"] = resolved_channel_id
            state["step"] = 2

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم (حذف المسابقة وإنهائها)", callback_data="calc_results_yes"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="calc_results_no")
            )
            text = (
                "⛔ <b>[ إنهاء المسابقة ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل أنت متأكد من رغبتك في <b>إنهاء مسابقة هذه القناة/القروب وحذف منشورها نهائياً؟</b>"
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

    # معالجة خطوات إنشاء المسابقة الكاملة (الأسئلة والنصوص)
    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)

        if step == 1:
            raw_input_text = text_content
            resolved_channel_id = raw_input_text
            
            if "t.me/" in raw_input_text:
                parts = raw_input_text.split("t.me/")[-1].split("?")[0].strip("/")
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
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>سؤال أو نص المسابقة</b>:"
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
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="has_prize_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="has_prize_no")
            )
            text = (
                "🐾 <b>[ إدراج جائزة ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تريد إدراج <b>هدية أو جائزة</b> لهذه المسابقة؟"
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

        elif step == 3.5:
            state_data["prize"] = text_content if text_content else "[هدية مميزة]"
            finalize_and_publish_contest(bot, chat_id, target_message_id, user_id)
            return

    # معالجة الرسائل المحولة واستخراج المعرفات
    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        if message.forward_from:
            user = message.forward_from
            uname = user.username if user.username else None
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            acc_type = "حساب بوت رسمي" if user.is_bot else "مستخدم شخصي"
            report_text = format_unified_report(name, uname, user.id, acc_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
            return
        elif message.forward_from_chat:
            chat = message.forward_from_chat
            uname = chat.username if chat.username else None
            acc_type = "قناة عامة" if chat.type == "channel" else "مجموعة تفاعلية"
            report_text = format_unified_report(chat.title, uname, chat.id, acc_type)
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
            return
        elif message.forward_sender_name:
            report_text = format_unified_report(message.forward_sender_name, None, "غير متاح", "مستخدم شخصي (مخفي الهوية)")
            update_or_send_panel(chat_id, report_text, create_navigation_markup("cmd_id_help"))
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
