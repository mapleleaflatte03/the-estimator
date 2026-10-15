import React, { useState } from 'react';
import { Check, X } from 'lucide-react';
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
        <p className="text-slate-600 dark:text-slate-400 mt-1">Mỗi câu trả lời sẽ tính lại dự toán ngay.</p>
      </div>

      {version.clarifications.length === 0 ? (
        <div className={`${card} p-8 text-center text-slate-600 dark:text-slate-400`}>Không có câu hỏi nào. Mô tả đã đủ rõ.</div>
      ) : (
        version.clarifications.map((q) => (
          <section key={q.question_id} className={`${card} p-6 space-y-3`}>
            <h2 className="text-lg font-bold leading-snug">{q.question_text}</h2>
            {q.evidence[0] && (
              <p className="text-sm text-slate-700 dark:text-slate-300 border-l-4 border-amber-400 pl-3 italic">
                “{q.evidence[0].quote}”
              </p>
            )}
            <p className="text-sm text-slate-600 dark:text-slate-400">{q.context_reason}</p>
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
        ))
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
