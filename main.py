# ==========================================
# **بوتي شركس القط - الإصدار النهائي المحدث 2026**
# ==========================================
import os
import time
import threading
import base64
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
import arabic_reshaper
from bidi.algorithm import get_display
import telebot
from telebot import types
from http.server import HTTPServer, BaseHTTPRequestHandler
from hashids import Hashids

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
DEV_ID = 7963720007  # آيدي المطور حصرياً

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# هاش قصير وفريد
hashids = Hashids(salt="sharx_secure_salt_2026", min_length=4)


# ==========================================
# نظام رد المسابقة المضمّن داخل رسالة المسابقة
# لا يحتاج MongoDB أو JSON أو قاعدة بيانات خارجية
# ==========================================
RESPONSE_MARKER = "\u200b"

def encode_join_response(text):
    raw = (text or "").encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def decode_join_response(encoded):
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except Exception:
        return None

def build_hidden_response(hash_id, response_text):
    payload = f"{hash_id}:{encode_join_response(response_text)}"
    hidden = RESPONSE_MARKER.join(payload)
    return f"\n{RESPONSE_MARKER}{hidden}{RESPONSE_MARKER}"

def extract_join_response(message_text, hash_id):
    if not message_text:
        return None
    pattern = re.escape(RESPONSE_MARKER) + r"(.*?)" + re.escape(RESPONSE_MARKER)
    matches = re.findall(pattern, message_text, flags=re.DOTALL)
    for block in matches:
        payload = block.replace(RESPONSE_MARKER, "")
        if ":" not in payload:
            continue
        saved_hash, encoded = payload.split(":", 1)
        if saved_hash == hash_id:
            return decode_join_response(encoded)
    return None

def escape_markdown_v2_text(text):
    # Not used for the main contest text; kept available for custom replies.
    if not text:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

last_panel_message = {}
contest_creation_state = {}
end_contest_state = {}
template_state = {}

# ذاكرة لتخزين القنوات والمجموعات التي يخدمها البوت تلقائياً
served_chats = set()


# ==========================================
# 1. خادم الويب المصغر (Keep-Alive Server)
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Sharx Bot Clean Mode is active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    server.serve_forever()


# ==========================================
# 2. دوال إنشاء الأزرار والقوائم (Keyboards)
# ==========================================
def create_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎯 إنشاء مسابقة / تصويت تفاعلي", callback_data="cmd_create"),
        types.InlineKeyboardButton("🖼️ قوالب المنشورات", callback_data="cmd_templates"),
        types.InlineKeyboardButton("⛔ إنهاء المسابقة الحالية", callback_data="cmd_end"),
        types.InlineKeyboardButton("⚙️ لوحة المطور السرية", callback_data="cmd_dev_panel"),
        types.InlineKeyboardButton("💻 مطور البوت", callback_data="cmd_developer"),
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


# ==========================================
# 3. دوال التحقق من المطور والمشرفين
# ==========================================
def is_dev(user_id):
    return user_id == DEV_ID

def is_user_admin(chat_id, user_id):
    if is_dev(user_id):
        return True
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ["creator", "administrator"]:
            return True
    except Exception:
        pass
    return False


# ==========================================
# 4. التتبع التلقائي للمجموعات والقنوات
# ==========================================
@bot.my_chat_member_handler()
def track_chats(message):
    new_status = message.new_chat_member.status
    chat_id = message.chat.id
    if new_status in ['administrator', 'member']:
        served_chats.add(chat_id)
    elif new_status in ['left', 'kicked']:
        served_chats.discard(chat_id)


# ==========================================
# 5. دوال إدارة واجهة التحكم والتحديث
# ==========================================
def update_or_send_panel(chat_id, text, reply_markup):
    if chat_id in last_panel_message:
        try:
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=last_panel_message[chat_id],
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        except Exception:
            pass
     
    sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=reply_markup)
    last_panel_message[chat_id] = sent.message_id


# ==========================================
# 6. استقبال أمر البدء (Start Command)
# ==========================================
@bot.message_handler(commands=["start"])
def handle_start_command(message):
    # /start يبدأ جلسة جديدة ونظيفة دائماً.
    contest_creation_state.pop(message.from_user.id, None)
    end_contest_state.pop(message.from_user.id, None)
    template_state.pop(message.from_user.id, None)

    if message.chat.type != "private":
        if not is_user_admin(message.chat.id, message.from_user.id):
            return
    
    text = (
        "مياو أهلاً بك في عالم شركس القط! 🐱✨\n"
        "البوت الذكي لإدارة المسابقات بكل احترافية وبدون عشوائية.\n"
        "اختر ما يناسبك من القائمة أدناه:"
    )
    sent = bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=create_main_menu_markup())
    last_panel_message[message.chat.id] = sent.message_id


# ==========================================
# 7. أوامر المطور الاحترازية (كتم وقفل الجميع / إلغاء الكتم)
# ==========================================
@bot.message_handler(commands=['mute_all'])
def mute_all_command(message):
    if not is_dev(message.from_user.id):
        return
    
    chat_id = message.chat.id
    try:
        permissions = types.ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.set_chat_permissions(chat_id, permissions)
        bot.send_message(chat_id, "⚠️ **إجراء احترازي قاطع:** تم قفل الشات وكتم الجميع بالكامل! لا يمكن لأحد الكتابة باستثناء المطور 🐾")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تنفيذ الكتم العام: {e}")

@bot.message_handler(commands=['unmute_all'])
def unmute_all_command(message):
    if not is_dev(message.from_user.id):
        return
    
    chat_id = message.chat.id
    try:
        permissions = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.set_chat_permissions(chat_id, permissions)
        bot.send_message(chat_id, "✅ تم إلغاء الكتم العام وإعادة فتح الشات للجميع بنجاح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء فتح الشات: {e}")


