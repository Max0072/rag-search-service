# Iterative RAG Agent for Conference Call Analysis

## 🎯 Проект Overview

Система итеративного агента с инструментами для поиска и анализа информации из транскриптов конференций и созвонов. Агент использует Context-Augmented Generation (RAG) с комбинацией dense (векторного) и sparse (keyword) retrieval для эффективного поиска релевантной информации.

### Ключевая идея

**Итеративный подход**: Агент не делает один запрос и возвращает результат. Вместо этого он:
1. Анализирует запрос пользователя
2. Выполняет поиск с применением фильтров
3. Оценивает качество найденной информации
4. Решает: достаточно ли данных или нужно уточнить поиск
5. Итеративно улучшает результаты до получения качественного ответа

---

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Query                              │
│              "Что обсуждал Джон на последней встрече?"          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Iterative Agent (LLM)                        │
│  • Анализирует запрос                                           │
│  • Выбирает стратегию поиска                                    │
│  • Формирует параметры для search()                             │
│  • Оценивает результаты                                         │
│  • Решает: продолжить поиск или генерировать ответ              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Unified Search Tool                         │
│                        search(...)                              │
│                                                                 │
│  Единый интерфейс для всех типов поиска и фильтрации            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Filter Pipeline Engine                        │
│                                                                 │
│  Step 1: Metadata Filters (fast, cheap)                         │
│  ┌──────────────────────────────────────────┐                   │
│  │ • date_range                             │                   │
│  │ • attendants                             │                   │
│  │ • meeting_type                           │                   │
│  │ • call_id                                │                   │
│  └──────────┬───────────────────────────────┘                   │
│             │ 1000 calls → 50 calls                             │
│             ▼                                                   │
│  Step 2: Semantic Filters (expensive)                           │
│  ┌──────────────────────────────────────────┐                   │
│  │ Dense Retrieval (vector search)          │                   │
│  │ + Sparse Retrieval (keyword/BM25)        │                   │
│  │ → Hybrid fusion                          │                   │
│  └──────────┬───────────────────────────────┘                   │
│             │ 50 calls → 10 relevant results                    │
│             ▼                                                   │
│  Step 3: Post-processing                                        │
│  ┌──────────────────────────────────────────┐                   │
│  │ • Score threshold (min_score)            │                   │
│  │ • Top-K selection                        │                   │
│  │ • Sorting                                │                   │
│  │ • Field extraction                       │                   │
│  └──────────────────────────────────────────┘                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Storage Layer                         │
│                                                                 │
│  ┌─────────────────────┐        ┌──────────────────────┐        │
│  │   Vector Database   │        │  Metadata Database   │        │
│  │  (Pinecone/Qdrant)  │        │   (PostgreSQL/etc)   │        │
│  ├─────────────────────┤        ├──────────────────────┤        │
│  │ chunks:             │        │ calls:               │        │
│  │ • chunk_text        │        │ • call_id            │        │
│  │ • chunk_embedding   │◄───────┤ • summary            │        │
│  │ • call_id (FK)      │        │ • full_transcript    │        │
│  │ • chunk_index       │        │ • date               │        │
│  │ • metadata (denorm) │        │ • attendants         │        │
│  │                     │        │ • meta               │        │
│  ├─────────────────────┤        ├──────────────────────┤        │
│  │ summaries:          │        │                      │        │
│  │ • summary_text      │        │                      │        │
│  │ • summary_embedding │        │                      │        │
│  │ • call_id (FK)      │        │                      │        │
│  │ • metadata (denorm) │        │                      │        │
│  └─────────────────────┘        └──────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Структура данных

### Vector Database (для поиска)

```python
# Chunks - детальные фрагменты транскриптов
chunks = [
    {
        "chunk_id": "uuid",
        "chunk_text": "Alice: Мы обнаружили проблему с API...",
        "chunk_embedding": [1536-dim vector],
        "chunk_index": 5,  # порядковый номер в транскрипте

        # Денормализованные метаданные (для быстрой фильтрации)
        "call_id": "call-123",
        "date": "2024-03-15",
        "attendants": ["Alice", "Bob", "John"],
        "meeting_type": "client_call",
        "department": "engineering",

        # Опционально
        "timestamp_start": "00:15:30",
        "timestamp_end": "00:17:45",
        "speaker": "Alice"
    }
]

# Summaries - краткие содержания созвонов
summaries = [
    {
        "summary_id": "uuid",
        "summary_text": "Обсуждение проблем интеграции API с клиентом...",
        "summary_embedding": [1536-dim vector],

        # Метаданные
        "call_id": "call-123",
        "date": "2024-03-15",
        "attendants": ["Alice", "Bob", "John"],
        "topic": "API Integration Review",
        "meeting_type": "client_call",
        "department": "engineering"
    }
]
```

