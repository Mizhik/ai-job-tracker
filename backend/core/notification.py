import enum
from uuid import UUID

from .base import Base


class NotificationType(enum.Enum):
    NEW_MATCH = "new_match"
    STATUS_CHANGE = "status_change"


class Notification(Base):
    job_id: UUID
    user_id: UUID
    type: NotificationType
    message: str
    is_sent: bool = False
