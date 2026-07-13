from backend.app.jobs.commands.create_job import CreateJobCommand, CreateJobCommandHandler
from backend.app.jobs.queries.get_job_by_id import GetJobByIdQuery, GetJobByIdQueryHandler
from backend.app.jobs.queries.list_jobs import ListJobsQueryHandler
from backend.core.job import Job
from backend.core.repository.job_repository import JobRepository


class JobService:
    def __init__(self, job_repository: JobRepository):
        self._create_job_handler = CreateJobCommandHandler(job_repository)
        self._get_job_by_id_handler = GetJobByIdQueryHandler(job_repository)
        self._list_jobs_handler = ListJobsQueryHandler(job_repository)

    async def create_job(self, command: CreateJobCommand) -> Job:
        return await self._create_job_handler(command)

    async def get_job_by_id(self, query: GetJobByIdQuery) -> Job:
        return await self._get_job_by_id_handler(query)

    async def list_jobs(self) -> list[Job]:
        return await self._list_jobs_handler()
