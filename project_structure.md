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
├── local/                            # Локальная разработка с Docker
│   ├── docker-compose.local.yml      # Docker Compose для локальной разработки
│   │                                 # (PostgreSQL + API сервис)
│   ├── .env.local                    # Переменные окружения для Docker (не в git)
│   ├── .gitignore                    # Git ignore для local папки
│   └── README.md                     # Инструкции по локальному запуску
│
├── Dockerfile                        # Docker образ для Railway деплоя
├── requirements.txt                  # Python зависимости
├── .dockerignore                     # Исключения для Docker build
├── .gitignore                        # Git ignore для проекта
└── project_structure.md              # Этот файл - структура проекта
