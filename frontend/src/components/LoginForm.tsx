import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToRegister }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Заповніть всі обов’язкові поля');
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setError(err?.message || 'Помилка при вході у систему');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Вхід у систему</h2>
      <p className="form-description">
        Увійдіть до свого облікового запису AI Job Tracker
      </p>

      {error && (
        <div className="form-error-alert" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
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
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
            required
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
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
            required
          />
        </div>

        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Вхід...' : 'Увійти'}
        </button>
      </form>

      {onSwitchToRegister && (
        <div className="form-footer-switch">
          <span>Немає облікового запису? </span>
          <button type="button" className="btn-link" onClick={onSwitchToRegister} disabled={isSubmitting}>
            Зареєструватися
          </button>
        </div>
      )}
    </div>
  );
};
