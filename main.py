import os
import telebot
import json
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer


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

# ==============================================================================
# 💾 [المحرك المحلي المطور للحراسة والثبات لأسابيع بملف JSON بمقاييس هندسية]
DATA_FILE = "contests_data.json"

def save_contests_to_storage():
    """حفر فوري لهوية الفعالية وأسماء المشتركين في ملف نصي ثابت لحمايتها ضد الريستارت"""
    try:
        serializable_data = {}
        for ch_id, c_data in channel_contests.items():
            # تحويل قائمة المسجلين (set) إلى قائمة عادية ومفاتيح الرسائل لنصوص ليقبل الـ JSON حفظها
            serializable_data[str(ch_id)] = {
                "config": c_data["config"],
                "participants": {str(m_id): p for m_id, p in c_data.get("participants", {}).items()},
                "registered_users": list(c_data.get("registered_users", []))
            }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=4)
        print("💾 [محلي] تم حفر لقطة الفعالية بنجاح وثبات كامل في ملف contests_data.json!")
    except Exception as e:
        print(f"❌ خطأ أثناء الحفظ المحلي للملف: {e}")

def load_contests_from_storage():
    """استرجاع فوري وتلقيم للذاكرة بمجرد نهوض السيرفر لتبدأ المسابقة من حيث توقفت"""
    global channel_contests
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            for ch_id_str, c_data in raw_data.items():
                # إعادة مفتاح القناة رقمياً ليفهمه كود تليجرام
                ch_id = int(ch_id_str) if ch_id_str.replace('-', '').isdigit() else ch_id_str
                
                # إعادة أرقام الرسائل إلى صيغة أرقام صحيحة (int) لتتطابق مع الـ msg_id عند الفرز
                restored_participants = {int(m_id): p for m_id, p in c_data.get("participants", {}).items() if m_id.isdigit()}
                
                channel_contests[ch_id] = {
                    "config": c_data["config"],
                    "participants": restored_participants,
                    "registered_users": set(c_data.get("registered_users", []))
                }
            print(f"📦 [محلي] تم تفكيك ملف الـ JSON وإعادة شحن {len(channel_contests)} فعالية للذاكرة بنجاح صخر!")
    except Exception as e:
        print(f"❌ خطأ أثناء استرجاع الذاكرة من ملف JSON: {e}")

# استدعاء فوري قسري عند الإقلاع والنهوض لتلقيم البوت بمخازنه
load_contests_from_storage()

# ==============================================================================

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


# 🕵️‍♂️ أمر جلب وتحصيل الآيدي الشامل والمفتوح (قنوات، مجموعات، وأشخاص) للعامة مجاناً
@bot.message_handler(commands=['id_help'])
def cmd_id_help(message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "get_any_id_only"}
    
    guide_text = (
        "🔍 <b>مرحباً بك في حارس الآيديات الشامل والمطور لشركس!</b>\n\n"
        "👉 <b>طرق تحصيل وقشط آيدي أي حساب (شخص، قناة، أو جروب):</b>\n"
        "1️⃣ <b>طريقة التوجيه:</b> قم بعمل <b>توجيه (Forward)</b> لأي رسالة، صورة، أو رابط من الحساب المستهدف وأرسلها لي هنا فوراً!\n"
        "2️⃣ <b>طريقة المعرف:</b> أرسل لي <b>اليوزر نيم</b> الخاص بالحساب مباشرة هنا (مثال: <code>@z7xxq</code>).\n\n"
        "🚀 سأقوم بقشط واستخراج الآيدي الرقمي المخفي في أجزاء من الثانية مجاناً وببلّاش! 🐾\n"
        "❌ <i>لإلغاء العملية أرسل: /cancel أو كلمة الغاء</i>"
    )
    bot.reply_to(message, guide_text, parse_mode="HTML")


# 📥 ملتقط الخطوات الفولاذي لفك الخصوصية وقشط معرفات اليوزر والقنوات فوراً
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "get_any_id_only", 
                     content_types=['text', 'photo', 'video', 'document', 'animation'])
