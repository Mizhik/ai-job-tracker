import React from 'react';

export const RegisterForm: React.FC = () => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Реєстрація</h2>
      <p className="form-description">
        Створіть обліковий запис для відстеження збережених вакансій
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="first_name" className="form-label">
              Ім'я
            </label>
            <input
              id="first_name"
              type="text"
              name="first_name"
              className="form-input"
              placeholder="Іван"
              disabled
            />
          </div>

          <div className="form-group">
            <label htmlFor="last_name" className="form-label">
              Прізвище
            </label>
            <input
              id="last_name"
              type="text"
              name="last_name"
              className="form-input"
              placeholder="Петренко"
              disabled
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="register_email" className="form-label">
            Електронна пошта
          </label>
          <input
            id="register_email"
            type="email"
            name="email"
            className="form-input"
            placeholder="name@example.com"
            disabled
          />
        </div>

        <div className="form-group">
          <label htmlFor="register_password" className="form-label">
            Пароль
          </label>
          <input
            id="register_password"
            type="password"
            name="password"
            className="form-input"
            placeholder="••••••••"
            disabled
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirm_password" className="form-label">
            Підтвердження пароля
          </label>
          <input
            id="confirm_password"
            type="password"
            name="confirm_password"
            className="form-input"
            placeholder="••••••••"
            disabled
          />
        </div>

        <button type="submit" className="btn-primary" disabled>
          Зареєструватися (попередній перегляд)
        </button>
      </form>
    </div>
  );
};
