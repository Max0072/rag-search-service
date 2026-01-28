# Agent Structure

```
agent/
├── config.py           # Настройки (API keys, URLs)
├── prompts.py          # Системные промпты для Claude
├── graph.py            # LangGraph workflow + nodes
├── bot.py              # Telegram bot (aiogram)
└── requirements.txt    # Зависимости
```

## Файлы

**config.py** - API keys, URLs для RAG и Anthropic

**prompts.py** - 3 промпта: initial_search, evaluate_decide, generate_answer

**graph.py** - LangGraph граф с 4 нодами:
- plan_initial_search → execute_search → evaluate_decide → (loop или generate_answer)

**bot.py** - Telegram bot, принимает сообщения, запускает граф

**requirements.txt** - aiogram, langgraph, anthropic, httpx