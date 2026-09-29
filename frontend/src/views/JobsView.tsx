import React from 'react';
import { EmptyState } from '../components/EmptyState';

export const JobsView: React.FC = () => {
  return (
    <section aria-label="Збережені вакансії">
      <EmptyState
        title="Немає збережених вакансій"
        description="Ви ще не зберегли жодної вакансії. Збережені вакансії з'являться тут після підключення API."
      />
    </section>
  );
};
