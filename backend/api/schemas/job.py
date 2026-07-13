from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.jobs.commands.create_job import CreateJobCommand


class JobCreateInput(BaseModel):
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None

    def to_command(self) -> CreateJobCommand:
        return CreateJobCommand(
            title=self.title,
            company=self.company,
            description=self.description,
            location=self.location,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            technologies=self.technologies,
            source_url=self.source_url,
            source=self.source,
        )
    
class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    technologies: list[str] | None = None
    source_url: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
