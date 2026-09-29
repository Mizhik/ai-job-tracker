import React, { useState } from 'react';
import { createJob } from '../api/jobs';
import { JobResponse } from '../api/types';

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

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Title validation
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError('Вкажіть назву вакансії');
      return;
    }

    // Company validation
    const trimmedCompany = company.trim();
    if (!trimmedCompany) {
      setError('Вкажіть назву компанії');
      return;
    }

    // Salary validation
    let minNum: number | null = null;
    let maxNum: number | null = null;

    if (salaryMin.trim() !== '') {
      const num = Number(salaryMin);
      if (!Number.isFinite(num) || !Number.isInteger(num)) {
        setError('Мінімальна зарплата повинна бути цілим числом');
        return;
      }
      if (num < 0) {
        setError('Мінімальна зарплата не може бути від’ємною');
        return;
      }
      minNum = num;
    }

    if (salaryMax.trim() !== '') {
      const num = Number(salaryMax);
      if (!Number.isFinite(num) || !Number.isInteger(num)) {
        setError('Максимальна зарплата повинна бути цілим числом');
        return;
      }
      if (num < 0) {
        setError('Максимальна зарплата не може бути від’ємною');
        return;
      }
      maxNum = num;
    }

    if (minNum !== null && maxNum !== null && minNum > maxNum) {
      setError('Мінімальна зарплата не може бути більшою за максимальну');
      return;
    }

    const hasNumericSalary = minNum !== null || maxNum !== null;
    const trimmedCurrency = currency.trim().toUpperCase();

    if (hasNumericSalary) {
      if (!trimmedCurrency || !salaryPeriod) {
        setError('При вказівці зарплати необхідно вказати валюту та період оплати');
        return;
      }
    }

    if (trimmedCurrency !== '') {
      if (!/^[A-Z]{3}$/.test(trimmedCurrency)) {
        setError('Код валюти повинен складатися з 3 латинських літер (наприклад, USD, EUR, UAH)');
        return;
      }
    }

    // Source URL validation
    const trimmedSourceUrl = sourceUrl.trim();
    if (trimmedSourceUrl !== '') {
      try {
        const parsed = new URL(trimmedSourceUrl);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
          setError('Посилання на вакансію повинно починатися з http:// або https://');
          return;
        }
      } catch {
        setError('Вкажіть коректне посилання на вакансію (http:// або https://)');
        return;
      }
    }

    // Parse technologies
    const parsedTechs = technologies
      .split(/[\n,]+/)
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = {
      title: trimmedTitle,
      company: trimmedCompany,
      description: description.trim() || null,
      location: location.trim() || null,
      salary_min: minNum,
      salary_max: maxNum,
      currency: hasNumericSalary ? (trimmedCurrency || null) : null,
      salary_period: hasNumericSalary ? (salaryPeriod || null) : null,
      technologies: parsedTechs.length > 0 ? parsedTechs : null,
      source_url: trimmedSourceUrl || null,
      source: source.trim() || null,
    };

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
        Заповніть інформацію про вакансію для збереження в трекері.
      </p>

      {error && (
        <div className="form-error-alert" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
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
            disabled={isSubmitting}
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
            disabled={isSubmitting}
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
              disabled={isSubmitting}
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
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="job-source-url" className="form-label">
            Посилання на вакансію
          </label>
          <input
            id="job-source-url"
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
              disabled={isSubmitting}
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
              disabled={isSubmitting}
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
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
              placeholder="USD, EUR, UAH"
              maxLength={3}
              disabled={isSubmitting}
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
            disabled={isSubmitting}
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
            disabled={isSubmitting}
          />
        </div>

        <div className="form-actions-row">
          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Збереження...' : 'Зберегти вакансію'}
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
