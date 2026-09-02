# ==========================================
# 1. إعداد المتغيرات والاتصال والذاكرة المؤقتة
# ==========================================
import os
import time
import threading
import uuid
import sys
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
temp_button_storage = {}
end_contest_state = {}

# إجراء احترازي لحماية الذاكرة من الامتلاء عند كثرة الطلبات المفاجئة
MAX_MEMORY_ITEMS = 500

def check_memory_guard(chat_id):
    """فحص امتلاء الذاكرة المؤقتة وإعطاء عذر مؤقت سريع لحماية البوت من الحظر."""
    if len(temp_button_storage) > MAX_MEMORY_ITEMS or len(contest_creation_state) > MAX_MEMORY_ITEMS:
        try:
            bot.send_message(chat_id, "⚠️ جاري تحديث البيانات والذاكرة مؤقتاً، يرجى المحاولة بعد قليل...")
        except Exception:
            pass
        return True
    return False


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
    """تنقل القوائم السابقة."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔙 العودة للسابق", callback_data=back_callback),
        types.InlineKeyboardButton("🏠 الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_main_menu_markup():
    """القائمة الرئيسية للبوت."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 استخراج الآيدي والبحث الشامل ⚡", callback_data="cmd_id_help"),
        types.InlineKeyboardButton("🎯 إنشاء مسابقة تفاعلية", callback_data="cmd_create"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="cmd_cancel")
    )
    return markup

