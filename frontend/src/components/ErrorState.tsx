import React from 'react';

interface ErrorStateProps {
  title?: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Сталася помилка',
  message,
  retryLabel = 'Спробувати знову',
  onRetry,
}) => {
  return (
    <div className="error-state" role="alert">
      <h3 className="error-state-title">{title}</h3>
      <p className="error-state-desc">{message}</p>
      {onRetry && (
        <button type="button" className="btn-secondary" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
};
