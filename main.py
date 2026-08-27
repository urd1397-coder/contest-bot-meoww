import asyncio
import os
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

# جلب المتغيرات من Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()

# تهيئة قاعدة البيانات والبوت
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@app.get("/")
async def root():
    return {"status": "Bot is running online!"}

# أمر /start التجريبي
@app.message(Command("start"))
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

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(dp.start_polling(bot))
