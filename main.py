import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دالة رسالة الترحيب الموحدة
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
    # إيقاف علامة التحميل المزعجة فوراً من تيليجرام
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
    # مسح أي تضارب قديم في الويب هوك والبدء بالسحب الفوري
    await bot.delete_webhook(drop_pending_updates=True)
    print("Sharx Bot is running with instant polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
