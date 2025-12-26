Шаблон backend/.env:
```
database_url=postgresql+asyncpg://DB_USER:DB_PASS@DB_HOST:DB_PORT/DB_NAME
```
## Быстрый старт

### Предварительные требования

- Python 3.10+
- Node.js 20+
- npm/yarn
- Git

### Локальная разработка

#### 1️⃣ Запуск Backend

```bash
# Переход в директорию backend
cd backend

# Создание виртуального окружения
python -m venv .venv
# source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера разработки
python run.py
```

Backend будет доступен по адресу: **http://localhost:8000**, а также будет доступен в локальной сети

API документация (Swagger UI): **http://localhost:8000/docs**

Закрыть, если завис:
``` bash
taskkill /F /IM python.exe
```

#### 2️⃣️ Запуск Frontend

```bash
# Переход в директорию frontend (новый терминал)
cd frontend

# Установка зависимостей
npm install

# Запуск dev сервера
npm run dev

# Для запуска в локальной сети:
# npx vite --host 0.0.0.0
```

Frontend будет доступен по адресу: **http://localhost:5173**