### Metadata Database (холодное хранилище)

```python
# Полные данные о созвонах
calls = [
    {
        "call_id": "call-123",
        "full_transcript": "полный текст транскрипта...",
        "summary": "краткое содержание...",

        # Метаданные
        "date": "2024-03-15T14:30:00Z",
        "attendants": ["Alice", "Bob", "John"],
        "topic": "API Integration Review",
        "meeting_type": "client_call",
        "duration_minutes": 45,

        # Дополнительные данные
        "meta": {
            "department": "engineering",
            "project": "Project X",
            "client_name": "Acme Corp",
            "language": "ru",
            "recording_url": "https://..."
        },

        # Служебные поля
        "chunks_count": 42,
        "created_at": "2024-03-15T14:30:00Z",
        "processed_at": "2024-03-15T16:00:00Z"
    }
]
```

---

## 🔧 Unified Search Tool API

### Сигнатура

```python
def search(
    filter: dict = {},
    fields: list[str] = ["chunks"],
    top_k: int = 10,
    min_score: float = 0.0,
    sort_by: str = "relevance",
    sort_order: str = "desc"
) -> dict:
    """
    Универсальный инструмент поиска с единым интерфейсом
    """
    pass
```

### Параметры

#### `filter` - словарь фильтров

```python
filter = {
    # === METADATA FILTERS (применяются первыми) ===
    "call_id": "call-123",  # или ["call-123", "call-456"]
    "date": "2024-03-15",  # точная дата
    "date_range": {
        "from": "2024-03-01",
        "to": "2024-03-31"
    },
    "attendants": ["Alice", "Bob"],  # ANY logic (хотя бы один)
    "meeting_type": "client_call",
    "department": "engineering",

    # === SEMANTIC FILTERS (применяются после metadata) ===
    "chunks": "API integration problems",  # поиск по чанкам
    "summaries": "budget discussion",  # поиск по саммари

    # === KEYWORD FILTERS (точное совпадение) ===
    "contains": "API",  # должно содержать
    "not_contains": ["test", "demo"],  # не должно содержать

    # === ADVANCED ===
    "chunk_index_range": {"min": 0, "max": 10},  # начало созвона
    "timestamp_range": {
        "from": "00:05:00",
        "to": "00:15:00"
    },
    "speaker": "Alice"  # если есть speaker diarization
}
```

#### `fields` - какие поля вернуть

```python
fields = [
    "chunks",  # или "chunk_text"
    "call_id",
    "chunk_index",
    "summary",
    "date",
    "attendants",
    "meeting_type",
    "timestamp",
    "score",  # relevance score
    "speaker"
]
```

#### Другие параметры

- `top_k` - количество результатов (default: 10)
- `min_score` - минимальный similarity score для semantic filters (default: 0.0)
- `sort_by` - сортировка: "relevance" | "date" | "chunk_index" (default: "relevance")
- `sort_order` - порядок: "desc" | "asc" (default: "desc")

### Возвращаемое значение

```python
{
    "results": [
        {
            "call_id": "call-123",
            "chunk_text": "Alice: We found an API integration issue...",
            "chunk_index": 5,
            "score": 0.87,
            "date": "2024-03-15",
            "attendants": ["Alice", "Bob", "John"],
            "timestamp": "00:15:30",
            # ... другие запрошенные fields
        },
        # ... еще результаты
    ],
    "total_found": 150,  # всего найдено (до top_k)
    "calls_searched": 50,  # в скольки созвонах искали
    "avg_score": 0.76,  # средний score (для оценки качества)
    "execution_time_ms": 245
}
```

---

## 🔄 Итеративный процесс агента

### Пример: "Что Джон говорил на последней конференции?"

