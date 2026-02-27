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

### Настройка перед запуском

- Создать backend\.env по шаблону
- Создать frontend\.env по шаблону
- Заполнить БД стартовыми данными (backend\scripts\seed_db.py)

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

Добавьте API ключ нейросети по [Эндпоинту](http://localhost:8000/docs#/AI%20Setup/setup_ai_key_ai_setup_keys_post). Необходимо нажать "Try it out", вписать ключ в key и нажать "Execute".

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

#### 3️⃣ Миграция  БД
Миграцию выполняют при необходимости изменить структуру (добавить, изменить таблицы), не пересоздавая БД. Это может понадобиться, если в базе уже есть важные данные, которые нельзя просто удалить (например, когда сервис уже запущен в продакшн).

```bash
# Генерация миграции
alembic revision --autogenerate -m "Перечень изменений в структуре БД"
# Вывод предыдущей команды нужно проанализировать.
# Если он не соответствует желаемым изменениям,
# то нужно удалить файл миграции
# или проигнорировать её командой: "alembic stamp head" 

# Если всё устраивает применяем миграцию
alembic upgrade head

# Если миграция уже применена, но нужно откатить изменения,
# то это можно сделать командой: "alembic downgrade -1"
```
