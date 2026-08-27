import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global polling_task
    # حذف الـ Webhook وتنظيف التحديثات المعلقة أولاً
    await bot.delete_webhook(drop_pending_updates=True)
    
    # بدء الاستقبال
    polling_task = asyncio.create_task(dp.start_polling(bot))
    print("Bot polling started successfully!")
    
    yield
    
    # إغلاق نظيف عند الإيقاف
    if polling_task:
        polling_task.cancel()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot is running online!"}

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
