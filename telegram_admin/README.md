# Telegram Read-Only Admin Operator Bot

A read-only Telegram operator bot process for monitoring system health and viewing user registrations for the AI Job Tracker.

## Overview & Architecture
- **Read-only interface**: Provides `/start`, `/help`, `/status`, and `/users` commands with inline keyboard navigation.
- **Strict Authorization**: Requires matching `TELEGRAM_ADMIN_USER_ID` and a `private` chat for every message and callback query. Non-authorized users or non-private chats (e.g. groups/channels) will never receive user data.
- **Independent Execution & Resilient Startup**: Runs as a separate long polling process without open ports or webhook endpoints. It starts and remains operational even if the API or DB are initially down or fail intermittently.
- **Distinction between API and DB status**:
  - **API Availability**: Measured via HTTP GET requests to `{API_BASE_URL}/openapi.json`. This probes whether the FastAPI HTTP application server is responding, independent of database health.
  - **DB Availability**: Measured via direct connection and queries using `AdminQueriesService`.

## Configuration & Environment Variables

Configure the bot using environment variables (e.g. in `.env` or container environment):

| Environment Variable | Required | Description | Example |
|----------------------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Yes | Token obtained from Telegram @BotFather | `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ` |
| `TELEGRAM_ADMIN_USER_ID` | Yes | Numeric Telegram ID of the single authorized admin user | `987654321` |
| `API_BASE_URL` | No | Base URL of the backend FastAPI service | `http://app:8000` or `http://localhost:8000` |
| `POSTGRES_DBNAME` | Yes | PostgreSQL database name | `ai_job_tracker` |
| `POSTGRES_USER` | Yes | PostgreSQL user | `postgres` |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password | `postgres` |
| `POSTGRES_ADDRESS` | Yes | PostgreSQL host and port | `db:5432` or `localhost:5432` |

### How to Obtain Your Telegram User ID
1. You can obtain your numeric Telegram User ID using third-party Telegram helper bots such as `@userinfobot` or `@raw_data_bot` by forwarding a message to them.
2. Set `TELEGRAM_ADMIN_USER_ID=987654321` in your local `dev.env` or environment configuration. **Never commit bot tokens or numeric user IDs to public source code repositories.**

## Running locally

```bash
# 1. Set environment variables
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_ADMIN_USER_ID="123456789"
export API_BASE_URL="http://localhost:8000"
export POSTGRES_ADDRESS="localhost:5432"

# 2. Run bot process
python -m telegram_admin.main
```

## Running with Docker Compose

To run the Telegram admin bot alongside the application stack using local environment configuration:

```bash
docker compose --env-file dev.env -f dockerfiles/docker-compose.yml --profile telegram-bot --profile app up --build
```
