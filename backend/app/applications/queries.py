from dataclasses import dataclass
from uuid import UUID


@dataclass
class GetApplicationByIdQuery:
    application_id: UUID
    user_id: UUID
