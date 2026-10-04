import { apiClient } from './client';
import {
  CreateJobPayload,
  FetchJobsParams,
  ImportPreviewResponse,
  JobListResponse,
  JobResponse,
  UpdateJobPayload,
} from './types';

export async function getJobs(params: FetchJobsParams = {}): Promise<JobListResponse> {
  const query = new URLSearchParams();

  if (params.q !== undefined && params.q.trim() !== '') {
    query.append('q', params.q.trim());
  }
  if (params.status !== undefined && params.status.trim() !== '') {
    query.append('status', params.status.trim());
  }
  if (params.limit !== undefined) {
    query.append('limit', params.limit.toString());
  }
  if (params.offset !== undefined) {
    query.append('offset', params.offset.toString());
  }

  const queryString = query.toString();
  const endpoint = queryString ? `/jobs?${queryString}` : '/jobs';

  return apiClient.request<JobListResponse>(endpoint);
}

export async function getJobById(jobId: string): Promise<JobResponse> {
  return apiClient.request<JobResponse>(`/jobs/${jobId}`);
}

export async function createJob(payload: CreateJobPayload): Promise<JobResponse> {
  return apiClient.request<JobResponse>('/jobs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function updateJob(jobId: string, payload: UpdateJobPayload): Promise<JobResponse> {
  return apiClient.request<JobResponse>(`/jobs/${jobId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function deleteJob(jobId: string): Promise<void> {
  return apiClient.request<void>(`/jobs/${jobId}`, {
    method: 'DELETE',
  });
}

export async function importJobPreview(url: string): Promise<ImportPreviewResponse> {
  return apiClient.request<ImportPreviewResponse>('/jobs/import-preview', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });
}
