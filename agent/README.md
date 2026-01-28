# Telegram RAG Agent

Минималистичный агент с LangGraph для поиска по транскриптам созвонов.

## Установка

```bash
cd agent
pip install -r requirements.txt
```

## Настройка

Создай `.env`:
```bash
cp .env.example .env
```

Заполни:
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `OPENAI_API_KEY` - Anthropic API key
- `RAG_API_URL` - URL RAG API

## Запуск

```bash
python bot.py
```

## Как работает

1. Пользователь задает вопрос в Telegram
2. Claude планирует первый поиск (summaries)
3. Итеративный цикл (макс 5 итераций):
   - Claude анализирует результаты
   - Решает: искать детали (chunks) или отвечать
4. Claude генерирует финальный ответ