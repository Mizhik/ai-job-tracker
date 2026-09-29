import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { apiClient } from '../api/client';
import {
  AuthTokenResponse,
  CsrfResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from '../api/types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  logoutError: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  clearLogoutError: () => void;
  restoreSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  const restorePromiseRef = useRef<Promise<void> | null>(null);

  const performRefresh = useCallback(async (): Promise<string | null> => {
    try {
      const csrfRes = await apiClient.request<CsrfResponse>('/users/csrf', { skipAuth: true });
      const refreshRes = await apiClient.request<AuthTokenResponse>('/users/refresh', {
        method: 'POST',
        skipAuth: true,
        headers: {
          'X-CSRF-Token': csrfRes.csrf_token,
        },
      });
      return refreshRes.access_token;
    } catch {
      return null;
    }
  }, []);

  const handleUnauthenticated = useCallback(() => {
    apiClient.setAccessToken(null);
    setUser(null);
  }, []);

  const restoreSession = useCallback(async () => {
    if (restorePromiseRef.current) {
      return restorePromiseRef.current;
    }

    setIsLoading(true);
    setLogoutError(null);

    const promise = (async () => {
      try {
        const token = await performRefresh();
        if (token) {
          apiClient.setAccessToken(token);
          const currentUser = await apiClient.request<User>('/users/me');
          setUser(currentUser);
        } else {
          apiClient.setAccessToken(null);
          setUser(null);
        }
      } catch {
        apiClient.setAccessToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
        restorePromiseRef.current = null;
      }
    })();

    restorePromiseRef.current = promise;
    return promise;
  }, [performRefresh]);

  useEffect(() => {
    apiClient.setRefreshHandler(performRefresh);
    apiClient.setUnauthenticatedHandler(handleUnauthenticated);
    restoreSession();
  }, [performRefresh, handleUnauthenticated, restoreSession]);

  const login = async (payload: LoginPayload): Promise<void> => {
    setLogoutError(null);
    const bodyParams = new URLSearchParams();
    bodyParams.append('username', payload.email);
    bodyParams.append('password', payload.password);

    const tokenRes = await apiClient.request<AuthTokenResponse>('/users/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: bodyParams.toString(),
      skipAuth: true,
    });

    apiClient.setAccessToken(tokenRes.access_token);
    const currentUser = await apiClient.request<User>('/users/me');
    setUser(currentUser);
  };

  const register = async (payload: RegisterPayload): Promise<User> => {
    setLogoutError(null);
    return apiClient.request<User>('/users/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      skipAuth: true,
    });
  };

  const logout = async (): Promise<void> => {
    setLogoutError(null);

    let csrfToken = '';
    try {
      const csrfRes = await apiClient.request<CsrfResponse>('/users/csrf', { skipAuth: true });
      csrfToken = csrfRes.csrf_token;
    } catch {
      // Ignore CSRF fetch error; proceed to attempt logout
    }

    try {
      await apiClient.request<{ message: string }>('/users/logout', {
        method: 'POST',
        headers: {
          'X-CSRF-Token': csrfToken,
        },
        skipAuth: true,
      });

      // Clear state only after successful server session revocation
      apiClient.setAccessToken(null);
      setUser(null);
    } catch (err: any) {
      const msg = err?.message || 'Не вдалося вийти з системи на сервері';
      setLogoutError(msg);
      throw new Error(msg);
    }
  };

  const clearLogoutError = () => {
    setLogoutError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        logoutError,
        login,
        register,
        logout,
        clearLogoutError,
        restoreSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
