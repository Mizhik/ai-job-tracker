import React, { useRef, useState } from 'react';
import { createJob, importJobPreview } from '../api/jobs';
import { JobResponse } from '../api/types';
import { validateAndBuildJobPayload } from '../utils/validation';

interface CreateJobFormProps {
  onSuccess: (job: JobResponse) => void;
  onCancel: () => void;
}

export const CreateJobForm: React.FC<CreateJobFormProps> = ({ onSuccess, onCancel }) => {
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [source, setSource] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [salaryMin, setSalaryMin] = useState('');
  const [salaryMax, setSalaryMax] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [salaryPeriod, setSalaryPeriod] = useState<string>('month');
  const [technologies, setTechnologies] = useState('');
  const [description, setDescription] = useState('');

  // Track if user explicitly modified defaults for currency or salary period
  const isCurrencyTouchedRef = useRef(false);
  const isSalaryPeriodTouchedRef = useRef(false);

  const [error, setError] = useState<string | null>(null);
  const [infoNotice, setInfoNotice] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const handleImportPreview = async () => {
    setError(null);
    setInfoNotice(null);

    const urlToFetch = sourceUrl.trim();
    if (!urlToFetch) {
      setError('Вкажіть посилання на вакансію для автоматичного заповнення');
      return;
    }

    try {
      const parsed = new URL(urlToFetch);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setError('Посилання на вакансію повинно починатися з http:// або https://');
        return;
      }
    } catch {
      setError('Вкажіть коректне посилання на вакансію (http:// або https://)');
      return;
    }

    if (isPreviewLoading || isSubmitting) return;

    setIsPreviewLoading(true);

    try {
      const result = await importJobPreview(urlToFetch);

      if (result.status === 'unavailable') {
        let msg = 'Не вдалося автоматично прочитати вакансію з посилання. Заповніть форму вручну.';
        if (result.reason_code === 'access_denied') {
          msg = 'Сайт обмежив автоматичний доступ. Будь ласка, заповніть форму вручну.';
        } else if (result.reason_code === 'provider_unavailable') {
          msg = 'Сервіс автоматичного аналізу тимчасово недоступний. Заповніть форму вручну.';
        } else if (result.message) {
          msg = `Автоматичне читання недоступне: ${result.message}. Заповніть форму вручну.`;
        }
        setError(msg);
      } else {
        const fields = result.fields;

        // Populate only empty/untouched fields. Pre-existing user values are strictly preserved.
        if (fields.title) {
          setTitle((prev) => (prev.trim() === '' ? fields.title! : prev));
        }
        if (fields.company) {
          setCompany((prev) => (prev.trim() === '' ? fields.company! : prev));
        }
        if (fields.location) {
          setLocation((prev) => (prev.trim() === '' ? fields.location! : prev));
        }
        if (fields.source) {
          setSource((prev) => (prev.trim() === '' ? fields.source! : prev));
        }
        if (fields.salary_min !== null && fields.salary_min !== undefined) {
          setSalaryMin((prev) => (prev.trim() === '' ? fields.salary_min!.toString() : prev));
        }
        if (fields.salary_max !== null && fields.salary_max !== undefined) {
          setSalaryMax((prev) => (prev.trim() === '' ? fields.salary_max!.toString() : prev));
        }
        if (fields.currency) {
          setCurrency((prev) => (!isCurrencyTouchedRef.current ? fields.currency! : prev));
        }
        if (fields.salary_period) {
          setSalaryPeriod((prev) => (!isSalaryPeriodTouchedRef.current ? fields.salary_period! : prev));
        }
        if (fields.technologies && fields.technologies.length > 0) {
          setTechnologies((prev) =>
            prev.trim() === '' ? fields.technologies!.join(', ') : prev
          );
        }
        if (fields.description) {
          setDescription((prev) => (prev.trim() === '' ? fields.description! : prev));
        }

        if (result.status === 'complete') {
          setInfoNotice('Дані вакансії автоматично витягнуто з посилання. Перевірте їх перед збереженням.');
        } else {
          setInfoNotice('Частину даних заповнено з посилання. Будь ласка, перевірте та доповніть обов’язкові поля.');
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Помилка під час зчитування вакансії за посиланням.');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setInfoNotice(null);

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

    setIsSubmitting(true);

    try {
      const createdJob = await createJob(payload);
      onSuccess(createdJob);
    } catch (err: any) {
      setError(err?.message || 'Не вдалося зберегти вакансію. Перевірте дані та спробуйте знову.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="form-card create-job-card">
      <h2 className="form-title">Додати нову вакансію</h2>
      <p className="form-description">
        Заповніть інформацію про вакансію вручну або вставте посилання для автоматичного заповнення.
      </p>

      {infoNotice && (
        <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', borderRadius: '4px', backgroundColor: '#eef6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' }}>
          {infoNotice}
        </div>
      )}

      {error && (
        <div className="form-error-alert" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="form-group">
          <label htmlFor="job-source-url" className="form-label">
            Посилання на вакансію
          </label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              id="job-source-url"
              type="url"
              className="form-input"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://example.com/jobs/123"
              disabled={isSubmitting || isPreviewLoading}
              style={{ flex: 1 }}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={handleImportPreview}
              disabled={isSubmitting || isPreviewLoading || !sourceUrl.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {isPreviewLoading ? 'Зчитування...' : 'Заповнити з посилання'}
            </button>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="job-title" className="form-label">
            Назва вакансії <span className="required-star">*</span>
          </label>
          <input
            id="job-title"
            type="text"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="напр. Senior Python Engineer"
            disabled={isSubmitting || isPreviewLoading}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="job-company" className="form-label">
            Компанія <span className="required-star">*</span>
          </label>
          <input
            id="job-company"
            type="text"
            className="form-input"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="напр. Tech Solutions Inc."
            disabled={isSubmitting || isPreviewLoading}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="job-location" className="form-label">
              Локація
            </label>
            <input
              id="job-location"
              type="text"
              className="form-input"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="напр. Київ / Віддалено"
              disabled={isSubmitting || isPreviewLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="job-source" className="form-label">
              Джерело
            </label>
            <input
              id="job-source"
              type="text"
              className="form-input"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="напр. Djinni, DOU, LinkedIn"
              disabled={isSubmitting || isPreviewLoading}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="job-salary-min" className="form-label">
              Мін. зарплата
            </label>
            <input
              id="job-salary-min"
              type="number"
              min="0"
              step="1"
              className="form-input"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              placeholder="3000"
              disabled={isSubmitting || isPreviewLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="job-salary-max" className="form-label">
              Макс. зарплата
            </label>
            <input
              id="job-salary-max"
              type="number"
              min="0"
              step="1"
              className="form-input"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              placeholder="5000"
              disabled={isSubmitting || isPreviewLoading}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="job-currency" className="form-label">
              Валюта
            </label>
            <input
              id="job-currency"
              type="text"
              className="form-input"
              value={currency}
              onChange={(e) => {
                setCurrency(e.target.value.toUpperCase());
                isCurrencyTouchedRef.current = true;
              }}
              placeholder="USD, EUR, UAH"
              maxLength={3}
              disabled={isSubmitting || isPreviewLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="job-salary-period" className="form-label">
              Період оплати
            </label>
            <select
              id="job-salary-period"
              className="form-input"
              value={salaryPeriod}
              onChange={(e) => {
                setSalaryPeriod(e.target.value);
                isSalaryPeriodTouchedRef.current = true;
              }}
              disabled={isSubmitting || isPreviewLoading}
            >
              <option value="month">За місяць</option>
              <option value="hour">За годину</option>
              <option value="year">За рік</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="job-technologies" className="form-label">
            Технології (через кому)
          </label>
          <input
            id="job-technologies"
            type="text"
            className="form-input"
            value={technologies}
            onChange={(e) => setTechnologies(e.target.value)}
            placeholder="Python, FastAPI, React, PostgreSQL"
            disabled={isSubmitting || isPreviewLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="job-description" className="form-label">
            Опис вакансії
          </label>
          <textarea
            id="job-description"
            className="form-input form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Введіть ключові вимоги та опис вакансії..."
            rows={4}
            disabled={isSubmitting || isPreviewLoading}
          />
        </div>

        <div className="form-actions-row">
          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting || isPreviewLoading}
          >
            {isSubmitting ? 'Збереження...' : 'Зберегти вакансію'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            disabled={isSubmitting || isPreviewLoading}
          >
            Скасувати
          </button>
        </div>
      </form>
    </div>
  );
};
