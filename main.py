import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://contest-bot-meoww-3d8k.onrender.com")
WEBHOOK_URL = f"{BASE_URL}/webhook"

# إعداد الاتصال بـ MongoDB مع حل مشكلة TLS/SSL
mongo_client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    print(f"Webhook configured to: {WEBHOOK_URL}")
    yield
    await bot.delete_webhook()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot Webhook is active!"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        print(f"Error handling update: {e}")
    return {"ok": True}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    try:
        existing_user = await users_collection.find_one({"user_id": user_id})
        if not existing_user:
            await users_collection.insert_one({"user_id": user_id, "name": first_name})
            text = f"أهلاً بك يا {first_name}! تم تسجيلك في قاعدة البيانات بنجاح. 🚀"
        else:
            text = f"أهلاً بك مجدداً يا {first_name}! 👋"
    except Exception as e:
        print(f"Database error: {e}")
        text = f"أهلاً بك يا {first_name}! 👋"

    await message.answer(text)
