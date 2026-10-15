import React, { useState } from 'react';
import {
  HelpCircle,
  History,
  Check,
  X,
  Sparkles,
  ArrowRight,
  GitBranch,
} from 'lucide-react';
import type { EstimateVersion } from '../types';

interface ClarificationScreenProps {
  version: EstimateVersion;
  versionsHistory: EstimateVersion[];
  onAnswerQuestion: (questionId: string, answer: boolean, notes?: string) => Promise<void>;
  isLoading: boolean;
}

export const ClarificationScreen: React.FC<ClarificationScreenProps> = ({
  version,
  versionsHistory,
  onAnswerQuestion,
  isLoading,
}) => {
  const [answeringId, setAnsweringId] = useState<string | null>(null);

  const handleAnswer = async (qId: string, ans: boolean) => {
    setAnsweringId(qId);
    try {
      await onAnswerQuestion(qId, ans);
    } finally {
      setAnsweringId(null);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-950/80 border border-cyan-200 dark:border-cyan-800 text-cyan-700 dark:text-cyan-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
          <span>ACTIVE CLARIFICATION & EXPECTED VALUE OF INFORMATION (EVI)</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          What-if & Làm rõ Giả định để Giảm Sai số
        </h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">
          Không hỏi tràn lan 20 câu theo checklist cố định. Hệ thống tính toán câu hỏi nào làm thay đổi dự toán nhiều nhất (Độ nhạy Sensitivity Spread) để ưu tiên hỏi khách hàng trước.
        </p>
      </div>

      {/* Sensitivity Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
            <span>Câu hỏi có tác động lớn nhất ({version.clarifications.length})</span>
          </h2>
          <span className="text-xs text-slate-500">Xếp hạng theo biên độ lệch giờ công</span>
        </div>

        {version.clarifications.length === 0 ? (
          <div className="modern-card p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center text-slate-500 text-sm">
            Toàn bộ các giả định trọng yếu đã được xác nhận ở phiên bản này.
          </div>
        ) : (
          version.clarifications.map((q) => {
            const spread = Math.abs(q.hours_if_true - q.hours_if_false);
            const isAnswering = answeringId === q.question_id;

            return (
              <div
                key={q.question_id}
                className="modern-card p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-5 shadow-sm"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-cyan-400 border border-indigo-200 dark:border-indigo-800 font-bold">
                      {q.question_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 font-mono">
                      Mã giả định: {q.assumption_id}
                    </span>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-950 text-cyan-800 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800 text-xs font-mono font-extrabold">
                    Biên độ ảnh hưởng: &plusmn;{spread}h
                  </div>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
                    {q.question_text}
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1.5 leading-relaxed">
                    {q.context_reason}
                  </p>
                </div>

                {/* What-if comparison bars */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <X className="w-3.5 h-3.5 text-rose-500" />
                      <span>Kịch bản 1: KHÔNG triển khai</span>
                    </div>
                    <div className="text-2xl font-extrabold font-mono text-slate-800 dark:text-slate-200">
                      {q.hours_if_false}h
                    </div>
                    <div className="text-[11px] text-slate-500">Giảm bớt thời gian kết nối và rủi ro tích hợp</div>
                  </div>

                  <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 space-y-1">
                    <div className="text-xs font-bold text-indigo-700 dark:text-cyan-400 flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Kịch bản 2: CÓ triển khai</span>
                    </div>
                    <div className="text-2xl font-extrabold font-mono text-indigo-950 dark:text-white">
                      {q.hours_if_true}h
                    </div>
                    <div className="text-[11px] text-indigo-700 dark:text-indigo-300">Bao gồm adapter, hàng đợi thử lại và kiểm thử regression</div>
                  </div>
                </div>

                {/* Customer Response Action Buttons */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-xs font-medium text-slate-500">Xác nhận từ khách hàng:</span>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      disabled={isLoading || isAnswering}
                      onClick={() => handleAnswer(q.question_id, false)}
                      className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5 text-rose-500" />
                      <span>Không cần</span>
                    </button>
                    <button
                      type="button"
                      disabled={isLoading || isAnswering}
                      onClick={() => handleAnswer(q.question_id, true)}
                      className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-slate-950 font-bold text-xs transition-colors flex items-center gap-1.5 shadow-md shadow-indigo-600/20 dark:shadow-cyan-500/20 cursor-pointer disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Có yêu cầu &rarr;</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Version Progression Tree */}
      <div className="modern-card p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
            <span>Cây Phả hệ Phiên bản Dự toán (Estimate Version Lineage)</span>
          </h2>
          <span className="text-xs font-mono text-slate-500">{versionsHistory.length} phiên bản</span>
        </div>

        <p className="text-xs text-slate-600 dark:text-slate-400">
          Mỗi lần làm rõ sẽ sinh phiên bản con mới (v2, v3...), liên kết với phiên bản cha (`parent_version_id`) và không bao giờ ghi đè dự toán ban đầu để bảo đảm tính kiểm toán độc lập.
        </p>

        <div className="space-y-3 pt-2">
          {versionsHistory.map((v, idx) => {
            const isCurrent = v.version_id === version.version_id;
            return (
              <div
                key={v.version_id}
                className={`p-4 rounded-xl border flex items-center justify-between gap-4 transition-all ${
                  isCurrent
                    ? 'border-indigo-500 dark:border-cyan-400 bg-indigo-50/40 dark:bg-cyan-950/20 shadow-sm ring-1 ring-indigo-500/20'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl font-mono font-bold text-xs flex items-center justify-center ${
                    isCurrent ? 'bg-indigo-600 text-white' : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                  }`}>
                    v{idx + 1}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>{v.version_id}</span>
                      {v.parent_version_id && (
                        <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono font-normal flex items-center gap-1">
                          <GitBranch className="w-3 h-3 text-indigo-500" />
                          kế thừa từ {v.parent_version_id}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      {v.requirements.length} Yêu cầu &bull; {v.wbs.length} Hạng mục công việc WBS
                    </div>
                  </div>
                </div>

                <div className="text-right font-mono">
                  <div className="text-[11px] uppercase font-bold text-slate-500">P50 Dự toán</div>
                  <div className="text-lg font-extrabold text-indigo-700 dark:text-cyan-300">
                    {v.forecast.p50_hours}h
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