# ==========================================
# 8. معالج الرسائل في القروبات (استجابة كلمة "شركس" + كاشف البيانات)
# ==========================================
@bot.message_handler(chat_types=["supergroup", "group"], content_types=["text", "photo"])
def handle_group_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text_content = message.text.strip() if message.text else ""

    if not user_id in contest_creation_state and text_content in ["شركس", "Sharx", "شاركس"]:
        if not is_user_admin(chat_id, user_id):
            return

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            target_id = target_user.id
            target_first = target_user.first_name or "غير معروف"
            target_username = f"@{target_user.username}" if target_user.username else "لا يوجد"
            account_type = "🤖 بوت" if target_user.is_bot else "👤 مستخدم حقيقي"

            info_text = (
                "🐱 **بطاقة معلومات الحساب - شركس القط** 🐾\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **الاسم:** [{target_first}](tg://user?id={target_id})\n"
                f"🏷️ **المعرف (Username):** {target_username}\n"
                f"🆔 **الآيدي (Account ID):** `{target_id}`\n"
                f"📊 **نوع الحساب:** {account_type}\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
            try:
                bot.reply_to(message, info_text, parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending user info: {e}")
            return

        sent = bot.send_message(chat_id, "مياو! أهلاً بك يا مشرفنا العزيز 🐱✨\nإليك قائمة التحكم الخاصة بالمسابقات:", reply_markup=create_main_menu_markup())
        last_panel_message[chat_id] = sent.message_id
        return

    if user_id in template_state:
        state = template_state[user_id]
        step = state.get("step")
        target_message_id = last_panel_message.get(chat_id)
        if not target_message_id:
            sent = bot.send_message(chat_id, "🖼️ نكمل إعداد القالب من هنا.", reply_markup=create_main_menu_markup())
            target_message_id = sent.message_id
            last_panel_message[chat_id] = target_message_id

        if step == "destination" or step == "target":
            resolved = text_content.strip()
            # دعم @username والروابط العامة واسم المستخدم بدون @
            if resolved and not resolved.startswith(("@", "-", "+")) and "t.me/" not in resolved:
                resolved = "@" + resolved
            if "t.me/" in resolved:
                parts = resolved.split("t.me/")[-1].split("?")[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved = f"@{parts}"
            try:
                chat_obj = bot.get_chat(resolved)
                if not is_user_admin(chat_obj.id, user_id):
                    bot.edit_message_text(
                        "⚠️ يجب أن تكون مشرفاً في الوجهة المحددة.",
                        chat_id, target_message_id,
                        reply_markup=get_back_and_home_markup("cmd_templates")
                    )
                    return
                state["destination"] = chat_obj.id
                # احذف رسالة المستخدم التي تحتوي على رابط/معرف الوجهة بعد قراءتها
                # حتى يبقى شات البوت نظيفاً ولا تظهر بيانات القناة/القروب في المحادثة.
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception:
                    pass
                template_ask_photo(user_id, chat_id, target_message_id)
            except Exception as e:
                bot.edit_message_text(
                    f"⚠️ تعذر الوصول إلى الوجهة.\n`{e}`",
                    chat_id, target_message_id, parse_mode="Markdown",
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )
            return

        if step == "photo":
            if not message.photo:
                bot.edit_message_text(
                    "🖼️ أرسل صورة فعلية من فضلك.",
                    chat_id, target_message_id,
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )
                return
            state["photo"] = message.photo[-1].file_id
            template_ask_text(user_id, chat_id, target_message_id)
            return

        if step == "text":
            state["text"] = text_content
            state["step"] = "preview"
            bot.edit_message_text(
                template_preview_text(state),
                chat_id, target_message_id,
                parse_mode="Markdown",
                reply_markup=create_template_finish_markup()
            )
            return

    if user_id in contest_creation_state:
        if not is_user_admin(chat_id, user_id):
            return

        state_data = contest_creation_state[user_id]
        step = state_data.get("step", 2)
        target_message_id = last_panel_message.get(chat_id)

        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

        if step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("🎁 نعم (إرفاق صورة/رابط)", callback_data="prize_yes"),
                types.InlineKeyboardButton("⏭️ تخطي", callback_data="prize_no")
            )
            text = (
                "🐾 [ السؤال الثالث: إرفاق هدية أو صورة ] 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق صورة أو رابط هدية لتميز مسابقتك؟ (اضغط تخطي للانتقال مباشرة)."
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 3:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            ask_join_button_step(user_id, chat_id, target_message_id)
            return

        elif step == 5:
            state_data["button_text"] = text_content
            state_data["step"] = 6
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("⏭️ تخطي واستخدام الرد التلقائي", callback_data="join_msg_skip")
            )
            text = (
                "🐾 [ السؤال السادس: رسالة الرد ] 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **رسالة الرد** التي تظهر للمستخدم فور ضغطه على الزر (مثال: تم تسجيل اسمك في المسابقة بنجاح! 🔥):"
            )
            if target_message_id:
                try:
                    bot.edit_message_text(text, chat_id, target_message_id, reply_markup=markup)
                    return
                except Exception:
                    pass
            sent = bot.send_message(chat_id, text, reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id
            return

        elif step == 6:
            state_data["join_msg_text"] = text_content
            ask_mention_step(user_id, chat_id, target_message_id)
            return


# ==========================================
# 9. نظام قوالب المنشورات
# ==========================================
def create_template_size_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ كبير", callback_data="tpl_size_large"),
        types.InlineKeyboardButton("🖼️ متوسط", callback_data="tpl_size_medium"),
        types.InlineKeyboardButton("🖼️ صغير", callback_data="tpl_size_small"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_home"),
    )
    return markup

def create_template_target_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 قناة", callback_data="tpl_target_channel"),
        types.InlineKeyboardButton("👥 قروب", callback_data="tpl_target_group"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_templates"),
    )
    return markup

def create_template_finish_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ تعديل النص", callback_data="tpl_edit_text"),
        types.InlineKeyboardButton("👀 معاينة", callback_data="tpl_preview"),
        types.InlineKeyboardButton("🚀 نشر", callback_data="tpl_publish"),
    )
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="cmd_templates"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cmd_cancel"),
    )
    return markup

def template_preview_text(state):
    size_names = {"large": "كبير", "medium": "متوسط", "small": "صغير"}
    target_names = {"channel": "قناة", "group": "قروب"}
    size = size_names.get(state.get("size"), "غير محدد")
    target = target_names.get(state.get("target"), "غير محدد")
    body = state.get("text", "") or "لم تتم إضافة نص بعد."
    return (
        "🖼️ *معاينة قالب شركس* 🐾\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📐 الحجم: *{size}*\n"
        f"📍 الوجهة: *{target}*\n\n"
        f"{body}"
    )

def show_templates_menu(chat_id, message_id):
    markup = get_back_and_home_markup("cmd_home")
    markup.add(types.InlineKeyboardButton("➕ إنشاء قالب جديد", callback_data="tpl_new"))
    try:
        bot.edit_message_text(
            "🖼️ *قوالب المنشورات* 🐾\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "أنشئ منشوراً بصورة ونص، واختر الحجم والوجهة ثم انشره.\n\n"
            "اختر إنشاء قالب جديد للبدء:",
            chat_id, message_id, parse_mode="Markdown", reply_markup=markup
        )
    except Exception:
        sent = bot.send_message(
            chat_id,
            "🖼️ *قوالب المنشورات* 🐾\nاختر إنشاء قالب جديد للبدء:",
            parse_mode="Markdown",
            reply_markup=markup
        )
        last_panel_message[chat_id] = sent.message_id

def show_template_size(chat_id, message_id):
    bot.edit_message_text(
        "📐 *اختر حجم القالب*:\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "كبير = عرض أكبر\nمتوسط = الحجم المعتاد\nصغير = عرض مختصر",
        chat_id, message_id, parse_mode="Markdown",
        reply_markup=create_template_size_markup()
    )

def start_template(user_id, chat_id, message_id):
    template_state[user_id] = {
        "step": "size",
        "size": None,
        "target": None,
        "text": None,
        "photo": None,
        "destination": None,
    }
    show_template_size(chat_id, message_id)

def template_ask_target(user_id, chat_id, message_id):
    template_state[user_id]["step"] = "target"
    bot.edit_message_text(
        "📍 *أين تريد نشر القالب؟*",
        chat_id, message_id, parse_mode="Markdown",
        reply_markup=create_template_target_markup()
    )

def template_ask_photo(user_id, chat_id, message_id):
    template_state[user_id]["step"] = "photo"
    bot.edit_message_text(
        "🖼️ *أرسل صورة القالب الآن.*\n\n"
        "بعدها سأطلب منك النص الذي سيظهر معها.",
        chat_id, message_id, parse_mode="Markdown",
        reply_markup=get_back_and_home_markup("cmd_templates")
    )

def template_ask_text(user_id, chat_id, message_id):
    template_state[user_id]["step"] = "text"
    bot.edit_message_text(
        "✏️ *أرسل نص المنشور الآن.*",
        chat_id, message_id, parse_mode="Markdown",
        reply_markup=get_back_and_home_markup("cmd_templates")
    )

def _find_arabic_font(size):
    # خطوط عربية موجودة عادةً على Render؛ نفضّل Noto Naskh Arabic.
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Medium.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def _shape_arabic(text):
    # مهم: لا نعكس ترتيب العربي هنا إذا كان Pillow مبنيًا مع libraqm.
    # نعطي Pillow النص العربي بالترتيب الطبيعي ونجعله يرسمه RTL.
    # إذا لم تتوفر libraqm على السيرفر، نستخدم get_display كخطة بديلة.
    try:
        return arabic_reshaper.reshape(text)
    except Exception:
        return text

def _text_direction_kwargs(text):
    has_arabic = any(
        "\u0600" <= ch <= "\u06ff" or
        "\u0750" <= ch <= "\u077f" or
        "\u08a0" <= ch <= "\u08ff"
        for ch in text
    )
    if has_arabic:
        try:
            from PIL import features
            if features.check("raqm"):
                return {"direction": "rtl", "language": "ar"}
        except Exception:
            pass
    return {}

def _visual_fallback(text):
    # يستخدم فقط عندما لا يدعم Pillow/الخادم RTL مباشرة.
    try:
        return get_display(text, base_dir="R")
    except Exception:
        return text

def _remove_outer_background(image, tolerance=18):
    # يجعل الخلفية الخارجية المتصلة بحواف الصورة شفافة، مع إبقاء محتوى القالب
    # الأسود داخل الإطار كما هو. إذا كانت الصورة أصلًا شفافة لا نلمس ألفا.
    image = image.convert("RGBA")
    px = image.load()
    w, h = image.size
    corners = [px[0,0], px[w-1,0], px[0,h-1], px[w-1,h-1]]

    def near(a,b):
        return max(abs(a[i]-b[i]) for i in range(3)) <= tolerance and a[3] > 0

    from collections import deque
    q = deque()
    seen = set()
    for y in (0, h-1):
        for x in range(w):
            if (x,y) not in seen:
                seen.add((x,y)); q.append((x,y))
    for x in (0, w-1):
        for y in range(h):
            if (x,y) not in seen:
                seen.add((x,y)); q.append((x,y))

    while q:
        x,y=q.popleft()
        p=px[x,y]
        if not any(near(p,c) for c in corners):
            continue
        px[x,y]=(p[0],p[1],p[2],0)
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h and (nx,ny) not in seen:
                seen.add((nx,ny)); q.append((nx,ny))
    return image

def _prepare_lines(text):
    # نعالج كل سطر على حدة حتى لا نكسر الأسطر التي كتبها المستخدم.
    return [_shape_arabic(line) for line in text.splitlines() if line.strip()] or [_shape_arabic(text.strip())]

def _fit_text(draw, text, box_width, box_height):
    """Find the largest readable font that fits the whole text in the box.

    The available font size is derived from the actual template dimensions and
    the amount of text. Explicit newlines are respected; other text is wrapped
    automatically. Arabic is shaped once and rendered RTL when RAQM is present.
    """
    text = (text or "").strip()
    if not text:
        return "", _find_arabic_font(20), 0, {}

    has_arabic = any(
        "\u0600" <= ch <= "\u06ff" or
        "\u0750" <= ch <= "\u077f" or
        "\u08a0" <= ch <= "\u08ff"
        for ch in text
    )

    try:
        from PIL import features
        use_raqm = bool(features.check("raqm"))
    except Exception:
        use_raqm = False

    direction_kwargs = {"direction": "rtl", "language": "ar"} if has_arabic and use_raqm else {}

    def visual_text(t):
        shaped = _shape_arabic(t)
        if has_arabic and not use_raqm:
            shaped = _visual_fallback(shaped)
        return shaped

    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    # Leave a small but proportional safety margin inside the template.
    usable_w = max(20, int(box_width * 0.94))
    usable_h = max(20, int(box_height * 0.92))

    def make_lines(font):
        lines = []
        for paragraph in paragraphs:
            words = paragraph.split()
            if not words:
                continue
            current = ""
            for word in words:
                candidate = word if not current else current + " " + word
                visual = visual_text(candidate)
                bbox = draw.textbbox((0, 0), visual, font=font, **direction_kwargs)
                if bbox[2] - bbox[0] <= usable_w:
                    current = candidate
                else:
                    if current:
                        lines.append(visual_text(current))
                        current = word
                    else:
                        # A single very long token: hard-wrap by characters.
                        chunk = ""
                        for ch in word:
                            test = chunk + ch
                            vb = draw.textbbox((0, 0), visual_text(test), font=font, **direction_kwargs)
                            if vb[2] - vb[0] <= usable_w or not chunk:
                                chunk = test
                            else:
                                lines.append(visual_text(chunk))
                                chunk = ch
                        current = chunk
            if current:
                lines.append(visual_text(current))
        return lines

    # Start from a size based on the actual image/box, then binary-search the
    # largest size that can contain all lines. This avoids unnecessarily tiny text.
    high = max(12, min(420, int(usable_h * 0.82)))
    low = 10
    best = None

    while low <= high:
        mid = (low + high) // 2
        font = _find_arabic_font(mid)
        lines = make_lines(font)
        spacing = max(4, mid // 5)
        metrics = [draw.textbbox((0, 0), line, font=font, **direction_kwargs) for line in lines]
        heights = [max(1, b[3] - b[1]) for b in metrics]
        widths = [max(1, b[2] - b[0]) for b in metrics]
        total_h = sum(heights) + spacing * max(0, len(lines) - 1)
        max_w = max(widths, default=0)

        if max_w <= usable_w and total_h <= usable_h:
            best = ("\n".join(lines), font, total_h, direction_kwargs, spacing)
            low = mid + 1
        else:
            high = mid - 1

    if best is None:
        font = _find_arabic_font(10)
        lines = make_lines(font)
        spacing = 3
        metrics = [draw.textbbox((0, 0), line, font=font, **direction_kwargs) for line in lines]
        total_h = sum(max(1, b[3] - b[1]) for b in metrics) + spacing * max(0, len(lines) - 1)
        return "\n".join(lines), font, total_h, direction_kwargs, spacing

    return best

def render_template_sticker(photo_bytes, body, size_name):
    # Use the exact uploaded template. Never mirror/flip it.
    image = Image.open(BytesIO(photo_bytes))
    image = ImageOps.exif_transpose(image).convert("RGBA")

    # Always clean a solid outer background (including white) at the border.
    # This is important when Telegram receives a PNG template that contains an
    # opaque white canvas around an otherwise transparent/sticker-like design.
    image = _remove_outer_background(image, tolerance=28)

    # Large templates are allowed to stay large; medium/small are sticker-sized.
    # أحجام إخراج الصورة. نرفع المتوسط/الصغير حتى لا يبدو النص مصغراً عند عرضه.
    sizes = {"large": 2048, "medium": 1280, "small": 900}
    max_side = sizes.get(size_name, 512)
    scale = min(1.0, max_side / max(image.width, image.height))
    if scale != 1.0:
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )

    w, h = image.size
    draw = ImageDraw.Draw(image)

    # Text area is proportional to the actual template dimensions.
    # These ratios match the current frame: the black inner panel is not resized
    # independently, so the template's proportions remain intact.
    # منطقة النص داخل اللوحة الداخلية: أوسع وأعلى من النسخة السابقة،
    # مع هامش أمان حتى لا يلمس الإطار.
    left = int(w * 0.16)
    right = int(w * 0.94)
    top = int(h * 0.27)
    bottom = int(h * 0.91)
    box_w = max(20, right - left)
    box_h = max(20, bottom - top)

    final_text, font, text_h, direction_kwargs, spacing = _fit_text(
        draw, body, box_w, box_h
    )

    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    y = center_y - text_h // 2

    draw.multiline_text(
        (center_x, y),
        final_text,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="ma",
        align="center",
        spacing=spacing,
        **direction_kwargs,
    )

    # Keep PNG as the final output so transparency is preserved around the design.
    png = BytesIO()
    png.name = "sharx_template.png"
    image.save(png, format="PNG", optimize=True)
    png.seek(0)
    return png

def template_preview(user_id, chat_id, message_id, call):
    state = template_state.get(user_id)
    if not state:
        bot.answer_callback_query(call.id, "انتهت جلسة القالب.", show_alert=True)
        return

    destination = state.get("destination")
    photo = state.get("photo")
    body = state.get("text") or ""
    size_name = state.get("size") or "medium"
    if not photo or not body.strip():
        bot.answer_callback_query(call.id, "أرسل القالب والنص أولاً.", show_alert=True)
        return

    try:
        file_info = bot.get_file(photo)
        photo_bytes = bot.download_file(file_info.file_path)
        rendered = render_template_sticker(photo_bytes, body, size_name)

        # المعاينة بنفس طريقة النشر: صورة PNG شفافة، وليس Sticker.
        rendered.seek(0)
        bot.send_photo(
            chat_id, rendered,
            caption="👀 معاينة القالب — لم يتم النشر بعد."
        )

        bot.answer_callback_query(call.id, "تم إرسال المعاينة 👀")
    except Exception as e:
        print(f"Template preview error: {e}")
        bot.answer_callback_query(call.id, "⚠️ تعذر إنشاء المعاينة.", show_alert=True)

def template_publish(user_id, chat_id, message_id):
    state = template_state.get(user_id)
    if not state:
        return

    destination = state.get("destination")
    photo = state.get("photo")
    body = state.get("text") or ""
    size_name = state.get("size") or "medium"
    if not destination or not photo or not body.strip():
        bot.send_message(chat_id, "⚠️ بيانات القالب غير مكتملة.")
        return

    try:
        file_info = bot.get_file(photo)
        photo_bytes = bot.download_file(file_info.file_path)
        rendered = render_template_sticker(photo_bytes, body, size_name)

        # الوضع البديل: كل الأحجام تُنشر كصورة PNG شفافة.
        # لا يوجد Caption للنص؛ كل النص مرسوم داخل الصورة نفسها.
        # وبقاء الأطراف شفافة يعطي شكل "ملصق" بصرياً على خلفية تيليجرام.
        rendered.seek(0)
        sent = bot.send_photo(destination, rendered)
        success_text = "✅ *تم نشر القالب كصورة PNG شفافة، والنص داخل التصميم.* 🐾"

        try:
            bot.pin_chat_message(destination, sent.message_id)
        except Exception:
            pass

        template_state.pop(user_id, None)
        bot.edit_message_text(
            success_text,
            chat_id, message_id, parse_mode="Markdown",
            reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        print(f"Template publish error: {e}")
        bot.edit_message_text(
            f"⚠️ *تعذر نشر القالب.*\n`{e}`",
            chat_id, message_id, parse_mode="Markdown",
            reply_markup=create_main_menu_markup()
        )


# ==========================================
# 9. معالج الأزرار الشفافة والأوامر (Callback Handler)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id 
    user_id = call.from_user.id
    data = call.data
    message_id = call.message.message_id
    last_panel_message[chat_id] = message_id

    if call.message.chat.type != "private" and not data.startswith("vote_"):
        if not is_user_admin(chat_id, user_id):
            try:
                bot.answer_callback_query(call.id, "⚠️ هذه الأزرار مخصصة للمشرفين فقط يا صديقي! 🐾", show_alert=True)
            except Exception:
                pass
            return

    if data.startswith("vote_"):
        try:
            parts = data.split("_")
            h_id = parts[1]
            use_mention = (parts[2] == "1") if len(parts) > 2 else True

            message_text = call.message.text or call.message.caption or ""
            user_first_name = call.from_user.first_name or "المشارك"
            user_username = call.from_user.username
             
            if user_username:
                user_identity = f"@{user_username}"
            else:
                user_identity = f"[{user_first_name}](tg://user?id={user_id})"

            if user_identity in message_text:
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
                    new_lines.append(f"👥 عدد المسجلين: *{current_count}*")
                elif "قائمة المشاركين:" in line:
                    participants_line_idx = i
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if participants_line_idx != -1:
                old_participants_text = lines[participants_line_idx].replace("📋 قائمة المشاركين:", "").strip()
                if "لا يوجد مشاركين" in old_participants_text or not old_participants_text:
                    updated_participants = f"{user_identity}"
                else:
                    updated_participants = f"{old_participants_text}, {user_identity}"
                 
                new_lines[participants_line_idx] = f"📋 قائمة المشاركين: {updated_participants}"

            updated_full_text = "\n".join(new_lines)

            if call.message.photo:
                bot.edit_message_caption(
                    caption=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=call.message.reply_markup
                )
            else:
                bot.edit_message_text(
                    text=updated_full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode="Markdown",
                    reply_markup=call.message.reply_markup
                )

            custom_join_msg = extract_join_response(message_text, h_id)
            if not custom_join_msg:
                custom_join_msg = "انضم إلى المسابقة بنجاح! 🔥"
            if use_mention:
                announcement_to_send = f"{user_identity} {custom_join_msg}"
            else:
                announcement_to_send = custom_join_msg
             
            try:
                sent_notif = bot.send_message(chat_id, announcement_to_send, parse_mode="Markdown")
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
                    "🐾 *[ السؤال الأول: معرف القناة أو القروب المستهدف ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **معرف القناة أو القروب أو الرابط** المراد النشر فيه:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            else:
                if not is_user_admin(chat_id, user_id):
                    bot.answer_callback_query(call.id, "⚠️ عذراً، هذه الميزة للمشرفين فقط!", show_alert=True)
                    return
                contest_creation_state[user_id] = {"step": 2, "is_private": False, "channel": chat_id}
                markup = get_cancel_and_home_markup("cmd_create")
                text = (
                    "🐾 *[ السؤال الثاني: نص المسابقة ]* 🐱✨\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "أرسل لي الآن **نص المسابقة أو السؤال** المراد نشره:"
                )
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "prize_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 3
                markup = get_cancel_and_home_markup("cmd_create")
                text = "🎁 *[ السؤال الثالث ]*\nأرسل لي الآن **صورة الهدية أو رابطها** لتميز مسابقتك (أو اضغط رجوع للتخطي):"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "prize_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["prize_media"] = None
                ask_join_button_step(user_id, chat_id, message_id)

        elif data == "btn_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["step"] = 5
                markup = get_cancel_and_home_markup("cmd_create")
                text = "🔤 *[ السؤال الخامس: تسمية الزر ]*\nأرسل لي الآن **تسمية الزر** (مثال: انضم الآن 🔥):"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "btn_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["button_text"] = None
                contest_creation_state[user_id]["join_msg_text"] = "انضم إلى المسابقة بنجاح! 🔥"
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "join_msg_skip":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["join_msg_text"] = "انضم إلى المسابقة بنجاح! 🔥"
                ask_mention_step(user_id, chat_id, message_id)

        elif data == "mention_join_yes":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = True
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "mention_join_no":
            if user_id in contest_creation_state:
                contest_creation_state[user_id]["msg_mention"] = False
                finalize_and_publish_contest(bot, chat_id, message_id, user_id)

        elif data == "cmd_templates":
            show_templates_menu(chat_id, message_id)

        elif data == "tpl_new":
            start_template(user_id, chat_id, message_id)

        elif data.startswith("tpl_size_"):
            if user_id not in template_state:
                start_template(user_id, chat_id, message_id)
            else:
                template_state[user_id]["size"] = data.replace("tpl_size_", "")
                template_ask_target(user_id, chat_id, message_id)

        elif data == "tpl_target_channel":
            if user_id in template_state:
                template_state[user_id]["target"] = "channel"
                template_state[user_id]["step"] = "destination"
                bot.edit_message_text(
                    "📢 أرسل الآن *معرف القناة أو رابطها العام*.\n"
                    "يجب أن يكون البوت مشرفاً فيها.",
                    chat_id, message_id, parse_mode="Markdown",
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )

        elif data == "tpl_target_group":
            if user_id in template_state:
                template_state[user_id]["target"] = "group"
                template_state[user_id]["step"] = "destination"
                bot.edit_message_text(
                    "👥 أرسل الآن *معرف القروب أو رابط المجموعة*.\n"
                    "يجب أن يكون البوت مشرفاً فيها.",
                    chat_id, message_id, parse_mode="Markdown",
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )

        elif data == "tpl_edit_text":
            if user_id in template_state:
                template_ask_text(user_id, chat_id, message_id)

        elif data == "tpl_preview":
            if user_id in template_state:
                template_preview(user_id, chat_id, message_id, call)

        elif data == "tpl_publish":
            if user_id in template_state:
                template_publish(user_id, chat_id, message_id)

        elif data == "cmd_dev_panel":
            if not is_dev(user_id):
                bot.answer_callback_query(call.id, "⚠️ هذه القائمة خاصة بالمطور فقط!", show_alert=True)
                return
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("📊 القروبات والقنوات التي يخدمها البوت", callback_data="dev_chats"),
                types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="cmd_home")
            )
            bot.edit_message_text("⚙️ **أهلاً بك في لوحة تحكم المطور السرية** 🛠️\nاختر الخيار المطلوب:", chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "dev_chats":
            if not is_dev(user_id):
                return
            
            count = len(served_chats)
            msg = f"📊 **المجموعات والقنوات النشطة حالياً ({count}):**\n\n"
            for cid in served_chats:
                try:
                    c_info = bot.get_chat(cid)
                    msg += f"• **{c_info.title}** (`{cid}`)\n"
                except Exception:
                    msg += f"• المحادثة: `{cid}`\n"
            
            if count == 0:
                msg += "_لا توجد مجموعات مسجلة حالياً._"

            bot.edit_message_text(msg, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_and_home_markup("cmd_dev_panel"))

        elif data == "cmd_developer":
            try:
                dev_user = bot.get_chat(DEV_ID)
                dev_name = dev_user.first_name or "المطور"
                dev_bio = dev_user.bio or "لا توجد نبذة تعريفية مضافة."
                dev_username = f"@{dev_user.username}" if dev_user.username else "لا يوجد"
                
                dev_info_text = (
                    "💻 **معلومات مطور بوت شركس القط** 🐾\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **الاسم:** [{dev_name}](tg://user?id={DEV_ID})\n"
                    f"🏷️ **المعرف:** {dev_username}\n"
                    f"🆔 **الآيدي:** `{DEV_ID}`\n"
                    f"📝 **البايو:** {dev_bio}\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "✨ المبرمج والمسؤول عن تطوير أنظمة شركس الذكية."
                )
                
                markup = get_back_and_home_markup("cmd_home")
                if dev_user.username:
                    markup.row(types.InlineKeyboardButton("💬 تواصل مع المطور", url=f"https://t.me/{dev_user.username}"))
                
                bot.edit_message_text(dev_info_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            except Exception as e:
                fallback_text = (
                    "💻 **معلومات مطور بوت شركس القط** 🐾\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **آيدي المطور:** `{DEV_ID}`\n"
                    "✨ المبرمج والمسؤول عن تطوير أنظمة شركس الذكية."
                )
                bot.edit_message_text(fallback_text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_and_home_markup("cmd_home"), disable_web_page_preview=True)

        elif data == "cmd_end":
            if call.message.chat.type != "private":
                if not is_user_admin(chat_id, user_id):
                    return
                msg_txt = call.message.text or call.message.caption or ""
                count_val = "0"
                if "عدد المسجلين:" in msg_txt:
                    import re
                    nums = re.findall(r'\d+', msg_txt.split("عدد المسجلين:")[1].split("\n")[0])
                    if nums:
                        count_val = nums[0]
                 
                report = f"⛔ *تم إنهاء المسابقة بنجاح!*\n📊 إجمالي المشاركين: *{count_val}*"
                bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=create_main_menu_markup())
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception:
                    pass
            else:
                end_contest_state[user_id] = {"step": 1}
                markup = get_cancel_and_home_markup("cmd_home")
                text = "⛔ *[ إنهاء مسابقة شركس ]*\nأرسل لي *معرف أو رابط القناة/القروب* المراد إنهاء مسابقتها:"
                bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)

        elif data == "cmd_clean_chat":
            # لا نترك المحادثة الخاصة فارغة؛ نمسح الرسائل القديمة ثم ننشئ
            # رسالة قائمة جديدة حتى يبقى شات البوت ظاهراً في قائمة المحادثات.
            for m_id in range(message_id, max(0, message_id - 50), -1):
                try:
                    bot.delete_message(chat_id, m_id)
                except Exception:
                    pass
            try:
                sent = bot.send_message(
                    chat_id,
                    "🧹 *تم تنظيف الشات بنجاح!* 🐱✨\n\nاضغط أي خيار من القائمة للمتابعة.",
                    parse_mode="Markdown",
                    reply_markup=create_main_menu_markup()
                )
                last_panel_message[chat_id] = sent.message_id
            except Exception as e:
                print(f"Clean chat send error: {e}")

        elif data == "cmd_home":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            template_state.pop(user_id, None)
            update_or_send_panel(chat_id, "🏠 أهلاً بك مجدداً في القائمة الرئيسية لشركس 🐱:", create_main_menu_markup())

        elif data == "cmd_cancel":
            contest_creation_state.pop(user_id, None)
            end_contest_state.pop(user_id, None)
            template_state.pop(user_id, None)
            try:
                bot.send_message(chat_id, "❌ تم إغلاق القائمة.", reply_markup=types.ReplyKeyboardRemove())
            except Exception:
                pass
            update_or_send_panel(chat_id, "❌ تم إغلاق القائمة بنجاح. أرسل /start لإظهارها مجدداً.", create_main_menu_markup())

    except Exception as e:
        print(f"Callback Error ({data}): {e}")