```
┌─────────────────────────────────────────────────────────────┐
│ ITERATION 1: Найти последнюю конференцию с Джоном          │
└─────────────────────────────────────────────────────────────┘

search(
  filter={
    "attendants": ["John"],
    "meeting_type": "conference"
  },
  fields=["call_id", "date", "summary", "attendants"],
  sort_by="date",
  sort_order="desc",
  top_k=1
)

→ Result: {
    call_id: "call-456",
    date: "2024-03-20",
    summary: "Q1 Results Conference Call",
    attendants: ["John", "Alice", "CEO"]
  }

Agent evaluation: ✓ Нашли созвон, переходим к деталям

┌─────────────────────────────────────────────────────────────┐
│ ITERATION 2: Получить всё что говорил Джон                 │
└─────────────────────────────────────────────────────────────┘

search(
  filter={
    "call_id": "call-456",
    "chunks": "John",  # semantic search упоминаний
    "speaker": "John"  # если есть speaker diarization
  },
  fields=["chunks", "chunk_index", "timestamp", "score"],
  sort_by="chunk_index",  # хронологический порядок
  top_k=50
)

→ Result: [
    {chunk: "John: Our Q1 revenue exceeded...", chunk_index: 3, ...},
    {chunk: "John: The main challenge was...", chunk_index: 15, ...},
    {chunk: "John: Looking forward, we plan...", chunk_index: 28, ...},
    ...
  ]

Agent evaluation: ✓ Достаточно информации для ответа

┌─────────────────────────────────────────────────────────────┐
│ FINAL: Генерация ответа с контекстом                       │
└─────────────────────────────────────────────────────────────┘

LLM генерирует структурированный ответ на основе найденных чанков
```

### Пример: "Какие проблемы с API обсуждались в марте?"

```
┌─────────────────────────────────────────────────────────────┐
│ ITERATION 1: Широкий поиск по теме                         │
└─────────────────────────────────────────────────────────────┘

search(
  filter={
    "date_range": {"from": "2024-03-01", "to": "2024-03-31"},
    "chunks": "API problems issues errors bugs",
    "contains": "API"  # keyword must be present
  },
  fields=["chunks", "call_id", "date", "attendants", "score"],
  top_k=20,
  min_score=0.7
)

→ Result: 20 chunks from 8 different calls
→ avg_score: 0.75

Agent evaluation: ✓ Нашли релевантные упоминания, но разрозненно

┌─────────────────────────────────────────────────────────────┐
│ ITERATION 2: Получить summaries для структурирования       │
└─────────────────────────────────────────────────────────────┘

# Извлекаем call_ids из результатов iteration 1
call_ids = ["call-123", "call-456", "call-789", ...]

search(
  filter={
    "call_id": call_ids,
    "summaries": "API integration"
  },
  fields=["summary", "call_id", "date", "attendants", "topic"],
  sort_by="date"
)

→ Result: summaries для контекста каждого обсуждения

Agent evaluation: ✓ Достаточно для структурированного ответа

┌─────────────────────────────────────────────────────────────┐
│ FINAL: Генерация ответа                                    │
└─────────────────────────────────────────────────────────────┘

LLM группирует проблемы по темам:
1. "Проблемы с timeout API (обсуждалось 5 марта, 12 марта)"
2. "Ошибки аутентификации (7 марта, 20 марта)"
3. "Performance issues (15 марта)"
+ цитаты из chunks для каждой проблемы
```

---

## 🎯 Стратегии поиска

### 1. Metadata-first (для известных параметров)

```
Запрос: "Найти обсуждение проекта X с клиентом Y в феврале"

1. Фильтр metadata → узкий scope
2. Semantic search только в отфильтрованном
3. Quick results

Эффективность: ⭐⭐⭐⭐⭐
```

### 2. Content-first (для открытых вопросов)

```
Запрос: "Где упоминались проблемы с производительностью?"

1. Semantic search по всей базе
2. Находим релевантные chunks
3. Группируем по call_id

Эффективность: ⭐⭐⭐ (дороже, но необходимо)
```

### 3. Two-stage (комбинированный)

```
Запрос: "Что обсуждалось про бюджет на встречах с CEO?"

Stage 1: Summary-level search
  - Быстро находим релевантные созвоны
  - filter: summaries="budget", attendants=["CEO"]

Stage 2: Chunk-level details
  - Детальный поиск только в найденных созвонах
  - filter: call_id=[...], chunks="budget allocation"

Эффективность: ⭐⭐⭐⭐ (оптимальный баланс)
```

