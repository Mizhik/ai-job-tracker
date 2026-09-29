# AI Job Tracker

Личный трекер вакансий: FastAPI, PostgreSQL, React/TypeScript и Telegram-бот оператора. Первый сценарий уже работает: регистрация, вход, создание вакансии, список, карточка и выход. Отклики и AI-анализ запланированы на следующие этапы.

## Запуск всех сервисов в Docker

Нужен Docker Desktop с работающим Linux engine. Из корня проекта создайте локальный `dev.env` на основе `.env.example` и задайте реальные `POSTGRES_DBNAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `AUTH_SECRET_KEY`, `TELEGRAM_BOT_TOKEN` и числовой `TELEGRAM_ADMIN_USER_ID`. Для HTTP на localhost используйте `AUTH_COOKIE_SECURE=false`; срок access token — `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=15`. Не коммитьте `dev.env`.

```powershell
docker compose -f dockerfiles/docker-compose.yml --env-file dev.env up -d --build
docker compose -f dockerfiles/docker-compose.yml --env-file dev.env ps
```

Команда поднимает PostgreSQL, применяет миграции, затем запускает API, frontend и Telegram-бота. Повторный запуск миграций безопасен. Зависимости Python и frontend устанавливаются внутри образов; локальный `poetry install` или `npm install` для этого запуска не нужен. SQL-миграции и lock-файлы хранятся в Git.

- Frontend: http://localhost:3000
- API и Swagger: http://localhost:8000/docs
- Проверка API и БД: http://localhost:8000/users/health
- PostgreSQL с хоста: `localhost:5432`
- Telegram-бот: команды `/start`, `/status`, `/users` в личном чате с указанным `TELEGRAM_ADMIN_USER_ID`.

Если порты заняты, задайте `FRONTEND_PORT`, `APP_PORT` или `POSTGRES_PORT` в `dev.env`. Для просмотра проблем запуска: `docker compose -f dockerfiles/docker-compose.yml --env-file dev.env logs -f app frontend telegram-bot`.

Остановка с сохранением данных:

```powershell
docker compose -f dockerfiles/docker-compose.yml --env-file dev.env down
```

Данные находятся в именованном volume; `down -v` удалит его.

## Состояние проекта

Этап 07 (первый frontend и серверные сессии) реализован. Следующий функциональный этап — **08: backend откликов**: согласовать модель и SQL новой миграцией, добавить статусы, заметки и фильтрацию вакансий по отклику. После него этап 09 завершит интерфейс трекера. Локальный подробный план находится в `docs/Work_Plan.md`; папка `docs/` не публикуется в Git.
