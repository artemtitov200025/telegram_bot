from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from dotenv import load_dotenv
import os
import random
from PIL import Image, ImageDraw, ImageFont

# Загрузка токена
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📚 Вопросы для викторины
questions = [
    {
        "question": "Какой язык чаще всего используют для Telegram-ботов?",
        "options": ["Python", "Excel", "Java", "C++"],
        "answer": "Python"
    },
    {
        "question": "Что делает функция print() в Python?",
        "options": ["Печатает текст", "Удаляет файл", "Очищает память", "Закрывает окно"],
        "answer": "Печатает текст"
    }
]

# ▶️ Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот: создаю мемы и провожу викторины 🤖")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/menu — открой меню\n/start — перезапуск")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "привет" in text:
        await update.message.reply_text("Привет! Рад тебя видеть 👋")
    else:
        await update.message.reply_text(update.message.text)

# 📋 Главное меню
keyboard = [
    [InlineKeyboardButton("🎲 Случайный Мем", callback_data="random_meme"),
     InlineKeyboardButton("🖼️ Создать Мем", callback_data="create_meme")],
    [InlineKeyboardButton("❓ Викторина", callback_data="quiz"),
     InlineKeyboardButton("🏆 Топ Игроков", callback_data="top")]
]
menu = InlineKeyboardMarkup(keyboard)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери действие:", reply_markup=menu)

# 🔘 Обработка кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "random_meme":
        await query.edit_message_text("🎲 Мем будет здесь позже")
    elif data == "create_meme":
        await query.edit_message_text("🖼️ Пришли фото для мема")
        context.user_data["wait_for_photo"] = True
    elif data == "quiz":
        await send_quiz(update, context)  # ✅ ИСПРАВЛЕНО: запускаем викторину
    elif data == "top":
        await query.edit_message_text("🏆 Тут будет таблица лидеров")
    elif data.startswith("answer_"):
        await check_answer(update, context, data)

# 📸 Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("wait_for_photo"):
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    os.makedirs("temp", exist_ok=True)
    await file.download_to_drive("temp/meme.jpg")

    context.user_data["wait_for_photo"] = False
    context.user_data["wait_for_text"] = True

    await update.message.reply_text("✏️ А теперь пришли текст для мема!")

# 📝 Обработка текста мема
async def handle_meme_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("wait_for_text"):
        return

    text = update.message.text
    img = Image.open("temp/meme.jpg")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", size=40)
    except:
        font = ImageFont.load_default()

    width, height = img.size
    x, y = 20, height - 60

    for dx in range(-2, 3):
        for dy in range(-2, 3):
            draw.text((x + dx, y + dy), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill="white")

    img.save("temp/final_meme.jpg")
    await update.message.reply_photo(photo=open("temp/final_meme.jpg", "rb"))

    context.user_data["wait_for_text"] = False

# ❓ Отправка вопроса
async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    q = random.choice(questions)
    context.user_data["correct_answer"] = q["answer"]

    buttons = [
        InlineKeyboardButton(opt, callback_data=f"answer_{opt}")
        for opt in q["options"]
    ]
    markup = InlineKeyboardMarkup.from_column(buttons)

    await query.edit_message_text(q["question"], reply_markup=markup)

# ✅ Проверка ответа
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    query = update.callback_query
    selected = data.replace("answer_", "")
    correct = context.user_data.get("correct_answer")

    if selected == correct:
        await query.edit_message_text(f"✅ Верно! Это {correct}.")
    else:
        await query.edit_message_text(f"❌ Неверно. Правильный ответ: {correct}.")

# 🚀 Запуск приложения
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("menu", menu_handler))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_meme_text))
app.add_handler(MessageHandler(filters.TEXT, echo))

app.run_polling()
