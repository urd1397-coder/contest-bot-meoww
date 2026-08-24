import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# 🛠️ قراءة توكن البوت والمنفذ السحابي من إعدادات خادم Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

# 👑 تثبيت هويتك الموثقة كمطور ومالك رسمي ونهائي للبوت
OWNER_ID = 79636720007  
OWNER_USERNAME = "@z7xxq" 

bot = telebot.TeleBot(BOT_TOKEN)

# قواميس الذاكرة المؤقتة السحابية لشركس
user_states = {}
channel_contests = {}  # {channel_id: {msg_id: {user_id: {"mention": x, "votes": 0}}}}

# 🪐 دالة استقبال أمر /start بصيغة حيوية ومبهرة
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "انت من ايقظني 🙀 ؟\n\n"
        "يا أهلاً يا غالي! أنا **شركس** بوت المسابقات والفعاليات المتكاملة واللطيفة! 🐾🎈\n\n"
        "🚀 مهمتي زرع الحماس في الأجواء ومساعدتك على إشعال التحديات والتصويت، وأيضاً <b>أستطيع جلب وإحضار أرقام التعريف (الآيديات) الخاصة بالأشخاص والقنوات والجروبات تلقائياً!</b> 😎🪐\n\n"
        "👉 لطفاً أرسل أمر <b>/help</b> لعرض كافة الأكواد وسحري المتاح! 😸✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

# 📋 معالج الأوامر الشامل والمحمي لضمان عمل كافة الكلمات والأكواد بسلام
@bot.message_handler(commands=['help', 'create', 'id_help', 'end', 'cancel'])
def handle_all_commands(message):
    user_id = message.from_user.id
    command = message.text.split()[0].lower()

    # 1️⃣ تشغيل قائمة المساعدة عند إرسال /help بنظام HTML الآمن
    if command == '/help':
        commands_text = (
            "😸 <b>إليك قائمة أوامر شركس السحرية المتاحة حالياً:</b>\n\n"
            "➕ /create — لبدء إنشاء مسابقة جديدة داخل قناتك 🎯\n"
            "🔍 /id_help — لتحصيل وقشط آيدي أي قناة أو شخص أو جروب مجاناً 📡\n"
            "🏁 /end — إنهاء المسابقة الحالية واحتساب الأصوات وإعلان الفائزين 🏆\n"
            "❌ /cancel — لإلغاء العمليات الجارية وتصفير الخطوات معاً 🫧"
        )
        bot.reply_to(message, commands_text, parse_mode="HTML")
        return

    # 2️⃣ تصفير الذاكرة السحابية فوراً عند إرسال أمر /cancel المطلق بدون شروط
    elif command == '/cancel':
        if user_id in user_states:
            user_states.pop(user_id, None)
            bot.reply_to(message, "🫧 <b>تم إلغاء العملية الجارية فوراً وتصفير الخطوات المعلقة وتطهير الذاكرة بنجاح!</b>", parse_mode="HTML")
        else:
            bot.reply_to(message, "😸 عذراً يا غالي، لا توجد أي عملية جارية حالياً في حسابك لإلغائها!")
        return

    # 3️⃣ أمر جلب وتحصيل الآيدي الشامل والمفتوح (قنوات، جروبات، أشخاص)
    elif command == '/id_help':
        user_states[user_id] = {"step": "get_any_id_only"}
        guide_text = (
            "🔍 <b>مرحباً بك في حارس الآيديات الشامل والمجاني لشركس!</b>\n\n"
            "👉 <b>كل ما عليك فعله الآن لمعرفة آيدي أي شيء:</b>\n"
            "1️⃣ اذهب إلى (القناة، المجموعة، أو محادثة الشخص المطلوبة).\n"
            "2️⃣ قم بعمل <b>توجيه (Forward)</b> لأي رسالة أو منشور منها وأرسلها لي هنا فوراً!\n\n"
            "🚀 سأقوم بقشط واستخراج الآيدي الرقمي المخفي في أجزاء من الثانية مجاناً وببلّاش! 🐾\n"
            "❌ <i>لإلغاء العملية أرسل: /cancel أو كلمة الغاء</i>"
        )
        bot.reply_to(message, guide_text, parse_mode="HTML")
        return

    # 4️⃣ أمر بدء إنشاء مسابقة جديدة في قناتك الفخمة
    elif command == '/create':
        user_states[user_id] = {"step": "get_channel_for_contest"}
        bot.reply_to(message, "📢 <b>أرسل لي معرف أو آيدي القناة التي تود إطلاق المسابقة فيها الآن:</b>\n*(مثال: <code>@my_channel</code> أو أرسل آيدي رقمي سري)*\n\n💡 <i>إذا كنت لا تعرف الآيدي، أرسل الغاء ثم استخدم أمر /id_help لمساعدتك!</i>", parse_mode="HTML")
        return

    # 5️⃣ أمر إنهاء المسابقة الذكي بطلب توجيه رسالة المسابقة نفسها
    elif command == '/end':
        user_states[user_id] = {"step": "end_get_contest_msg"}
        guide_text = (
            "🏁 <b>مرحباً بك في وحدة حساب الفائزين الذكية لشركس!</b>\n\n"
            "👉 <b>كل ما عليك فعله الآن لحساب النتائج:</b>\n"
            "1️⃣ اذهب إلى القناة التي تحتوي على الفعالية الجارية.\n"
            "2️⃣ قم بعمل <b>توجيه (Forward)</b> لرسالة المسابقة الأساسية نفسها وأرسلها لي هنا فوراً!\n\n"
            "🚀 سأقوم بقراءة بيانات القناة وحساب أصوات التفاعلات والنجوم بدقة تلقائية! 🏆\n"
            "❌ <i>لإلغاء العملية أرسل: /cancel أو كلمة الغاء</i>"
        )
        bot.reply_to(message, guide_text, parse_mode="HTML")
        return
