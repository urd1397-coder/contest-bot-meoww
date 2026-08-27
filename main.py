import os
import certifi
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://contest-bot-meoww-3d8k.onrender.com")
WEBHOOK_URL = f"{BASE_URL}/webhook"

mongo_client = AsyncIOMotorClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ذاكرة مؤقتة لسرعة الفحص
cached_users = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. إنشاء فهرس لضمان سرعة الاستعلام وعدم تكرار الآيدي
    await users_collection.create_index("user_id", unique=True)
    
    # 2. تحميل كافة الآيديات المحفوظة سابقاً من MongoDB عند بدء التشغيل
    existing_ids = await users_collection.distinct("user_id")
    cached_users.update(existing_ids)
    print(f"✅ Loaded {len(cached_users)} users from MongoDB into memory.")
    
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
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
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        print(f"Error: {e}")
    return {"ok": True}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # فحص سريع جداً في الذاكرة (بدون الانتظار عبر الشبكة)
    if user_id in cached_users:
        await message.answer(f"أهلاً بك مجدداً يا {first_name}! 👋")
    else:
        # إضافة الآيدي للكاش الفوري
        cached_users.add(user_id)
        
        # حفظ المستخدم بشكل دائم ورسمي في قاعدة البيانات MongoDB
        try:
            await users_collection.insert_one({
                "user_id": user_id, 
                "name": first_name
            })
            print(f"💾 User {user_id} saved to MongoDB successfully.")
        except Exception as e:
            print(f"⚠️ DB Save Error: {e}")

        await message.answer(f"أهلاً بك يا {first_name}! تم تسجيلك في قاعدة البيانات بنجاح. 🚀")
