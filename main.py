# ==========================================
# 1. إعداد المتغيرات والاتصال
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


# ==========================================
# 2. خادم الويب ومسار الأمان
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    """خادم ويب بسيط للتحقق من عمل البوت على منصات الاستضافة."""
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
    """تشغيل خادم الويب في خلفية النظام."""
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# ==========================================
# 3. لوحات المفاتيح والأزرار التفاعلية
# ==========================================
def create_navigation_markup(back_callback="cmd_id_help"):
    """1. إنشاء لوحة التنقل والرجوع للقوائم السابقة."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_main_menu_markup():
    """2. إنشاء أزرار القائمة الرئيسية للبوت."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث الشامل ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    """3. إنشاء أزرار قسم البحث واستخراج المعرفات."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع للأعضاء والجهات", callback_data="show_keyboard"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة الذكي", callback_data="method_forward"),
        types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    """4. إنشاء لوحة مفاتيح ريبلاي سفلية لاختيار المستخدمين والمجموعات."""
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
    """5. تنسيق تقرير البطاقة الموحدة لعرض تفاصيل الحسابات."""
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
    """6. تحديث رسالة اللوحة الحالية لمنع تراكم الرسائل، أو إرسال واحدة جديدة."""
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
# 4. معالجة الأوامر ورسائل البدء
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    """7. معالجة أمر البداية /start وإرسال القائمة الرئيسية."""
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
# 5. معالجة الأزرار والردود المتسلسلة للمسابقات
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    """8. معالجة كافة تفاعلات الأزرار الشفافة Inline وتحكم خطوات المسابقات."""
    chat_id = call.message.chat.id 
    user_id = call.from_user.id
    data = call.data
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    try:
        if data == "cmd_create":
            contest_creation_state[user_id] = {"step": 1}
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(types.InlineKeyboardButton("❓ لا أعرف كيف أجلب الآيدي (مساعدة)", callback_data="cmd_id_help_sub"))
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 1/6 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>رابط أو معرف (Username) القناة</b> المستهدفة للنشر:"
            )
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_1":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 1
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 1/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>رابط أو معرف (Username) القناة</b> المستهدفة للنشر:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_2":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 2
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_1"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 2/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص إعلان المسابقة</b> الذي سيعرض للمشاركين:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_3":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 3
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 3/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تريد إضافة <b>رابط أو تفاصيل جائزة</b> للمسابقة؟"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_4":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 4
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 4/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>رابط الجائزة أو الصورة المرفقة</b> لعرضها ضمن تفاصيل المسابقة:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "step_back_5":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 5
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_4"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 5/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>المنشن أو اسم المُشارِك/الحساب</b> لإضافته في المسابقة (أو اكتب 'لا' لتخطي ذلك):"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "cmd_end":
            bot.answer_callback_query(call.id, "هذه الميزة الرائعة قيد التطوير حالياً 🚧", show_alert=True)

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
                    "💡 <b>طريقة جلب معرف القناة أو الآيدي:</b>\n\n"
                    "1. قم بتحويل أي رسالة من القناة إلى البوت هنا، وسيعطيك الآيدي فوراً.\n"
                    "2. أو أرسل معرف القناة مباشرة مثل: <code>@ChannelName</code>"
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⬅️ رجوع لإنشاء المسابقة", callback_data="step_back_1"))
            
            update_or_send_panel(chat_id, help_text, markup)

        elif data == "show_keyboard":
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "📂 <b>[ لوحة الاختيار السريع للأعضاء والجهات ]</b>\n\n"
                "👇 استخدم لوحة المفاتيح السفلية الظاهرة لديك الآن لاختيار مستخدم أو مجموعة، وسأعرض لك بطاقته هنا فوراً 🚀",
                create_navigation_markup("cmd_id_help")
            )
            try:
                bot.send_message(
                    chat_id, 
                    "👇 لوحة الاختيار السفلية:", 
                    reply_markup=create_dynamic_reply_keyboard()
                )
            except Exception:
                pass

        elif data == "method_username":
            user_search_mode[chat_id] = True
            update_or_send_panel(
                chat_id,
                "🌐 <b>[ وضع البحث اليدوي والروابط والقنوات ]</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "✍️ أرسل الآن اليوزر المطلوب (مثل `@username`)، رابط القناة، أو معرفها وسأقوم بجلب تفاصيلها فوراً 🚀",
                create_navigation_markup("cmd_id_help")
            )

        elif data == "method_forward":
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "📥 <b>[ وضع تحليل الرسائل المحولة ]</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "🐾 قم بإعادة توجيه أي رسالة من أي شخص أو قناة هنا لاستخراج بياناتها بدقة!",
                create_navigation_markup("cmd_id_help")
            )

        elif data == "has_prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 4
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 4/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>رابط الجائزة أو الصورة المرفقة</b> لعرضها ضمن تفاصيل المسابقة:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "has_prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_link"] = None
                contest_creation_state[user_id]["step"] = 5
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 5/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>المنشن أو اسم المُشارِك/الحساب</b> لإضافته في المسابقة (أو اكتب 'لا' لتخطي ذلك):"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "mention_skip":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["mention"] = None
                contest_creation_state[user_id]["step"] = 6
                
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_4"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                markup.row(
                    types.InlineKeyboardButton("✅ نعم، أضف زر مشاركة تفاعلي", callback_data="btn_yes"),
                    types.InlineKeyboardButton("❌ لا، بدون زر", callback_data="btn_no")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة الأخيرة 6/6 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تريد إرفاق <b>زر تفاعلي للمشاركة</b> أسفل رسالة المسابقة في القناة؟"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data in ["btn_yes", "btn_no"]:
            if user_id in contest_creation_state:
                state_data = contest_creation_state.pop(user_id, None)
                channel = state_data.get("channel", "@Channel")
                announcement = state_data.get("announcement", "مسابقة جديدة!")
                prize_link = state_data.get("prize_link")
                mention = state_data.get("mention")
                
                final_text = f"🎉 <b>مسابقة شركس الجديدة!</b> 🐾\n\n{announcement}"
                if mention:
                    formatted_mention = mention if mention.startswith("@") else f"@{mention}"
                    final_text += f"\n\n👤 <b>المُشارِك/المنشن:</b> {formatted_mention}"
                if prize_link:
                    final_text += f"\n\n🎁 <b>رابط/تفاصيل الجائزة:</b> {prize_link}"

                channel_markup = None
                if data == "btn_yes":
                    channel_markup = types.InlineKeyboardMarkup()
                    channel_markup.add(types.InlineKeyboardButton("🏆 اضغط هنا للمشاركة (تفاعل) 🐾", callback_data="participate_click"))

                try:
                    bot.send_message(channel, final_text, parse_mode="HTML", reply_markup=channel_markup)
                    bot.edit_message_text("✅ <b>تم إنشاء ونشر المسابقة بنجاح في القناة!</b> 🐾", chat_id, message_id, parse_mode="HTML")
                except Exception as e:
                    bot.edit_message_text(f"⚠️ تعذر النشر في القناة تأكد من صلاحيات البوت: {e}", chat_id, message_id, parse_mode="HTML")

        elif data == "participate_click":
            bot.answer_callback_query(call.id, "🐾 تم تسجيل مشاركتك بنجاح في المسابقة! بالتوفيق 🚀", show_alert=True)

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            user_search_mode[chat_id] = False
            update_or_send_panel(
                chat_id,
                "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:",
                create_main_menu_markup()
            )

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            try:
                bot.send_message(chat_id, "❌ تم إغلاق القائمة.", reply_markup=types.ReplyKeyboardRemove())
            except Exception:
                pass
            update_or_send_panel(
                chat_id,
                "❌ تم إغلاق القائمة بنجاح. أرسل /start في أي وقت لإظهارها مجدداً.",
                None
            )

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# 6. معالجة الرسائل المحولة والخاصة
# ==========================================
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    """9. معالجة مشاركة المستخدمين أو المجموعات عبر لوحة المفاتيح الأصلية."""
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
            if isinstance(raw_target, dict):
                target_id = raw_target.get("user_id")
            elif hasattr(raw_target, "user_id"):
                target_id = raw_target.user_id
            else:
                target_id = raw_target
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

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handler_private_messages(message):
    """10. معالجة الرسائل الواردة في المحادثة الخاصة (الرسائل المحولة وإدخال خطوات المسابقات الست)."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)
        text_content = message.text.strip() if message.text else ""

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        if step == 1:
            state_data["channel"] = text_content
            state_data["step"] = 2
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_1"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 2/6 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>نص إعلان المسابقة</b> الذي سيعرض للمشاركين:"
            )
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
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
                types.InlineKeyboardButton("✅ نعم، توجد جائزة", callback_data="has_prize_yes"),
                types.InlineKeyboardButton("❌ لا، بدون جائزة", callback_data="has_prize_no")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 3/6 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تريد إضافة <b>رابط أو تفاصيل جائزة</b> للمسابقة؟"
            )
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 4:
            state_data["prize_link"] = text_content
            state_data["step"] = 5
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(types.InlineKeyboardButton("⏭️ تخطي المنشن", callback_data="mention_skip"))
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 5/6 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>المنشن أو اسم المُشارِك/الحساب</b> لإضافته في المسابقة (أو اضغط تخطي):"
            )
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            return

        elif step == 5:
            if text_content.lower() in ["لا", "تخطي", "no", "-"]:
                state_data["mention"] = None
            else:
                state_data["mention"] = text_content
                
            state_data["step"] = 6
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_4"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم، أضف زر مشاركة تفاعلي", callback_data="btn_yes"),
                types.InlineKeyboardButton("❌ لا، بدون زر", callback_data="btn_no")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة الأخيرة 6/6 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تريد إرفاق <b>زر تفاعلي للمشاركة</b> أسفل رسالة المسابقة في القناة؟"
            )
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            return

    # معالجة الرسائل المحولة لاستخراج البيانات
    if message.forward_from or message.forward_from_chat or message.forward_sender_name:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

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

    if message.text:
        text = message.text.strip()
        if text.startswith("/"):
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            return

        if not user_search_mode.get(chat_id, False):
            return

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass


# ==========================================
# 7. معالجة رسائل المجموعات والمشرفين
# ==========================================
@bot.message_handler(chat_types=["supergroup", "group"], content_types=["text"])
def handler_group_messages(message):
    """11. معالجة رسائل المجموعات والمشرفين عند طلب كلمة شركس."""
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""

    if text != "شركس":
        return

    try:
        member_status = bot.get_chat_member(chat_id, message.from_user.id)
        if member_status.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if message.reply_to_message:
        target_msg = message.reply_to_message
        target_user = target_msg.from_user
        
        if target_user:
            uname = target_user.username if target_user.username else None
            name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip()
            acc_type = "حساب بوت رسمي" if target_user.is_bot else "مستخدم شخصي"
            
            report_text = format_unified_report(name, uname, target_user.id, acc_type)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🎯 إنشاء مسابقة", callback_data="cmd_create"),
                types.InlineKeyboardButton("⛔ إنهاء المسابقة", callback_data="cmd_end")
            )
            
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
                
            update_or_send_panel(chat_id, report_text, markup)
            return

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة", callback_data="cmd_end")
    )
    
    menu_text = (
        "🐾 <b>[ لوحة إدارة المسابقات - شركس ]</b> 🐱✨\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "أهلاً بك يا مشرفنا العزيز! اختر الإجراء المطلوب:"
    )
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass
        
    update_or_send_panel(chat_id, menu_text, markup)


# ==========================================
# 8. تشغيل السيرفر وخوادم الـ Polling
# ==========================================
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"HTTP Server started on port %s" % PORT)
    
    time.sleep(2)
    
    # إيقاف أي اتصال قديم وتصفية التحديثات المعلقة لمنع تعارض الـ 409
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
