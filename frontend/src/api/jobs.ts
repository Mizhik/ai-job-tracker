import { apiClient } from './client';
import { FetchJobsParams, JobListResponse, JobResponse } from './types';

export async function getJobs(params: FetchJobsParams = {}): Promise<JobListResponse> {
  const query = new URLSearchParams();

  if (params.q !== undefined && params.q.trim() !== '') {
    query.append('q', params.q.trim());
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