def process_any_id_fetching(message):
    user_id = message.from_user.id
    input_text = message.text.strip() if message.text else ""
    
    if input_text in ["/cancel", "الغاء"]:
        if user_id in user_states: user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 تم إلغاء عملية جلب الآيدي بنجاح وتصفير الخطوات معاً! 🐾")
        return


    loading_msg = bot.reply_to(message, "⏳ <b>جاري قشط وتحصيل البيانات السحرية الآن... لطفاً انتظر ثانية واحدة!</b> 🐾", parse_mode="HTML")


    fetched_id = None
    source_type = "غير معروف"
    fetched_name = "معرف مخفي"
    fetched_username = "لا يوجد"


    # المسار 1: فحص التوجيه من القنوات والمجموعات السوبر
    if message.forward_from_chat:
        fetched_id = message.forward_from_chat.id
        source_type = "قناة / مجموعة سوبر"
        fetched_name = message.forward_from_chat.title or "معرف سحابي سري"
        fetched_username = f"@{message.forward_from_chat.username}" if message.forward_from_chat.username else "لا يوجد"
    
    # المسار 2: فحص التوجيه من حساب شخصي مفتوح الخصوصية
    elif message.forward_from:
        fetched_id = message.forward_from.id
        source_type = "حساب شخصي (أشخاص)"
        fetched_name = message.forward_from.first_name or "مستخدم"
        fetched_username = f"@{message.forward_from.username}" if message.forward_from.username else "لا يوجد"
    
    # المسار 3: فك التوجيه المقفل كلياً واختراق بصمة الكائن الممرر للحسابات المقفلة
    elif message.forward_sender_name:
        source_type = "حساب شخصي (خصوصية قوية مخفية)"
        fetched_name = message.forward_sender_name
        if message.entities:
            for entity in message.entities:
                if entity.type == 'text_mention' and entity.user:
                    fetched_id = entity.user.id
                    fetched_username = f"@{entity.user.username}" if entity.user.username else "لا يوجد"
                    fetched_name = entity.user.first_name


    # المسار 4: معالجة نصوص اليوزر نيم @ المكتوبة يدوياً للبحث الشامل والمفتوح
    if not fetched_id and input_text.startswith('@'):
        cleaned_username = input_text
        try:
            chat_info = bot.get_chat(cleaned_username)
            fetched_id = chat_info.id
            fetched_username = cleaned_username
            if chat_info.type in ['channel', 'supergroup', 'group']:
                source_type = f"قناة / جروب (عبر اليوزر)"
                fetched_name = chat_info.title or "عنوان سحابي"
            else:
                source_type = "حساب شخصي (عبر اليوزر)"
                fetched_name = chat_info.first_name or "مستخدم"
        except Exception:
            try:
                chat_info = bot.get_chat(cleaned_username.lower())
                fetched_id = chat_info.id
                fetched_username = cleaned_username.lower()
                source_type = "البحث السريع المطور"
                fetched_name = chat_info.title or "حساب عام"
            except Exception:
                pass


    # إذا عجزت كل المسارات تماماً عن فك التوجيه أو اليوزر نيم
    if not fetched_id:
        try: bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
        except Exception: pass
        if message.forward_sender_name:
            bot.reply_to(message, f"⚠️ <b>المستخدم المقصد قفل خصوصية التوجيه بالكامل في إعداداته!</b>\n👤 الاسم الظاهر: <code>{message.forward_sender_name}</code>\n\n💡 <i>بسبب أمان تليجرام الصارم، للحصول على آيديه اطلب منه إرسال أي رسالة عادية أو يوزر نيمه مبدوءاً بـ @ لأقشطه فوراً!</i>", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ <b>لم أستطع العثور على هذا المعرف أو قشطه!</b> تأكد من كتابة اليوزر نيم بشكل صحيح مبدوءاً بـ @، أو وجه رسالة حية صحيحة.")
        user_states.pop(user_id, None)
        return


    success_text = (
        f"✅ <b>تم تحصيل وقشط بيانات الحساب بنجاح صاروخي!</b>\n\n"
        f"📡 <b>نوع المصدر:</b> {source_type}\n"
        f"👤 <b>الاسم والعنوان:</b> {fetched_name}\n"
        f"🎫 <b>معرف الحساب:</b> {fetched_username}\n"
        f"🆔 <b>الآيدي الرقمي المستخرج:</b> <code>{fetched_id}</code>\n\n"
        f"👉 <i>اضغط على الآيدي الرقمي بالأعلى لنسخه بلمسة واحدة واستخدامه!</i> 🪐"
    )
    try: bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
    except Exception: pass
    bot.reply_to(message, success_text, parse_mode="HTML")
    user_states.pop(user_id, None)


# 📦 تخزين مؤقت لحالات منشئي المسابقات أثناء التجهيز
user_states = {}

@bot.message_handler(commands=['create'])
def cmd_create_contest(message):
    """الخطوة 0: فتح مرشد شركس التفاعلي فوراً والبدء بحيوية بدون حظر مسبق"""
    user_id = message.from_user.id
    chat_id = message.chat.id

    # فتح حالة التجهيز والربط بجروب الإطلاق فوراً وبحرية كاملة
    user_states[user_id] = {"step": "get_channel_target", "creator_id": user_id, "group_chat_id": chat_id}
    
    guide_msg = (
        "🪐 مياووو! أهلاً بك في عرين شركس لإطلاق المسابقات الأسطورية! 🐾🔥\n\n"
        "يسعدني جداً وبكل حماس بدء مسابقة جديدة تحت إشرافك، لكن لكي نربط البوابات أحتاج أولاً معرف القناة أو آيدي القناة المستهدفة! 📡\n\n"
        "💡 ارسل لي معرف قناتك المسبوق بـ @ (مثل @channel_name) أو الآيدي الرقمي تبعه.. أو ببساطة وجه لي أي منشور أو رسالة من القناة الحين وأنا سأتولى قشط المعرف وتأمين الاتصال بالباقي كلياً! 👇"
    )
    bot.reply_to(message, guide_msg)

@bot.message_handler(func=lambda msg: msg.from_user.id in user_states)
def process_contest_creation_steps(message):
    """المعالج المتتالي المطور: التقاط معطيات الفعالية وحفظها بمفتاح موحد صخر وتأمين الفحص الذكي"""
    user_id = message.from_user.id
    state = user_states[user_id]
    current_step = state["step"]
    input_text = message.text.strip() if message.text else ""

    # 🛑 خيار إلغاء العملية فوراً وبشكل قاطع ومنع التداخل
    if input_text.lower() in ["/cancel", "إلغاء"] or message.text == "إلغاء":
        user_states.pop(user_id, None)
        hide_markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "⚙️ تم إلغاء خطوات إنشاء المسابقة بطلبك، وتطهير غرف التجهيز بسلام كامل!", reply_markup=hide_markup)
        return

    # 📡 الخطوة 1: استلام المعرف ذكياً (سواء بالتوجيه، أو المعرف) وضبط صيغته الرقمية تلقائياً
    if current_step == "get_channel_target":
        target_channel = None
        if message.forward_from_chat:
            target_channel = message.forward_from_chat.id
        else:
            if not input_text:
                bot.reply_to(message, "❌ يرجى إرسال معرف قناة أو آيدي صحيح:")
                return
            target_channel = input_text

        try:
            # تنظيف المعرف وضبط صيغته الرقمية أو النصية بدقة بالغة لمنع انهيار الفحص
            if str(target_channel).replace('-', '').isdigit():
                cleaned_channel = int(target_channel)
                if cleaned_channel > 0:
                    cleaned_channel = int(f"-100{cleaned_channel}")
            else:
                cleaned_channel = target_channel if str(target_channel).startswith('@') else f"@{target_channel}"
            
            # 🔒 جدار حماية الصلاحيات التلقائي والنظيف 100% لأي مستخدم
            member_status = bot.get_chat_member(cleaned_channel, user_id).status
            if member_status not in ['administrator', 'creator']:
                bot.reply_to(message, "❌ عذراً يا بطل! تبين لي أن حسابك الحالي ليس مشرفاً أو مسؤولاً داخل هذه القناة المحددة! هالبوابة محصورة للآدمنز فقط! 🐾")
                user_states.pop(user_id, None)
                return
                
            state["target_channel"] = cleaned_channel
            state["step"] = "get_contest_text"
            bot.reply_to(message, "✅ كفو! تم التحقق من هويتك كمسؤول والتقاط القناة بنجاح! 🚀\n\n📝 الحين ارسل لي نص رسالة أو منشور المسابقة الفخم الذي تود بثه داخل القناة لكي نصنع زر الاشتراك أسفله:")
        except Exception as e:
            bot.reply_to(message, f"⚠️ لم أستطع فحص القناة! تأكد من إضافة البوت كمشرف أولاً داخل قناتك المحددة، ومن صحة المعرف المكتوب!\n\n🔍 الخطأ الفني: {e}")
        return

    elif current_step == "get_contest_text":
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال نص برمي واضح للمسابقة يا بطل!")
            return
        state["contest_text"] = input_text
        
        state["step"] = "get_custom_alert_choice"
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("نعم", "لا")
        bot.send_message(message.chat.id, "💬 السؤال الثالث والأهم: هل تحب إرفاق رسالة مخصصة يرسلها البوت تلقائياً في القناة كلما ضغط متسابق جديد على زر الاشتراك؟", reply_markup=markup)
        return

    elif current_step == "get_custom_alert_choice":
        if input_text == "نعم":
            state["step"] = "get_custom_alert_text"
            hide_markup = telebot.types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, "📝 على راسي! ارسل لي الحين الجملة أو الرسالة التنبيهية التي تريدني أن أبثها فوراً كلما انضم بطل جديد للسباق:", reply_markup=hide_markup)
        else:
            state["custom_alert_text"] = ""
            state["step"] = "get_username_choice"
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add("نعم", "لا")
            bot.send_message(message.chat.id, "👤 السؤال الرابع: هل تود إرفاق ومناداة اليوزر نيم الخاص بمن يضغط على الزر لتوجيه التحية له علناً؟", reply_markup=markup)
        return

    elif current_step == "get_custom_alert_text":
        state["custom_alert_text"] = input_text
        state["step"] = "get_username_choice"
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("نعم", "لا")
        bot.send_message(message.chat.id, "👤 السؤال الرابع: هل تود إرفاق ومناداة اليوزر نيم الخاص بمن يضغط على الزر لتوجيه التحية له علناً؟", reply_markup=markup)
        return

    elif current_step == "get_username_choice":
        include_username = True if input_text == "نعم" else False
        hide_markup = telebot.types.ReplyKeyboardRemove()
        
        target_channel = state["target_channel"]
        contest_text = state["contest_text"]
        custom_alert = state["custom_alert_text"]
        creator_id = state["creator_id"]
        group_chat_id = state["group_chat_id"]
        
        # 🔑 كسر قيد الـ 64 بايت لتليجرام: نربط المسابقة بمفتاح ثابت وقصير "live" دائماً لحمايتها من العبث!
        inline_markup = telebot.types.InlineKeyboardMarkup()
        btn_subscribe = telebot.types.InlineKeyboardButton("🎯 زر الاشتراك في الفعالية 🎯", callback_data="join_live")
        inline_markup.add(btn_subscribe)
        
        example_footer = (
            "\n\n━━━━━━━━━━━━━━━\n"
            "📊 ميزان شركس العادل لاحتساب النقاط:\n"
            "👍 الريأكشن العادي = صوت واحد فقط (ممنوع التكرار والغش).\n"
            "⭐ الريأكشن المدفوع (نجوم تليجرام) = صوتين (2) على كل نجمة لدعم متسابقك المفضل!"
        )
        
        full_post_text = contest_text + example_footer
        
        try:
            deployed_msg = bot.send_message(chat_id=target_channel, text=full_post_text, reply_markup=inline_markup)
            
            # حفر المسابقة تحت المفتاح الموحد "live" ليتطابق مع ضغطة زر المشتركين كلياً
            channel_contests["live"] = {
                "config": {
                    "status": "active",
                    "creator": creator_id,
                    "target_channel": target_channel,
                    "msg_id": deployed_msg.message_id,
                    "custom_alert": custom_alert,
                    "include_username": include_username
                },
                "registered_users": set(),
                "participants": {}
            }
            
            # تخزين فوري بالملف النصي JSON لحفظ ثبات الفعالية تماماً ضد الريستارت لأسابيع
            save_contests_to_storage()
            
            bot.send_message(message.chat.id, "🚀 مياووو! تم تفجير وإطلاق المسابقة بنجاح باهر داخل قناتك الحين!\n\nالبيانات محفورة في صخر ملف الـ JSON ولن تختفي مطلقاً بمسح الكاش، والتحكم بالفرز محصور عبر أمر /end الحاسم! انطلقوا! 🔥🐾", reply_markup=hide_markup)
            user_states.pop(user_id, None)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ حرج أثناء بث المنشور للقناة: {e}", reply_markup=hide_markup)
            user_states.pop(user_id, None)
        return


