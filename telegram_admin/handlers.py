import html
import logging
from uuid import UUID
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from telegram_admin.auth import is_authorized
from telegram_admin.services import AdminBotService

logger = logging.getLogger(__name__)


async def _safe_edit_message_text(query, text: str, parse_mode: str, reply_markup):
    try:
        await query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.debug("Message text unchanged on edit_message_text, ignoring BadRequest.")
        else:
            raise


class TelegramAdminHandlers:
    def __init__(self, service: AdminBotService, admin_user_id: int):
        self.service = service
        self.admin_user_id = admin_user_id

    def check_auth(self, update: Update) -> bool:
        return is_authorized(update, self.admin_user_id)

    async def start_or_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.check_auth(update):
            if update.message:
                await update.message.reply_text("Unauthorized access.")
            return

        keyboard = [
            [
                InlineKeyboardButton("📊 System Status", callback_data="cmd_status"),
                InlineKeyboardButton("👥 User List", callback_data="users_page:1"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            "<b>🤖 AI Job Tracker Admin Bot</b>\n\n"
            "Welcome! Choose an option below or use commands:\n"
            "• /status - Check API &amp; DB availability\n"
            "• /users - View registered users (10 per page)\n"
            "• /help - Show this menu"
        )
        if update.message:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.answer()
            await _safe_edit_message_text(update.callback_query, text, parse_mode="HTML", reply_markup=reply_markup)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.check_auth(update):
            if update.message:
                await update.message.reply_text("Unauthorized access.")
            elif update.callback_query:
                await update.callback_query.answer("Unauthorized access.", show_alert=True)
            return

        status = await self.service.get_system_status()
        text = (
            "<b>📊 System Status Report</b>\n\n"
            f"• <b>API Availability:</b> {html.escape(status['api_status'])}\n"
            f"• <b>DB Availability:</b> {html.escape(status['db_status'])}\n"
            f"• <b>Total Users:</b> {html.escape(str(status['total_users']))}\n"
            f"• <b>Checked At:</b> {html.escape(status['check_time'])}"
        )

        keyboard = [[InlineKeyboardButton("🔄 Refresh Status", callback_data="cmd_status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.answer("Status refreshed")
            await _safe_edit_message_text(update.callback_query, text, parse_mode="HTML", reply_markup=reply_markup)

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.check_auth(update):
            if update.message:
                await update.message.reply_text("Unauthorized access.")
            return
        await self._render_users_page(update, page=1)

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return

        if not self.check_auth(update):
            await query.answer("Unauthorized access.", show_alert=True)
            return

        data = query.data or ""

        if data == "noop":
            await query.answer("Current Page")
            return

        if data == "cmd_status":
            await self.status_command(update, context)
        elif data == "cmd_help":
            await self.start_or_help(update, context)
        elif data.startswith("users_page:"):
            try:
                page = int(data.split(":", 1)[1])
            except ValueError:
                page = 1
            await self._render_users_page(update, page=page)
        elif data.startswith("back_users_page:"):
            try:
                page = int(data.split(":", 1)[1])
            except ValueError:
                page = 1
            await self._render_users_page(update, page=page)
        elif data.startswith("user_detail:"):
            raw_id = data.split(":", 1)[1]
            try:
                user_id = UUID(raw_id)
            except ValueError:
                await query.answer("Invalid User ID format.", show_alert=True)
                return
            await self._render_user_detail(update, user_id=user_id)
        else:
            await query.answer("Unknown action.", show_alert=True)

    async def _render_users_page(self, update: Update, page: int):
        query = update.callback_query

        try:
            users, total_count, total_pages = await self.service.get_users_page(page=page, page_size=10)
        except Exception:
            err_msg = "⚠️ Database unavailable. Cannot fetch users list."
            if query:
                await query.answer("Database unavailable.", show_alert=True)
                await _safe_edit_message_text(query, err_msg, parse_mode="HTML", reply_markup=None)
            elif update.message:
                await update.message.reply_text(err_msg)
            return

        if total_count == 0 or not users:
            empty_msg = "<b>👥 User List</b>\n\nNo users registered yet."
            keyboard = [[InlineKeyboardButton("📊 System Status", callback_data="cmd_status")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if query:
                await query.answer()
                await _safe_edit_message_text(query, empty_msg, parse_mode="HTML", reply_markup=reply_markup)
            elif update.message:
                await update.message.reply_text(empty_msg, parse_mode="HTML", reply_markup=reply_markup)
            return

        if page > total_pages:
            page = total_pages
        if page < 1:
            page = 1

        header = f"<b>👥 User List (Page {page}/{total_pages})</b> | Total: {total_count}\n\n"
        lines = []
        user_buttons = []

        for idx, user in enumerate(users, start=1):
            created_str = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
            status_str = "Active" if user.is_active else "Inactive"
            safe_email = html.escape(user.email)
            lines.append(f"{idx}. <code>{safe_email}</code> ({created_str}) [{status_str}]")
            user_buttons.append([
                InlineKeyboardButton(
                    f"🔍 {user.email}",
                    callback_data=f"user_detail:{user.id}"
                )
            ])

        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"users_page:{page - 1}"))

        nav_row.append(InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="noop"))

        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"users_page:{page + 1}"))

        keyboard = user_buttons + [nav_row]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = header + "\n".join(lines)

        if query:
            await query.answer()
            await _safe_edit_message_text(query, full_text, parse_mode="HTML", reply_markup=reply_markup)
        elif update.message:
            await update.message.reply_text(full_text, parse_mode="HTML", reply_markup=reply_markup)

    async def _render_user_detail(self, update: Update, user_id: UUID):
        query = update.callback_query

        try:
            user = await self.service.get_user_detail(user_id)
        except Exception:
            if query:
                await query.answer("Database unavailable.", show_alert=True)
            return

        if not user:
            if query:
                await query.answer("User not found or deleted.", show_alert=True)
            return

        reg_date = user.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if user.created_at else "N/A"
        active_str = "Yes" if user.is_active else "No"
        safe_email = html.escape(user.email)

        detail_text = (
            "<b>👤 User Details</b>\n\n"
            f"• <b>Email:</b> <code>{safe_email}</code>\n"
            f"• <b>UUID:</b> <code>{user.id}</code>\n"
            f"• <b>Registered:</b> {reg_date}\n"
            f"• <b>Active Status:</b> {active_str}"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Back to Users List", callback_data="back_users_page:1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if query:
            await query.answer()
            await _safe_edit_message_text(query, detail_text, parse_mode="HTML", reply_markup=reply_markup)
        elif update.message:
            await update.message.reply_text(detail_text, parse_mode="HTML", reply_markup=reply_markup)
