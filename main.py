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

# رسالة الترحيب بأسلوب شركس اللطيف
async def send_welcome(message_or_callback, is_edit=False):
    builder = InlineKeyboardBuilder()
    builder.button(text="🐾 الأوامر والمساعدة", callback_data="show_help")
    
    text = (
        "مرحباً! معك **شركس** 🐱\n"
        "جاهز لمساعدتك في كل ما تخصه الإدارة والمسابقات. اضغط على الزر أدناه لنلقي نظرة على الأوامر."
    )
    
    if is_edit:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        await message_or_callback.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await send_welcome(message, is_edit=False)

# قائمة المساعدة مع إيموجيز تفاعلية واستجابة سريعة
@dp.callback_query(F.data == "show_help")
async def help_cb(callback: types.CallbackQuery):
    await callback.answer("تم فتح الأوامر بنجاح 📋")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 العودة للرئيسية", callback_data="back_home")
    
    help_text = (
        "📋 **قائمة خيارات وأوامر شركس:**\n\n"
        "🔹 `/id_help` : إحضار معرفات القنوات والقروبات والحسابات.\n"
        "🔹 `/create` : لبدء وإنشاء مسابقة جديدة.\n"
        "🔹 `/end` : لإنهاء المسابقة الحالية.\n"
        "🔹 `/cancel` : لتلغيم أي عملية جارية وتصفير الحالة.\n\n"
        "*(ملاحظة: الأوامر الأساسية تُكتب يدوياً في الشات تبدأ بـ /)*"
    )
    
    await callback.message.edit_text(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_home")
async def home_cb(callback: types.CallbackQuery):
    await callback.answer("عادت الأمور للبداية 🐾")
    await send_welcome(callback, is_edit=True)
