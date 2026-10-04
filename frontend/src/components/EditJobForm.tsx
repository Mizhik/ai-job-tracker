import React, { useState } from 'react';
import { updateJob } from '../api/jobs';
import { JobResponse, UpdateJobPayload } from '../api/types';
import { validateAndBuildJobPayload } from '../utils/validation';

interface EditJobFormProps {
  job: JobResponse;
  onSuccess: (updatedJob: JobResponse) => void;
  onCancel: () => void;
}

export const EditJobForm: React.FC<EditJobFormProps> = ({ job, onSuccess, onCancel }) => {
  const [title, setTitle] = useState(job.title || '');
  const [company, setCompany] = useState(job.company || '');
  const [location, setLocation] = useState(job.location || '');
  const [source, setSource] = useState(job.source || '');
  const [sourceUrl, setSourceUrl] = useState(job.source_url || '');
  const [salaryMin, setSalaryMin] = useState(job.salary_min != null ? job.salary_min.toString() : '');
  const [salaryMax, setSalaryMax] = useState(job.salary_max != null ? job.salary_max.toString() : '');
  const [currency, setCurrency] = useState(job.currency || 'USD');
  const [salaryPeriod, setSalaryPeriod] = useState<string>(job.salary_period || 'month');
  const [technologies, setTechnologies] = useState(job.technologies ? job.technologies.join(', ') : '');
  const [description, setDescription] = useState(job.description || '');

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const { payload, error: valError } = validateAndBuildJobPayload({
      title,
      company,
      location,
      source,
      sourceUrl,
      salaryMin,
      salaryMax,
      currency,
      salaryPeriod,
      technologies,
      description,
    });

    if (valError || !payload) {
      setError(valError || 'Перевірте правильність заповнення форми');
      return;
    }

    // Build diff patch to avoid empty PATCH or redundant fields
    const patchPayload: UpdateJobPayload = {};
    if (payload.title !== job.title) patchPayload.title = payload.title;
    if (payload.company !== job.company) patchPayload.company = payload.company;
    if (payload.description !== (job.description || null)) patchPayload.description = payload.description;
    if (payload.location !== (job.location || null)) patchPayload.location = payload.location;
    if (payload.salary_min !== (job.salary_min ?? null)) patchPayload.salary_min = payload.salary_min;
    if (payload.salary_max !== (job.salary_max ?? null)) patchPayload.salary_max = payload.salary_max;
    if (payload.currency !== (job.currency || null)) patchPayload.currency = payload.currency;
    if (payload.salary_period !== (job.salary_period || null)) patchPayload.salary_period = payload.salary_period;
    if (payload.source_url !== (job.source_url || null)) patchPayload.source_url = payload.source_url;
    if (payload.source !== (job.source || null)) patchPayload.source = payload.source;

    const existingTechs = job.technologies ? job.technologies.join(',') : '';
    const newTechs = payload.technologies ? payload.technologies.join(',') : '';
    if (existingTechs !== newTechs) {
      patchPayload.technologies = payload.technologies;
    }

    if (Object.keys(patchPayload).length === 0) {
      // Nothing changed, return current job without making a network request
      onSuccess(job);
      return;
    }

    setIsSubmitting(true);

    try {
      const updatedJob = await updateJob(job.id, patchPayload);
      onSuccess(updatedJob);
    } catch (err: any) {
      setError(err?.message || 'Не вдалося оновити вакансію. Перевірте дані та спробуйте знову.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-card create-job-card" aria-label="Редагування вакансії">
      <h2 className="form-title">Редагувати вакансію</h2>
      <p className="form-description">
        Внесіть необхідні зміни та збережіть нову інформацію.
      </p>

      {error && (
        <div className="form-error-alert" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="form-group">
          <label htmlFor="edit-job-title" className="form-label">
            Назва вакансії <span className="required-star">*</span>
          </label>
          <input
            id="edit-job-title"
            type="text"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isSubmitting}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="edit-job-company" className="form-label">
            Компанія <span className="required-star">*</span>
          </label>
          <input
            id="edit-job-company"
            type="text"
            className="form-input"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            disabled={isSubmitting}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="edit-job-location" className="form-label">
              Локація
            </label>
            <input
              id="edit-job-location"
              type="text"
              className="form-input"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="edit-job-source" className="form-label">
              Джерело
            </label>
            <input
              id="edit-job-source"
              type="text"
              className="form-input"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="edit-job-source-url" className="form-label">
            Посилання на вакансію
          </label>
          <input
            id="edit-job-source-url"
            type="url"
            className="form-input"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder="https://example.com/jobs/123"
            disabled={isSubmitting}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="edit-job-salary-min" className="form-label">
              Мін. зарплата
            </label>
            <input
              id="edit-job-salary-min"
              type="number"
              min="0"
              step="1"
              className="form-input"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="edit-job-salary-max" className="form-label">
              Макс. зарплата
            </label>
            <input
              id="edit-job-salary-max"
              type="number"
              min="0"
              step="1"
              className="form-input"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="edit-job-currency" className="form-label">
              Валюта
            </label>
            <input
              id="edit-job-currency"
              type="text"
              className="form-input"
              value={currency}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
              placeholder="USD, EUR, UAH"
              maxLength={3}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="edit-job-salary-period" className="form-label">
              Період оплати
            </label>
            <select
              id="edit-job-salary-period"
              className="form-input"
              value={salaryPeriod}
              onChange={(e) => setSalaryPeriod(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="month">За місяць</option>
              <option value="hour">За годину</option>
              <option value="year">За рік</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="edit-job-technologies" className="form-label">
            Технології (через кому)
          </label>
          <input
            id="edit-job-technologies"
            type="text"
            className="form-input"
            value={technologies}
            onChange={(e) => setTechnologies(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edit-job-description" className="form-label">
            Опис вакансії
          </label>
          <textarea
            id="edit-job-description"
            className="form-input form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-actions-row">
          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Збереження...' : 'Зберегти зміни'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );
};
