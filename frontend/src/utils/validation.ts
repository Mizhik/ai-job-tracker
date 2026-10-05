export interface JobFormInputs {
  title: string;
  company: string;
  location: string;
  source: string;
  sourceUrl: string;
  salaryMin: string;
  salaryMax: string;
  currency: string;
  salaryPeriod: string;
  technologies: string;
  description: string;
}

export interface ValidatedJobPayload {
  title: string;
  company: string;
  description: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  salary_period: string | null;
  technologies: string[] | null;
  source_url: string | null;
  source: string | null;
}

export function validateAndBuildJobPayload(inputs: JobFormInputs): {
  payload?: ValidatedJobPayload;
  error?: string;
} {
  const trimmedTitle = inputs.title.trim();
  if (!trimmedTitle) {
    return { error: 'Вкажіть назву вакансії' };
  }

  const trimmedCompany = inputs.company.trim();
  if (!trimmedCompany) {
    return { error: 'Вкажіть назву компанії' };
  }

  let minNum: number | null = null;
  let maxNum: number | null = null;

  if (inputs.salaryMin.trim() !== '') {
    const num = Number(inputs.salaryMin);
    if (!Number.isFinite(num) || !Number.isInteger(num)) {
      return { error: 'Мінімальна зарплата повинна бути цілим числом' };
    }
    if (num < 0) {
      return { error: 'Мінімальна зарплата не може бути від’ємною' };
    }
    minNum = num;
  }

  if (inputs.salaryMax.trim() !== '') {
    const num = Number(inputs.salaryMax);
    if (!Number.isFinite(num) || !Number.isInteger(num)) {
      return { error: 'Максимальна зарплата повинна бути цілим числом' };
    }
    if (num < 0) {
      return { error: 'Максимальна зарплата не може бути від’ємною' };
    }
    maxNum = num;
  }

  if (minNum !== null && maxNum !== null && minNum > maxNum) {
    return { error: 'Мінімальна зарплата не може бути більшою за максимальну' };
  }

  const hasNumericSalary = minNum !== null || maxNum !== null;
  const trimmedCurrency = inputs.currency.trim().toUpperCase();

  if (hasNumericSalary) {
    if (!trimmedCurrency || !inputs.salaryPeriod) {
      return { error: 'При вказівці зарплати необхідно вказати валюту та період оплати' };
    }
  }

  if (trimmedCurrency !== '') {
    if (!/^[A-Z]{3}$/.test(trimmedCurrency)) {
      return { error: 'Код валюти повинен складатися з 3 латинських літер (наприклад, USD, EUR, UAH)' };
    }
  }

  const trimmedSourceUrl = inputs.sourceUrl.trim();
  if (trimmedSourceUrl !== '') {
    try {
      const parsed = new URL(trimmedSourceUrl);
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        return { error: 'Посилання на вакансію повинно починатися з http:// або https://' };
      }
    } catch {
      return { error: 'Вкажіть коректне посилання на вакансію (http:// або https://)' };
    }
  }

  const parsedTechs = inputs.technologies
    .split(/[\n,]+/)
    .map((t) => t.trim())
    .filter(Boolean);

  return {
    payload: {
      title: trimmedTitle,
      company: trimmedCompany,
      description: inputs.description.trim() || null,
      location: inputs.location.trim() || null,
      salary_min: minNum,
      salary_max: maxNum,
      currency: hasNumericSalary ? (trimmedCurrency || null) : null,
      salary_period: hasNumericSalary ? (inputs.salaryPeriod || null) : null,
      technologies: parsedTechs.length > 0 ? parsedTechs : null,
      source_url: trimmedSourceUrl || null,
      source: inputs.source.trim() || null,
    },
  };
}
