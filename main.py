import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

# جلب المتغيرات البيئية
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# تهيئة قاعدة البيانات والبوت
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# إدارة دورة حياة التطبيق لتشغيل وإيقاف البوت مع FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # مسح أي Webhook قديم لتفعيل Polling بنجاح
    await bot.delete_webhook(drop_pending_updates=True)
    # تشغيل استقبال الرسائل في الخلفية
    polling_task = asyncio.create_task(dp.start_polling(bot))
    print("Bot polling started successfully!")
    yield
    # إيقاف التحديثات عند إغلاق السيرفر
    polling_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot is running online!"}

# أمر /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    existing_user = await users_collection.find_one({"user_id": user_id})
    if not existing_user:
        await users_collection.insert_one({"user_id": user_id, "name": first_name})
        text = f"أهلاً بك يا {first_name}! تم تسجيلك في قاعدة البيانات بنجاح. 🚀"
    else:
        text = f"أهلاً بك مجدداً يا {first_name}! 👋"

    await message.answer(text)
