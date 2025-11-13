Ты — опытный Python-разработчик. Сгенерируй монорепозиторий: Telegram-бот (aiogram v3) + веб-админка (FastAPI+Jinja+HTMX) + Postgres + Redis + Alembic + Nginx с авто-TLS (Let’s Encrypt) + Certbot. Добавь файловую «память модели»: общую папку с JSONL-контекстом, куда сервисы пишут/читают сводки диалогов и действий. Выводи структуру и ПОЛНЫЕ содержимые файлов в отдельных код-блоках. Комментарии в коде — на русском.

## ЦЕЛЬ
— Логика бота: как в предыдущем ТЗ (легковой/грузовой/акции) с твоими правками по кнопкам и «переклейке» (галерея макетов из БД).  
— БД: Postgres (SQLAlchemy 2.x, Alembic миграции).  
— Веб-админка: вход только через Telegram Login (проверка подписи), допуск только role=admin, остальным — заглушка «Доступ запрещён». Управление макетами «переклейки» (CRUD + сортировка drag&drop), заявками, пользователями.  
— Деплой: docker-compose (postgres, redis, bot, web, nginx, certbot).  
— Авто-TLS: Nginx reverse-proxy + Certbot (стартовая выдача и автоматическое продление).  
— Файловая «память»/контекст: общий volume `context/`, куда bot и web складывают краткие JSONL-сводки шагов/интентов/статусов; есть библиотека `common/context_store.py` для append/read/rotate. Эти файлы могут читать все сервисы (в перспективе — внешние модели).

## ТЕХНО-СТЕК
- Python 3.11+
- Бот: aiogram 3.x (Router/States), pydantic-settings
- Веб: FastAPI + Jinja2 + HTMX + Tailwind (через CDN), Uvicorn
- ORM: SQLAlchemy 2.x + Alembic
- БД: PostgreSQL
- Кэш/очереди: Redis (модуль нотификаций)
- Логи: JSON-логи, ротация, уровень INFO
- Контейнеры: отдельные Dockerfile для bot и web
- Nginx: один конфиг, reverse proxy на web:8000, статик/загрузки отдаёт напрямую, а также обслуживает challenge для Certbot
- Certbot: автоматическая выдача и renew (cron в отдельном контейнере/entrypoint)
- Тесты: pytest (валидатор года, загрузка 4 фото, CRUD макетов, верификация Telegram Login)

## ДОМЕННАЯ СХЕМА (Postgres)
- users(id PK, tg_id BIGINT UNIQUE, username, first_name, last_name, role ENUM['user','admin'] DEFAULT 'user', created_at TIMESTAMPTZ, last_seen TIMESTAMPTZ)
- requests(id PK, user_id FK users.id, category ENUM['легковой','грузовой'], status ENUM['draft','submitted','approved','rejected'] DEFAULT 'draft', has_brand BOOL NULL, year INT NULL, has_license BOOL NULL, body_size ENUM['S','M','L','XL','XXL'] NULL, option ENUM['free_wrap','paid_wrap','rebrand','stripes','full_wrap_gost'] NULL, comment TEXT NULL, created_at TIMESTAMPTZ, submitted_at TIMESTAMPTZ)
- files(id PK, request_id FK, kind ENUM['auto_photo','sts_photo'], file_id TEXT, path TEXT, mime TEXT, size INT, created_at TIMESTAMPTZ)
- rebrand_templates(id PK, title TEXT, description TEXT NULL, image_path TEXT, image_hash TEXT, sort_order INT DEFAULT 0, is_active BOOL DEFAULT TRUE, created_at TIMESTAMPTZ)
- audit(id PK, event TEXT, payload JSONB, created_at TIMESTAMPTZ)

## ЛОГИКА БОТА (кратко, как в предыдущем ТЗ с правками)
- /start → «Какой у вас автомобиль?» [Легковой][Грузовой][Акции]
- Легковой → «Есть ли бренд?» [Да/Нет]
  - Да → кнопки в порядке: «Бесплатная оклейка», «Платная оклейка», «Переклейка устаревшего бренда»
    - «Переклейка…» → галерея макетов (из rebrand_templates), выбор → текст про «живая очередь… помыть 🧽» → собрать 4 фото → submitted
    - Остальные → сразу собрать 4 фото → submitted
  - Нет → спросить «Год выпуска (1980–текущий)» → «Есть ли лицензия?» [Да/Нет]
    - Да → те же 3 кнопки, как выше → фото → submitted
    - Нет → две кнопки:
      1) «Светоотражающие полосы + шашечный пояс — 4 000 руб.»
      2) «Полная оклейка для получения лицензии по ГОСТ СПб — от 25 000 руб.»
      → фото → submitted
- Грузовой → «Какой размер кузова?» [S/M/L/XL/XXL] → «Отправьте 4 фото…» → submitted
- Акции → заглушка
- Везде: «Назад», «Отмена», проверка типа фото, итог с № заявки #REQ-{id}
- Нотификации админам о новых заявках (inline Approve/Reject)

