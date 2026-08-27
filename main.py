import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://contest-bot-meoww-3d8k.onrender.com")
WEBHOOK_URL = f"{BASE_URL}/webhook"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # تفعيل الـ Webhook فوراً عند التشغيل
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    yield
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Sharx Bot is active and purring! 🐱"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        print(f"Error handling update: {e}")
    return {"ok": True}

# 1. أمر /start (الترحيب بشخصية القط شركس + زر Help)
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    first_name = message.from_user.first_name
    
    # بناء زر Help التفاعلي
    builder = InlineKeyboardBuilder()
    builder.button(text="help 🐾", callback_data="show_help")
    
    welcome_text = (
        f"مرحباً بك يا {first_name} 🐱\n"
        f"أنا **شركس**، قط لطيف ولكني ذكي جداً!\n\n"
        f"أنا بوت مخصص ليكون **مساعدك + منظم للمسابقات**. "
        f"يمكنني مساعدتك في إدارة مجموعتك وإحضار المعرفات وغيرها من المهام.\n\n"
        f"اضغط على الزر أدناه لمعرفة الأوامر والخيارات المتاحة:"
    )
    
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# 2. عرض قائمة المساعدة عند الضغط على زر help
@dp.callback_query(F.data == "show_help")
async def help_callback_handler(callback: types.CallbackQuery):
    help_text = (
        "📖 **قائمة خيارات وأوامر شركس:**\n\n"
        "🔹 **id_help**: يساعد في إحضار معرفات القنوات، القروبات، والحسابات لأغراض الحماية.\n"
        "🔹 **create**: مهمته إنشاء المسابقات.\n"
        "🔹 **end**: مهمته إنهاء المسابقات.\n"
        "🔹 **cancel**: مهمته إلغاء أي عملية جارية وتصفير الحالة.\n\n"
        "*(ملاحظة: الأوامر التي تحتاج كتابة يدوية تبدأ بـ / مثل /start)*"
    )
    
    await callback.message.edit_text(help_text, parse_mode="Markdown")
    await callback.answer()
