import asyncio
import logging
import sys

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from backend.infrastructure.postgres.pool.settings import DBSettings

from telegram_admin.config import load_settings
from telegram_admin.handlers import TelegramAdminHandlers
from telegram_admin.services import AdminBotService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# HTTP request logs include the bot token in Telegram API URLs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("telegram_admin")


async def run_bot():
    settings = load_settings()

    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not configured. Exiting.")
        sys.exit(1)

    if settings.telegram_admin_user_id <= 0:
        logger.error("TELEGRAM_ADMIN_USER_ID is not configured or invalid. Exiting.")
        sys.exit(1)

    db_settings = DBSettings(
        dbname=settings.postgres_dbname,
        user=settings.postgres_user,
        password=settings.postgres_password,
        address=settings.postgres_address,
    )

    bot_service = AdminBotService(
        api_base_url=settings.api_base_url,
        db_settings=db_settings,
    )

    handlers = TelegramAdminHandlers(
        service=bot_service,
        admin_user_id=settings.telegram_admin_user_id,
    )

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler(["start", "help"], handlers.start_or_help))
    app.add_handler(CommandHandler("status", handlers.status_command))
    app.add_handler(CommandHandler("users", handlers.users_command))
    app.add_handler(CallbackQueryHandler(handlers.handle_callback_query))

    logger.info("Starting Telegram Admin Bot (long polling mode)...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping Telegram Admin Bot...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await bot_service.close()


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
