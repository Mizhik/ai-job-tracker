# AI Job Tracker

Личный трекер вакансий: FastAPI, PostgreSQL, React/TypeScript и Telegram-бот оператора. Работают регистрация, вход, вакансии и отслеживание откликов. AI-анализ запланирован на следующий релиз.

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

## Демонстрация v0.1

После запуска откройте http://localhost:3000 в браузере. Зарегистрируйте демонстрационный аккаунт и войдите в него. Добавьте вакансию вручную или вставьте ссылку, проверьте предложенные поля и сохраните черновик. Откройте карточку, создайте отклик, измените его статус и добавьте заметку. Обновите страницу: вход, вакансия и отклик должны сохраниться. Затем проверьте поиск и фильтр по статусу, редактирование вакансии и подтверждение удаления отклика и вакансии.

Для проверки сборки frontend без CI выполните из каталога `frontend` команды `npm ci`, `npm run typecheck` и `npm run build`. Для проверки backend из корня проекта выполните `poetry run pytest -q`. Эти проверки запускаются вручную перед релизным PR.

## Состояние проекта

Этапы 07–09 реализовали frontend, backend откликов и интерфейс трекера. Локальная приёмка этапа 10 выполнена; релиз v0.1 готовится. Локальный подробный план находится в `docs/Work_Plan.md`; папка `docs/` не публикуется в Git.