### 4. Iterative refinement

```
Запрос: "Расскажи про проблемы команды разработки"

Iteration 1: Широкий поиск
  - filter: department="engineering", chunks="problems issues"
  - Result: много шума, avg_score=0.65

Iteration 2: Уточнение через reformulation
  - Agent reformulates: "technical challenges blockers bugs"
  - Result: лучше, avg_score=0.78

Iteration 3: Фокусировка на топ созвонах
  - Берём top-5 calls из iteration 2
  - Детальный поиск только в них

Эффективность: ⭐⭐⭐⭐ (качественно, но медленнее)
```

---

## 🚀 Integration с n8n

### Вариант 1: HTTP API Server

```
n8n Workflow:
[Webhook Trigger]
    ↓
[Set Variables]
  - user_query
  - max_iterations
    ↓
[HTTP Request] → POST /agent/query
  Body: {
    "query": "{{$json.user_query}}",
    "max_iterations": 5,
    "config": {...}
  }
    ↓
[Parse Response]
    ↓
[Format Output]
    ↓
[Send to User]
```

### Вариант 2: Python Code Node

```javascript
// n8n Code Node
const AgentAPI = {
  async query(userQuery) {
    const response = await fetch('http://localhost:8000/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        filter: {
          attendants: ["John"],
          chunks: userQuery
        },
        top_k: 10
      })
    });
    return await response.json();
  }
};

// Main logic
const query = $input.item.json.query;
const results = await AgentAPI.query(query);

return {
  json: {
    answer: results.answer,
    sources: results.sources,
    confidence: results.avg_score
  }
};
```

### Вариант 3: Direct Python Integration

```python
# В n8n Python Code Node (если поддерживается)

from rag_agent import IterativeAgent, SearchTool

# Initialize agent
agent = IterativeAgent(
    llm_config={"model": "claude-3-5-sonnet"},
    tools=[SearchTool()],
    max_iterations=5
)

# Execute query
user_query = item['query']
result = agent.run(user_query)

return {
    'answer': result.answer,
    'iterations_used': result.iterations,
    'sources': result.sources
}
```

---

## 🛠️ Technology Stack

### Core Components

**Agent Framework:**
- LLM: Claude 3.5 Sonnet (Anthropic) или GPT-4 (OpenAI)
- Tool calling: Native function calling support

**Vector Database:**
- **Option 1**: Pinecone (managed, easy)
- **Option 2**: Qdrant (open-source, fast)
- **Option 3**: Weaviate (GraphQL, hybrid search built-in)

**Metadata Database:**
- PostgreSQL (если нужны сложные запросы)
- MongoDB (для гибкой схемы)

**Embeddings:**
- OpenAI `text-embedding-3-large` (1536 dim)
- Cohere Embed v3 (многоязычные)

**Keyword Search:**
- BM25 (rank-bm25 library)
- Elasticsearch (для production)

### Optional Enhancements

**Reranking:**
- Cohere Rerank API
- Cross-encoder models (sentence-transformers)

**Chunking:**
- LangChain TextSplitter
- Custom semantic chunker

**Orchestration:**
- n8n (workflow automation)
- LangGraph (для сложных agent flows)

---

## 📈 Evaluation Metrics

### Search Quality

```python
metrics = {
    # Relevance
    "avg_relevance_score": 0.82,  # среднее по top-K
    "score_distribution": [0.95, 0.87, 0.82, 0.76, ...],

    # Coverage
    "recall@10": 0.75,  # нашли 75% релевантных
    "precision@10": 0.80,  # 80% найденного релевантно

    # Efficiency
    "calls_searched": 50,  # из 1000 total
    "search_time_ms": 245,
    "tokens_in_context": 3500,

    # Agent behavior
    "iterations_used": 3,  # из max 5
    "tools_called": ["search", "search", "evaluate"]
}
```

### Answer Quality

```python
answer_metrics = {
    "is_grounded": True,  # ответ подтверждён контекстом
    "completeness": 0.9,  # полнота ответа
    "citation_count": 5,  # количество источников
    "hallucination_score": 0.05  # низко = хорошо
}
```

---

## 🎯 Use Cases

### 1. Meeting Intelligence

```
"Что команда решила про Q2 планирование?"
"Какие action items были на встрече с клиентом X?"
"Когда последний раз обсуждали проблему Y?"
```

