import React from 'react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Завантаження...',
}) => {
  return (
    <div className="loading-state" role="status">
      <div className="loading-spinner" />
      <span>{message}</span>
    </div>
  );
};
