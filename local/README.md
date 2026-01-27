# Локальный запуск RAG Service

Минимальная конфигурация для запуска на локальной машине.

## Предварительные требования

1. **Docker Desktop** установлен и запущен
2. **OpenAI API Key** - [получить здесь](https://platform.openai.com/api-keys)
3. **Pinecone Account** - [зарегистрироваться здесь](https://app.pinecone.io/) (есть бесплатный план)

## Быстрый старт

### 1. Настройка API ключей

Откройте файл `local/.env.local` и замените заглушки на реальные ключи:

```bash
# Вместо этого:
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# Вставьте свой ключ:
OPENAI_API_KEY=sk-proj-...
```

То же самое для `PINECONE_API_KEY`.

### 2. Создание индексов в Pinecone

Перед запуском нужно создать два индекса в Pinecone:

1. Зайдите в [Pinecone Console](https://app.pinecone.io/)
2. Создайте индекс `conference-calls`:
   - **Name**: `conference-calls`
   - **Dimensions**: `1536`
   - **Metric**: `cosine`
   - **Cloud**: `AWS`
   - **Region**: `us-east-1`

3. Создайте индекс `conference-summaries`:
   - **Name**: `conference-summaries`
   - **Dimensions**: `1536`
   - **Metric**: `cosine`
   - **Cloud**: `AWS`
   - **Region**: `us-east-1`

### 3. Запуск сервиса

```bash
# Из директории local/ выполните:
docker-compose -f docker-compose.local.yml up --build
```

Или из корня проекта:
```bash
docker-compose -f local/docker-compose.local.yml up --build
```

### 4. Проверка

Откройте в браузере:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

Ожидаемый ответ от health check:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "services": {
    "vector_db": "connected",
    "metadata_db": "connected"
  }
}
```

## Остановка

```bash
# Остановить с сохранением данных
docker-compose -f local/docker-compose.local.yml down

# Остановить и удалить все данные (включая PostgreSQL)
docker-compose -f local/docker-compose.local.yml down -v
```

## Загрузка тестовых данных

После запуска можете загрузить тестовые данные:

```bash
# Из корня проекта
python real_test_data_for_api/test.py
```

## Структура

```
local/
├── docker-compose.local.yml  # Docker Compose конфигурация
├── .env.local                # API ключи и настройки (не коммитить!)
└── README.md                 # Эта инструкция
```

## Troubleshooting

### Ошибка: "Connection refused" при старте API

PostgreSQL еще не успел запуститься. Подождите 10-15 секунд и API автоматически переподключится.

### Ошибка: "Invalid API Key"

Проверьте что в `.env.local` прописаны реальные ключи без лишних пробелов.

### Ошибка: "Index not found"

Создайте индексы в Pinecone согласно шагу 2.

### Порт 5432 уже занят

Если у вас уже запущен PostgreSQL на хосте, измените порт в `docker-compose.local.yml`:
```yaml
ports:
  - "5433:5432"  # Изменить на 5433 или другой свободный порт
```

## Логи

Смотреть логи в реальном времени:
```bash
docker-compose -f local/docker-compose.local.yml logs -f api
```

## Доступ к PostgreSQL

```bash
# Подключиться к базе данных
docker exec -it rag_postgres_local psql -U raguser -d conference_db
```