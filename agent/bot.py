import asyncio
import logging
import sys
from pathlib import Path
from threading import Thread

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime

from config import TELEGRAM_TOKEN
from graph import agent

# Import Flask для dashboard
from flask import Flask, render_template, jsonify
from graph import CURRENT_CHAT_STATE, CURRENT_SEARCH_STATE

logging.basicConfig(level=logging.INFO)

# Flask app для dashboard (указываем путь к templates)
template_dir = Path(__file__).parent / "templates"
flask_app = Flask(__name__, template_folder=str(template_dir))

@flask_app.route('/')
def index():
    return render_template('dashboard.html')

@flask_app.route('/api/chat_state')
def get_chat_state():
    return jsonify(CURRENT_CHAT_STATE)

@flask_app.route('/api/search_state')
def get_search_state():
    return jsonify(CURRENT_SEARCH_STATE)

def run_flask():
    """Запуск Flask в отдельном потоке"""
    flask_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)


bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()




@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я RAG-агент для поиска по транскриптам конференций.\n\n"
        "Задай мне вопрос о созвонах, и я найду информацию."
    )



@dp.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    user_query = message.text

    # Уведомление
    await message.answer("🔍 Ищу информацию...")


    try:
        # Запуск Chat Agent с памятью диалога
        config = {"configurable": {"thread_id": str(chat_id)}}
        result = await agent.ainvoke(
            {
                "user_query": user_query,
                "chat_id": chat_id,
                "messages": [{"role": "user", "content": user_query}],  # operator.add добавит к истории в формате messages

            },
            config=config
        )

        # Отправляем ответ
        answer = result["messages"][-1]["content"]
        await message.answer(answer, parse_mode="")

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запускаем Flask dashboard в отдельном потоке
    dashboard_thread = Thread(target=run_flask, daemon=True)
    dashboard_thread.start()
    logging.info("🌐 Dashboard запущен на http://localhost:5001")

    # Запускаем Telegram бота
    asyncio.run(main())