from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator, model_validator

from backend.core.application import ApplicationStatus


class ApplicationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ApplicationStatus
    applied_at: datetime

    @field_serializer("applied_at")
    def serialize_applied_at(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    status: ApplicationStatus
    notes: str | None = None
    applied_at: datetime
    created_at: datetime
    updated_at: datetime | None = None

    @field_serializer("applied_at", "created_at", "updated_at")
    def serialize_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ApplicationCreateInput(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None

    @field_validator("applied_at", mode="after")
    @classmethod
    def validate_tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and (v.tzinfo is None or v.tzinfo.utcoffset(v) is None):
            raise ValueError("applied_at must be a timezone-aware datetime")
        return v


class ApplicationUpdateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def check_non_empty_and_nulls(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if not data:
            raise ValueError("PATCH body cannot be empty")
        if "status" in data and data["status"] is None:
            raise ValueError("status cannot be null")
        if "applied_at" in data and data["applied_at"] is None:
            raise ValueError("applied_at cannot be null")
        return data

    @field_validator("applied_at", mode="after")
    @classmethod
    def validate_tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is not None and (v.tzinfo is None or v.tzinfo.utcoffset(v) is None):
            raise ValueError("applied_at must be a timezone-aware datetime")
        return v
