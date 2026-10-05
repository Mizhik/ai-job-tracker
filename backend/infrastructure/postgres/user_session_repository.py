from uuid import UUID
from asyncpg import Pool

from backend.core.repository.user_session_repository import UserSessionRepository
from backend.core.session import UserSession


class AsyncpgUserSessionRepository(UserSessionRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create(self, session: UserSession) -> None:
        query = """
            INSERT INTO user_sessions (id, user_id, refresh_token_hash, expires_at, created_at, updated_at, revoked_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await self._pool.execute(
            query,
            session.id,
            session.user_id,
            session.refresh_token_hash,
            session.expires_at,
            session.created_at,
            session.updated_at,
            session.revoked_at,
        )

    async def get_by_id(self, session_id: UUID) -> UserSession | None:
        query = """
            SELECT id, user_id, refresh_token_hash, expires_at, created_at, updated_at, revoked_at
            FROM user_sessions
            WHERE id = $1::UUID
        """
        row = await self._pool.fetchrow(query, session_id)
        if row:
            return UserSession(
                id=row["id"],
                user_id=row["user_id"],
                refresh_token_hash=row["refresh_token_hash"],
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                revoked_at=row["revoked_at"],
            )
        return None

    async def rotate_refresh_token(
        self,
        session_id: UUID,
        old_refresh_token_hash: str,
        new_refresh_token_hash: str,
    ) -> UserSession | None:
        query = """
            UPDATE user_sessions
            SET refresh_token_hash = $1,
                updated_at = NOW()
            WHERE id = $2::UUID
              AND refresh_token_hash = $3
              AND revoked_at IS NULL
              AND expires_at > NOW()
            RETURNING id, user_id, refresh_token_hash, expires_at, created_at, updated_at, revoked_at
        """
        row = await self._pool.fetchrow(
            query,
            new_refresh_token_hash,
            session_id,
            old_refresh_token_hash,
        )
        if row:
            return UserSession(
                id=row["id"],
                user_id=row["user_id"],
                refresh_token_hash=row["refresh_token_hash"],
                expires_at=row["expires_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                revoked_at=row["revoked_at"],
            )
        return None

    async def revoke(self, session_id: UUID) -> None:
        query = """
            UPDATE user_sessions
            SET revoked_at = NOW(),
                updated_at = NOW()
            WHERE id = $1::UUID
              AND revoked_at IS NULL
        """
        await self._pool.execute(query, session_id)
