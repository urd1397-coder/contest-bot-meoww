import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 🛠️ قراءة توكن البوت والمنفذ السحابي إجبارياً لإرضاء سيرفر Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# 👑 تثبيت هويتك الموثقة كمطور ومالك رسمي للبوت
OWNER_ID = 79636720007  
OWNER_USERNAME = "@z7xxq" 

# 🚀 إيقاظ محرك البوت للاستماع الصاروخي للأوامر
bot = telebot.TeleBot(BOT_TOKEN)

# 💾 القواميس السحابية (الخزنات المؤقتة) لتتبع الفعاليات والخطوات لاحقاً
user_states = {}
channel_contests = {}

# 🪐 دالة استقبال أمر /start بصيغة حيوية ومبهرة بنظام HTML
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "انت من ايقظني 🙀 ؟\n\n"
        "يا أهلاً يا غالي! أنا <b>شركس</b> بوت المسابقات والفعاليات المتكاملة واللطيفة! 🐾🎈\n\n"
        "🚀 مهمتي زرع الحماس في الأجواء ومساعدتك على إشعال التحديات والتصويت، وأيضاً <b>أستطيع جلب وإحضار أرقام التعريف (الآيديات) الخاصة بالأشخاص والقنوات والجروبات تلقائياً!</b> 😎🪐\n\n"
        "👉 لطفاً أرسل أمر <b>/help</b> لعرض كافة الأكواد وسحري المتاح! 😸✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

# 📋 دالة قائمة المساعدة المصلحة بنظام HTML الآمن كلياً
@bot.message_handler(commands=['help'])
def handle_help(message):
    commands_text = (
        "😸 <b>إليك قائمة أوامر شركس السحرية المتاحة حالياً:</b>\n\n"
        "➕ /create — لبدء إنشاء مسابقة جديدة داخل قناتك 🎯\n"
        "🔍 /id_help — لتحصيل وقشط آيدي أي قناة أو شخص تلقائياً بالتوجيه مجاناً 📡\n"
        "🏁 /end — إنهاء المسابقة الحالية واحتساب الأصوات وإعلان الفائزين 🏆\n"
        "❌ /cancel — لإلغاء أي عملية جارية وتصفير الخطوات 🫧"
    )
    bot.reply_to(message, commands_text, parse_mode="HTML")

# =========================================================================
# 🌐 خادم الويب (Web Server) الصامت لفتح المنفذ وإرضاء فحص ريندر الأمني وحل المشكلة
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Port is open! Cherkes is listening to Telegram.")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()
    
    # 🕵️‍♂️ أمر جلب وتحصيل الآيدي الشامل والمفتوح (قنوات، مجموعات، وأشخاص) للعامة مجاناً
@bot.message_handler(commands=['id_help'])
def cmd_id_help(message):
    user_id = message.from_user.id
    # تفعيل الخطوة السحرية في الذاكرة لتشغيل الدالة المكتوبة أسفلها بلقطة الشاشة
    user_states[user_id] = {"step": "get_any_id_only"}
    
    guide_text = (
        "🔍 <b>مرحباً بك في حارس الآيديات الشامل والمجاني لشركس!</b>\n\n"
        "👉 <b>طرق تحصيل وقشط آيدي أي حساب (شخص، قناة، أو جروب):</b>\n"
        "1️⃣ <b>طريقة التوجيه:</b> قم بعمل <b>توجيه (Forward)</b> لأي رسالة، صورة، أو رابط من الحساب المستهدف وأرسلها لي هنا فوراً!\n"
        "2️⃣ <b>طريقة المعرف:</b> أرسل لي <b>اليوزر نيم</b> الخاص بالحساب مباشرة هنا (مثال: <code>@z7xxq</code>).\n\n"
        "🚀 سأقوم بقشط واستخراج الآيدي الرقمي المخفي في أجزاء من الثانية مجاناً وببلّاش! 🐾\n"
        "❌ <i>لإلغاء العملية أرسل: /cancel أو كلمة الغاء</i>"
    )
    bot.reply_to(message, guide_text, parse_mode="HTML")

# 📥 ملتقط الخطوات الذكي لمعالجة النصوص والميديا الموجهة أو اليوزرات المدخلة مع تنبيه فوري
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "get_any_id_only", 
                     content_types=['text', 'photo', 'video', 'document', 'animation'])
