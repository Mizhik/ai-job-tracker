import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getJobById } from '../api/jobs';
import { JobResponse } from '../api/types';
import { formatDate, formatSalary } from '../utils/formatters';
import { ErrorState } from './ErrorState';
import { LoadingState } from './LoadingState';

interface JobDetailViewProps {
  jobId: string;
  onBack: () => void;
}

export const JobDetailView: React.FC<JobDetailViewProps> = ({ jobId, onBack }) => {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const requestIdRef = useRef<number>(0);

  const fetchJobDetails = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const data = await getJobById(jobId);
      if (requestId === requestIdRef.current) {
        setJob(data);
        setIsLoading(false);
      }
    } catch (err: any) {
      if (requestId === requestIdRef.current) {
        setError(err?.message || 'Не вдалося завантажити деталі вакансії.');
        setIsLoading(false);
      }
    }
  }, [jobId]);

  useEffect(() => {
    fetchJobDetails();
    return () => {
      requestIdRef.current++;
    };
  }, [fetchJobDetails]);

  const salaryFormatted = job
    ? formatSalary(job.salary_min, job.salary_max, job.currency, job.salary_period)
    : null;

  return (
    <article className="job-detail-container" aria-label="Деталі вакансії">
      <div className="job-detail-top-bar">
        <button type="button" className="btn-secondary back-button" onClick={onBack}>
          ← Назад до списку вакансій
        </button>
      </div>

      {isLoading ? (
        <LoadingState message="Завантаження деталей вакансії..." />
      ) : error ? (
        <div className="job-detail-error-wrapper">
          <ErrorState
            title="Помилка завантаження вакансії"
            message={error}
            retryLabel="Спробувати знову"
            onRetry={fetchJobDetails}
          />
        </div>
      ) : job ? (
        <div className="job-detail-card">
          <header className="job-detail-header">
            <h2 className="job-detail-title">{job.title}</h2>
            <p className="job-detail-company">{job.company}</p>

            <div className="job-meta-badges">
              {job.location && (
                <span className="job-badge job-badge-location" title="Локація">
                  {job.location}
                </span>
              )}
              {salaryFormatted && (
                <span className="job-badge job-badge-salary" title="Зарплата">
                  {salaryFormatted}
                </span>
              )}
              {job.source && (
                <span className="job-badge job-badge-source" title="Джерело">
                  {job.source}
                </span>
              )}
              <span className="job-badge job-badge-date" title="Дата збереження">
                {formatDate(job.created_at)}
              </span>
            </div>

            {job.source_url && (
              <div className="job-source-link-container">
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="job-source-link btn-link"
                >
                  Перейти до оригінального оголошення ↗
                </a>
              </div>
            )}
          </header>

          {job.technologies && job.technologies.length > 0 && (
            <section className="job-detail-section" aria-label="Технології">
              <h3 className="job-section-title">Технології та навички</h3>
              <div className="tech-tags-list">
                {job.technologies.map((tech, idx) => (
                  <span key={`${tech}-${idx}`} className="tech-tag">
                    {tech}
                  </span>
                ))}
              </div>
            </section>
          )}

          <section className="job-detail-section" aria-label="Опис вакансії">
            <h3 className="job-section-title">Опис вакансії</h3>
            <div className="job-description-content">
              {job.description ? (
                <p className="job-description-text">{job.description}</p>
              ) : (
                <p className="job-description-empty">Опис вакансії відсутній.</p>
              )}
            </div>
          </section>
        </div>
      ) : null}
    </article>
  );
};
