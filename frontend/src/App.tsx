import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginForm } from './components/LoginForm';
import { RegisterForm } from './components/RegisterForm';
import { JobsView } from './views/JobsView';
import { LoadingState } from './components/LoadingState';
import { ErrorState } from './components/ErrorState';

const AppContent: React.FC = () => {
  const { user, isAuthenticated, isLoading, sessionError, logoutError, logout, restoreSession } = useAuth();
  const [guestView, setGuestView] = useState<'login' | 'register'>('login');
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      setGuestView('login');
    } catch {
      // Error is caught and stored in logoutError by AuthContext
    } finally {
      setIsLoggingOut(false);
    }
  };

  if (isLoading) {
    return (
      <div className="app-layout">
        <main className="app-main">
          <LoadingState message="Перевірка сесії авторизації..." />
        </main>
      </div>
    );
  }

  const userDisplayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ');

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-container">
          <h1 className="brand-title">AI Job Tracker</h1>
          <nav aria-label="Навігація додатка">
            <ul className="nav-list">
              {isAuthenticated ? (
                <>
                  <li>
                    <button
                      type="button"
                      className="nav-button active"
                    >
                      Збережені вакансії
                    </button>
                  </li>
                  <li className="user-nav-info">
                    <span className="user-email-badge">
                      {userDisplayName ? `${userDisplayName} (${user?.email})` : user?.email}
                    </span>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={handleLogout}
                      disabled={isLoggingOut}
                    >
                      {isLoggingOut ? 'Вихід...' : 'Вийти'}
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <button
                      type="button"
                      className={`nav-button ${guestView === 'login' ? 'active' : ''}`}
                      onClick={() => setGuestView('login')}
                    >
                      Вхід
                    </button>
                  </li>
                  <li>
                    <button
                      type="button"
                      className={`nav-button ${guestView === 'register' ? 'active' : ''}`}
                      onClick={() => setGuestView('register')}
                    >
                      Реєстрація
                    </button>
                  </li>
                </>
              )}
            </ul>
          </nav>
        </div>
      </header>

      <main className="app-main">
        {logoutError && (
          <ErrorState
            title="Помилка виходу"
            message={logoutError}
            retryLabel="Спробувати знову"
            onRetry={handleLogout}
          />
        )}

        {sessionError && !isAuthenticated ? (
          <ErrorState
            title="Не вдалося перевірити сесію"
            message={sessionError}
            retryLabel="Спробувати знову"
            onRetry={restoreSession}
          />
        ) : isAuthenticated ? (
          <JobsView />
        ) : (
          guestView === 'login' ? (
            <LoginForm
              onSwitchToRegister={() => setGuestView('register')}
            />
          ) : (
            <RegisterForm
              onSwitchToLogin={() => setGuestView('login')}
            />
          )
        )}
      </main>

      <footer className="app-footer">
        <p>AI Job Tracker</p>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