def process_any_id_fetching(message):
    user_id = message.from_user.id
    input_text = message.text.strip() if message.text else ""
    
    # 🚨 صمام حماية الإلغاء المطلق الفوري في مرحلة جلب الآيدي
    if input_text in ["/cancel", "الغاء"]:
        if user_id in user_states: user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 تم إلغاء عملية جلب الآيدي بنجاح وتصفير الخطوات معاً! 🐾")
        return

    # ⏳ إرسال التنبيه الفوري الحركي في محادثة البوت لتأكيد بدء القشط السحري
    loading_msg = bot.reply_to(message, "⏳ <b>جاري قشط وتحصيل البيانات السحرية الآن... لطفاً انتظر ثانية واحدة!</b> 🐾", parse_mode="HTML")

    # المسار 1️⃣: إذا قام المستخدم بعمل توجيه (Forward) حقيقي لأي نوع ميديا أو نص
    if message.forward_from_chat:
        fetched_id = message.forward_from_chat.id
        source_type = "قناة / مجموعة سوبر"
        fetched_name = message.forward_from_chat.title or "معرف سحابي سري"
        fetched_username = f"@{message.forward_from_chat.username}" if message.forward_from_chat.username else "لا يوجد"
    elif message.forward_from:
        fetched_id = message.forward_from.id
        source_type = "حساب شخصي (أشخاص)"
        fetched_name = message.forward_from.first_name or "مستخدم"
        fetched_username = f"@{message.forward_from.username}" if message.forward_from.username else "لا يوجد"
    
    # المسار 2️⃣: إذا كتب المستخدم يوزر نيم فقط لقناة أو شخص أو قروب (يبدأ بـ @)
    elif input_text.startswith('@'):
        try:
            # استخدام دالة البحث الداخلي لتليجرام لجلب الكائن من المعرف النصي
            chat_info = bot.get_chat(input_text)
            fetched_id = chat_info.id
            fetched_username = input_text
            
            if chat_info.type in ['channel', 'supergroup', 'group']:
                source_type = f"قناة / جروب (عبر اليوزر)"
                fetched_name = chat_info.title or "عنوان سحابي"
            else:
                source_type = "حساب شخصي (عبر اليوزر)"
                fetched_name = chat_info.first_name or "مستخدم"
        except Exception:
            try: bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
            except Exception: pass
            bot.reply_to(message, "❌ <b>لم أستطع العثور على هذا المعرف!</b> تأكد من كتابة اليوزر نيم بشكل صحيح، أو أن الحساب عام وليس سرياً تماماً.")
            return
    else:
        # مسح رسالة التحميل المؤقتة في حال حدوث خطأ إدخال
        try: bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
        except Exception: pass
        
        # حماية في حال قفل خصوصية التوجيه للأشخاص
        if message.forward_sender_name:
            bot.reply_to(message, f"⚠️ <b>المستخدم المقصد قفل خصوصية التوجيه في حسابه!</b>\n👤 الاسم الظاهر: <code>{message.forward_sender_name}</code>\n\n💡 <i>بسبب أمان تليجرام، جرب إرسال اليوزر نيم الخاص به مبدوءاً بـ @ لأقشط آيديه تلقائياً!</i>", parse_mode="HTML")
            user_states.pop(user_id, None)
            return
        else:
            bot.reply_to(message, "⚠️ لطفاً، قم بعمل <b>توجيه (Forward)</b> لرسالة أو ميديا من الحساب، أو أرسل <b>اليوزر نيم</b> مبدوءاً بـ @ (مثال: <code>@z7xxq</code>).")
            return

    # صياغة لوحة البيانات الفخمة المستخرجة بنظام HTML والنسخ بلمسة واحدة <code>
    success_text = (
        f"✅ <b>تم تحصيل وقشط بيانات الحساب بنجاح باهر!</b>\n\n"
        f"📡 <b>نوع المصدر:</b> {source_type}\n"
        f"👤 <b>الاسم والعنوان:</b> {fetched_name}\n"
        f"🎫 <b>معرف الحساب:</b> {fetched_username}\n"
        f"🆔 <b>الآيدي الرقمي المستخرج:</b> <code>{fetched_id}</code>\n\n"
        f"👉 <i>اضغط على الآيدي الرقمي بالأعلى لنسخه بلمسة واحدة واستخدامه في حمايتك!</i> 🪐"
    )
    
    # حذف رسالة الجاري التحميل وبث النتيجة الصافية الفخمة مكان الطلب فوراً
    try: bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
    except Exception: pass
    
    bot.reply_to(message, success_text, parse_mode="HTML")
    user_states.pop(user_id, None) # تطهير ذاكرة خطوة المستخدم الحالية فوراً
