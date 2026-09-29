import React, { useState } from 'react';
import { LoginForm } from './components/LoginForm';
import { RegisterForm } from './components/RegisterForm';
import { JobsView } from './views/JobsView';

type ViewMode = 'login' | 'register' | 'jobs';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewMode>('jobs');

  return (
    <div className="app-layout">
      <div className="preview-banner">
        Попередній перегляд (Stage 07.1) — Інтеграція з API та авторизація виконуються на наступних етапах
      </div>

      <header className="app-header">
        <div className="header-container">
          <h1 className="brand-title">AI Job Tracker</h1>
          <nav aria-label="Попередній перегляд навігації">
            <ul className="nav-list">
              <li>
                <button
                  type="button"
                  className={`nav-button ${activeView === 'jobs' ? 'active' : ''}`}
                  onClick={() => setActiveView('jobs')}
                >
                  Збережені вакансії
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-button ${activeView === 'login' ? 'active' : ''}`}
                  onClick={() => setActiveView('login')}
                >
                  Вхід
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-button ${activeView === 'register' ? 'active' : ''}`}
                  onClick={() => setActiveView('register')}
                >
                  Реєстрація
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="app-main">
        {activeView === 'login' && <LoginForm />}
        {activeView === 'register' && <RegisterForm />}
        {activeView === 'jobs' && <JobsView />}
      </main>

      <footer className="app-footer">
        <p>AI Job Tracker</p>
      </footer>
    </div>
  );
};

export default App;
