# Search API Server for Conference Calls

Простой API сервер для поиска по транскриптам конференций.
Используется вместе с n8n для построения агентных workflows.

## Структура проекта

```
best_search_engine/
├── app/
│   ├── api/          # FastAPI endpoints
│   ├── database/     # Подключение к Vector DB и Metadata DB
│   └── search/       # Логика поиска (hybrid search, фильтры)
├── tests/            # Тесты
├── .env              # Переменные окружения (создать из .env.example)
└── main.py           # Точка входа
```

## Что делает этот сервер?

**Два типа endpoints:**
1. **POST /search** - Поиск по chunks с фильтрами (hybrid retrieval)
2. **CRUD endpoints для calls** - Управление полными данными звонков

### Пример запроса:

```json
POST /search
{
  "filter": {
    "date_range": {"from": "2024-03-01", "to": "2024-03-31"},
    "attendants": ["John"],
    "chunks": "API problems"
  },
  "top_k": 10,
  "min_score": 0.7
}
```

### Пример ответа:

```json
{
  "results": [
    {
      "call_id": "call-123",
      "chunk_text": "John: We found API timeout issues...",
      "score": 0.87,
      "date": "2024-03-15",
      "attendants": ["John", "Alice"]
    }
  ],
  "total_found": 45,
  "avg_score": 0.76
}
```

## Логика агента - в n8n

Вся итеративная логика, принятие решений, повторные запросы - всё это делается в n8n workflow.
Этот сервер просто отвечает на search запросы.

## Быстрый старт

### Вариант 1: Docker (Рекомендуется)

```bash
# 1. Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env и добавьте свои API ключи

# 2. Запуск через Docker Compose
docker-compose up -d

# 3. Проверка здоровья
curl http://localhost:8000/api/v1/health

# Документация API: http://localhost:8000/docs
```

### Вариант 2: Локальная установка

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка .env
cp .env.example .env
# Добавить API ключи в .env

# 3. Запуск PostgreSQL (если не используете Docker)
# Убедитесь что PostgreSQL запущен и доступен

# 4. Запуск сервера
python main.py

# Сервер доступен на http://localhost:8000
# Документация API: http://localhost:8000/docs
```

## Архитектура двух баз данных

Система использует две базы данных согласно архитектуре из project_idea.md:

### 1. Vector Database (Pinecone)
- **Назначение**: Быстрый поиск по chunks с semantic search
- **Хранит**: Embeddings chunks, денормализованные метаданные
- **Используется для**: Real-time поиск, similarity queries

### 2. Metadata Database (PostgreSQL)
- **Назначение**: "Холодное хранилище" - полные данные звонков
- **Хранит**: Полные транскрипты, summaries, метаданные
- **Используется для**: Получение полного контекста после поиска

## API Endpoints

### Search Endpoint
- `POST /api/v1/search` - Поиск по chunks (vector DB)

### Call Management
- `POST /api/v1/calls` - Создать новый звонок (metadata DB)
- `GET /api/v1/calls/{call_id}` - Получить полный звонок с транскриптом
- `GET /api/v1/calls` - Список звонков с фильтрами
- `DELETE /api/v1/calls/{call_id}` - Удалить звонок

### Utility Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/stats` - Статистика обеих баз данных
- `POST /api/v1/embed` - Генерация embedding (для отладки)

## Деплой на Railway

Railway автоматически поддерживает Docker деплой. Следуйте этим шагам:

### 1. Подготовка

```bash
# Убедитесь что все файлы готовы
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Создание проекта в Railway

1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите свой репозиторий

### 3. Добавление PostgreSQL

1. В Railway проекте нажмите "New"
2. Выберите "Database" → "PostgreSQL"
3. Railway автоматически создаст переменную `DATABASE_URL`

### 4. Настройка переменных окружения

В Railway добавьте следующие переменные:

```
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_CLOUD=aws
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=conference-calls
PINECONE_SUMMARIES_INDEX_NAME=conference-summaries
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=1536
DATABASE_ECHO=false
MAX_ITERATIONS=5
DEFAULT_TOP_K=10
MIN_RELEVANCE_SCORE=0.7
API_RELOAD=false
```

**Важно**: Railway автоматически установит `DATABASE_URL` и `PORT`

### 5. Деплой

Railway автоматически:
- Обнаружит Dockerfile
- Соберет образ
- Запустит контейнер
- Настроит networking

После деплоя ваш API будет доступен по адресу вида: `https://your-app.railway.app`

### 6. Проверка

```bash
# Замените URL на свой Railway URL
curl https://your-app.railway.app/api/v1/health
```

## Технологии

- **API**: FastAPI
- **Vector DB**: Pinecone (для chunks + embeddings)
- **Metadata DB**: PostgreSQL + SQLAlchemy (для полных данных)
- **Embeddings**: OpenAI text-embedding-3-large
- **Search**: Hybrid (dense + sparse/BM25)
- **Deploy**: Docker + Railway