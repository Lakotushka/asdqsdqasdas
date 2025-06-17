from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from collections import defaultdict

TOKEN = '8016045720:AAGfuGdwcaK2S8w6_CQMlUhICA2v8svrg4g'

user_data = defaultdict(lambda: {"games": [], "current_game": set(), "game_count": 0})

def game_kb(active):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("💣" if i in active else "🍪", callback_data=f"cell_{i}") for i in range(r * 5, r * 5 + 5)] for r in range(5)]
        + [[InlineKeyboardButton("Стоп", callback_data="stop")]]
    )

def prediction_kb(safe_cells):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("💎" if i in safe_cells else "💣", callback_data="none") for i in range(r * 5, r * 5 + 5)] for r in range(5)]
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {"games": [], "current_game": set(), "game_count": 0}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="start_game")]])
    await update.message.reply_text("Нажмите «Начать игру»", reply_markup=kb)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()
    d = q.data
    u = user_data[uid]

    if d == "start_game":
        u["current_game"] = set()
        await q.edit_message_text("Игра началась!", reply_markup=game_kb(u["current_game"]))

    elif d.startswith("cell_"):
        i = int(d.split("_")[1])
        u["current_game"].symmetric_difference_update({i})
        await q.edit_message_reply_markup(reply_markup=game_kb(u["current_game"]))

    elif d == "stop":
        u["games"].append(u["current_game"].copy())
        u["game_count"] += 1
        if u["game_count"] < 4:
            await q.edit_message_text(
                f"Игра {u['game_count']} завершена.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="start_game")]])
            )
        else:
            await q.edit_message_text(
                "Все 4 игры завершены. Получить прогноз?",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Получить прогноз", callback_data="get_prediction")]])
            )

    elif d == "get_prediction":
        safe_scores = [0] * 25
        for game in u["games"]:
            for i in range(25):
                if i not in game:
                    safe_scores[i] += 1

        top_safe = sorted(range(25), key=lambda i: safe_scores[i], reverse=True)[:5]
        safe_set = set(top_safe)

        kb = prediction_kb(safe_set)
        await q.edit_message_text("Прогноз: 5 безопасных клеток 💎", reply_markup=kb)
        await q.message.reply_text(
            "Новая сессия?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Новый прогноз", callback_data="new_session")]])
        )

    elif d == "new_session":
        user_data[uid] = {"games": [], "current_game": set(), "game_count": 0}
        await q.edit_message_text(
            "Новая сессия",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать игру", callback_data="start_game")]])
        )

    elif d == "none":
        await q.answer("Это только визуализация", show_alert=False)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Бот запущен...")
    app.run_polling()