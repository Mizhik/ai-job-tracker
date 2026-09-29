import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getJobs } from '../api/jobs';
import { JobResponse } from '../api/types';
import { CreateJobForm } from '../components/CreateJobForm';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { JobDetailView } from '../components/JobDetailView';
import { LoadingState } from '../components/LoadingState';
import { formatDate, formatSalary } from '../utils/formatters';

export const JobsView: React.FC = () => {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState<boolean>(false);

  const [searchInput, setSearchInput] = useState<string>('');
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [offset, setOffset] = useState<number>(0);
  const [listRevision, setListRevision] = useState<number>(0);
  const limit = 20;

  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const requestIdRef = useRef<number>(0);

  const fetchJobsList = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);

    try {
      const response = await getJobs({
        q: activeQuery,
        limit,
        offset,
      });
      if (requestId === requestIdRef.current) {
        setJobs(response.items);
        setTotal(response.total);
        setIsLoading(false);
      }
    } catch (err: any) {
      if (requestId === requestIdRef.current) {
        setError(err?.message || 'Не вдалося завантажити список вакансій.');
        setIsLoading(false);
      }
    }
  }, [activeQuery, offset, listRevision]);

  useEffect(() => {
    fetchJobsList();
    return () => {
      requestIdRef.current++;
    };
  }, [fetchJobsList]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveQuery(searchInput);
    setOffset(0);
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setActiveQuery('');
    setOffset(0);
  };

  const handleCreateSuccess = (createdJob: JobResponse) => {
    setSearchInput('');
    setActiveQuery('');
    setOffset(0);
    setListRevision((revision) => revision + 1);
    setIsCreating(false);
    setSelectedJobId(createdJob.id);
  };

  const totalPages = Math.ceil(total / limit) || 1;
  const currentPage = Math.floor(offset / limit) + 1;

  const handlePrevPage = () => {
    if (offset >= limit) {
      setOffset(offset - limit);
    }
  };

  const handleNextPage = () => {
    if (offset + limit < total) {
      setOffset(offset + limit);
    }
  };

  if (selectedJobId) {
    return (
      <JobDetailView
        jobId={selectedJobId}
        onBack={() => setSelectedJobId(null)}
      />
    );
  }

  if (isCreating) {
    return (
      <section className="jobs-view-container" aria-label="Створення вакансії">
        <CreateJobForm
          onSuccess={handleCreateSuccess}
          onCancel={() => setIsCreating(false)}
        />
      </section>
    );
  }

  return (
    <section className="jobs-view-container" aria-label="Збережені вакансії">
      <div className="jobs-header-actions">
        <h2 className="jobs-view-title">Збережені вакансії</h2>
        <button
          type="button"
          className="btn-primary create-job-btn"
          onClick={() => setIsCreating(true)}
        >
          + Додати вакансію
        </button>
      </div>

      <div className="jobs-search-section">
        <form className="search-form" onSubmit={handleSearchSubmit}>
          <div className="search-input-wrapper">
            <input
              type="text"
              className="form-input search-input"
              placeholder="Пошук за назвою або компанією..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              aria-label="Пошуковий запит вакансій"
            />
            {searchInput && (
              <button
                type="button"
                className="search-input-clear-btn"
                onClick={handleClearSearch}
                aria-label="Очистити поле пошуку"
              >
                ✕
              </button>
            )}
          </div>
          <button type="submit" className="btn-primary search-submit-btn">
            Шукати
          </button>
          {activeQuery && (
            <button
              type="button"
              className="btn-secondary clear-search-btn"
              onClick={handleClearSearch}
            >
              Скинути фільтр
            </button>
          )}
        </form>
      </div>

      {isLoading ? (
        <LoadingState message="Завантаження вакансій..." />
      ) : error ? (
        <ErrorState
          title="Помилка завантаження"
          message={error}
          retryLabel="Спробувати знову"
          onRetry={fetchJobsList}
        />
      ) : total === 0 ? (
        activeQuery ? (
          <EmptyState
            title="Нічого не знайдено"
            description={`За вашим запитом «${activeQuery}» не знайдено жодної вакансії.`}
            actionLabel="Очистити пошук"
            onAction={handleClearSearch}
          />
        ) : (
          <EmptyState
            title="Немає збережених вакансій"
            description="У вас ще немає збережених вакансій. Додайте першу вакансію, щоб розпочати відстеження."
            actionLabel="Додати вакансію"
            onAction={() => setIsCreating(true)}
          />
        )
      ) : (
        <div className="jobs-content">
          <div className="jobs-list-info">
            <span className="jobs-total-badge">
              {activeQuery
                ? `Знайдено вакансій: ${total}`
                : `Усього збережених вакансій: ${total}`}
            </span>
          </div>

          <ul className="jobs-list" aria-label="Список вакансій">
            {jobs.map((job) => {
              const salaryFormatted = formatSalary(
                job.salary_min,
                job.salary_max,
                job.currency,
                job.salary_period
              );

              return (
                <li key={job.id} className="job-card-item">
                  <article className="job-card">
                    <div className="job-card-main">
                      <div className="job-card-header">
                        <h3 className="job-card-title">
                          <button
                            type="button"
                            className="job-title-btn"
                            onClick={() => setSelectedJobId(job.id)}
                          >
                            {job.title}
                          </button>
                        </h3>
                        <p className="job-card-company">{job.company}</p>
                      </div>

                      <div className="job-card-meta">
                        {job.location && (
                          <span className="job-badge job-badge-location">
                            {job.location}
                          </span>
                        )}
                        {salaryFormatted && (
                          <span className="job-badge job-badge-salary">
                            {salaryFormatted}
                          </span>
                        )}
                        {job.source && (
                          <span className="job-badge job-badge-source">
                            {job.source}
                          </span>
                        )}
                        <span className="job-badge job-badge-date">
                          {formatDate(job.created_at)}
                        </span>
                      </div>

                      {job.technologies && job.technologies.length > 0 && (
                        <div className="job-card-techs">
                          {job.technologies.slice(0, 6).map((tech, idx) => (
                            <span key={`${tech}-${idx}`} className="tech-tag tech-tag-sm">
                              {tech}
                            </span>
                          ))}
                          {job.technologies.length > 6 && (
                            <span className="tech-tag-more">
                              +{job.technologies.length - 6}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="job-card-actions">
                      <button
                        type="button"
                        className="btn-secondary view-details-btn"
                        onClick={() => setSelectedJobId(job.id)}
                      >
                        Детальніше →
                      </button>
                    </div>
                  </article>
                </li>
              );
            })}
          </ul>

          {totalPages > 1 && (
            <nav className="pagination-container" aria-label="Навігація по сторінках">
              <button
                type="button"
                className="btn-secondary"
                onClick={handlePrevPage}
                disabled={offset === 0}
              >
                ← Попередня
              </button>
              <span className="pagination-info">
                Сторінка {currentPage} з {totalPages}
              </span>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleNextPage}
                disabled={offset + limit >= total}
              >
                Наступна →
              </button>
            </nav>
          )}
        </div>
      )}
    </section>
  );
};
