/** Semantic palette used across screens: one meaning per colour. */
export const TONE = {
  primary: { bar: 'bg-indigo-600 dark:bg-indigo-400', text: 'text-indigo-700 dark:text-indigo-300', soft: 'bg-indigo-50 dark:bg-indigo-950/50' },
  attention: { bar: 'bg-amber-500', text: 'text-amber-800 dark:text-amber-300', soft: 'bg-amber-50 dark:bg-amber-950/40' },
  ai: { bar: 'bg-violet-500', text: 'text-violet-700 dark:text-violet-300', soft: 'bg-violet-50 dark:bg-violet-950/40' },
  good: { bar: 'bg-emerald-500', text: 'text-emerald-700 dark:text-emerald-400', soft: 'bg-emerald-50 dark:bg-emerald-950/40' },
  risk: { bar: 'bg-rose-500', text: 'text-rose-700 dark:text-rose-400', soft: 'bg-rose-50 dark:bg-rose-950/40' },
  muted: { bar: 'bg-slate-400 dark:bg-slate-500', text: 'text-slate-600 dark:text-slate-400', soft: 'bg-slate-50 dark:bg-slate-900' },
} as const;
export type Tone = keyof typeof TONE;
