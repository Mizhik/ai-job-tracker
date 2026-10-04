import { ApplicationStatus } from '../api/types';

export const STATUS_LABELS: Record<ApplicationStatus | 'saved', string> = {
  saved: 'Збережено',
  applied: 'Подано',
  interview: 'Співбесіда',
  offer: 'Офер',
  rejected: 'Відмова',
  withdrawn: 'Відкликано',
};

export function getStatusLabel(status?: ApplicationStatus | 'saved' | null): string {
  if (!status) return STATUS_LABELS.saved;
  return STATUS_LABELS[status] || status;
}

export function getStatusBadgeClass(status?: ApplicationStatus | 'saved' | null): string {
  if (!status || status === 'saved') return 'status-badge-saved';
  switch (status) {
    case 'applied':
      return 'status-badge-applied';
    case 'interview':
      return 'status-badge-interview';
    case 'offer':
      return 'status-badge-offer';
    case 'rejected':
      return 'status-badge-rejected';
    case 'withdrawn':
      return 'status-badge-withdrawn';
    default:
      return 'status-badge-saved';
  }
}

export function formatSalary(
  salaryMin?: number | null,
  salaryMax?: number | null,
  currency?: string | null,
  salaryPeriod?: string | null
): string | null {
  if (salaryMin == null && salaryMax == null) {
    return null;
  }

  const curr = currency ? ` ${currency}` : '';
  const periodMap: Record<string, string> = {
    month: '/ міс.',
    year: '/ рік',
    hour: '/ год.',
    day: '/ день',
  };
  const periodStr = salaryPeriod ? ` ${periodMap[salaryPeriod.toLowerCase()] || salaryPeriod}` : '';

  if (salaryMin != null && salaryMax != null) {
    if (salaryMin === salaryMax) {
      return `${salaryMin.toLocaleString('uk-UA')}${curr}${periodStr}`;
    }
    return `${salaryMin.toLocaleString('uk-UA')} – ${salaryMax.toLocaleString('uk-UA')}${curr}${periodStr}`;
  }

  if (salaryMin != null) {
    return `від ${salaryMin.toLocaleString('uk-UA')}${curr}${periodStr}`;
  }

  if (salaryMax != null) {
    return `до ${salaryMax.toLocaleString('uk-UA')}${curr}${periodStr}`;
  }

  return null;
}

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString;
    }
    return date.toLocaleDateString('uk-UA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString;
    }
    return date.toLocaleString('uk-UA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function isoToDateTimeLocal(dateString?: string | null): string {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    const pad = (n: number) => n.toString().padStart(2, '0');
    const year = date.getFullYear();
    const month = pad(date.getMonth() + 1);
    const day = pad(date.getDate());
    const hours = pad(date.getHours());
    const minutes = pad(date.getMinutes());
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  } catch {
    return '';
  }
}

export function localToIsoWithTimezone(localDateTimeString: string): string {
  if (!localDateTimeString) return '';
  const date = new Date(localDateTimeString);
  if (isNaN(date.getTime())) return '';
  return date.toISOString();
}
