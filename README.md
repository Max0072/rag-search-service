## Предварительные требования

1. Docker Desktop установлен и запущен
2. OpenAI API Key
3. Pinecone Account


### 1. Настройка API ключей

Откройте файл `.env` и замените заглушки на реальные ключи


### 2. Запуск сервиса

```bash
docker-compose up --build -d
```

## 3. Остановка

```bash
# Остановить с сохранением данных
docker-compose -f docker-compose.yml down
```

```bash 
# Остановить и удалить все данные (включая PostgreSQL)
docker-compose -f docker-compose.yml down -v
```
