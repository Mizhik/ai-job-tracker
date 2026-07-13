from fastapi import Depends
from backend.app.jobs.service import JobService
from dependency_injector.wiring import inject, Provide


@inject
async def list_jobs(
    job_service: JobService = Depends(Provide["job_service"]),
):
    return await job_service.list_jobs()