# 🌐 خادم الويب (Web Server) الصامت لفتح المنفذ وإرضاء فحص ريندر الأمني وحل المشكلة
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Port is open! Cherkes is listening to Telegram.")

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), MyServer)
    server.serve_forever()
# ➕ أمر بدء إنشاء مسابقة تفاعلية مخصصة بالكامل (Customizable Callback)
@bot.message_handler(commands=['create'])
def cmd_create_contest(message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "get_channel_target"}
    
    guide_create = (
        "📢 <b>مرحباً بك في وحدة إنشاء المسابقات الذكية لشركس!</b>\n\n"
        "👉 <b>أرسل لي الآن معرف أو آيدي القناة المراد بث المسابقة داخلها:</b>\n"
        "• <b>التعيين اليدوي:</b> اكتب معرف القناة العام هنا (مثال: <code>@my_channel</code>).\n"
        "• <b>التوجيه التلقائي الفخم:</b> إذا كنت لا تعرف الآيدي السري، قم بعمل <b>توجيه (Forward)</b> لأي رسالة قديمة من قناتك هنا فوراً وأنا سأتكفل بالباقي وقشط المعرف تلقائياً! 📡🐾\n\n"
        "❌ <i>لإلغاء العملية في أي وقت أرسل: /cancel أو كلمة الغاء</i>"
    )
    bot.reply_to(message, guide_create, parse_mode="HTML")

# 📥 ملتقط الرسائل لتتبع خطوات هندسة وإنشاء الفعالية بالكامل خطوة بخطوة
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") in ["get_channel_target", "get_contest_banner", "get_custom_alert_text", "ask_attach_username"])
def process_contest_creation_steps(message):
    user_id = message.from_user.id
    input_text = message.text.strip() if message.text else ""
    state = user_states.get(user_id, {})
    current_step = state.get("step")

    # 🚨 صمام حماية الإلغاء المطلق الفوري لكسر خطوة الإنشاء المعلقة
    if input_text in ["/cancel", "الغاء"]:
        if user_id in user_states: user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 تم إلغاء عملية إنشاء المسابقة وتصفير الخطوات بنجاح! 🐾")
        return

    # 1️⃣ [الخطوة الأولى]: استخراج وقشط معرف القناة سواء بالتوجيه أو الكتابة اليدوية
    if current_step == "get_channel_target":
        if message.forward_from_chat:
            target_channel = message.forward_from_chat.id
        else:
            target_channel = input_text
            if target_channel.replace('-', '').isdigit():
                target_channel = int(target_channel)

        # التحقق الأمني الأولي من رتبة وصلاحية الأدمن داخل القناة المستهدفة
        try:
            member = bot.get_chat_member(target_channel, user_id)
            if member.status in ['creator', 'administrator'] or int(user_id) == 79636720007:
                user_states[user_id] = {"step": "get_contest_banner", "channel": target_channel}
                bot.reply_to(message, "✅ <b>تم التحقق من الصلاحيات السحابية بنجاح!</b>\n\n📝 أرسل لي الآن <b>نص ومنشور المسابقة الفخم</b> الذي سيتم بثه وعرضه للأعضاء في القناة:")
            else:
                bot.reply_to(message, "❌ عذراً! الكود كشف أنك لست مسؤولاً (Admin) في هذه القناة حالياً ولا تملك صلاحية الإدارة.")
                user_states.pop(user_id, None)
        except Exception:
            bot.reply_to(message, "⚠️ <b>البوت لم يستطع جلب بيانات القناة!</b> تأكد من إضافة البوت كـ مسؤول (Admin) داخل القناة أولاً ومنحه صلاحية نشر الرسائل، ثم أعد إرسال المعرف أو التوجيه:")
        return

    # 2️⃣ [الخطوة الثانية]: استلام منشور المسابقة والانتقال لتخصيص رسالة الزر
    elif current_step == "get_contest_banner":
        if not message.text:
            bot.reply_to(message, "⚠️ لطفاً، أرسل منشور المسابقة كـ نص مكتوب:")
            return
        
        user_states[user_id]["banner"] = message.text
        user_states[user_id]["step"] = "get_custom_alert_text"
        
        guide_alert = (
            "⚙️ <b>نظام لوحة التحكم التفاعلية المخصصة (Customizable Callback)</b>\n\n"
            "📝 أرسل لي الآن <b>الرسالة والنص المخصص</b> الذي ترغب in أن يرسله البوت في القناة كـ تنبيه فوري كلما قام عضو بالضغط على زر الاشتراك المشتعل:\n"
            "*(مثال: انضم للتحدي وبدأ التصويت له علناً، صوتوا له بالأسفل!)* 👇"
        )
        bot.reply_to(message, guide_alert, parse_mode="HTML")
        return

    # 3️⃣ [الخطوة الثالثة]: استلام نص التنبيه المخصص والسؤال عن إرفاق اليوزر نيم
    elif current_step == "get_custom_alert_text":
        if not message.text:
            bot.reply_to(message, "⚠️ لطفاً، أرسل نص التنبيه المخصص كـ نص مكتوب:")
            return
            
        user_states[user_id]["custom_alert"] = message.text
        user_states[user_id]["step"] = "ask_attach_username"
        
        # إنشاء أزرار تفاعلية فورية للسؤال (نعم / لا)
        markup_ask = InlineKeyboardMarkup()
        markup_ask.add(
            InlineKeyboardButton("✅ نعم، ارفق اليوزر", callback_data="attach_yes"),
            InlineKeyboardButton("❌ لا، بدون يوزر", callback_data="attach_no")
        )
        bot.reply_to(message, "❓ <b>هل تود أن يقوم شركس بإرفاق ودمج المعرف النصي (@username) الخاص بالعضو تلقائياً داخل رسالة التنبيه المخصصة؟</b>", reply_markup=markup_ask, parse_mode="HTML")
        return

