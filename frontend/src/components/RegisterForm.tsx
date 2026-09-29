import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const { register } = useAuth();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password) {
      setError('Заповніть всі обов’язкові поля');
      return;
    }

    if (password !== confirmPassword) {
      setError('Паролі не збігаються');
      return;
    }

    if (password.length < 8) {
      setError('Пароль повинен містити не менше 8 символів');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
      });

      setSuccessMessage('Реєстрація успішна! Тепер ви можете увійти до свого облікового запису.');
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err?.message || 'Помилка при реєстрації');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Реєстрація</h2>
      <p className="form-description">
        Створіть обліковий запис для відстеження збережених вакансій
      </p>

      {error && (
        <div className="form-error-alert" role="alert">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="form-success-alert" role="status">
          <p>{successMessage}</p>
          {onSwitchToLogin && (
            <button type="button" className="btn-primary" onClick={onSwitchToLogin} style={{ marginTop: '0.75rem' }}>
              Перейти до входу
            </button>
          )}
        </div>
      )}

      {!successMessage && (
        <form onSubmit={handleSubmit} noValidate>
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
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={isSubmitting}
                required
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
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                disabled={isSubmitting}
                required
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              required
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
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
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
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isSubmitting}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Реєстрація...' : 'Зареєструватися'}
          </button>
        </form>
      )}

      {onSwitchToLogin && !successMessage && (
        <div className="form-footer-switch">
          <span>Вже є обліковий запис? </span>
          <button type="button" className="btn-link" onClick={onSwitchToLogin} disabled={isSubmitting}>
            Увійти
          </button>
        </div>
      )}
    </div>
  );
};