## ВЕБ-АДМИНКА
- Telegram Login Widget: верификация подписи; если tg_id не admin — страница «Доступ запрещён»
- Разделы:
  1) Заявки: фильтры (дата/статус/категория/tg_id), пагинация, карточка, смена статуса, комментарий, экспорт CSV
  2) Пользователи: список, назначение/снятие роли admin
  3) Макеты переклейки: CRUD + drag&drop сортировка (HTMX reorder), загрузка изображений (валидация mime/size), хранение в `storage/rebrand/`, превью; JSON API `/api/rebrand-templates?active=1`
  4) Аудит/логи: лента событий
- Безопасность: CSRF, лимиты upload (напр. 6 МБ), строгие заголовки

## «ПАМЯТЬ МОДЕЛИ» — ФАЙЛОВЫЙ КОНТЕКСТ
Сделай модуль `common/context_store.py`:
- Папка: `./context/` (общий docker volume)
- Формат: JSONL; одна строка = один объект вида:
  {
    "ts":"2025-01-01T12:34:56Z",
    "source":"bot|web",
    "actor":"user|admin|system",
    "chat_id": 123456789,
    "user_id": 42,
    "request_id": 1001,
    "intent": "choose_option|upload_photo|approve|reject|login",
    "payload": {...}     // любые поля шага
  }
- Файлы: ротация по дате (context-YYYYMMDD.jsonl), автоматическое создание; утилиты: append_event(), read_range(date_from,date_to), tail(n), rotate(max_days=30)
- Конфиг: включение/выключение через ENV `CONTEXT_ENABLED=true`
- Приватность: в README пункт о данных, возможность анонимизировать `chat_id` (sha256) через `CONTEXT_HASH_IDS=true`

Бот и веб при значимых действиях вызывают append_event() (например: выбор опции, отправка N-го фото, сабмит заявки, логин админа, CRUD макета, approve/reject).  
Добавь CLI `python -m common.context_dump --from 2025-01-01 --to 2025-01-31 --out export.jsonl`.

## DOCKER-COMPOSE + NGINX + CERTBOT (АВТО-TLS)
- Сервисы: postgres, redis, bot, web (uvicorn), nginx, certbot
- Домены/переменные:
  - `PUBLIC_BASE_URL=https://example.com`
  - `LETSENCRYPT_EMAIL=admin@example.com`
  - `LETSENCRYPT_DOMAINS=example.com,www.example.com`
- Nginx:
  - Проксирует `/:` → web:8000
  - `/static` и `/uploads` — как статика (read-only)
  - HTTP-порт 80: отдаёт `.well-known/acme-challenge` для валидации
  - HTTPS-порт 443: использует сертификаты из volume `certs/`
- Certbot:
  - Команда для начальной выдачи сертификатов (webroot-plugin на `/.well-known/acme-challenge`)
  - Скрипт renew (ежедневно через crond в контейнере) + `nginx -s reload` по окончании
- Volumes: `pgdata`, `uploads`, `logs`, `context`, `certs`, `acme-challenge`
- README: пошагово
  1) заполнить .env (домены/почта)
  2) `docker compose up -d --build`
  3) `docker compose exec certbot /entrypoint-init` (первичная выдача)
  4) проверить HTTPS
  5) `alembic upgrade head`

## ENV / Конфиги
`.env.example`:
BOT_TOKEN=…
ADMIN_IDS=123,456
DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/app
REDIS_URL=redis://redis:6379/0
WEB_HOST=0.0.0.0
WEB_PORT=8000
PUBLIC_BASE_URL=https://example.com
SECRET_KEY=change_me
TELEGRAM_BOT_NAME=@your_bot
LETSENCRYPT_EMAIL=admin@example.com
LETSENCRYPT_DOMAINS=example.com,www.example.com
CONTEXT_ENABLED=true
CONTEXT_HASH_IDS=false

## СТРУКТУРА РЕПО
.
├─ bot/ (aiogram приложение; FSM, клавиатуры, handlers, сервисы)
├─ web/ (FastAPI; routers, templates, static, auth, admin UI)
├─ common/ (settings.py, db.py, models.py, enums.py, context_store.py, logging.py)
├─ migrations/ (alembic.ini, env.py, versions/*.py)
├─ nginx/nginx.conf
├─ certbot/ (Dockerfile, entrypoints для issue/renew)
├─ storage/uploads/.gitkeep
├─ storage/rebrand/.gitkeep
├─ context/.gitkeep
├─ logs/.gitkeep
├─ docker-compose.yml
├─ pyproject.toml (общие зависимости, ruff, pytest)
├─ .editorconfig
├─ .env.example
└─ README.md (локальный запуск, Docker, Telegram Login, авто-TLS, контекст-файлы)

## ТЕСТЫ
- pytest: валидация года, сценарий 4 фото, подпись Telegram Login, CRUD макетов + сортировка, append_event()/tail() для контекста

Сделай:
1) Полный код всех модулей (bot, web, common, nginx, certbot)  
2) Рабочий docker-compose с авто-TLS и томами  
3) Alembic миграции  
4) README с командами для первичной выдачи и renew  
5) Пример .env и мок-данные для rebrand_templates
