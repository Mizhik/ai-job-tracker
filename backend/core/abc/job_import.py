from abc import ABC, abstractmethod
from backend.core.job_import import JobImportFields


class JobUrlExtractorPort(ABC):
    @abstractmethod
    async def extract_job_fields_from_url(
        self, source_url: str
    ) -> tuple[JobImportFields | None, str | None, str | None]:
        """
        Extracts job posting facts directly from source_url via URL context provider.
        Returns tuple of (fields, reason_code, error_message).
        If extraction fails or content is invalid/unreadable, fields is None.
        """
        pass
