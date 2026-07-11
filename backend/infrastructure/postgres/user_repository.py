import asyncpg
from asyncpg import Pool
from uuid import UUID

from backend.core.errors import UserAlreadyExistsException
from backend.core.repository.user_repository import UserRepository
from backend.core.user import User


class AsyncpgUserRepository(UserRepository):
    def __init__(self, pool: Pool):
        self._pool = pool

    async def create(self, user: User) -> None:
        query = """
            INSERT INTO users (first_name, last_name, email, hashed_password)
            VALUES ($1, $2, $3, $4)
        """
        user_data = self._user_to_db_dict(user)
        try:
            await self._pool.execute(query, *user_data.values())
        except asyncpg.exceptions.UniqueViolationError:
            raise UserAlreadyExistsException()

    async def get_by_email(self, email: str) -> User | None:
        query = """
            SELECT *
            FROM users
            WHERE email = $1::VARCHAR
        """
        user_data = await self._pool.fetchrow(query, email)
        if user_data:
            return User(
                id=user_data["id"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                telegram_chat_id=user_data["telegram_chat_id"],
                hashed_password=user_data["hashed_password"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
            )
        return None

    async def update(self, user: User) -> None:
        query = """
            UPDATE users
            SET first_name = $1::VARCHAR,
                last_name = $2::VARCHAR,
                email = $3::VARCHAR
            WHERE id = $4::UUID
        """
        await self._pool.execute(
            query,
            user.first_name,
            user.last_name,
            user.email,
            user.id,
        )


    async def delete(self, user: User) -> None:
        query = """
            DELETE FROM users
            WHERE id = $1::UUID
        """
        await self._pool.execute(query, user.id)


    async def get_by_id(self, user_id: UUID) -> User | None:
        query = """
            SELECT *
            FROM users
            WHERE id = $1::UUID
        """
        user_data = await self._pool.fetchrow(query, user_id)
        if user_data:
            return User(
                id=user_data["id"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                telegram_chat_id=user_data["telegram_chat_id"],
                hashed_password=user_data["hashed_password"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
            )
        return None


    def _user_to_db_dict(self, user: User) -> dict:
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "hashed_password": user.hashed_password,
        }
