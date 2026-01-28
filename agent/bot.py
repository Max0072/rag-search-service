import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime

from config import TELEGRAM_TOKEN, MAX_ITERATIONS
from graph import agent

logging.basicConfig(level=logging.INFO)

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
        # Запуск агента
        config = {"configurable": {"thread_id": str(chat_id)}}

        result = await agent.ainvoke(
            {
                "user_query": user_query,
                "chat_id": chat_id,
                "iteration_count": 0,
                "max_iterations": MAX_ITERATIONS,
                "search_history": [],
                "accumulated_results": [],
                "action": "",
                "reasoning": "",
                "search_request": {},
                "final_answer": ""
            },
            config=config
        )

        # Отправляем ответ
        answer = result.get("final_answer", "Не удалось сформировать ответ")
        await message.answer(answer, parse_mode="")

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())