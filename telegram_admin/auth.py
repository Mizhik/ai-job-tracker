import logging
from functools import wraps
from telegram import Update, Chat
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def is_authorized(update: Update, admin_user_id: int) -> bool:
    """
    Checks if update is sent by the exact authorized admin_user_id AND in a private chat.
    """
    if admin_user_id <= 0:
        return False

    effective_user = update.effective_user
    effective_chat = update.effective_chat

    if not effective_user or not effective_chat:
        return False

    if effective_user.id != admin_user_id:
        return False

    if effective_chat.type != Chat.PRIVATE:
        return False

    return True


def require_admin_auth(admin_user_id: int):
    """
    Decorator for telegram bot command / callback handlers enforcing single admin user ID + private chat.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not is_authorized(update, admin_user_id):
                logger.warning(
                    "Unauthorized access attempt from user_id=%s in chat_type=%s",
                    update.effective_user.id if update.effective_user else None,
                    update.effective_chat.type if update.effective_chat else None,
                )
                if update.callback_query:
                    await update.callback_query.answer("Unauthorized access.", show_alert=True)
                elif update.message:
                    await update.message.reply_text("Unauthorized access.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
