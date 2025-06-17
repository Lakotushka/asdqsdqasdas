from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
)
import logging
from collections import defaultdict
import random

# ВСТАВЬ СЮДА СВОЙ ТОКЕН
TOKEN = '8016045720:AAGfuGdwcaK2S8w6_CQMlUhICA2v8svrg4g'

logging.basicConfig(level=logging.INFO)
user_data = defaultdict(lambda: {
    "games": [],
    "current_game": set(),
    "game_count": 0
})

# Создание клавиатуры 5x5
def create_game_keyboard():
    keyboard = []
    for i in range(5):
        row = [InlineKeyboardButton(f"{i*5+j+1}", callback_data=f"cell_{i*5+j}") for j in range(5)]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Стоп", callback_data="stop")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {
        "games": [],
        "current_game": set(),
        "game_count": 0
    }
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="start_game")]])
    await update.message.reply_text("Добро пожаловать! Нажмите кнопку, чтобы начать игру.", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data

    if data == "start_game":
        user_data[user_id]["current_game"] = set()
        await query.edit_message_text("Игра началась! Нажимайте на клетки.", reply_markup=create_game_keyboard())

    elif data.startswith("cell_"):
        cell = int(data.split("_")[1])
        user_data[user_id]["current_game"].add(cell)
        await query.answer(f"Мина установлена в клетке {cell}")

    elif data == "stop":
        user_data[user_id]["games"].append(user_data[user_id]["current_game"].copy())
        user_data[user_id]["game_count"] += 1

        if user_data[user_id]["game_count"] < 4:
            await query.edit_message_text(f"Игра {user_data[user_id]['game_count']} завершена. Нажмите «Начать игру» для следующей.",
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="start_game")]]))
        else:
            await query.edit_message_text("Все 4 игры завершены. Получить прогноз?",
                                          reply_markup=InlineKeyboardMarkup([
                                              [InlineKeyboardButton("Получить прогноз", callback_data="get_prediction")]
                                          ]))

    elif data == "get_prediction":
        safe_prob = [0] * 25
        for game in user_data[user_id]["games"]:
            for i in range(25):
                if i not in game:
                    safe_prob[i] += 1  # безопасные клетки получают баллы

        # Сортируем по наименьшей вероятности мины (наибольшей безопасности)
        sorted_cells = sorted([(i + 1, safe_prob[i]) for i in range(25)], key=lambda x: -x[1])

        top_safe_cells = [f"{cell[0]}" for cell in sorted_cells[:5]]
        msg = "Наиболее безопасные клетки (по истории):\n" + ", ".join(top_safe_cells)

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Новый прогноз", callback_data="new_session")]
        ]))

    elif data == "new_session":
        user_data[user_id] = {
            "games": [],
            "current_game": set(),
            "game_count": 0
        }
        await query.edit_message_text("Новая сессия. Начнем заново!", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Начать игру", callback_data="start_game")]
        ]))


if name == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()