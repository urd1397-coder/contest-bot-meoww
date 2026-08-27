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

# الاتصال المشفر بـ MongoDB مع دعم شهادات certifi وتجاوز أخطاء SSL الاحتياطي
mongo_client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    tlsAllowInvalidCertificates=True,  # لضمان عدم توقف البوت في حال فشل شهادة SSL
    serverSelectionTimeoutMS=5000     # تقليل مهلة الاتصال لمنع أي تأخير في الاستجابة
)
db = mongo_client["contest_db"]
users_collection = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ذاكرة سريعة جداً في الـ RAM للرد اللحظي
cached_users = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. تفعيل الـ Webhook فوراً
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    
    # 2. تحميل المستخدمين للكاش في الخلفية بدون تعطيل تشغيل البوت
    try:
        await users_collection.create_index("user_id", unique=True)
        existing_ids = await users_collection.distinct("user_id")
        cached_users.update(existing_ids)
        print(f"✅ Loaded {len(cached_users)} users into RAM cache.")
    except Exception as e:
        print(f"⚠️ Warning during Mongo setup: {e}")
        
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
        print(f"Error handling update: {e}")
    return {"ok": True}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # ⚡ رد فوري ولحظي في جزء من الثانية عبر الذاكرة
    if user_id in cached_users:
        await message.answer(f"أهلاً بك مجدداً يا {first_name}! 👋")
    else:
        cached_users.add(user_id)
        await message.answer(f"أهلاً بك يا {first_name}! تم تسجيلك في قاعدة البيانات بنجاح. 🚀")
        
        # 💾 حفظ المستفيد في MongoDB في الخفاء
        try:
            await users_collection.insert_one({"user_id": user_id, "name": first_name})
        except Exception as e:
            print(f"DB Insert Warning: {e}")
