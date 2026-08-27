import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دالة مسؤولة عن إرجاع رسالة الترحيب الأساسية (للصفر) مع زر الـ Help
async def send_welcome_message(message_or_callback, is_callback=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="help 🐾", callback_data="show_help")
    
    welcome_text = (
        "مرحباً بك يا غالي 🐱\n"
        "أنا **شركس**، قطك المساعد هيهي!\n\n"
        "أنا بوت مخصص ليكون **مساعدك + منظم للمسابقات**.\n"
        "يمكنني مساعدتك في إحضار المعرفات وغيرها من المهام.\n\n"
        "اضغط على الزر أدناه لمعرفة الأوامر والخيارات المتاحة:"
    )
    
    if is_callback:
        await message_or_callback.message.edit_text(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message_or_callback.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# 1. أمر /start (الترحيب الأساسي)
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await send_welcome_message(message, is_callback=False)

# 2. عرض قائمة المساعدة عند الضغط على زر help مع زر للرجوع
@dp.callback_query(F.data == "show_help")
async def help_callback_handler(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع للرئيسية", callback_data="back_to_home")
    
    help_text = (
        "📖 **قائمة خيارات وأوامر شركس:**\n\n"
        "🔹 **id_help**: يساعد في إحضار معرفات القنوات، القروبات، والحسابات لأغراض الحماية.\n"
        "🔹 **create**: مهمته إنشاء المسابقات.\n"
        "🔹 **end**: مهمته إنهاء المسابقات.\n"
        "🔹 **cancel**: مهمته إلغاء أي عملية جارية وتصفير الحالة.\n\n"
        "*(ملاحظة: الأوامر التي تحتاج كتابة يدوية تبدأ بـ / مثل /start)*"
    )
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

# 3. زر الرجوع أو تصفير الحالة والعودة للبداية
@dp.callback_query(F.data == "back_to_home")
async def back_home_handler(callback: types.CallbackQuery):
    await send_welcome_message(callback, is_callback=True)
    await callback.answer("تمت العودة للبداية 🐱")

async def main():
    # مسح أي Webhook قديم عالق لضمان عدم تداخل البيانات
    await bot.delete_webhook(drop_pending_updates=True)
    print("🐱 Sharx Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