# 🎯 معالجة ضغط أزرار تخصيص اليوزر وبث المسابقة الفعلية داخل القناة المستهدفة
@bot.callback_query_handler(func=lambda call: call.data.startswith("attach_"))
def handle_customize_username_and_broadcast(call):
    user_id = call.from_user.id
    state = user_states.get(user_id, {})
    
    if not state or state.get("step") != "ask_attach_username":
        bot.answer_callback_query(call.id, text="⚠️ انتهت صلاحية الجلسة أو تم إلغاؤها مسبقاً.")
        return
        
    attach_choice = call.data.replace("attach_", "")
    channel_id = state["channel"]
    contest_banner = state["banner"]
    custom_alert = state["custom_alert"]
    
    # حفظ خيار إرفاق اليوزر داخل سجل المسابقة لهذه القناة في الذاكرة
    channel_contests[channel_id] = {
        "config": {
            "custom_alert": custom_alert,
            "attach_username": (attach_choice == "yes")
        },
        "participants": {} # تجهيز مصفوفة فارغة لاستقبال المشتركين الجدد والـ Reactions
    }
    
    # تصميم زر الاشتراك الذكي المانع للتكرار الموجه للقناة
    markup_contest = InlineKeyboardMarkup()
    markup_contest.add(InlineKeyboardButton("🎯 إشتراك 🎯", callback_data=f"join_{channel_id}"))
    
    try:
        # بث المسابقة الرسمية داخل القناة بنجاح
        bot.send_message(chat_id=channel_id, text=f"🌌 <b>مسابقة جديدة في قناة درب التبانة!</b> 🏆\n\n{contest_banner}", reply_markup=markup_contest, parse_mode="HTML")
        
        # تعديل رسالة الأدمن لتأكيد الإطلاق الصاروخي وتصفير حالته بسلام
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🚀 <b>طيييييرااان! تم تصميم وبث مسابقتك التفاعلية المخصصة بنجاح ساحق داخل القناة: {channel_id}!</b>\n\n🫧 <i>تنبيهات الأزرار المخصصة أصبحت حية وشغالة الآن!</i>",
            parse_mode="HTML"
        )
    except Exception:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ <b>فشل بث المسابقة برمجياً!</b> تأكد من أن البوت ما زال مسؤولاً داخل القناة ويمتلك رتبة كافية لنشر الرسائل المدمجة بالأزرار أولاً.",
            parse_mode="HTML"
        )
        channel_contests.pop(channel_id, None)
        
    user_states.pop(user_id, None) # تصفير وتطهير خطوة الأدمن الحالية فوراً

