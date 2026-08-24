import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🛠️ قراءة توكن البوت السري بأمان من إعدادات Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

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

# 🏁 جذع التشغيل الحتمي وإدخال البوت في وضع الاستماع المباشر الصافي
if __name__ == '__main__':
    print("جاري تشغيل شركس بنمط الاستماع المباشر الصافي المطور...")
    bot.infinity_polling()
    # 🕵️‍♂️ أمر جلب وتحصيل الآيدي الشامل والمفتوح (قنوات، مجموعات، وأشخاص) للعامة مجاناً
@bot.message_handler(commands=['id_help'])
def cmd_id_help(message):
    user_id = message.from_user.id
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

# 📥 ملتقط الخطوات الذكي لتجهيز عملية قشط آيدي الميديا أو النصوص الموجهة
@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("step") == "get_any_id_only", 
                     content_types=['text', 'photo', 'video', 'document', 'animation'])
def process_any_id_fetching(message):
    user_id = message.from_user.id
    input_text = message.text.strip() if message.text else ""
    
    # 🚨 صمام حماية الإلغاء المطلق الفوري بدون تحديد
    if input_text in ["/cancel", "الغاء"]:
        if user_id in user_states: user_states.pop(user_id, None)
        bot.reply_to(message, "🫧 تم إلغاء عملية جلب الآيدي بنجاح وتصفير الخطوات معاً! 🐾")
        return

    # قشط واستخراج المعرف الرقمي السري اعتماداً على نوع المصدر الموجه
    if message.forward_from_chat:
        # يمسك القنوات والمجموعات العامة والخاصة على حد سواء
        fetched_id = message.forward_from_chat.id
        source_type = "قناة / مجموعة سوبر"
        fetched_name = message.forward_from_chat.title or "معرف سحابي سري"
    elif message.forward_from:
        # يمسك الحسابات الشخصية المفتوحة للأشخاص والمستخدمين
        fetched_id = message.forward_from.id
        source_type = "حساب شخصي (أشخاص)"
        fetched_name = message.forward_from.first_name or "مستخدم"
    else:
        # حماية إضافية في حال كان الحساب الشخصي المستهدف يغلق خصوصية التوجيه لديه
        if message.forward_sender_name:
            bot.reply_to(message, f"⚠️ <b>المستخدم المقصد قفل خصوصية التوجيه في حسابه!</b>\n👤 الاسم الظاهر: <code>{message.forward_sender_name}</code>\n\n💡 <i>بسبب إعدادات تليجرام الأمنية، لا يمكن جلب آيدي هذا الحساب إلا إذا أرسل معرّفه النصي علناً.</i>", parse_mode="HTML")
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
    user_states.pop(user_id, None) # تصفير وتطهير خطوة المستخدم الحالية فوراً
if __name__ == '__main__':
    print("جاري تشغيل شركس بنمط الاستماع المباشر الصافي المطور...")
    bot.infinity_polling()

