export interface User {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
}

export interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface ValidationErrorDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
}

export interface ApiErrorResponse {
  detail?: string | ValidationErrorDetail[];
}

export class ApiError extends Error {
  status: number;
  details?: ValidationErrorDetail[];

  constructor(message: string, status: number, details?: ValidationErrorDetail[]) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export type ApplicationStatus = 'applied' | 'interview' | 'offer' | 'rejected' | 'withdrawn';

export interface ApplicationSummaryResponse {
  id: string;
  status: ApplicationStatus;
  applied_at: string;
}

export interface ApplicationResponse {
  id: string;
  job_id: string;
  status: ApplicationStatus;
  notes?: string | null;
  applied_at: string;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateApplicationPayload {
  status?: ApplicationStatus;
  notes?: string | null;
  applied_at?: string | null;
}

export interface UpdateApplicationPayload {
  status?: ApplicationStatus;
  notes?: string | null;
  applied_at?: string | null;
}

export interface JobResponse {
  id: string;
  title: string;
  company: string;
  description?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  salary_period?: string | null;
  technologies?: string[] | null;
  source_url?: string | null;
  source?: string | null;
  application?: ApplicationSummaryResponse | null;
  created_at: string;
  updated_at?: string | null;
}

export interface JobListResponse {
  items: JobResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface FetchJobsParams {
  q?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface CreateJobPayload {
  title: string;
  company: string;
  description?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  salary_period?: string | null;
  technologies?: string[] | null;
  source_url?: string | null;
  source?: string | null;
}

export interface UpdateJobPayload {
  title?: string;
  company?: string;
  description?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  salary_period?: string | null;
  technologies?: string[] | null;
  source_url?: string | null;
  source?: string | null;
}

export interface JobImportFields {
  title?: string | null;
  company?: string | null;
  description?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  salary_period?: 'hour' | 'month' | 'year' | null;
  technologies?: string[] | null;
  source?: string | null;
}

export interface ImportPreviewRequest {
  url: string;
}

export interface ImportPreviewResponse {
  status: 'complete' | 'partial' | 'unavailable';
  source_url: string;
  fields: JobImportFields;
  reason_code?: string | null;
  message?: string | null;
}
