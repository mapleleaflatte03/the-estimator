import React, { useState } from 'react';
import {
  HelpCircle,
  History,
  Check,
  X,
  Sparkles,
  ArrowRight,
  GitBranch,
  Sliders,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Info,
} from 'lucide-react';
import type { EstimateVersion, ClarificationQuestion } from '../types';

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

  // Interactive local simulation map: questionId -> simulated answer (true | false | null)
  const [simulatedChoices, setSimulatedChoices] = useState<Record<string, boolean | null>>({});

  const handleSimulate = (qId: string, choice: boolean) => {
    setSimulatedChoices((prev) => ({
      ...prev,
      [qId]: prev[qId] === choice ? null : choice,
    }));
  };

  const handleAnswer = async (qId: string, ans: boolean) => {
    setAnsweringId(qId);
    try {
      await onAnswerQuestion(qId, ans);
    } finally {
      setAnsweringId(null);
    }
  };

  // Calculate simulated net delta on P50 hours
  const simulatedHourDelta = Object.entries(simulatedChoices).reduce((sum, [qId, choice]) => {
    if (choice === null) return sum;
    const q = version.clarifications.find((item) => item.question_id === qId);
    if (!q) return sum;
    // Current baseline is roughly halfway or true
    const currentBase = q.hours_if_true;
    const targetVal = choice ? q.hours_if_true : q.hours_if_false;
    return sum + (targetVal - currentBase);
  }, 0);

  const simulatedP50Hours = Math.max(10, version.forecast.p50_hours + simulatedHourDelta);

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 text-cyan-300 dark:bg-cyan-950/80 dark:border dark:border-cyan-800 text-[11px] font-mono font-bold">
          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
          <span>ACTIVE CLARIFICATION & EXPECTED VALUE OF INFORMATION (EVI)</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          What-if &amp; Làm rõ Giả định Trọng yếu
        </h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">
          Không hỏi tràn lan 20 câu checklist cố định. PARALLAX tính toán các câu hỏi có độ nhạy giờ công lớn nhất (Sensitivity Spread) và cho phép mô phỏng tức thời tác động ngân sách trước khi chốt cam kết.
        </p>
      </div>

      {/* Simulated Live Impact Header Bar */}
      {Object.keys(simulatedChoices).some((k) => simulatedChoices[k] !== null) && (
        <div className="p-4 rounded-2xl bg-slate-900 text-white border border-cyan-500/40 shadow-lg flex flex-col sm:flex-row items-center justify-between gap-3 animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">
              &Delta;
            </div>
            <div>
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                Mô phỏng Tác động Giờ Công (What-if Preview)
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Baseline P50: <span className="font-mono text-white font-bold">{version.forecast.p50_hours}h</span>
                {' '}&rarr; Sau mô phỏng:{' '}
                <span className="font-mono text-cyan-300 font-extrabold text-sm">{simulatedP50Hours}h</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-xl text-xs font-mono font-bold flex items-center gap-1 ${
              simulatedHourDelta <= 0
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-amber-950 text-amber-400 border border-amber-800'
            }`}>
              {simulatedHourDelta <= 0 ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
              <span>{simulatedHourDelta > 0 ? `+${simulatedHourDelta}h` : `${simulatedHourDelta}h`}</span>
            </div>

            <button
              onClick={() => setSimulatedChoices({})}
              className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
            >
              Hủy mô phỏng
            </button>
          </div>
        </div>
      )}

      {/* Sensitivity Cards List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
            <span>Câu hỏi có tác động sai số lớn nhất ({version.clarifications.length})</span>
          </h2>
          <span className="text-xs font-mono text-slate-500 font-medium">Xếp hạng theo biên độ lệch giờ công</span>
        </div>

        {version.clarifications.length === 0 ? (
          <div className="modern-card p-8 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 text-center text-slate-500 dark:text-slate-400 text-sm">
            Toàn bộ các giả định trọng yếu đã được xác nhận ở phiên bản này.
          </div>
        ) : (
          version.clarifications.map((q) => {
            const spread = Math.abs(q.hours_if_true - q.hours_if_false);
            const isAnswering = answeringId === q.question_id;
            const currentSimChoice = simulatedChoices[q.question_id];

            return (
              <div
                key={q.question_id}
                className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 space-y-5 shadow-sm"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-indigo-700 dark:text-cyan-300 border border-slate-200 dark:border-slate-700 font-bold">
                      {q.question_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 font-mono">
                      Mã giả định: {q.assumption_id}
                    </span>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-950/70 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/80 text-xs font-mono font-extrabold shadow-xs">
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

                {/* What-if comparison interactive scenario cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  {/* Option False (No) */}
                  <div
                    onClick={() => handleSimulate(q.question_id, false)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      currentSimChoice === false
                        ? 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-50/50 dark:bg-rose-950/40 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-[#0b0f1a] hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                        <X className="w-3.5 h-3.5 text-rose-500" />
                        <span>Kịch bản 1: KHÔNG triển khai</span>
                      </div>
                      {currentSimChoice === false && (
                        <span className="text-[10px] font-mono font-bold bg-rose-600 text-white px-2 py-0.5 rounded-full">
                          ĐANG MÔ PHỎNG
                        </span>
                      )}
                    </div>
                    <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white mt-1">
                      {q.hours_if_false}h
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Giảm bớt thời gian kết nối và rủi ro tích hợp
                    </div>
                  </div>

                  {/* Option True (Yes) */}
                  <div
                    onClick={() => handleSimulate(q.question_id, true)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      currentSimChoice === true
                        ? 'border-indigo-500 dark:border-cyan-400 ring-2 ring-indigo-500/20 dark:ring-cyan-500/20 bg-indigo-50/50 dark:bg-indigo-950/40 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-[#0b0f1a] hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-bold text-indigo-700 dark:text-cyan-400 flex items-center gap-1.5">
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                        <span>Kịch bản 2: CÓ triển khai</span>
                      </div>
                      {currentSimChoice === true && (
                        <span className="text-[10px] font-mono font-bold bg-indigo-600 dark:bg-cyan-400 text-white dark:text-slate-950 px-2 py-0.5 rounded-full">
                          ĐANG MÔ PHỎNG
                        </span>
                      )}
                    </div>
                    <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white mt-1">
                      {q.hours_if_true}h
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                      Bao gồm adapter, hàng đợi thử lại và kiểm thử regression
                    </div>
                  </div>
                </div>

                {/* Customer Response Action Buttons */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                    Chốt quyết định chính thức để sinh phiên bản mới:
                  </span>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      disabled={isLoading || isAnswering}
                      onClick={() => handleAnswer(q.question_id, false)}
                      className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-rose-50 dark:hover:bg-rose-950/40 hover:text-rose-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50 border border-slate-200 dark:border-slate-700"
                    >
                      <X className="w-3.5 h-3.5 text-rose-500" />
                      <span>Không cần</span>
                    </button>
                    <button
                      type="button"
                      disabled={isLoading || isAnswering}
                      onClick={() => handleAnswer(q.question_id, true)}
                      className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-cyan-300 dark:bg-cyan-400 dark:hover:bg-cyan-300 dark:text-slate-950 font-bold text-xs transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50 font-mono"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Có yêu cầu &rarr; Tạo v{versionsHistory.length + 1}</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Version Lineage Tree */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
            <span>Cây Phả hệ Phiên bản Dự toán (Version Lineage &bull; Immutability)</span>
          </h2>
          <span className="text-xs font-mono text-slate-500 dark:text-slate-400 font-semibold">{versionsHistory.length} phiên bản</span>
        </div>

        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
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
                    ? 'border-indigo-500 dark:border-cyan-400 bg-indigo-50/30 dark:bg-cyan-950/20 shadow-xs ring-1 ring-indigo-500/20'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-[#0b0f1a]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl font-mono font-bold text-xs flex items-center justify-center ${
                    isCurrent ? 'bg-indigo-600 text-white dark:bg-cyan-400 dark:text-slate-950' : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
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