# 🎯 معالجة ضغط زر الاشتراك وبث رسالة التنبيه المخصصة وقفل التكرار
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def handle_user_subscription(call):
    """حارس الاشتراك الفولاذي: يكسر تعليق اللمبة قسرياً في أول سطر ويحمي المسابقة من التكرار والمطابق للـ JSON"""
    # ⚡ 1. إغلاق قسري فوري للمبة التحميل الدائرية على شاشة العضو في أول جزء من الثانية لمنع أي تعليق!
    bot.answer_callback_query(call.id)
    
    # التقاط مفتاح المسابقة النصي الموحد "live" ليتطابق مع الـ create
    group_chat_id = call.data.split("_")[1]
        
    if group_chat_id not in channel_contests:
        bot.send_message(call.message.chat.id, "⚠️ عذراً، لا توجد مسابقة نشطة حالياً مخصصة لهذا المفتاح!")
        return
        
    contest = channel_contests[group_chat_id]
    user_id = call.from_user.id
    raw_channel = contest["config"]["target_channel"]
    
    # 🛡️ جدار حظر الغش ومنع التكرار الصافي المتوافق مع ملف الـ JSON
    if "registered_users" not in contest or not isinstance(contest["registered_users"], list):
        contest["registered_users"] = []
        
    if user_id in contest["registered_users"]:
        bot.answer_callback_query(call.id, text="❌ أوه يا غالي! عذراً، أنت موجود بالمسابقة بالفعل ومستحيل تشترك مرتين! 🐾", show_alert=True)
        return

    # بناء هويات وبصمة المشترك الجديد بنص عادي صافي لتفادي أخطاء المارك داون
    first_name = call.from_user.first_name
    username = call.from_user.username
    
    if contest["config"]["include_username"] and username:
        user_mention = f"{first_name} (@{username})"
    else:
        user_mention = f"{first_name}"
        
    # قراءة التخصيص الكامل للرسالة الكستوم من الصفر حسب رغبة منشئ المسابقة
    custom_alert = contest["config"]["custom_alert"]
    if custom_alert:
        final_alert_msg = f"{custom_alert}\n\n👤 المتسابق: {user_mention}"
    else:
        final_alert_msg = f"🎯 متسابق جديد انضم للمسابقة الحين:\n\n👤 الحساب: {user_mention}"
        
    try:
        # بث منشور المتسابق داخل قناتك المستهدفة بسلام كامل
        vote_msg = bot.send_message(chat_id=target_channel, text=final_alert_msg)
        
        # حفر وتثبيت بصمة المشترك بقوائم متوافقة 100% مع الـ JSON لحمايتها ضد الفرمتة
        if "participants" not in contest: 
            contest["participants"] = {}
            
        contest["registered_users"].append(user_id)
        contest["participants"][str(vote_msg.message_id)] = {"user_id": user_id, "name": first_name}
        
        # تخليد فوري في ملف الـ JSON لتأمين الذاكرة المحلية لأسابيع
        save_contests_to_storage()
        
        # نافذة منبثقة تفرح المشترك بنجاح تسجيله
        bot.answer_callback_query(call.id, text="🎉 كفو! تم تسجيل انضمامك بنجاح وبث منشور تصويتك داخل القناة الحين! 🚀", show_alert=True)
    except Exception as e:
        print(f"❌ فشل البث بالقناة: {e}")


