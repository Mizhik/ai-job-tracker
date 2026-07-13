from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from backend.api.schemas.job import JobCreateInput
from backend.app.jobs.commands.create_job import CreateJobCommand
from backend.app.jobs.service import JobService


@inject
async def create_job(
    job_create_input: JobCreateInput,
    job_service: JobService = Depends(Provide["job_service"]),
):
    return await job_service.create_job(job_create_input.to_command())