# 🎯 معالجة ضغط زر "🎯 اشتراك 🎯" من الأعضاء بدون استثناء وبث رسالة التنبيه المخصصة بالملي
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def handle_user_subscription(call):
    channel_id = call.data.replace("join_", "")
    user_id = call.from_user.id
    username = call.from_user.username
    first_name = call.from_user.first_name
    
    # تحويل معرف القناة لرقم مجرد أو نص متطابق حسب الخزنة
    if str(channel_id).replace('-', '').isdigit():
        channel_id = int(channel_id)
        
    if channel_id not in channel_contests:
        bot.answer_callback_query(call.id, text="❌ عذراً، لا توجد مسابقة نشطة مسجلة لهذه القناة حالياً.", show_alert=True)
        return
        
    contest_node = channel_contests[channel_id]
    
    # منع التكرار البرمجي الصارم: فحص هل الحساب مسجل مسبقاً في قائمة المشتركين
    if user_id in contest_node["participants"]:
        bot.answer_callback_query(call.id, text="عذراً، أنت مسجل في هذه الفعالية بالفعل ولا يمكنك الاشتراك مرتين! 🐾", show_alert=True)
        return
        
    registered_count = len(contest_node["participants"]) + 1
    user_mention = f"@{username}" if username else first_name
    
    # قراءة لوحة الإعدادات المخصصة التي صممها الأدمن للمسابقة بالملي
    config = contest_node["config"]
    custom_alert_text = config["custom_alert"]
    should_attach_user = config["attach_username"]
    
    # صياغة التنبيه المخصص: دمج اليوزر نيم إذا اختار الأدمن "نعم"، أو إرسال النص بمفرده
    if should_attach_user:
        final_alert_msg = f"🔥 <b>المتسابق رقم {registered_count}: {user_mention} {custom_alert_text}</b>\n\n⭐ <i>كل نجمة مدفوعة = صوتين | وأي ريأكشن عادي = صوت واحد 🐾</i>"
    else:
        final_alert_msg = f"🔥 <b>المتسابق رقم {registered_count}: {custom_alert_text}</b>\n\n⭐ <i>كل نجمة مدفوعة = صوتين | وأي ريأكشن عادي = صوت واحد 🐾</i>"
        
    try:
        # بث رسالة التنبيه المخصصة الفردية داخل القناة المستهدفة لجمع الأصوات والتفاعلات
        vote_msg = bot.send_message(chat_id=channel_id, text=final_alert_msg, parse_mode="HTML")
        
        # حفر بيانات المشترك وربط آيدي رسالته الفردية بـ عداد الأصوات للمستقبل
        contest_node["participants"][vote_msg.message_id] = {
            "user_id": user_id,
            "mention": user_mention,
            "votes": 0
        }
        bot.answer_callback_query(call.id, text="🎉 تم تسجيل انضمامك بنجاح وبث رسالة تصويتك المخصصة داخل القناة! انطلق! 🚀", show_alert=False)
    except Exception:
        bot.answer_callback_query(call.id, text="⚠️ فشل بث رسالة تصويتك، تأكد من صلاحيات البوت الإدارية بالقناة أولاً.", show_alert=True)

# 🔍 تتبع التفاعلات وحساب الأصوات آلياً بنظام العدالة الشاملة وحماية الـ CPU
@bot.message_reaction_handler()
def handle_contest_reactions(message_reaction):
    chat_id = message_reaction.chat.id
    message_id = message_reaction.message_id
    
    if channel_id := next((ch for ch in channel_contests if ch == chat_id or f"@{bot.get_chat(ch).username}" == f"@{message_reaction.chat.username}"), None):
        if message_id in channel_contests[channel_id]["participants"]:
            competitor = channel_contests[channel_id]["participants"][message_id]
            voter_id = message_reaction.user.id if message_reaction.user else None
            if not voter_id: return

            # 1️⃣ نجوم تليجرام المدفوعة: مفتوحة للجميع وصوتين (2) على كل نجمة
            paid_stars_count = 0
            if message_reaction.new_reaction:
                for r in message_reaction.new_reaction:
                    if getattr(r, 'type', None) == 'paid':
                        paid_stars_count += getattr(r, 'count', 1)
            competitor["votes"] += (paid_stars_count * 2)

            # 2️⃣ التفاعلات العادية: صوت واحد مجاني (1) فقط لكل بصمة مستخدم (الجميع متساوٍ)
            has_regular_reaction = False
            if message_reaction.new_reaction:
                for r in message_reaction.new_reaction:
                    if getattr(r, 'type', None) != 'paid':
                        has_regular_reaction = True
                        break

            if has_regular_reaction:
                if voter_id not in competitor["voted_users"]:
                    competitor["voted_users"].add(voter_id)
                    competitor["votes"] += 1

            # 🚨 حامي شركس الذكي للذاكرة والـ CPU عند حد الـ 1000 صوت
            if competitor["votes"] >= 1000:
                alert_text = (
                    f"🚨 <b>تنبيه حامي شركس السحابي لحفظ التقدم!</b> 🚨\n\n"
                    f"🔥 المتسابق الفخم: {competitor['mention']} حرق العداد ووصل لحد الذاكرة المؤقتة المسموح!\n"
                    f"⭐️ <b>حصد حالياً:</b> <code>1000</code> صوت من النجوم والتفاعلات الحية.\n\n"
                    f"💬 <b>البوت بيقولكم:</b>\n"
                    f"<i>\"أوف تعبت يرحم أبوك هدي ههههه.. فلان حصل 1000 نجمة يعني 2000 صوت رجاءً من المشرفين التثبيت!\"</i> 😾💨\n\n"
                    f"📌 <b>يا أدمنز يا فخمين:</b> ثبتوا هذه الرسالة فوراً لتوثيق نقاطه بسلام!\n"
                    f"🫧 <i>تم تصفير عداد الذاكرة للمتسابق لتخفيف الحمل عن الـ CPU ومتابعة صعود الحماس بأمان!</i>"
                )
                try: bot.send_message(chat_id=channel_id, text=alert_text, parse_mode="HTML")
                except Exception: pass
                competitor["votes"] = competitor["votes"] % 1000

