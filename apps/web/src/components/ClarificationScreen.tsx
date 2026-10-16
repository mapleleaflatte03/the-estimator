import React, { useState } from 'react';
import { Check, Sparkles, X } from 'lucide-react';
import type { EstimateVersion, ClarificationQuestion } from '../types';
import { card, hours } from '../ui';

interface ClarificationScreenProps {
  version: EstimateVersion;
  versionsHistory: EstimateVersion[];
  onAnswerQuestion: (questionId: string, answer: boolean) => Promise<void>;
  isLoading: boolean;
}

export const ClarificationScreen: React.FC<ClarificationScreenProps> = ({
  version,
  versionsHistory,
  onAnswerQuestion,
  isLoading,
}) => {
  const [answeringId, setAnsweringId] = useState<string | null>(null);

  const answer = async (q: ClarificationQuestion, value: boolean) => {
    setAnsweringId(q.question_id);
    try {
      await onAnswerQuestion(q.question_id, value);
    } finally {
      setAnsweringId(null);
    }
  };

  const impact = (q: ClarificationQuestion) => {
    const h = Math.round(q.sensitivity_spread_hours);
    const included = q.answer ?? q.current_assumption;
    return included ? `Chọn “Không” sẽ bớt khoảng ${hours(h)}` : `Chọn “Có” sẽ thêm khoảng ${hours(h)}`;
  };

  const maxSpread = Math.max(...version.clarifications.map((q) => q.sensitivity_spread_hours), 1);
  const ordered = [...version.clarifications].sort(
    (a, b) => Number(a.answer != null) - Number(b.answer != null) || b.sensitivity_spread_hours - a.sensitivity_spread_hours,
  );
  const openCount = ordered.filter((q) => q.answer == null).length;
  const atStake = Math.round(ordered.filter((q) => q.answer == null).reduce((s, q) => s + q.sensitivity_spread_hours, 0));

  const choiceClass = (selected: boolean) =>
    `px-5 py-2 rounded-xl font-bold text-sm flex items-center gap-1.5 border cursor-pointer disabled:opacity-50 ${
      selected
        ? 'bg-indigo-600 border-indigo-600 text-white'
        : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 hover:border-indigo-400'
    }`;

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Câu hỏi cần làm rõ</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          {openCount > 0 ? (
            <>
              Còn <strong className="text-amber-800 dark:text-amber-300">{openCount} câu</strong>, ảnh hưởng tới khoảng{' '}
              <strong className="text-amber-800 dark:text-amber-300">{hours(atStake)}</strong>. Câu quan trọng nhất ở trên cùng; mỗi
              câu trả lời tính lại dự toán ngay.
            </>
          ) : (
            'Đã trả lời hết. Bạn vẫn có thể đổi câu trả lời.'
          )}
        </p>
      </div>

      {version.clarifications.length === 0 ? (
        <div className={`${card} p-8 text-center text-slate-600 dark:text-slate-400`}>Không có câu hỏi nào. Mô tả đã đủ rõ.</div>
      ) : (
        ordered.map((q, idx) => {
          const answered = q.answer != null;
          const top = idx === 0 && !answered;
          return (
          <section
            key={q.question_id}
            className={`${card} space-y-3 ${answered ? 'p-4 opacity-80 border-emerald-200 dark:border-emerald-900' : 'p-6'} ${top ? 'border-2 border-amber-300 dark:border-amber-700' : ''}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              {top && <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-500 text-white">Ảnh hưởng lớn nhất</span>}
              {answered && (
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200">
                  Đã trả lời: {q.answer ? 'Có' : 'Không'}
                </span>
              )}
            </div>
            {(q.question_id.endsWith('-AI') || q.context_reason.includes('AI')) && (
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-violet-50 dark:bg-violet-950/50 text-violet-700 dark:text-violet-300">
                <Sparkles className="w-3.5 h-3.5" /> Gợi ý từ AI
              </span>
            )}
            <h2 className={`${answered ? 'text-base' : 'text-lg'} font-bold leading-snug`}>{q.question_text}</h2>
            <div className="flex items-center gap-2" aria-hidden="true">
              <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${answered ? 'bg-emerald-500' : 'bg-amber-500'}`}
                  style={{ width: `${Math.max(3, (q.sensitivity_spread_hours / maxSpread) * 100)}%` }}
                />
              </div>
              <span className="text-xs font-bold tabular-nums text-slate-700 dark:text-slate-300 w-16 text-right">{hours(q.sensitivity_spread_hours)}</span>
            </div>
            {q.evidence[0] && !answered && (
              <p className="text-sm text-slate-700 dark:text-slate-300 border-l-4 border-amber-400 pl-3 italic">
                “{q.evidence[0].quote}”
              </p>
            )}
            {!answered && <p className="text-sm text-slate-600 dark:text-slate-400">{q.context_reason}</p>}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
              <span className="text-sm font-semibold text-amber-800 dark:text-amber-300">{impact(q)}</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={isLoading || answeringId !== null}
                  aria-pressed={q.answer === true}
                  onClick={() => answer(q, true)}
                  className={choiceClass(q.answer === true)}
                >
                  <Check className="w-4 h-4" /> Có
                </button>
                <button
                  type="button"
                  disabled={isLoading || answeringId !== null}
                  aria-pressed={q.answer === false}
                  onClick={() => answer(q, false)}
                  className={choiceClass(q.answer === false)}
                >
                  <X className="w-4 h-4" /> Không
                </button>
              </div>
            </div>
          </section>
          );
        })
      )}

      {versionsHistory.length > 1 && (
        <section className={`${card} p-5`}>
          <h2 className="font-bold mb-2">Các lần tính</h2>
          <ol className="space-y-1 text-sm">
            {versionsHistory.map((v, i) => (
              <li key={v.version_id} className={`flex justify-between ${v.version_id === version.version_id ? 'font-bold' : 'text-slate-700 dark:text-slate-300'}`}>
                <span>
                  Lần {i + 1} · {new Date(v.created_at).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' })}
                </span>
                <span>{hours(v.forecast.p50_hours)}</span>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  );
};