# 📥 معالج الرسائل والنصوص المستقبلة لتتبع خطوات الأوامر (إنشاء، إنهاء، وجلب آيدي)
@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo', 'video', 'document', 'animation'])
def handle_steps_and_forwarding(message):
    user_id = message.from_user.id
    input_text = message.text.strip() if message.text else ""
    state = user_states.get(user_id, {})
    current_step = state.get("step")

    # 🚨 حماية الإلغاء المطلق الفوري بكلمة "الغاء" أو أمر التراجع في أي خطوة جارية
    if input_text in ["/cancel", "الغاء"]:
        if user_id in user_states: user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 <b>تم إلغاء العملية الجارية فوراً وتصفير الخطوات وتطهير الذاكرة السحابية بنجاح!</b>", parse_mode="HTML")
        return

    if not current_step:
        return

    # 🕵️‍♂️ [مرحلة id_help]: قشط الآيدي الشامل (قنوات، مجموعات، حسابات أشخاص) مجاناً للجميع
    if current_step == "get_any_id_only":
        if message.forward_from_chat:
            fetched_id = message.forward_from_chat.id
            source_type = "قناة/مجموعة" if message.forward_from_chat.type == "channel" else "مجموعة سوبر"
            fetched_name = message.forward_from_chat.title or "معرف سحابي"
        elif message.forward_from:
            fetched_id = message.forward_from.id
            source_type = "حساب شخصي (أشخاص)"
            fetched_name = message.forward_from.first_name or "مستخدم"
        else:
            if message.forward_sender_name:
                bot.reply_to(message, f"⚠️ <b>المستخدم المقصد قفل خصوصية التوجيه في حسابه!</b>\n👤 الاسم الظاهر: <code>{message.forward_sender_name}</code>\n\n💡 <i>بسبب أمان تليجرام، لا يمكن قشط آيدي الحسابات المقفلة إلا إذا كتب معرفه علناً.</i>", parse_mode="HTML")
                user_states.pop(user_id, None)
                return
            else:
                bot.reply_to(message, "⚠️ لطفاً، قم بعمل <b>توجيه (Forward)</b> حقيقي لرسالة من (قناة، جروب، أو شخص) لأقشط الآيدي، أو أرسل <code>الغاء</code>.")
                return

        success_text = (
            f"✅ <b>تم تحصيل وقشط الآيدي بنجاح باهر!</b>\n\n"
            f"📡 <b>نوع المصدر:</b> {source_type}\n"
            f"👤 <b>الاسم/العنوان:</b> {fetched_name}\n"
            f"🆔 <b>الآيدي الرقمي المستخرج:</b> <code>{fetched_id}</code>\n\n"
            f"👉 <i>انسخ الآيدي الرقمي الظاهر بالأعلى (بما في ذلك إشارة السالب -) واستخدمه بحرية!</i> 🪐"
        )
        bot.reply_to(message, success_text, parse_mode="HTML")
        user_states.pop(user_id, None)
        return

    # ➕ [مرحلة create]: فحص رتبة منشئ المسابقة ومعرف القناة المستهدفة
    elif current_step == "get_channel_for_contest":
        channel_user = input_text
        try:
            member = bot.get_chat_member(channel_user, user_id)
            if member.status in ['creator', 'administrator'] or int(user_id) == 79636720007:
                user_states[user_id] = {"step": "contest_text", "channel": channel_user}
                bot.reply_to(message, f"✅ <b>تم التحقق من صلاحيات الآدمن بنجاح!</b>\n📡 القناة المستهدفة: <b>{channel_user}</b>\n\n📝 أرسل لي الآن نص وعنوان المسابقة الفخم وعوامل التحدي:")
            else:
                bot.reply_to(message, "❌ عذراً! الكود كشف أنك لست مسؤولاً (Admin) في هذه القناة حالياً.")
                user_states.pop(user_id, None)
        except Exception:
            bot.reply_to(message, "⚠️ البوت لم يستطع جلب بيانات القناة! تأكد من كتابة المعرف بشكل صحيح وإضافة البوت كـ Admin بالداخل أولاً، ثم أعد إرساله.")
        return

    # 📝 [مرحلة create]: بث رسابقة المسابقة الأساسية المرفقة بزر "🎯 اشتراك 🎯"
    elif current_step == "contest_text":
        channel_id = state["channel"]
        contest_text = message.text
        
        channel_contests[channel_id] = {} # تصفير وتجهيز سجل الأصوات والمشتركين لهذه القناة
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎯 إشتراك 🎯", callback_data=f"join_{channel_id}"))
        
        try:
            bot.send_message(chat_id=channel_id, text=f"🌌 <b>مسابقة جديدة في قناة درب التبانة!</b> 🏆\n\n{contest_text}", reply_markup=markup, parse_mode="HTML")
            bot.reply_to(message, f"🚀 طييرااان! تم بث وتصميم رسالة المسابقة بنجاح في القناة {channel_id}!")
        except Exception:
            bot.reply_to(message, "❌ فشل بث المسابقة. تأكد من رتبة البوت كمسؤول داخل القناة أولاً مع صلاحية إرسال الرسائل.")
        user_states.pop(user_id, None)
        return

    # 🏁 [مرحلة end]: قشط آيدي القناة من منشور المسابقة الموجه لحساب النتائج
    elif current_step == "end_get_contest_msg":
        if message.forward_from_chat:
            channel_id = message.forward_from_chat.id
        else:
            bot.reply_to(message, "⚠️ أوه! هذه الرسالة ليست موجهة من القناة التي تحتوي على المسابقة. لطفاً وجه منشور المسابقة نفسه، أو أرسل <code>الغاء</code>.")
            return

        if channel_id not in channel_contests or not channel_contests[channel_id]:
            bot.reply_to(message, f"❌ <b>لا توجد مسابقة نشطة مسجلة في ذاكرة شركس لهذه القناة حالياً!</b>\n🆔 آيدي القناة المستخرج: <code>{channel_id}</code>", parse_mode="HTML")
            user_states.pop(user_id, None)
            return

        user_states[user_id] = {"step": "get_prizes_count", "channel": channel_id}
        bot.reply_to(message, "🔢 <b>كم عدد المراكز الفائزة المطلوبة؟</b>\n*(اكتب رقماً مجرداً واضغط إرسال، مثال: 3)* 👇\n\n❌ *أو أرسل الغاء للتراجع*")
        return

    # 🔢 [مرحلة end]: استقبال عدد المراكز تمهيداً لحساب الأصوات بالقسم الثالث
    elif current_step == "get_prizes_count":
        user_states[user_id]["prizes_text"] = input_text
        # نترك التنفيذ النهائي وحساب الفرز الفعلي للقسم الثالث لكي لا ينهار السيرفر
        return