### 2. Knowledge Base

```
"Как мы решали подобную проблему раньше?"
"Найди все обсуждения темы Z"
"Что говорил эксперт A про технологию B?"
```

### 3. Analytics

```
"Какие темы чаще всего обсуждались в Q1?"
"С какими клиентами было больше всего встреч?"
"Какие проблемы повторяются из месяца в месяц?"
```

### 4. Compliance & Audit

```
"Найти все упоминания соглашения с клиентом X"
"Кто присутствовал при обсуждении решения Y?"
"Когда было принято решение о проекте Z?"
```

---

## 🚦 Implementation Roadmap

### Phase 1: MVP (2-3 недели)

- [ ] Базовая структура данных (chunks + metadata)
- [ ] Простой `search()` инструмент с metadata фильтрами
- [ ] Vector DB интеграция (Pinecone или Qdrant)
- [ ] Базовый semantic search
- [ ] Простой agent loop (без итераций)
- [ ] Тестирование на 10-20 созвонах

### Phase 2: Core Features (2-3 недели)

- [ ] Hybrid search (dense + sparse)
- [ ] Summary-level поиск
- [ ] Итеративный agent с оценкой качества
- [ ] Полный набор metadata фильтров
- [ ] Keyword фильтры (contains/not_contains)
- [ ] Базовая интеграция с n8n

### Phase 3: Quality & Performance (1-2 недели)

- [ ] Reranking (cross-encoder)
- [ ] Context compression
- [ ] Hallucination detection
- [ ] Оптимизация chunking strategy
- [ ] Метрики и логирование
- [ ] A/B тестирование стратегий

### Phase 4: Advanced Features (2-3 недели)

- [ ] Multi-hop reasoning
- [ ] Query reformulation
- [ ] Speaker diarization поддержка
- [ ] Temporal search с time decay
- [ ] Clustering результатов
- [ ] Advanced n8n workflows

### Phase 5: Production Ready (1-2 недели)

- [ ] Мониторинг и алерты
- [ ] Caching layer
- [ ] Rate limiting
- [ ] Authentication & authorization
- [ ] Документация API
- [ ] Deployment (Docker, Kubernetes)

---

## 💡 Key Design Decisions

### ✅ Unified Search Interface
**Решение**: Один `search()` инструмент вместо множества специализированных

**Обоснование**:
- Проще для LLM (меньше выбора)
- Автоматическая оптимизация под капотом
- Естественная композиция запросов

### ✅ Metadata Denormalization
**Решение**: Дублировать metadata в chunks для быстрой фильтрации

**Обоснование**:
- Избегаем JOIN операций
- Vector DB поддерживают metadata filtering
- Созвоны immutable (не меняются после создания)

### ✅ Two-tier Search (Summaries + Chunks)
**Решение**: Отдельные индексы для summaries и chunks

**Обоснование**:
- Summary search = быстрый overview
- Chunk search = детальный анализ
- Можно делать cascade поиск

### ✅ Filter as Pipeline
**Решение**: Фильтры применяются последовательно (metadata → semantic)

**Обоснование**:
- Оптимизация: дешёвые фильтры сначала
- Semantic search только на отфильтрованном scope
- Контролируем порядок выполнения

---

## 🎓 References & Inspiration

- **RAG Patterns**: LangChain documentation, LlamaIndex guides
- **Hybrid Search**: Weaviate hybrid search, Pinecone sparse-dense vectors
- **Agent Architecture**: Claude tool use, OpenAI function calling
- **Iterative Retrieval**: Self-Ask, ReAct, Chain-of-Verification patterns
- **n8n Integration**: n8n workflow templates, HTTP Request node patterns

---

## 📝 Notes

### Optimization Ideas
- Cache embeddings для частых запросов
- Batch processing для множественных searches
- Adaptive threshold для min_score на основе query complexity
- Query expansion для улучшения recall

### Future Enhancements
- Multi-modal support (audio, video timestamps)
- Real-time indexing новых созвонов
- Персонализация на основе user feedback
- Graph-based связи между созвонами и темами
- Auto-tagging созвонов через LLM

### Known Limitations
- Semantic search зависит от качества embeddings
- Chunking может разрезать важный контекст
- Metadata должны быть качественными (garbage in = garbage out)
- Стоимость LLM вызовов при многих итерациях