# ==========================================
# 10. خطوات إعداد وإنشاء المسابقة (Steps Functions)
# ==========================================
def ask_join_button_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 4
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(
            types.InlineKeyboardButton("✅ نعم", callback_data="btn_join_yes"),
            types.InlineKeyboardButton("❌ لا", callback_data="btn_join_no")
        )
        text = "🎯 *[ السؤال الرابع ]*\nهل تود إضافة زر اشتراك/تسجيل أسفل الرسالة؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id

def ask_mention_step(user_id, chat_id, message_id):
    if user_id in contest_creation_state:
        contest_creation_state[user_id]["step"] = 7
        markup = get_cancel_and_home_markup("cmd_create")
        markup.row(
            types.InlineKeyboardButton("✅ نعم (مع منشن)", callback_data="mention_join_yes"),
            types.InlineKeyboardButton("❌ لا (بدون منشن)", callback_data="mention_join_no")
        )
        text = "🏷️ *[ السؤال الأخير ]*\nهل تود عمل تاغ أو منشن للشخص الضاغط على الزر عند الانضمام؟"
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            last_panel_message[chat_id] = sent.message_id


# ==========================================
# 11. دالة نشر المسابقة النهائية (Finalize & Publish)
# ==========================================
def finalize_and_publish_contest(bot_instance, chat_id, message_id, user_id):
    state_data = contest_creation_state.pop(user_id, None)
    if not state_data:
        return
         
    raw_channel = state_data.get("channel", chat_id)
    announcement = state_data.get("announcement", "مسابقة جديدة!")
    button_text = state_data.get("button_text", "تسجيل / انضمام 🏆")
    prize_media = state_data.get("prize_media") 
     
    msg_mention_bool = state_data.get("msg_mention", True)
    
    unique_hash = hashids.encode(int(time.time()))
     
    target_chat_id = raw_channel
    try:
        chat_obj = bot_instance.get_chat(raw_channel)
        target_chat_id = chat_obj.id
    except Exception as e:
        print(f"Error resolving target chat ID: {e}")

    if prize_media:
        final_text = (
            f"🎉 *مسابقة شركس القط الجديدة* (كود: `{unique_hash}`)\n\n"
            f"❓ *السؤال:*\n{announcement}\n\n"
            f"🎁 *الهدية:* {prize_media}\n\n"
            f"👥 عدد المسجلين: *0*\n"
            f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
        )
    else:
        final_text = (
            f"🎉 *مسابقة شركس القط الجديدة* (كود: `{unique_hash}`)\n\n"
            f"❓ *السؤال:*\n{announcement}\n\n"
            f"👥 عدد المسجلين: *0*\n"
            f"📋 قائمة المشاركين: _لا يوجد مشاركين حتى الآن_"
        )

    # نخزن الرد نفسه داخل رسالة المسابقة بشكل غير ظاهر،
    # والهاش الموجود في الزر يحدد أي رد يتم استخراجه.
    join_response = state_data.get(
        "join_msg_text", "انضم إلى المسابقة بنجاح! 🔥"
    )
    final_text += build_hidden_response(unique_hash, join_response)

    mention_flag = "1" if msg_mention_bool else "0"
    callback_payload = f"vote_{unique_hash}_{mention_flag}"

    channel_markup = types.InlineKeyboardMarkup()
    if button_text:
        channel_markup.add(types.InlineKeyboardButton(button_text, callback_data=callback_payload))

    try:
        sent_msg = bot_instance.send_message(target_chat_id, final_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=channel_markup)

        try:
            bot_instance.pin_chat_message(target_chat_id, sent_msg.message_id)
        except Exception as pin_err:
            print(f"Pin message error: {pin_err}")

        bot_instance.edit_message_text(
            f"✅ *تم نشر المسابقة وتثبيتها بنجاح تام يا بطل!* 🐾\n🔑 كود الهاش: `{unique_hash}`",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )
    except Exception as e:
        bot_instance.edit_message_text(
            f"⚠️ تعذر النشر، تأكد من صلاحيات البوت كمسؤول في المكان المستهدف: {e}",
            chat_id, message_id, parse_mode="Markdown", reply_markup=create_main_menu_markup()
        )


