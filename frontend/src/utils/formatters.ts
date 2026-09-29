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
