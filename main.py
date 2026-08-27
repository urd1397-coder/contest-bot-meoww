import os
import asyncio
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Sharx Bot is active and purring! 🐱"}

async def send_welcome(message_or_callback, is_edit=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="help 🐾", callback_data="show_help")
    
    text = (
        "مرحباً بك يا غالي 🐱\n"
        "أنا **شركس**، قطك المساعد هيهي!\n\n"
        "أنا بوت مخصص ليكون **مساعدك + منظم للمسابقات**.\n"
        "يمكنني مساعدتك في إحضار المعرفات وغيرها من المهام.\n\n"
        "اضغط على الزر أدناه لمعرفة الأوامر والخيارات المتاحة:"
    )
    
    if is_edit:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message_or_callback.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await send_welcome(message, is_edit=False)

@dp.callback_query(F.data == "show_help")
async def help_cb(callback: types.CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع للرئيسية", callback_data="back_home")
    
    help_text = (
        "📖 **قائمة خيارات وأوامر شركس:**\n\n"
        "🔹 **id_help**: يساعد في إحضار معرفات القنوات، القروبات، والحسابات لأغراض الحماية.\n"
        "🔹 **create**: مهمته إنشاء المسابقات.\n"
        "🔹 **end**: مهمته إنهاء المسابقات.\n"
        "🔹 **cancel**: مهمته إلغاء أي عملية جارية وتصفير الحالة.\n\n"
        "*(ملاحظة: الأوامر التي تحتاج كتابة يدوية تبدأ بـ / مثل /start)*"
    )
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_home")
async def home_cb(callback: types.CallbackQuery):
    await callback.answer("تمت العودة للبداية 🐱")
    await send_welcome(callback, is_edit=True)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    
    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