# ==========================================
# 12. معالج المحادثات الخاصة والخطوات (Private Messages Handler)
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
    if not target_message_id:
        sent = bot.send_message(chat_id, "🐾 نكمل من هنا.", reply_markup=create_main_menu_markup())
        target_message_id = sent.message_id
        last_panel_message[chat_id] = target_message_id

    # ==========================
    # خطوات القوالب داخل الخاص
    # ==========================
    if user_id in template_state:
        state = template_state[user_id]
        step = state.get("step")

        if step in ("destination", "target"):
            resolved = text_content.strip()
            if resolved and not resolved.startswith(("@", "-", "+")) and "t.me/" not in resolved:
                resolved = "@" + resolved
            if "t.me/" in resolved:
                parts = resolved.split("t.me/", 1)[1].split("?", 1)[0].strip("/")
                if parts and not (parts.startswith("+") or parts.startswith("joinchat/")):
                    resolved = "@" + parts

            try:
                chat_obj = bot.get_chat(resolved)
                if not is_user_admin(chat_obj.id, user_id):
                    bot.edit_message_text(
                        "⚠️ يجب أن تكون مشرفاً في الوجهة المحددة.\n\n"
                        "تأكد أن البوت موجود فيها كمشرف أيضاً.",
                        chat_id, target_message_id,
                        reply_markup=get_back_and_home_markup("cmd_templates")
                    )
                    return

                state["destination"] = chat_obj.id
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception:
                    pass

                template_ask_photo(user_id, chat_id, target_message_id)
            except Exception as e:
                bot.edit_message_text(
                    "⚠️ لم أستطع الوصول إلى هذه القناة/المجموعة.\n\n"
                    "أرسل @المعرف أو الرابط العام الصحيح مرة أخرى.",
                    chat_id, target_message_id,
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )
            return

        if step == "photo":
            if not message.photo:
                bot.edit_message_text(
                    "🖼️ أرسل صورة القالب كصورة، وليس كنص.",
                    chat_id, target_message_id,
                    reply_markup=get_back_and_home_markup("cmd_templates")
                )
                return
            state["photo"] = message.photo[-1].file_id
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            template_ask_text(user_id, chat_id, target_message_id)
            return

        if step == "text":
            state["text"] = text_content
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass
            state["step"] = "preview"
            bot.edit_message_text(
                template_preview_text(state),
                chat_id, target_message_id,
                parse_mode="Markdown",
                reply_markup=create_template_finish_markup()
            )
            return

    if user_id in end_contest_state:
        end_contest_state.pop(user_id, None)
        update_or_send_panel(chat_id, f"⛔ *تم إنهاء معالجة الطلب بنجاح.* 🐾", create_main_menu_markup())
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

            # التحقق المرن المحدث لضمان عدم حدوث خطأ
            try:
                chat_obj = bot.get_chat(resolved_channel_id)
                resolved_channel_id = chat_obj.id
            except Exception as e:
                markup = get_back_and_home_markup("cmd_create")
                bot.edit_message_text(
                    f"⚠️ **تعذر الوصول إلى القناة أو القروب!** (الخطأ: {e})\n\n"
                    "تأكد من:\n"
                    "1. إضافة البوت كـ **مشرف (Admin)** في القناة أو القروب.\n"
                    "2. صحة المعرف المكتوب (مثل: `@ChannelName` أو رابط عام صحيح).\n\n"
                    "أرسل المعرف أو الرابط مجدداً:",
                    chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup
                )
                return

            state_data["channel"] = resolved_channel_id
            state_data["step"] = 2

            markup = get_cancel_and_home_markup("cmd_create")
            text = (
                "🐾 *[ السؤال الثاني: نص المسابقة ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **نص المسابقة أو سؤال التصويت** المراد نشره:"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 2:
            state_data["announcement"] = text_content
            state_data["step"] = 3
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("🎁 نعم (إرفاق صورة/رابط)", callback_data="prize_yes"),
                types.InlineKeyboardButton("⏭️ تخطي", callback_data="prize_no")
            )
            text = (
                "🐾 *[ السؤال الثالث: إرفاق هدية أو صورة ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "هل تود إرفاق صورة أو رابط هدية لتميز مسابقتك؟ (اضغط تخطي للانتقال مباشرة)."
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 3:
            if message.photo:
                state_data["prize_media"] = message.photo[-1].file_id
            else:
                state_data["prize_media"] = text_content
            ask_join_button_step(user_id, chat_id, target_message_id)
            return

        elif step == 5:
            state_data["button_text"] = text_content
            state_data["step"] = 6
            markup = get_cancel_and_home_markup("cmd_create")
            markup.row(
                types.InlineKeyboardButton("⏭️ تخطي واستخدام الرد التلقائي", callback_data="join_msg_skip")
            )
            text = (
                "🐾 *[ السؤال السادس: رسالة الرد ]* 🐱✨\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "أرسل لي الآن **رسالة الرد** التي تظهر للمستخدم فور ضغطه على الزر (مثال: تم تسجيل اسمك في المسابقة بنجاح! 🔥):"
            )
            bot.edit_message_text(text, chat_id, target_message_id, parse_mode="Markdown", reply_markup=markup)
            return

        elif step == 6:
            state_data["join_msg_text"] = text_content
            ask_mention_step(user_id, chat_id, target_message_id)
            return


# ==========================================
# 13. نقطة تشغيل البوت الأساسية (Main Execution)
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
            bot.infinity_polling(
                skip_pending=True, 
                timeout=15, 
                long_polling_timeout=15, 
                allowed_updates=['message', 'edited_message', 'channel_post', 'my_chat_member', 'chat_member', 'callback_query']
            )
        except Exception as e:
            print(f"Polling error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
