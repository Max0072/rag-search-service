# Структура проекта RAG Service

```
rag_service/
│
├── app/                              # Основной код приложения
│   ├── api/                          # API эндпоинты и маршруты
│   │   ├── __init__.py
│   │   ├── main.py                   # Инициализация FastAPI приложения
│   │   │                             # + Startup event для автоинициализации БД
│   │   ├── routes_prod.py            # Production API routes (search, upload, admin)
│   │   └── test_routes.py            # Тестовые/debug эндпоинты
│   │
│   ├── database/                     # Слой работы с базами данных
│   │   ├── __init__.py
│   │   ├── db_models.py              # SQLAlchemy модели для PostgreSQL
│   │   ├── main_db.py                # Операции с PostgreSQL (metadata DB)
│   │   └── vector_db.py              # Операции с Pinecone (vector DB)
│   │
│   ├── embeddings/                   # Генерация векторных эмбеддингов
│   │   ├── __init__.py
│   │   └── openai_embeddings.py      # Сервис генерации эмбеддингов через OpenAI
│   │
│   ├── search/                       # Логика поискового движка
│   │   ├── __init__.py
│   │   └── search_engine.py          # 3-ступенчатый pipeline поиска
│   │
│   ├── __init__.py
│   ├── config.py                     # Настройки приложения (Pydantic Settings)
│   ├── data_manager.py               # Менеджер синхронизации между БД
│   └── models.py                     # Pydantic модели для API requests/responses
│
├── .env                              # Переменные окружения для Docker (не в git)
├── .env.example                      # Example of env file
├── .dockerignore                     # Исключения для Docker build
├── .gitignore                        # Git ignore для проекта
│
├── docker-compose.yml                # Docker Compose для локальной разработки
│                                     # (PostgreSQL + API сервис)
├── Dockerfile                        # Docker образ для Railway деплоя
├── project_structure.md              # Этот файл - структура проекта
├── README.md                         # Инструкции по локальному запуску
└── requirements.txt                  # Python зависимости
```
