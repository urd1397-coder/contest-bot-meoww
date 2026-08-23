import os
import telebot

# قراءة التوكن ومعرف القناة من الخزانة السرية في ريندر
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! البوت يعمل الآن بنجاح سحابياً ومستقر 100%")

if __name__ == '__main__':
    print("جاري تشغيل البوت سحابياً بنجاح...")
    bot.infinity_polling()
