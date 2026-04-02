## Prerequisites
1. Docker Desktop installed and running
2. OpenAI API Key
3. Pinecone Account

### 1. Setting Up API Keys
Open the `.env` file and replace the placeholders with your actual keys

### 2. Starting the Service
```bash
docker-compose up --build -d
```

## 3. Stopping
```bash
# Stop while preserving data
docker-compose -f docker-compose.yml down
```
```bash 
# Stop and remove all data (including PostgreSQL)
docker-compose -f docker-compose.yml down -v
```
