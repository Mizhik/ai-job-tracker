import { ApiError, ApiErrorResponse, ValidationErrorDetail } from './types';

export function parseApiErrorMessage(status: number, data: unknown): { message: string; details?: ValidationErrorDetail[] } {
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const errorObj = data as ApiErrorResponse;
    if (typeof errorObj.detail === 'string') {
      return { message: errorObj.detail };
    }
    if (Array.isArray(errorObj.detail)) {
      const details = errorObj.detail;
      const messages = details
        .map((item) => {
          const field = item.loc ? item.loc.filter((loc) => loc !== 'body').join('.') : '';
          return field ? `${field}: ${item.msg}` : item.msg;
        })
        .filter(Boolean);
      return {
        message: messages.length > 0 ? messages.join('; ') : 'Помилка перевірки даних',
        details,
      };
    }
  }

  if (status === 401) {
    return { message: 'Необхідна авторизація або сесія закінчилася' };
  }
  if (status === 403) {
    return { message: 'Доступ заборонено' };
  }
  if (status === 404) {
    return { message: 'Ресурс не знайдено' };
  }
  if (status >= 500) {
    return { message: 'Сервер тимчасово недоступний. Спробуйте ще раз пізніше.' };
  }

  return { message: 'Сталася невідома помилка' };
}

type RefreshHandler = () => Promise<string | null>;
type UnauthenticatedHandler = () => void;

class ApiClient {
  private accessToken: string | null = null;
  private refreshHandler: RefreshHandler | null = null;
  private unauthenticatedHandler: UnauthenticatedHandler | null = null;
  private refreshPromise: Promise<string | null> | null = null;

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  setRefreshHandler(handler: RefreshHandler): void {
    this.refreshHandler = handler;
  }

  setUnauthenticatedHandler(handler: UnauthenticatedHandler): void {
    this.unauthenticatedHandler = handler;
  }

  private async refreshSingleFlight(): Promise<string | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    if (!this.refreshHandler) {
      return null;
    }

    this.refreshPromise = (async () => {
      try {
        const token = await this.refreshHandler!();
        this.setAccessToken(token);
        return token;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit & { skipAuth?: boolean; isRetry?: boolean } = {}
  ): Promise<T> {
    const { skipAuth, isRetry, headers: customHeaders, ...restOptions } = options;

    const headers: Record<string, string> = {
      ...(customHeaders as Record<string, string>),
    };

    if (!skipAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    let response: Response;
    try {
      response = await fetch(endpoint, {
        ...restOptions,
        headers,
        credentials: 'include',
      });
    } catch (err) {
      throw new ApiError(
        'Помилка мережі. Перевірте з’єднання з інтернетом',
        0
      );
    }

    if (response.status === 401 && !skipAuth && !isRetry && this.refreshHandler) {
      const newToken = await this.refreshSingleFlight();

      if (newToken) {
        try {
          return await this.request<T>(endpoint, {
            ...options,
            isRetry: true,
          });
        } catch (retryErr: any) {
          if (retryErr instanceof ApiError && retryErr.status === 401) {
            this.setAccessToken(null);
            if (this.unauthenticatedHandler) {
              this.unauthenticatedHandler();
            }
          }
          throw retryErr;
        }
      } else {
        this.setAccessToken(null);
        if (this.unauthenticatedHandler) {
          this.unauthenticatedHandler();
        }
      }
    }

    if (!response.ok) {
      let data: unknown;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      const { message, details } = parseApiErrorMessage(response.status, data);
      throw new ApiError(message, response.status, details);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json() as Promise<T>;
  }
}

export const apiClient = new ApiClient();
