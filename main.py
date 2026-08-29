import os
import asyncio
import fcntl
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ملف قفل لمنع تشغيل بولينغ من نسختين في نفس الوقت
LOCK_FILE = "/tmp/bot_polling.lock"

def acquire_lock():
    f = open(LOCK_FILE, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except IOError:
        return None

@app.get("/")
async def root():
    return {"status": "Sharx Polling Bot is running safely! 🐱"}

# تشغيل البوت بالبوليغ المقفل بذكاء
@app.on_event("startup")
async def on_startup():
    lock = acquire_lock()
    if not lock:
        print("Another instance is already running polling. Skipping...")
        return
    
    # تنظيف أي ويبهوك قديم وبدء الاستماع بأمان تام
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))
    print("Sharx Bot polling started safely with file lock!")
