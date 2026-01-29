### 1. Настройте переменные окружения

Найдите `.env` и заполните необходимые значения:

### 2. Запустите с помощью Docker Compose

```bash
docker-compose -f docker-compose.yml up --build
```

### 3. Проверьте статус

```bash
docker-compose ps
docker-compose logs -f bot
```

### 4. Откройте Dashboard

Откройте в браузере: http://localhost:5001

## Команды управления

### Остановить бота
```bash
docker-compose down
```

### Перезапустить бота
```bash
docker-compose restart
```

### Просмотр логов
```bash
docker-compose logs -f bot
```

### Пересобрать образ после изменений
```bash
docker-compose up -d --build
```

## Запуск через Docker напрямую

Если не хотите использовать Docker Compose:

```bash
# Собрать образ
docker build -t telegram-rag-bot .

# Запустить контейнер
docker run -d \
  --name telegram-bot \
  -p 5001:5001 \
  --env-file .env \
  telegram-rag-bot
```

## Требования

- Docker 20.10+
- Docker Compose 1.29+ (опционально)
- Файл `.env` с настройками