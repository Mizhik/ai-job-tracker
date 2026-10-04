import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createApplication, deleteApplication, getApplicationById, updateApplication } from '../api/applications';
import { deleteJob, getJobById } from '../api/jobs';
import { ApplicationResponse, ApplicationStatus, JobResponse, UpdateApplicationPayload } from '../api/types';
import {
  formatDate,
  formatDateTime,
  formatSalary,
  getStatusBadgeClass,
  getStatusLabel,
  isoToDateTimeLocal,
  localToIsoWithTimezone,
} from '../utils/formatters';
import { EditJobForm } from './EditJobForm';
import { ErrorState } from './ErrorState';
import { LoadingState } from './LoadingState';

interface JobDetailViewProps {
  jobId: string;
  onBack: (wasModified?: boolean) => void;
}

export const JobDetailView: React.FC<JobDetailViewProps> = ({ jobId, onBack }) => {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [isJobLoading, setIsJobLoading] = useState<boolean>(true);
  const [jobError, setJobError] = useState<string | null>(null);

  // Job edit state
  const [isEditingJob, setIsEditingJob] = useState<boolean>(false);

  // Job delete modal state
  const [showDeleteJobModal, setShowDeleteJobModal] = useState<boolean>(false);
  const [isDeletingJob, setIsDeletingJob] = useState<boolean>(false);
  const [deleteJobError, setDeleteJobError] = useState<string | null>(null);

  // Full Application state
  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [isAppLoading, setIsAppLoading] = useState<boolean>(false);
  const [appError, setAppError] = useState<string | null>(null);

  // Application creation form state
  const [createAppStatus, setCreateAppStatus] = useState<ApplicationStatus>('applied');
  const [createAppDateLocal, setCreateAppDateLocal] = useState<string>('');
  const [createAppNotes, setCreateAppNotes] = useState<string>('');
  const [isCreatingApp, setIsCreatingApp] = useState<boolean>(false);
  const [createAppError, setCreateAppError] = useState<string | null>(null);

  // Application edit form state
  const [isEditingApp, setIsEditingApp] = useState<boolean>(false);
  const [editAppStatus, setEditAppStatus] = useState<ApplicationStatus>('applied');
  const [editAppDateLocal, setEditAppDateLocal] = useState<string>('');
  const [isEditDateTouched, setIsEditDateTouched] = useState<boolean>(false);
  const [editAppNotes, setEditAppNotes] = useState<string>('');
  const [isUpdatingApp, setIsUpdatingApp] = useState<boolean>(false);
  const [editAppError, setEditAppError] = useState<string | null>(null);

  // Application delete modal state
  const [showDeleteAppModal, setShowDeleteAppModal] = useState<boolean>(false);
  const [isDeletingApp, setIsDeletingApp] = useState<boolean>(false);
  const [deleteAppError, setDeleteAppError] = useState<string | null>(null);

  const [wasModified, setWasModified] = useState<boolean>(false);

  // Focus and keyboard refs for accessibility in modals
  const previousActiveElementRef = useRef<HTMLElement | null>(null);
  const deleteJobCancelBtnRef = useRef<HTMLButtonElement | null>(null);
  const deleteJobModalRef = useRef<HTMLDivElement | null>(null);
  const deleteAppCancelBtnRef = useRef<HTMLButtonElement | null>(null);
  const deleteAppModalRef = useRef<HTMLDivElement | null>(null);

  const jobRequestIdRef = useRef<number>(0);

  const fetchJobDetails = useCallback(async () => {
    const requestId = ++jobRequestIdRef.current;
    setIsJobLoading(true);
    setJobError(null);

    try {
      const data = await getJobById(jobId);
      if (requestId === jobRequestIdRef.current) {
        setJob(data);
        setIsJobLoading(false);
      }
    } catch (err: any) {
      if (requestId === jobRequestIdRef.current) {
        setJobError(err?.message || 'Не вдалося завантажити деталі вакансії.');
        setIsJobLoading(false);
      }
    }
  }, [jobId]);

  useEffect(() => {
    fetchJobDetails();
    return () => {
      jobRequestIdRef.current++;
    };
  }, [fetchJobDetails]);

  // Fetch full application when job application exists
  const fetchFullApplication = useCallback(async (appId: string) => {
    setIsAppLoading(true);
    setAppError(null);
    try {
      const appData = await getApplicationById(appId);
      setApplication(appData);
    } catch (err: any) {
      setAppError(err?.message || 'Не вдалося завантажити дані відгуку.');
    } finally {
      setIsAppLoading(false);
    }
  }, []);

  useEffect(() => {
    if (job?.application?.id) {
      fetchFullApplication(job.application.id);
    } else {
      setApplication(null);
    }
  }, [job?.application?.id, fetchFullApplication]);

  // Accessibility & Focus trap effect for Job Delete Modal
  useEffect(() => {
    if (!showDeleteJobModal) return;

    previousActiveElementRef.current = document.activeElement as HTMLElement;
    setTimeout(() => {
      deleteJobCancelBtnRef.current?.focus();
    }, 50);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowDeleteJobModal(false);
      } else if (e.key === 'Tab' && deleteJobModalRef.current) {
        const focusables = deleteJobModalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      previousActiveElementRef.current?.focus();
    };
  }, [showDeleteJobModal]);

  // Accessibility & Focus trap effect for Application Delete Modal
  useEffect(() => {
    if (!showDeleteAppModal) return;

    previousActiveElementRef.current = document.activeElement as HTMLElement;
    setTimeout(() => {
      deleteAppCancelBtnRef.current?.focus();
    }, 50);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowDeleteAppModal(false);
      } else if (e.key === 'Tab' && deleteAppModalRef.current) {
        const focusables = deleteAppModalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      previousActiveElementRef.current?.focus();
    };
  }, [showDeleteAppModal]);

  // Handler for job deletion
  const handleDeleteJobConfirm = async () => {
    if (!job) return;
    setIsDeletingJob(true);
    setDeleteJobError(null);
    try {
      await deleteJob(job.id);
      onBack(true);
    } catch (err: any) {
      setDeleteJobError(err?.message || 'Не вдалося видалити вакансію.');
      setIsDeletingJob(false);
    }
  };

  // Handler for application creation
  const handleCreateAppSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!job) return;
    setIsCreatingApp(true);
    setCreateAppError(null);

    const payload: { status?: ApplicationStatus; notes?: string | null; applied_at?: string | null } = {
      status: createAppStatus,
    };

    if (createAppNotes.trim()) {
      payload.notes = createAppNotes.trim();
    }

    if (createAppDateLocal.trim()) {
      const isoStr = localToIsoWithTimezone(createAppDateLocal.trim());
      if (isoStr) {
        payload.applied_at = isoStr;
      }
    }

    try {
      const createdApp = await createApplication(job.id, payload);
      setWasModified(true);
      setJob((prev) =>
        prev
          ? {
              ...prev,
              application: {
                id: createdApp.id,
                status: createdApp.status,
                applied_at: createdApp.applied_at,
              },
            }
          : null
      );
      setApplication(createdApp);
      // Reset form
      setCreateAppNotes('');
      setCreateAppDateLocal('');
      setCreateAppStatus('applied');
    } catch (err: any) {
      setCreateAppError(err?.message || 'Не вдалося створити відгук.');
    } finally {
      setIsCreatingApp(false);
    }
  };

  // Initialize application edit form
  const handleStartEditingApp = () => {
    if (!application) return;
    setEditAppStatus(application.status);
    setEditAppDateLocal(isoToDateTimeLocal(application.applied_at));
    setIsEditDateTouched(false);
    setEditAppNotes(application.notes || '');
    setEditAppError(null);
    setIsEditingApp(true);
  };

  // Handler for application update
  const handleUpdateAppSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!application || !job) return;
    setIsUpdatingApp(true);
    setEditAppError(null);

    const payload: UpdateApplicationPayload = {};

    if (editAppStatus !== application.status) {
      payload.status = editAppStatus;
    }

    if (isEditDateTouched) {
      const trimmedDate = editAppDateLocal.trim();
      if (!trimmedDate) {
        setEditAppError('Вкажіть дату та час відгуку (дата не може бути порожньою)');
        setIsUpdatingApp(false);
        return;
      }
      const isoStr = localToIsoWithTimezone(trimmedDate);
      if (!isoStr) {
        setEditAppError('Вкажіть коректну дату та час відгуку');
        setIsUpdatingApp(false);
        return;
      }
      payload.applied_at = isoStr;
    }

    const trimmedNotes = editAppNotes.trim();
    const origNotes = application.notes || '';
    if (trimmedNotes !== origNotes) {
      payload.notes = trimmedNotes ? trimmedNotes : null;
    }

    if (Object.keys(payload).length === 0) {
      setIsEditingApp(false);
      setIsUpdatingApp(false);
      return;
    }

    try {
      const updatedApp = await updateApplication(application.id, payload);
      setWasModified(true);
      setApplication(updatedApp);
      setJob((prev) =>
        prev
          ? {
              ...prev,
              application: {
                id: updatedApp.id,
                status: updatedApp.status,
                applied_at: updatedApp.applied_at,
              },
            }
          : null
      );
      setIsEditingApp(false);
    } catch (err: any) {
      setEditAppError(err?.message || 'Не вдалося оновити відгук.');
    } finally {
      setIsUpdatingApp(false);
    }
  };

  // Handler for application deletion
  const handleDeleteAppConfirm = async () => {
    if (!application || !job) return;
    setIsDeletingApp(true);
    setDeleteAppError(null);
    try {
      await deleteApplication(application.id);
      setWasModified(true);
      setJob((prev) => (prev ? { ...prev, application: null } : null));
      setApplication(null);
      setShowDeleteAppModal(false);
    } catch (err: any) {
      setDeleteAppError(err?.message || 'Не вдалося видалити відгук.');
    } finally {
      setIsDeletingApp(false);
    }
  };

  // Preserves existing job.application summary on job update (Defect 1 fix)
  const handleJobUpdateSuccess = (updatedJob: JobResponse) => {
    setJob((prevJob) => {
      const appSummary = prevJob?.application ?? updatedJob.application ?? null;
      return {
        ...updatedJob,
        application: appSummary,
      };
    });
    setWasModified(true);
    setIsEditingJob(false);
  };

  const salaryFormatted = job
    ? formatSalary(job.salary_min, job.salary_max, job.currency, job.salary_period)
    : null;

  const currentStatus: ApplicationStatus | 'saved' = job?.application?.status || 'saved';

  return (
    <article className="job-detail-container" aria-label="Деталі вакансії">
      <div className="job-detail-top-bar">
        <button
          type="button"
          className="btn-secondary back-button"
          onClick={() => onBack(wasModified)}
        >
          ← Назад до списку вакансій
        </button>
      </div>

      {isJobLoading ? (
        <LoadingState message="Завантаження деталей вакансії..." />
      ) : jobError ? (
        <div className="job-detail-error-wrapper">
          <ErrorState
            title="Помилка завантаження вакансії"
            message={jobError}
            retryLabel="Спробувати знову"
            onRetry={fetchJobDetails}
          />
        </div>
      ) : isEditingJob && job ? (
        <EditJobForm
          job={job}
          onSuccess={handleJobUpdateSuccess}
          onCancel={() => setIsEditingJob(false)}
        />
      ) : job ? (
        <div className="job-detail-card">
          <header className="job-detail-header">
            <div className="job-detail-title-row">
              <div>
                <h2 className="job-detail-title">{job.title}</h2>
                <p className="job-detail-company">{job.company}</p>
              </div>
              <div className="job-detail-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setIsEditingJob(true)}
                >
                  Редагувати вакансію
                </button>
                <button
                  type="button"
                  className="btn-danger"
                  onClick={() => {
                    setDeleteJobError(null);
                    setShowDeleteJobModal(true);
                  }}
                >
                  Видалити вакансію
                </button>
              </div>
            </div>

            <div className="job-meta-badges">
              <span className={`job-badge ${getStatusBadgeClass(currentStatus)}`}>
                {getStatusLabel(currentStatus)}
              </span>
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
                Збережено: {formatDate(job.created_at)}
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

          {/* APPLICATION TRACKING SECTION */}
          <section className="job-detail-section application-section" aria-label="Інформація про відгук">
            <h3 className="job-section-title">Відгук та трекінг</h3>

            {!job.application ? (
              <div className="app-card app-create-card">
                <p className="app-not-applied-msg">
                  Ви ще не подавали відгук на цю вакансію. Заповніть форму нижче, щоб розпочати відстеження.
                </p>

                {createAppError && (
                  <div className="form-error-alert" role="alert">
                    {createAppError}
                  </div>
                )}

                <form onSubmit={handleCreateAppSubmit} noValidate className="app-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="create-app-status" className="form-label">
                        Статус відгуку
                      </label>
                      <select
                        id="create-app-status"
                        className="form-input"
                        value={createAppStatus}
                        onChange={(e) => setCreateAppStatus(e.target.value as ApplicationStatus)}
                        disabled={isCreatingApp}
                      >
                        <option value="applied">Подано (Applied)</option>
                        <option value="interview">Співбесіда (Interview)</option>
                        <option value="offer">Офер (Offer)</option>
                        <option value="rejected">Відмова (Rejected)</option>
                        <option value="withdrawn">Відкликано (Withdrawn)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="create-app-date" className="form-label">
                        Дата та час подачі (необов’язково)
                      </label>
                      <input
                        id="create-app-date"
                        type="datetime-local"
                        className="form-input"
                        value={createAppDateLocal}
                        onChange={(e) => setCreateAppDateLocal(e.target.value)}
                        disabled={isCreatingApp}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="create-app-notes" className="form-label">
                      Замітки / Нотатки
                    </label>
                    <textarea
                      id="create-app-notes"
                      className="form-input form-textarea"
                      value={createAppNotes}
                      onChange={(e) => setCreateAppNotes(e.target.value)}
                      placeholder="Введіть замітки (контакти рекрутера, супровідний лист, нотатки)..."
                      rows={3}
                      disabled={isCreatingApp}
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={isCreatingApp}
                    style={{ width: 'auto' }}
                  >
                    {isCreatingApp ? 'Створення відгуку...' : 'Створити відгук'}
                  </button>
                </form>
              </div>
            ) : isAppLoading ? (
              <LoadingState message="Завантаження інформації про відгук..." />
            ) : appError ? (
              <ErrorState
                title="Помилка завантаження відгуку"
                message={appError}
                retryLabel="Спробувати знову"
                onRetry={() => job.application?.id && fetchFullApplication(job.application.id)}
              />
            ) : isEditingApp && application ? (
              <div className="app-card app-edit-card">
                <h4 className="app-card-title">Редагування відгуку</h4>

                {editAppError && (
                  <div className="form-error-alert" role="alert">
                    {editAppError}
                  </div>
                )}

                <form onSubmit={handleUpdateAppSubmit} noValidate className="app-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="edit-app-status" className="form-label">
                        Статус відгуку
                      </label>
                      <select
                        id="edit-app-status"
                        className="form-input"
                        value={editAppStatus}
                        onChange={(e) => setEditAppStatus(e.target.value as ApplicationStatus)}
                        disabled={isUpdatingApp}
                      >
                        <option value="applied">Подано (Applied)</option>
                        <option value="interview">Співбесіда (Interview)</option>
                        <option value="offer">Офер (Offer)</option>
                        <option value="rejected">Відмова (Rejected)</option>
                        <option value="withdrawn">Відкликано (Withdrawn)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label htmlFor="edit-app-date" className="form-label">
                        Дата та час подачі
                      </label>
                      <input
                        id="edit-app-date"
                        type="datetime-local"
                        className="form-input"
                        value={editAppDateLocal}
                        onChange={(e) => {
                          setEditAppDateLocal(e.target.value);
                          setIsEditDateTouched(true);
                        }}
                        disabled={isUpdatingApp}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="edit-app-notes" className="form-label">
                      Замітки
                    </label>
                    <textarea
                      id="edit-app-notes"
                      className="form-input form-textarea"
                      value={editAppNotes}
                      onChange={(e) => setEditAppNotes(e.target.value)}
                      placeholder="Введіть замітки..."
                      rows={3}
                      disabled={isUpdatingApp}
                    />
                  </div>

                  <div className="form-actions-row">
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={isUpdatingApp}
                    >
                      {isUpdatingApp ? 'Збереження...' : 'Зберегти відгук'}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setIsEditingApp(false)}
                      disabled={isUpdatingApp}
                    >
                      Скасувати
                    </button>
                  </div>
                </form>
              </div>
            ) : application ? (
              <div className="app-card app-info-card">
                <div className="app-info-header">
                  <div className="app-info-meta">
                    <span className={`job-badge ${getStatusBadgeClass(application.status)}`}>
                      {getStatusLabel(application.status)}
                    </span>
                    <span className="app-date-info">
                      Дата подачі: <strong>{formatDateTime(application.applied_at)}</strong>
                    </span>
                  </div>
                  <div className="app-info-actions">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={handleStartEditingApp}
                    >
                      Редагувати відгук
                    </button>
                    <button
                      type="button"
                      className="btn-danger-outline"
                      onClick={() => {
                        setDeleteAppError(null);
                        setShowDeleteAppModal(true);
                      }}
                    >
                      Видалити відгук
                    </button>
                  </div>
                </div>

                <div className="app-notes-box">
                  <h5 className="app-notes-title">Замітки:</h5>
                  {application.notes ? (
                    <p className="app-notes-text">{application.notes}</p>
                  ) : (
                    <p className="app-notes-empty">Замітки відсутні.</p>
                  )}
                </div>
              </div>
            ) : null}
          </section>
        </div>
      ) : null}

      {/* DELETE JOB MODAL CONFIRMATION */}
      {showDeleteJobModal && job && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-job-modal-title">
          <div className="modal-card" ref={deleteJobModalRef}>
            <h3 id="delete-job-modal-title" className="modal-title">
              Видалення вакансії
            </h3>
            <p className="modal-text">
              Ви дійсно бажаєте видалити вакансію <strong>«{job.title}»</strong> ({job.company})?
            </p>
            <p className="modal-warning-text">
              Увага: Усі пов’язані дані та відгук також будуть видалені. Цю дію неможливо скасувати.
            </p>

            {deleteJobError && (
              <div className="form-error-alert" role="alert">
                {deleteJobError}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn-danger"
                onClick={handleDeleteJobConfirm}
                disabled={isDeletingJob}
              >
                {isDeletingJob ? 'Видалення...' : 'Так, видалити вакансію'}
              </button>
              <button
                ref={deleteJobCancelBtnRef}
                type="button"
                className="btn-secondary"
                onClick={() => setShowDeleteJobModal(false)}
                disabled={isDeletingJob}
              >
                Скасувати
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE APPLICATION MODAL CONFIRMATION */}
      {showDeleteAppModal && application && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-app-modal-title">
          <div className="modal-card" ref={deleteAppModalRef}>
            <h3 id="delete-app-modal-title" className="modal-title">
              Видалення відгуку
            </h3>
            <p className="modal-text">
              Ви дійсно бажаєте видалити відгук? Вакансія повернеться у стан «Збережено».
            </p>

            {deleteAppError && (
              <div className="form-error-alert" role="alert">
                {deleteAppError}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn-danger"
                onClick={handleDeleteAppConfirm}
                disabled={isDeletingApp}
              >
                {isDeletingApp ? 'Видалення...' : 'Так, видалити відгук'}
              </button>
              <button
                ref={deleteAppCancelBtnRef}
                type="button"
                className="btn-secondary"
                onClick={() => setShowDeleteAppModal(false)}
                disabled={isDeletingApp}
              >
                Скасувати
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
};
