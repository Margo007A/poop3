import logging
import json
import random
import asyncio
from datetime import datetime, timedelta
import pytz

from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# === ТВОИ ДАННЫЕ ===
BOT_TOKEN = "8276571944:AAF3ypIPxV-IPJYW-Rr6PiEql8vUONzEGeE"
GROUP_CHAT_ID = -1002444770684
THREAD_ID = 2
REMINDER_HOUR = 20
REMINDER_MINUTE = 50
USER_DATA_FILE = "subscribers.json"
MSK = pytz.timezone("Europe/Moscow")

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)

# === ЗАГРУЗКА/СОХРАНЕНИЕ ===
def load_users():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

subscribers = load_users()

# === ШУТКИ ===
JOKES = [
    "📸 Скрин или позор. Ты знаешь, что делать!",
    "⏰ Не забудь про актив в 20:50!",
    "😴 Просыпайся, пора скринить!",
] + [f"🎭 Шутка #{i}" for i in range(10)]

# === ПРОВЕРКА УЧАСТНИКА ГРУППЫ ===
async def is_user_in_group(bot, user_id):
    try:
        member = await bot.get_chat_member(GROUP_CHAT_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except:
        return False

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return

    if not await is_user_in_group(context.bot, user.id):
        await update.message.reply_text("❌ Только участники группы могут подписаться.")
        return

    if user.id not in subscribers:
        subscribers.append(user.id)
        save_users(subscribers)
        await update.message.reply_text("✅ Подписка оформлена.")
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=THREAD_ID,
            text=f"✅ @{user.username or user.first_name} нажал /start и подписался на напоминание."
        )
    else:
        await update.message.reply_text("🙂 Ты уже подписан.")

# === /stop ===
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in subscribers:
        subscribers.remove(update.effective_user.id)
        save_users(subscribers)
        await update.message.reply_text("❌ Подписка отменена.")
    else:
        await update.message.reply_text("Ты и так не подписан.")

# === /list ===
async def list_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not subscribers:
        text = "📭 Никто не подписан."
    else:
        text = "📋 Список подписчиков:\n" + "\n".join([f"[{uid}](tg://user?id={uid})" for uid in subscribers])
    await update.message.reply_text(text, parse_mode="Markdown")

# === ЦИКЛ НАПОМИНАНИЯ ===
async def reminder_loop(bot):
    while True:
        now = datetime.now(MSK)
        target = now.replace(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait = (target - now).total_seconds()
        await asyncio.sleep(wait)

        try:
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=THREAD_ID,
                text="⏰ Все участники группы получили уведомление о скринах в 20:50 по МСК!"
            )
        except Exception as e:
            logging.warning(f"Ошибка при отправке в тему: {e}")

        for uid in subscribers:
            try:
                await bot.send_message(chat_id=uid, text=random.choice(JOKES))
            except Exception as e:
                logging.warning(f"Ошибка отправки пользователю {uid}: {e}")

# === ЗАПУСК ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("list", list_subs))
    asyncio.create_task(reminder_loop(app.bot))
    print("✅ Бот запущен и ждёт 20:50 по МСК...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())



