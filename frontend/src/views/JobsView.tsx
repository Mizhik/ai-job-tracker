import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getJobs } from '../api/jobs';
import { JobResponse } from '../api/types';
import { CreateJobForm } from '../components/CreateJobForm';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { JobDetailView } from '../components/JobDetailView';
import { LoadingState } from '../components/LoadingState';
import { formatDate, formatSalary, getStatusBadgeClass, getStatusLabel } from '../utils/formatters';

export const JobsView: React.FC = () => {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState<boolean>(false);

  const [searchInput, setSearchInput] = useState<string>('');
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [activeStatus, setActiveStatus] = useState<string>('');
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
        status: activeStatus,
        limit,
        offset,
      });

      if (requestId === requestIdRef.current) {
        // Boundary check: if items were deleted and offset is at or beyond total, adjust offset
        if (offset > 0 && offset >= response.total) {
          const newOffset = response.total > 0
            ? Math.max(0, (Math.ceil(response.total / limit) - 1) * limit)
            : 0;
          setOffset(newOffset);
          return;
        }

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
  }, [activeQuery, activeStatus, offset, listRevision]);

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

  const handleStatusSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setStatusFilter(val);
    setActiveStatus(val);
    setOffset(0);
  };

  const handleResetFilters = () => {
    setSearchInput('');
    setActiveQuery('');
    setStatusFilter('');
    setActiveStatus('');
    setOffset(0);
  };

  const handleCreateSuccess = (createdJob: JobResponse) => {
    handleResetFilters();
    setListRevision((revision) => revision + 1);
    setIsCreating(false);
    setSelectedJobId(createdJob.id);
  };

  const handleBackFromDetail = (wasModified?: boolean) => {
    setSelectedJobId(null);
    if (wasModified) {
      setListRevision((revision) => revision + 1);
    }
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
        onBack={handleBackFromDetail}
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

  const isFilterActive = Boolean(activeQuery || activeStatus);

  return (
    <section className="jobs-view-container" aria-label="Трекер вакансій">
      <div className="jobs-header-actions">
        <h2 className="jobs-view-title">Трекер вакансій</h2>
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
                onClick={() => {
                  setSearchInput('');
                  setActiveQuery('');
                  setOffset(0);
                }}
                aria-label="Очистити поле пошуку"
              >
                ✕
              </button>
            )}
          </div>

          <div className="status-filter-wrapper">
            <select
              className="form-input status-select"
              value={statusFilter}
              onChange={handleStatusSelectChange}
              aria-label="Фільтр за статусом"
            >
              <option value="">Всі статуси</option>
              <option value="saved">Збережено (без відгуку)</option>
              <option value="applied">Подано</option>
              <option value="interview">Співбесіда</option>
              <option value="offer">Офер</option>
              <option value="rejected">Відмова</option>
              <option value="withdrawn">Відкликано</option>
            </select>
          </div>

          <button type="submit" className="btn-primary search-submit-btn">
            Шукати
          </button>

          {isFilterActive && (
            <button
              type="button"
              className="btn-secondary clear-search-btn"
              onClick={handleResetFilters}
            >
              Скинути фільтри
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
        isFilterActive ? (
          <EmptyState
            title="Нічого не знайдено"
            description="За вашим запитом або обраним фільтром не знайдено жодної вакансії."
            actionLabel="Очистити фільтри"
            onAction={handleResetFilters}
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
              {isFilterActive
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
              const currentStatus = job.application?.status || 'saved';

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
                        <span className={`job-badge ${getStatusBadgeClass(currentStatus)}`}>
                          {getStatusLabel(currentStatus)}
                        </span>
                        {job.application?.applied_at && (
                          <span className="job-badge job-badge-date" title="Дата відгуку">
                            Відгук: {formatDate(job.application.applied_at)}
                          </span>
                        )}
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
                        <span className="job-badge job-badge-date" title="Дата збереження">
                          Збережено: {formatDate(job.created_at)}
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
