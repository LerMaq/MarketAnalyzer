# MarketAnalyzer

MarketAnalyzer — это web-сервис для автоматизированного анализа отзывов о товарах на маркетплейсе Ozon. Пользователь вставляет ссылку на товар, после чего система собирает отзывы, обрабатывает их с помощью LLM и формирует краткий аналитический отчёт: основные плюсы, минусы, общую оценку товара и ответы на уточняющие вопросы через чат.

Проект состоит из трёх основных частей:

- backend на Python/FastAPI для обработки запросов, работы с базой данных и интеграции с LLM;
- frontend для пользовательского интерфейса;
- scraper для сбора данных о товарах и отзывах.

В качестве базы данных используется PostgreSQL. Проект ориентирован на покупателей, которым нужно быстро понять реальное качество товара без ручного чтения сотен отзывов.

---

## Быстрый старт

### Предварительные требования

- Python 3.10+
- Node.js 20+
- npm/yarn
- Git
- Docker

### Настройка перед запуском

Создать файлы .env в папках `backend`, `frontend`, `scraper` по шаблонам `.env.example`, которые лежат в соответствующих папках.

### Локальная разработка

#### 1. Запуск Backend

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

API документация (Swagger UI): **http://localhost:8000/docs**

Добавьте API ключ нейросети по адресу: [ai-setup/keys](http://localhost:8000/docs#/AI%20Setup/setup_ai_key_ai_setup_keys_post). Необходимо нажать "Try it out", вписать ключ в key и нажать "Execute".

Закрыть, если завис:
``` bash
taskkill /F /IM python.exe
```

#### 2. Запуск Frontend

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


#### 3. Запуск Scraper
Для запуска скрапера используйте докер контейнер, либо воспользуйтесь иной реализацией скрапера (скоро будет доступно для различных платформ и опубликовано в отдельном репозиории).

Запуск через Docker может быть в двух вариантах:
- Сборка (5-10 мин) и запуск Docker контейнера локально:
```bash
cd scraper
docker compose -f docker-compose.dev.yml up -d --build
```
- Скачивание готового образа с docker hub и запуск:
```bash
cd scraper
docker compose up -d
```

Просмотр логов:
```bash
docker logs -f marketanalyzer-scraper-dev
```

#### 4. Миграция БД
Миграцию выполняют при необходимости изменить структуру (добавить, изменить таблицы), не пересоздавая БД. Это может понадобиться, если в базе уже есть важные данные, которые нельзя просто удалить (например, когда сервис уже запущен в продакшн).

```bash
# Генерация файла миграции
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

---

### Деплой на сервер

#### 1. Деплой Backend

coming soon...

#### 2. Деплой Frontend

coming soon...

#### 3. Деплой Scraper

##### Сборка production image

Заменить `VERSION` на номер версии, например `0.1.0`.

```bash
cd scraper

VERSION=0.1.0

docker build -t lermak/marketanalyzer-scraper:$VERSION .
docker build -t lermak/marketanalyzer-scraper:latest .

docker push lermak/marketanalyzer-scraper:$VERSION
docker push lermak/marketanalyzer-scraper:latest
```
##### Публикация на сервер
Требуется предварительно установить Docker на сервер.
```bash
mkdir -p /opt/marketanalyzer-scraper
cd /opt/marketanalyzer-scraper

# Вставить из файла scraper/.env.example и заменить необходимые параметры
nano .env

# Вставить из файла scraper/docker-compose.yml
nano docker-compose.yml
docker compose up -d

docker logs -f marketanalyzer-scraper
```


