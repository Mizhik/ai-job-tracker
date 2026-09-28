from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Chat, User as TgUser, Message, CallbackQuery
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from backend.core.repository.admin_repository import AdminRepository, AdminUserReadModel
from backend.app.admin.queries import AdminQueriesService
from backend.infrastructure.postgres.pool.settings import DBSettings

from telegram_admin.auth import is_authorized, require_admin_auth
from telegram_admin.services import AdminBotService
from telegram_admin.handlers import TelegramAdminHandlers, _safe_edit_message_text


class InMemoryAdminRepository(AdminRepository):
    def __init__(self, users: list[AdminUserReadModel] | None = None, fail_next: bool = False):
        self.users = users or []
        self.fail_next = fail_next

    async def get_total_users_count(self) -> int:
        if self.fail_next:
            raise RuntimeError("DB Connection error")
        return len(self.users)

    async def get_paginated_users(self, limit: int, offset: int) -> list[AdminUserReadModel]:
        if self.fail_next:
            raise RuntimeError("DB Connection error")
        sorted_users = sorted(
            self.users,
            key=lambda u: (u.created_at or datetime.min.replace(tzinfo=timezone.utc), u.id),
            reverse=True,
        )
        return sorted_users[offset: offset + limit]

    async def get_user_by_id(self, user_id: UUID) -> AdminUserReadModel | None:
        if self.fail_next:
            raise RuntimeError("DB Connection error")
        for u in self.users:
            if u.id == user_id:
                return u
        return None


def make_tg_update(
    user_id: int,
    chat_type: str = Chat.PRIVATE,
    text: str | None = None,
    callback_data: str | None = None,
) -> MagicMock:
    update = MagicMock(spec=Update)

    user = MagicMock(spec=TgUser)
    user.id = user_id
    update.effective_user = user

    chat = MagicMock(spec=Chat)
    chat.type = chat_type
    update.effective_chat = chat

    if text is not None:
        message = MagicMock(spec=Message)
        message.text = text
        message.reply_text = AsyncMock()
        update.message = message
        update.callback_query = None
    elif callback_data is not None:
        query = MagicMock(spec=CallbackQuery)
        query.data = callback_data
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.message = None
    else:
        update.message = None
        update.callback_query = None

    return update


# --- 1. Authorization Tests ---

def test_is_authorized():
    ADMIN_ID = 123456789

    assert is_authorized(make_tg_update(ADMIN_ID, chat_type=Chat.PRIVATE, text="/start"), ADMIN_ID) is True
    assert is_authorized(make_tg_update(999999999, chat_type=Chat.PRIVATE, text="/start"), ADMIN_ID) is False
    assert is_authorized(make_tg_update(ADMIN_ID, chat_type=Chat.GROUP, text="/start"), ADMIN_ID) is False
    assert is_authorized(make_tg_update(ADMIN_ID, chat_type=Chat.SUPERGROUP, text="/start"), ADMIN_ID) is False
    assert is_authorized(make_tg_update(ADMIN_ID, chat_type=Chat.CHANNEL, text="/start"), ADMIN_ID) is False


@pytest.mark.asyncio
async def test_require_admin_auth_decorator_blocks_unauthorized():
    ADMIN_ID = 100
    handler_mock = AsyncMock()
    decorated = require_admin_auth(ADMIN_ID)(handler_mock)

    up_auth = make_tg_update(ADMIN_ID, text="/status")
    ctx = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    await decorated(up_auth, ctx)
    handler_mock.assert_called_once_with(up_auth, ctx)

    handler_mock.reset_mock()

    up_unauth = make_tg_update(200, text="/status")
    await decorated(up_unauth, ctx)
    handler_mock.assert_not_called()
    up_unauth.message.reply_text.assert_called_once_with("Unauthorized access.")


# --- 2. Pagination, Sorting, and HTML Escaping Tests ---

@pytest.mark.asyncio
async def test_admin_queries_service_pagination_and_sorting():
    now = datetime.now(timezone.utc)
    u1 = AdminUserReadModel(id=uuid4(), email="oldest@example.com", created_at=now, is_active=True)
    u2 = AdminUserReadModel(id=uuid4(), email="newer1@example.com", created_at=now + timedelta(seconds=10), is_active=True)
    u3 = AdminUserReadModel(id=uuid4(), email="newer2@example.com", created_at=now + timedelta(seconds=10), is_active=True)

    repo = InMemoryAdminRepository([u1, u2, u3])
    service = AdminQueriesService(repo)

    users, total_count, total_pages = await service.get_paginated_users(page=1, page_size=2)
    assert total_count == 3
    assert total_pages == 2
    assert len(users) == 2
    assert users[0].created_at >= users[1].created_at


