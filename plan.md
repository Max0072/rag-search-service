# План разработки Search API Server

## Цель проекта
Создать простой API сервер с endpoint `/search` для поиска по транскриптам конференций.
Вся агентная логика будет в n8n, сервер только обрабатывает search запросы.

---

## Phase 1: Базовая инфраструктура

### 1.1 Настройка проекта
- [ ] `requirements.txt` - зависимости (FastAPI, Pinecone, OpenAI, etc.)
- [ ] `main.py` - точка входа для запуска сервера
- [ ] `.env` - создать из `.env.example` и настроить

### 1.2 FastAPI основа
- [ ] `app/api/main.py` - FastAPI приложение
- [ ] `app/api/routes.py` - роуты (пока пустые)
- [ ] Базовый endpoint `GET /health` для проверки работоспособности

### 1.3 Data Models
- [ ] `app/models.py` - Pydantic модели для:
  - `SearchRequest` (входящий запрос)
  - `SearchFilter` (фильтры)
  - `SearchResult` (результат)
  - `ChunkResult` (один chunk из результатов)

---

## Phase 2: Database Layer

### 2.1 Vector Database (Pinecone)
- [ ] `app/database/vector_db.py` - подключение к Pinecone
  - Инициализация клиента
  - Метод `query()` для vector search
  - Метод `upsert()` для добавления данных (для тестов)

### 2.2 Metadata Database (опционально для MVP)
- [ ] Решить: PostgreSQL или просто хранить всё в Pinecone metadata?
- [ ] Если отдельная БД - `app/database/metadata_db.py`

### 2.3 Embeddings
- [ ] `app/database/embeddings.py` - генерация эмбеддингов
  - OpenAI `text-embedding-3-large`
  - Кеширование если нужно

---

## Phase 3: Search Logic

### 3.1 Unified Search Tool
- [ ] `app/search/search_engine.py` - главная логика поиска
  - Функция `search(filter, top_k, min_score, ...)`
  - Обработка metadata фильтров
  - Semantic search (dense retrieval)

### 3.2 Фильтры
- [ ] Metadata фильтры:
  - `call_id` - поиск по конкретному созвону
  - `date_range` - диапазон дат
  - `attendants` - участники (ANY logic)
  - `meeting_type` - тип встречи
- [ ] Semantic фильтры:
  - `chunks` - семантический поиск по содержимому

### 3.3 Hybrid Search (опционально для MVP)
- [ ] Sparse retrieval (BM25/keyword)
- [ ] Fusion результатов dense + sparse
- [ ] `app/search/hybrid.py`

---

## Phase 4: API Implementation

### 4.1 Main Search Endpoint
- [ ] `POST /search` - основной endpoint
  - Парсинг `SearchRequest`
  - Валидация параметров
  - Вызов `search_engine.search()`
  - Форматирование ответа `SearchResult`

### 4.2 Вспомогательные endpoints
- [ ] `POST /embed` - получить embedding для текста (для отладки)
- [ ] `GET /stats` - статистика по базе (сколько созвонов, chunks, etc.)

---

## Phase 5: Testing & Data

### 5.1 Тестовые данные
- [ ] Создать скрипт для загрузки тестовых данных
  - 5-10 фейковых транскриптов
  - Разбиение на chunks
  - Генерация embeddings
  - Загрузка в Pinecone

### 5.2 Тесты
- [ ] `tests/test_api.py` - тесты API endpoints
- [ ] `tests/test_search.py` - тесты логики поиска
- [ ] `tests/test_filters.py` - тесты фильтров

---

## Phase 6: Integration & Documentation

### 6.1 n8n Integration
- [ ] Пример n8n workflow для вызова API
- [ ] Документация как подключить из n8n

### 6.2 API Documentation
- [ ] FastAPI автодокументация (Swagger UI)
- [ ] Примеры запросов в README.md

---

## Минимальный MVP (что нужно в первую очередь)

1. ✅ Структура проекта
2. ⬜ FastAPI сервер с базовым `/health`
3. ⬜ Pydantic модели для запросов/ответов
4. ⬜ Подключение к Pinecone
5. ⬜ Базовый semantic search (только по `chunks`)
6. ⬜ Простые metadata фильтры (`call_id`, `date_range`)
7. ⬜ Тестовые данные (3-5 созвонов)
8. ⬜ Работающий `POST /search` endpoint

После MVP можно добавлять:
- Hybrid search
- Больше фильтров
- Оптимизации
- Reranking
- И т.д.

---

## Технические решения

### Vector DB: Pinecone
- Простая интеграция
- Managed solution
- Поддержка metadata filtering из коробки

### Структура данных в Pinecone:
```python
{
  "id": "chunk-uuid",
  "values": [1536-dim embedding],
  "metadata": {
    "chunk_text": "Alice: We discussed...",
    "call_id": "call-123",
    "date": "2024-03-15",
    "attendants": ["Alice", "Bob"],
    "meeting_type": "client_call",
    "chunk_index": 5
  }
}
```

### API Request/Response format:
**Request:**
```json
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

**Response:**
```json
{
  "results": [
    {
      "call_id": "call-123",
      "chunk_text": "...",
      "score": 0.87,
      "date": "2024-03-15",
      "attendants": ["John", "Alice"],
      "chunk_index": 5
    }
  ],
  "total_found": 45,
  "avg_score": 0.76,
  "execution_time_ms": 123
}
```

---

## Следующие шаги
1. Начать с Phase 1 - базовая инфраструктура
2. Создать requirements.txt и main.py
3. Запустить пустой FastAPI сервер
4. Подключить Pinecone
5. Реализовать простейший search