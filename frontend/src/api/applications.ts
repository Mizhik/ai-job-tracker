import { apiClient } from './client';
import {
  ApplicationResponse,
  CreateApplicationPayload,
  UpdateApplicationPayload,
} from './types';

export async function createApplication(
  jobId: string,
  payload: CreateApplicationPayload
): Promise<ApplicationResponse> {
  return apiClient.request<ApplicationResponse>(`/jobs/${jobId}/application`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function getApplicationById(applicationId: string): Promise<ApplicationResponse> {
  return apiClient.request<ApplicationResponse>(`/applications/${applicationId}`);
}

export async function updateApplication(
  applicationId: string,
  payload: UpdateApplicationPayload
): Promise<ApplicationResponse> {
  return apiClient.request<ApplicationResponse>(`/applications/${applicationId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function deleteApplication(applicationId: string): Promise<void> {
  return apiClient.request<void>(`/applications/${applicationId}`, {
    method: 'DELETE',
  });
}