@pytest.mark.asyncio
async def test_email_with_special_characters_and_html_escaping():
    now = datetime.now(timezone.utc)
    special_email = "user_name_with_underscores&special@example.com"
    u = AdminUserReadModel(id=uuid4(), email=special_email, created_at=now, is_active=True)

    repo = InMemoryAdminRepository([u])
    q_service = AdminQueriesService(repo)
    bot_service = AdminBotService(api_base_url="http://app:8000", admin_queries_service=q_service)
    handlers = TelegramAdminHandlers(service=bot_service, admin_user_id=123)

    up = make_tg_update(123, text="/users")
    ctx = MagicMock()
    await handlers.users_command(up, ctx)

    up.message.reply_text.assert_called_once()
    rendered_text = up.message.reply_text.call_args[0][0]
    assert "user_name_with_underscores&amp;special@example.com" in rendered_text


@pytest.mark.asyncio
async def test_single_page_navigation_and_noop_callback():
    now = datetime.now(timezone.utc)
    u = AdminUserReadModel(id=uuid4(), email="single_page@example.com", created_at=now, is_active=True)

    repo = InMemoryAdminRepository([u])
    q_service = AdminQueriesService(repo)
    bot_service = AdminBotService(api_base_url="http://app:8000", admin_queries_service=q_service)
    handlers = TelegramAdminHandlers(service=bot_service, admin_user_id=123)

    up = make_tg_update(123, text="/users")
    ctx = MagicMock()
    await handlers.users_command(up, ctx)

    reply_markup = up.message.reply_text.call_args[1]["reply_markup"]
    nav_row = reply_markup.inline_keyboard[-1]
    assert len(nav_row) == 1
    assert nav_row[0].text == "Page 1/1"
    assert nav_row[0].callback_data == "noop"

    up_noop = make_tg_update(123, callback_data="noop")
    await handlers.handle_callback_query(up_noop, ctx)
    up_noop.callback_query.answer.assert_called_once_with("Current Page")


# --- 3. Health Checks: API UP & DB DOWN ---

@pytest.mark.asyncio
async def test_api_up_and_db_down():
    bot_service = AdminBotService(api_base_url="http://mock-api:8000", admin_queries_service=None)

    with patch.object(bot_service, "check_api_health", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = (True, "Available")

        status = await bot_service.get_system_status()
        assert status["api_status"] == "Available"
        assert status["db_status"] == "Unavailable"
        assert status["total_users"] == "N/A"


# --- 4. Mock create_pool Creation/Failure/Closing/Recovery Test ---

@pytest.mark.asyncio
async def test_create_pool_failure_closing_and_recovery():
    db_settings = DBSettings(dbname="test", user="u", password="p", address="localhost:5432")
    bot_service = AdminBotService(api_base_url="http://mock-api:8000", db_settings=db_settings)

    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    mock_pool._closed = False

    # Simulate DB pool fetchval failure
    mock_pool.fetchval = AsyncMock(side_effect=RuntimeError("Connection lost"))

    with patch("telegram_admin.services.create_pool", new_callable=AsyncMock) as mock_create_pool:
        # First attempt fails pool creation
        mock_create_pool.side_effect = Exception("DB host unreachable")
        ok, status = await bot_service.check_db_health()
        assert ok is False
        assert status == "Unavailable"

        # Second attempt succeeds pool creation, but query fails
        mock_create_pool.side_effect = None
        mock_create_pool.return_value = mock_pool

        ok2, status2 = await bot_service.check_db_health()
        assert ok2 is False
        assert status2 == "Unavailable"
        # Verify failed pool was closed
        mock_pool.close.assert_called_once()

        # Third attempt succeeds pool creation and query succeeds
        mock_pool_ok = MagicMock()
        mock_pool_ok.close = AsyncMock()
        mock_pool_ok._closed = False
        mock_pool_ok.fetchval = AsyncMock(return_value=5)
        mock_create_pool.return_value = mock_pool_ok

        ok3, status3 = await bot_service.check_db_health()
        assert ok3 is True
        assert status3 == "Available"

    await bot_service.close()


# --- 5. Message Is Not Modified Handling Test ---

@pytest.mark.asyncio
async def test_safe_edit_message_text_ignores_not_modified_bad_request():
    query = MagicMock()
    query.edit_message_text = AsyncMock(side_effect=BadRequest("Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"))

    # Should not raise exception
    await _safe_edit_message_text(query, "same text", "HTML", None)

    query.edit_message_text.assert_called_once()

    # Different BadRequest should be re-raised
    query.edit_message_text = AsyncMock(side_effect=BadRequest("Chat not found"))
    with pytest.raises(BadRequest, match="Chat not found"):
        await _safe_edit_message_text(query, "text", "HTML", None)


# --- 6. No Data-Changing Methods in Read Model Repository ---

def test_no_data_changing_access_in_admin_repository():
    admin_repo_methods = set(dir(AdminRepository))
    forbidden_words = {"create", "update", "delete", "insert", "drop", "alter", "modify"}

    for method_name in admin_repo_methods:
        if not method_name.startswith("_"):
            assert not any(word in method_name for word in forbidden_words), f"Forbidden method found: {method_name}"