def create_id_help_menu_markup():
    """قسم البحث واستخراج المعرفات."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📂 لوحة الاختيار السريع للأعضاء والجهات", callback_data="show_keyboard"),
        types.InlineKeyboardButton("📥 تحليل الرسائل المحولة الذكي", callback_data="method_forward"),
        types.InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="cmd_home")
    )
    return markup

def create_dynamic_reply_keyboard():
    """لوحة مفاتيح سفلية لاختيار المستخدمين والمجموعات."""
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
    """تنسيق تقرير البطاقة الموحدة لعرض تفاصيل الحسابات."""
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
    """تحديث رسالة اللوحة الحالية لمنع تراكم الرسائل، أو إرسال واحدة جديدة."""
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
    """معالجة أمر البداية /start وإرسال القائمة الرئيسية."""
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
# 5. معالجة الأزرار التفاعلية (Inline Callbacks)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    """معالجة كافة تفاعلات الأزرار الشفافة واستمرار خطوات المسابقات والإنهاء."""
    chat_id = call.message.chat.id 
    user_id = call.from_user.id
    data = call.data
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id

    if check_memory_guard(chat_id):
        return

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
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 1/4 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>رابط القناة، أو معرفها (Username)، أو الآيدي</b> المستهدفة للنشر:"
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
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 1/4 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>رابط القناة، أو معرفها (Username)، أو الآيدي</b> المستهدفة للنشر:"
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
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 2/4 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص المسابقة</b>:"
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
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="has_prize_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="has_prize_no")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 3/4 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تريد إدراج <b>صورة أو رابط لجائزة</b>؟"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        # ==========================================
        # تسلسل زر إنهاء المسابقة والحساب الذكي
        # ==========================================
        elif data == "cmd_end":
            end_contest_state[user_id] = {"step": 1}
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            text = (
                "⛔ <b>[ إنهاء مسابقة شركس - الخطوة 1 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>رابط أو معرف القناة</b> المراد إنهاء المسابقة وحساب نتائجها:"
            )
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "calc_results_yes":
            if user_id in end_contest_state:
                end_contest_state[user_id]["calc_mode"] = True
                end_contest_state[user_id]["step"] = 3
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="diff_calc_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="diff_calc_no")
                )
                text = (
                    "📊 <b>[ إنهاء المسابقة - طريقة الحساب ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل للتفاعلات العادية أو المدفوعة (النجوم) <b>طريقة حساب مختلفة؟</b>\n"
                    "<i>(مثال: صوت للتفاعل العادي، وصوتان للنجمة المدفوعة)</i>"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "calc_results_no":
            if user_id in end_contest_state:
                # إذا كانت الإجابة لا، البوت ينهي المسابقة فوراً ويمسح الذاكرة
                end_contest_state.pop(user_id, None)
                temp_button_storage.clear()
                update_or_send_panel(
                    chat_id,
                    "⛔ <b>تم إنهاء المسابقة بنجاح دون حساب نتائج!</b>\nتم تفريغ الذاكرة بالكامل لتبدأ من الصفر 🐾",
                    create_main_menu_markup()
                )

        elif data == "diff_calc_yes" or data == "diff_calc_no":
            if user_id in end_contest_state:
                end_contest_state[user_id]["different_calc"] = (data == "diff_calc_yes")
                end_contest_state[user_id]["step"] = 4
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🔢 <b>[ إنهاء المسابقة - أصوات التفاعل العادي ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "كم عدد الأصوات التي يتم حسابها لكل <b>تفاعل عادي</b> (ريأكشن / إيموجي)؟\n"
                    "<i>أرسل الرقم عبر رسالة نصية (مثال: 1)</i>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "congrats_yes":
            if user_id in end_contest_state:
                end_contest_state[user_id]["want_congrats"] = True
                end_contest_state[user_id]["step"] = 7
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🎉 <b>[ إنهاء المسابقة - رسالة التهنئة ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>نص رسالة التهنئة النهائية</b> التي ستنشر في القناة أو القروب:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "congrats_no":
            if user_id in end_contest_state:
                # إنهاء المسابقة بالكامل وتفريغ الذاكرة للصفر
                end_contest_state.pop(user_id, None)
                temp_button_storage.clear()
                update_or_send_panel(
                    chat_id,
                    "🏆 <b>تم حساب النتائج وإنهاء المسابقة بنجاح!</b>\nتم مسح الذاكرة بالكامل وتصفير النظام 🐾",
                    create_main_menu_markup()
                )

        # ==========================================
        # باقي خيارات المسابقات والبحث
        # ==========================================
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
                    "2. أو أرسل معرف القناة مباشرة مثل: <code>@ChannelName</code> أو الآيدي الخاص بها."
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
                bot.send_message(chat_id, "👇 لوحة الاختيار السفلية:", reply_markup=create_dynamic_reply_keyboard())
            except Exception:
                pass

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
                contest_creation_state[user_id]["step"] = 3.5
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_2"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - إدراج الجائزة ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>صورة أو رابط الهدية</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "has_prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize"] = None
                contest_creation_state[user_id]["step"] = 4
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                markup.row(
                    types.InlineKeyboardButton("✅ نعم", callback_data="btn_add_yes"),
                    types.InlineKeyboardButton("❌ لا", callback_data="btn_add_no")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 4/4 ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "هل تود إضافة <b>زر تفاعلي للمشاركة</b>؟"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "btn_add_no":
            if user_id in contest_creation_state:
                state_data = contest_creation_state.pop(user_id, None)
                channel = state_data.get("channel", "@Channel")
                announcement = state_data.get("announcement", "مسابقة جديدة!")
                prize = state_data.get("prize")
                
                final_text = f"🎉 <b>مسابقة شركس الجديدة!</b> 🐾\n\n{announcement}"
                if prize:
                    final_text += f"\n\n🎁 <b>الجائزة:</b> {prize}"

                try:
                    bot.send_message(channel, final_text, parse_mode="HTML")
                    bot.edit_message_text("✅ <b>تم نشر المسابقة في القناة بنجاح!</b> 🐾", chat_id, message_id, parse_mode="HTML")
                except Exception as e:
                    bot.edit_message_text(f"⚠️ تعذر النشر في القناة تأكد من صلاحيات البوت: {e}", chat_id, message_id, parse_mode="HTML")

        elif data == "btn_add_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 4.1
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
                )
                text = (
                    "🐾 <b>[ إنشاء مسابقة شركس - تسمية الزر ]</b> 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن <b>النص أو التسمية التي ستظهر على الزر</b>:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)

        elif data == "mention_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["include_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["include_mention"] = False
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        # زر المشاركة الفعال والمصلح تماماً
        elif data.startswith("part_cb_"):
            action_id = data.replace("part_cb_", "")
            user_id_click = call.from_user.id
            user_first_name = call.from_user.first_name or "المشارك"
            
            stored_info = temp_button_storage.get(action_id, {"msg": "تم استلام مشاركتك!", "mention": True})
            
            text_response = stored_info["msg"]
            if stored_info["mention"]:
                user_mention = f'<a href="tg://user?id={user_id_click}">{user_first_name}</a>'
                alert_text = f"👤 أهلاً بك: {user_mention}\n\n{text_response}"
            else:
                alert_text = text_response
                
            bot.answer_callback_query(call.id, alert_text, show_alert=True)

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
                "❌ تم إغلاق القائمة بنجاح. أرسل /start في أي وقت لإظهارها مجدداً.",
                None
            )

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    """نشر المسابقة النهائية في القناة مع ربط الزر بـ temp_button_storage ليعمل بسلاسة."""
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
        
    channel = state_data.get("channel", "@Channel")
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    prize = state_data.get("prize")
    btn_text = state_data.get("button_text", "مشاركة بالمسابقة 🏆")
    btn_msg = state_data.get("button_msg", "تم تسجيل مشاركتك بنجاح!")
    include_mention = state_data.get("include_mention", True)
    
    final_text = f"🎉 <b>مسابقة شركس الجديدة!</b> 🐾\n\n{announcement}"
    if prize:
        final_text += f"\n\n🎁 <b>الجائزة:</b> {prize}"

    unique_key = str(uuid.uuid4())[:8]
    temp_button_storage[unique_key] = {
        "msg": btn_msg,
        "mention": include_mention
    }

    channel_markup = types.InlineKeyboardMarkup()
    channel_markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"part_cb_{unique_key}"))

    try:
        bot_instance.send_message(channel, final_text, parse_mode="HTML", reply_markup=channel_markup)
        bot_instance.edit_message_text("✅ <b>تم نشر المسابقة وزر التفاعل في القناة بنجاح!</b> 🐾", chat_id, message_id, parse_mode="HTML")
    except Exception as e:
        bot_instance.edit_message_text(f"⚠️ تعذر النشر في القناة تأكد من صلاحيات البوت: {e}", chat_id, message_id, parse_mode="HTML")


# ==========================================
# 6. معالجة الرسائل والخطوات النصية المتسلسلة
# ==========================================
@bot.message_handler(content_types=["users_shared", "chat_shared"])
def handle_shared_native_targets(message):
    """معالجة مشاركة المستخدمين أو المجموعات عبر لوحة المفاتيح الأصلية."""
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

@bot.message_handler(chat_types=["private"], content_types=["text", "photo", "video", "document", "audio", "voice", "sticker", "animation"])
def handler_private_messages(message):
    """معالجة الرسائل الخاصة لإنهاء المسابقة وخطوات إنشائها."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    target_message_id = last_panel_message.get(chat_id)

    # ==========================================
    # معالجة خطوات إنهاء المسابقة وسلسلة الأسئلة
    # ==========================================
    if user_id in end_contest_state:
        state = end_contest_state[user_id]
        step = state.get("step", 1)

        if step == 1:
            state["channel"] = text_content
            state["step"] = 2
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="calc_results_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="calc_results_no")
            )
            text = (
                "⛔ <b>[ إنهاء مسابقة شركس - حساب النتائج ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود من البوت <b>حساب النتائج وتحديد الفائزين</b> لهذه المسابقة؟"
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

        elif step == 4:
            state["normal_vote_count"] = text_content
            state["step"] = 5
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
            text = (
                "⭐ <b>[ إنهاء المسابقة - أصوات التفاعل المدفوع ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "كم عدد الأصوات لكل <b>تفاعل مدفوع (نجوم تيليجرام)</b>؟\n"
                "<i>أرسل الرقم عبر رسالة نصية (مثال: 2)</i>:"
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

        elif step == 5:
            state["paid_vote_count"] = text_content
            state["step"] = 6
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"))
            text = (
                "🏆 <b>[ إنهاء المسابقة - عدد الفائزين ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "كم عدد الفائزين المطلوب إعلاناً عنهم؟\n"
                "<i>أرسل رقماً صحيحاً (مثال: 1 أو 2 أو 3)</i>:"
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
            state["winners_count"] = text_content
            state["step"] = 6.5
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="congrats_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="congrats_no")
            )
            text = (
                "🎉 <b>[ إنهاء المسابقة - رسالة التهنئة ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرسال <b>رسالة تهنئة للفائزين</b> في القناة أو القروب؟"
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

        elif step == 7:
            state["congrats_text"] = text_content
            channel_target = state.get("channel", "@Channel")
            
            try:
                bot.send_message(channel_target, f"🎉 <b>تهنئة الفائزين بالمسابقة!</b>\n\n{text_content}", parse_mode="HTML")
            except Exception as e:
                print(f"Error sending congrats: {e}")

            # إنهاء كامل للمسابقة وتفريغ الذاكرة للصفر
            end_contest_state.pop(user_id, None)
            temp_button_storage.clear()
            
            update_or_send_panel(
                chat_id,
                "✅ <b>تم إنهاء المسابقة ونشر التهنئة بنجاح!</b>\nتمت تصصفية الذاكرة بالكامل والعودة للصفر 🐾",
                create_main_menu_markup()
            )
            return

    # ==========================================
    # معالجة خطوات إنشاء المسابقة الأصلية
    # ==========================================
    if user_id in contest_creation_state:
        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 1)

        if step == 1:
            state_data["channel"] = text_content
            state_data["step"] = 2
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_1"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 2/4 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>نص المسابقة</b>:"
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
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 3/4 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تريد إدراج <b>صورة أو رابط لجائزة</b>؟"
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
            state_data["prize"] = text_content if text_content else "[صورة الجائزة المرفقة]"
            state_data["step"] = 4
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم", callback_data="btn_add_yes"),
                types.InlineKeyboardButton("❌ لا", callback_data="btn_add_no")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - الخطوة 4/4 ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إضافة <b>زر تفاعلي للمشاركة</b>؟"
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

        elif step == 4.1:
            state_data["button_text"] = text_content if text_content else "مشاركة 🏆"
            state_data["step"] = 4.2
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - نص الرسالة عند الضغط ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن <b>النص أو التنبيه الذي سيتم إرساله وإظهاره</b> لكل شخص يضغط على الزر:"
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

        elif step == 4.2:
            state_data["button_msg"] = text_content if text_content else "تم تسجيل مشاركتك!"
            state_data["step"] = 4.3
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔙 رجوع", callback_data="step_back_3"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel")
            )
            markup.row(
                types.InlineKeyboardButton("✅ نعم (إرفاق منشن وترحيب)", callback_data="mention_yes"),
                types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_no")
            )
            text = (
                "🐾 <b>[ إنشاء مسابقة شركس - إرفاق المنشن ]</b> 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود <b>إرفاق منشن (إشارة ترحيبية)</b> باسم الشخص الذي ضغط على الزر داخل الرسالة؟"
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

    # معالجة الرسائل المحولة لاستخراج البيانات
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
# 7. معالجة رسائل المجموعات والمشرفين
# ==========================================
@bot.message_handler(chat_types=["supergroup", "group"], content_types=["text"])
def handler_group_messages(message):
    """معالجة رسائل المجموعات والمشرفين عند طلب كلمة شركس."""
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