# 🏁 أمر إطلاق واجهة استقبال الفرز والإنهاء للآدمنز المسؤولين
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


# ❌ أمر إلغاء العمليات الجارية المطور والمفتوح لك ولآدمنز الإنشاء بشكل مطلق وصافي في أي محادثة للبوت
@bot.message_handler(commands=['cancel'])
def cmd_global_cancel(message):
    user_id = message.from_user.id
    if user_id in user_states:
        user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 <b>هيهي 😸! تم إلغاء العملية الجارية فوراً وتصفير الخطوات المعلقة كلياً وتطهير الذاكرة السحابية بنجاح!</b>", parse_mode="HTML")
    else:
        bot.reply_to(message, "😸 عذراً يا غالي، لا توجد أي عملية جارية حالياً في حسابك لإلغائها!")


# 🏆 معالجة الفرز النهائي وجلب صورة بروفايل الفائز الأول وبث التهنئة الكبرى مع قشط الأصوات الحقيقية
def finalize_contest_results(message, channel_id, requested_winners, input_text, state, user_id):
    contest_node = channel_contests.get(channel_id, {})
    participants_dict = contest_node.get("participants", {})
    
    for msg_id, p_data in participants_dict.items():
        try:
            chat_msg = bot.forward_message(chat_id=OWNER_ID, from_chat_id=channel_id, message_id=int(msg_id))
            bot.delete_message(chat_id=OWNER_ID, message_id=chat_msg.message_id)
        except Exception:
            pass


    sorted_competitors = sorted(participants_dict.values(), key=lambda x: x["votes"], reverse=True)
    total_participants = len(sorted_competitors)
    
    if total_participants == 0:
        bot.reply_to(message, "🛑 لم يقم أحد بالاشتراك في هذه المسابقة ليتم احتساب النتائج!")
        user_states.pop(user_id, None)
        return
        
    if requested_winners > total_participants:
        requested_winners = total_participants
        
    actual_winners = sorted_competitors[:requested_winners]
    winner_hero = actual_winners[0] if actual_winners else None
    
    if not winner_hero:
        bot.reply_to(message, "🛑 لم يقم أحد بالاشتراك في هذه المسابقة ليتم احتساب النتائج!")
        user_states.pop(user_id, None)
        return


    medals = ["🥇 المركز الأول", "🥈 المركز الثاني", "🥉 المركز الثالث"]
    
    result_text = f"🥳 <b>نتائج المسابقة الرسمية وقفل باب التصويت السحابي!</b> 🏆\n\n"
    for i, winner in enumerate(actual_winners):
        medal = medals[i] if i < 3 else f"🔹 المركز {i+1}"
        result_text += f"{medal}: {winner['mention']} بـ ({winner['votes']} صوت) ✨\n"
        
    celebration_msg = (
        f"👑 <b>تتويج البطل الفائز باللقب الأعلى للمسابقة!</b> 👑\n\n"
        f"🎯 <b>ألف ألف مبروك للفائز بالمركز الأول:</b> {winner_hero['mention']} 🎯\n"
        f"🔥 <b>اكتسح الساحة وحصد:</b> <code>{winner_hero['votes']}</code> صوت من تفاعلاتكم المشتعلة ونجومكم الفخمة! 🏆⭐\n\n"
        f"🎁 تواصل مع الإدارة فوراً لاستلام جائزتك الكبرى يا ملك! 🎉✨\n\n"
        f"🐾 <b>بصمة شركس الحتمية للفعالية:</b> مياووو 🐾😸"
    )


    try:
        winner_id = winner_hero["user_id"]
        user_photos = bot.get_user_profile_photos(winner_id, limit=1)
        
        if user_photos.total_count > 0:
            bot.send_photo(chat_id=channel_id, photo=user_photos.photos[0][0].file_id, caption=celebration_msg, parse_mode="HTML")
            bot.send_message(chat_id=channel_id, text=result_text, parse_mode="HTML")
        else:
            bot.send_message(chat_id=channel_id, text=celebration_msg, parse_mode="HTML")
            bot.send_message(chat_id=channel_id, text=result_text, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(chat_id=channel_id, text=celebration_msg, parse_mode="HTML")
            bot.send_message(chat_id=channel_id, text=result_text, parse_mode="HTML")
        except Exception: pass
        
    bot.reply_to(message, f"🏆 <b>تم قفل الفعالية وتتويج البطل بصورته بنجاح، وبث كارت التهنئة الضخم بالأصوات الحية داخل قناتك!</b>", parse_mode="HTML")
    channel_contests.pop(channel_id, None)
    save_contests_to_storage() 
    user_states.pop(user_id, None)


# =========================================================================
# 🏁 جذع التشغيل الحتمي الموحد والوحيد الذي يغلق الملف بالكامل في القاع إجبارياً
if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("جاري فتح المنافذ وتشغيل شركس بنمط الاستماع المباشر الصافي المطور...")
    # التشغيل الفولاذي المقيد للأخطاء لمنع الاصطدام والتصادم الدوري في ريندر
if __name__ == "__main__":
    import time
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ خطأ مؤقت في الاتصال، إعادة المحاولة خلال 5 ثوانٍ... {e}")
            time.sleep(5)






