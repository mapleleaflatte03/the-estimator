export const ROLE_COLORS: Record<string, string> = {
  Backend: 'bg-indigo-600',
  Frontend: 'bg-cyan-500',
  QA: 'bg-emerald-500',
  DevOps: 'bg-purple-500',
};

/** PERT mean of a three-point estimate, rounded to whole hours. */
export const typicalHours = (o: number, m: number, p: number) => Math.round((o + 4 * m + p) / 6);

export const card = 'rounded-2xl bg-white dark:bg-[#121829] border border-slate-200 dark:border-slate-800 shadow-sm';

export const HOURS_PER_PERSON_WEEK = 32;