# 🎯 التعامل مع ضغط زر "🎯 اشتراك 🎯" من قبل الأعضاء بدون استثناء وبث رسالة التصويت الفردية
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def handle_join(call):
    channel_id = call.data.replace("join_", "")
    user_id = call.from_user.id
    username = call.from_user.username
    first_name = call.from_user.first_name
    
    if channel_id not in channel_contests:
        channel_contests[channel_id] = {}
        
    # منع التكرار البرمجي الحازم: فحص هل الشخص مسجل مسبقاً في قائمة المشتركين لهذه القناة
    if any(user_id == msg_data["user_id"] for msg_data in channel_contests[channel_id].values()):
        bot.answer_callback_query(call.id, text="عذراً، أنت مسجل في المسابقة بالفعل ولا يمكنك الاشتراك مرتين! 🐾", show_alert=True)
        return
        
    registered_users_count = len(channel_contests[channel_id]) + 1
    user_mention = f"@{username}" if username else first_name
    
    # 🚀 تصميم وبث رسالة التصويت القصيرة الخاصة والمحددة لكل شخص بالملي كما طلبتها للمتعة والحماس
    vote_msg = bot.send_message(
        chat_id=channel_id,
        text=(
            f"🔥 <b>هل يستحق ؟ ({user_mention})</b>\n\n"
            f"🏅 المتسابق رقم {registered_users_count} انضم للتحدي المشتعل!\n"
            f"👇 صوتوا له الآن بالتفاعلات أسفل هذه الرسالة:\n"
            f"⭐ <b>كل نجمة مدفوعة = صوتين (2)</b>\n"
            f"👍 <b>وأي ريأكشن عادي مجاني = صوت واحد (1) فقط!</b>\n\n"
            f"🐾 <i>درب التبانة تشعل الحماس! بالتوفيق!</i>"
        ),
        parse_mode="HTML"
    )
    
    # حفر بيانات المشترك الجديد في سجل الأصوات آلياً لربطه بالـ Reactions
    channel_contests[channel_id][vote_msg.message_id] = {
        "user_id": user_id,
        "mention": user_mention,
        "votes": 0
    }
    bot.answer_callback_query(call.id, text="🎉 تم تسجيل انضمامك بنجاح وبث رسالة تصويتك الفردية في القناة! انطلق! 🚀", show_alert=False)
