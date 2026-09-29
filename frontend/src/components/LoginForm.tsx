import React from 'react';

export const LoginForm: React.FC = () => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Вхід у систему</h2>
      <p className="form-description">
        Увійдіть до свого облікового запису AI Job Tracker
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Електронна пошта
          </label>
          <input
            id="email"
            type="email"
            name="email"
            className="form-input"
            placeholder="name@example.com"
            disabled
          />
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">
            Пароль
          </label>
          <input
            id="password"
            type="password"
            name="password"
            className="form-input"
            placeholder="••••••••"
            disabled
          />
        </div>

        <button type="submit" className="btn-primary" disabled>
          Увійти (попередній перегляд)
        </button>
      </form>
    </div>
  );
};