# 🏁 أمر إنهاء الفعالية وفرز حساب الفائزين الفوري
@bot.message_handler(commands=['end'])
def cmd_end_contest_trigger(message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "end_get_contest_msg"}
    guide_text = (
        "🏁 <b>مرحباً بك في وحدة حساب الفائزين لشركس!</b>\n\n"
        "👉 <b>كل ما عليك فعله الآن لحساب النتائج:</b>\n"
        "قم بعمل <b>توجيه (Forward)</b> لرسالة المسابقة الأساسية نفسها التي تحتوي على زر الاشتراك وأرسلها لي هنا فوراً!\n\n"
        "❌ <i>لإلغاء العملية أرسل: /cancel أو كلمة الغاء</i>"
    )
    bot.reply_to(message, guide_text, parse_mode="HTML")

# ❌ أمر إلغاء العمليات الجارية المطور والمحمي بصلاحيات ورتب الإنتاج والإدارة
@bot.message_handler(commands=['cancel'])
def cmd_global_cancel(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, {})
    current_step = state.get("step")
    
    if not current_step:
        bot.reply_to(message, "😸 لا توجد أي عملية جارية حالياً في حسابك لإلغائها، البوت مستقر وجاهز!")
        return

    if current_step == "get_any_id_only":
        user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 <b>تم إلغاء عملية جلب الآيدي بنجاح وتصفير الخطوات معاً!</b>", parse_mode="HTML")
        return
    else:
        channel_target = state.get("channel")
        if int(user_id) == 79636720007:
            user_states.pop(user_id, None)
            bot.reply_to(message, "🫧 <b>أهلاً بالمطور الأعلى! تم إلغاء عملية إنشاء المسابقة وتطهير الذاكرة فوراً!</b>", parse_mode="HTML")
            return
        if channel_target:
            try:
                member = bot.get_chat_member(channel_target, user_id)
                if member.status in ['creator', 'administrator']:
                    user_states.pop(user_id, None)
                    bot.reply_to(message, "🫧 <b>تم إلغاء عملية إنشاء المسابقة وتصفير الخطوات بنجاح من قِبَل المشرف!</b>", parse_mode="HTML")
                else:
                    bot.reply_to(message, "⚠️ <b>عذراً! لا تملك صلاحية إرسال أمر إلغاء لهذه المسابقة الخاصة بالإدارة.</b>", parse_mode="HTML")
            except Exception:
                user_states.pop(user_id, None)
                bot.reply_to(message, "🫧 تم التراجع وإلغاء الجلسة المعلقة بنجاح.")
        else:
            user_states.pop(user_id, None)
            bot.reply_to(message, "🫧 تم إلغاء العملية الجارية وتصفير خطوات البدء بسلام.")

# =========================================================================
# 🏁 جذع التشغيل الحتمي الموحد والوحيد الذي يغلق الملف بالكامل في القاع إجبارياً
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري فتح المنافذ وتشغيل شركس بنمط الاستماع المباشر الصافي المطور...")
    bot.infinity_polling()
