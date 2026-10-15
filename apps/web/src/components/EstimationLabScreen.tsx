import React from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ShieldAlert,
  Sparkles,
  Info,
  CheckCircle2,
} from 'lucide-react';
import type { EstimateVersion } from '../types';

interface EstimationLabScreenProps {
  version: EstimateVersion;
}

export const EstimationLabScreen: React.FC<EstimationLabScreenProps> = ({ version }) => {
  const { forecast, critic_findings } = version;

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-semibold">
          <Activity className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>PROBABILISTIC ESTIMATION & ADVERSARIAL CRITIC</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Phòng thí nghiệm Dự toán (Estimation Laboratory)
        </h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">
          Ngừng tạo con số chính xác giả. PARALLAX tổng hợp ước lượng 3 điểm từng task qua mô phỏng Monte Carlo Beta-PERT (10.000 lần lặp) kết hợp cú sốc tương quan hệ thống log-normal.
        </p>
      </div>

      {/* Divergence Warning if exists */}
      {forecast.divergence_warning && (
        <div className="p-4 rounded-xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-3 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block text-amber-900 dark:text-amber-100">
              Cảnh báo phân kỳ / Tham chiếu lịch sử:
            </span>
            <span>{forecast.divergence_warning}</span>
          </div>
        </div>
      )}

      {/* Quantiles Cards Grid */}
      {/* Quantiles Cards Grid with Chromatic Risk Spectrum */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* P10 Card */}
        <div className="modern-card p-5 bg-gradient-to-br from-emerald-50/70 to-white dark:from-emerald-950/30 dark:to-[#121829] border border-emerald-200/90 dark:border-emerald-800/60 shadow-sm space-y-2 hover:border-emerald-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-emerald-700 dark:text-emerald-400 font-extrabold tracking-wider">
              P10 (Lạc quan)
            </span>
            <span className="text-[10px] bg-emerald-100/80 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 px-2 py-0.5 rounded-full font-mono font-bold">
              10%
            </span>
          </div>
          <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-300 font-mono">
            {forecast.p10_hours}h
          </div>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Kịch bản thuận lợi tối đa, mọi công việc hoàn thành nhanh và không có blocker.
          </p>
        </div>

        {/* P50 Card (Primary Target Commit) */}
        <div className="modern-card p-5 bg-gradient-to-b from-indigo-50/90 via-white to-cyan-50/40 dark:from-indigo-950/50 dark:via-[#141c30] dark:to-[#0f172a] border-2 border-indigo-600 dark:border-cyan-400 shadow-xl shadow-indigo-600/15 dark:shadow-cyan-400/10 space-y-2 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-indigo-500/15 to-transparent rounded-bl-full pointer-events-none" />
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-indigo-700 dark:text-cyan-400 font-extrabold tracking-wider">
              P50 (Kỳ vọng chuẩn)
            </span>
            <span className="text-[10px] bg-gradient-to-r from-indigo-600 to-violet-600 text-white dark:bg-cyan-400 dark:text-slate-950 px-2.5 py-0.5 rounded-full font-mono font-extrabold shadow-xs">
              TARGET COMMIT
            </span>
          </div>
          <div className="text-3xl font-extrabold text-indigo-950 dark:text-white font-mono">
            {forecast.p50_hours}h
          </div>
          <p className="text-[11px] text-indigo-900/90 dark:text-slate-300 font-medium leading-relaxed">
            Điểm trung vị khuyến nghị dùng cho cam kết hợp đồng và kế hoạch ngân sách.
          </p>
        </div>

        {/* P80 Card */}
        <div className="modern-card p-5 bg-gradient-to-br from-amber-50/70 to-white dark:from-amber-950/30 dark:to-[#121829] border border-amber-200/90 dark:border-amber-800/60 shadow-sm space-y-2 hover:border-amber-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-amber-700 dark:text-amber-400 font-extrabold tracking-wider">
              P80 (An toàn)
            </span>
            <span className="text-[10px] bg-amber-100/80 dark:bg-amber-950 text-amber-800 dark:text-amber-300 px-2 py-0.5 rounded-full font-mono font-bold">
              80%
            </span>
          </div>
          <div className="text-3xl font-extrabold text-amber-600 dark:text-amber-300 font-mono">
            {forecast.p80_hours}h
          </div>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Bao gồm đệm dự phòng rủi ro kỹ thuật và thời gian tinh chỉnh ổn định hệ thống.
          </p>
        </div>

        {/* P90 Card */}
        <div className="modern-card p-5 bg-gradient-to-br from-purple-50/70 to-white dark:from-purple-950/30 dark:to-[#121829] border border-purple-200/90 dark:border-purple-800/60 shadow-sm space-y-2 hover:border-purple-400 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono uppercase text-purple-700 dark:text-purple-400 font-extrabold tracking-wider">
              P90 (Biên độ cao)
            </span>
            <span className="text-[10px] bg-purple-100/80 dark:bg-purple-950 text-purple-800 dark:text-purple-300 px-2 py-0.5 rounded-full font-mono font-bold">
              90%
            </span>
          </div>
          <div className="text-3xl font-extrabold text-purple-600 dark:text-purple-300 font-mono">
            {forecast.p90_hours}h
          </div>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            Kịch bản gặp nhiều trục trặc kỹ thuật hoặc thay đổi API từ nhà cung cấp ngoài.
          </p>
        </div>
      </div>

      {/* Visual Probability Distribution Curve */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
            <span>Phân phối xác suất Monte Carlo (Beta-PERT &amp; Correlated Shock)</span>
          </h2>
          <div className="text-xs font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-200/60 dark:border-slate-700">
            Mean: <span className="font-bold text-indigo-700 dark:text-cyan-400">{forecast.mean_hours}h</span> &bull; Std: <span className="font-bold text-amber-600 dark:text-amber-400">&plusmn;{forecast.std_hours}h</span>
          </div>
        </div>

        {/* Interactive SVG Curve with chromatic stops */}
        <div className="w-full bg-slate-50/80 dark:bg-[#0b0f1a] rounded-xl p-4 border border-slate-200/80 dark:border-slate-800">
          <svg viewBox="0 0 800 200" className="w-full h-36">
            <defs>
              <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.5" />
                <stop offset="60%" stopColor="#38bdf8" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {/* Density Curve Path */}
            <path
              d="M 50,180 Q 200,180 300,130 T 400,30 T 500,120 T 750,180 Z"
              fill="url(#curveGradient)"
              stroke="#6366f1"
              strokeWidth="3"
            />

            {/* P10 Marker */}
            <line x1="260" y1="30" x2="260" y2="180" stroke="#059669" strokeWidth="2" strokeDasharray="4 3" />
            <text x="260" y="24" textAnchor="middle" fill="#059669" fontSize="11" fontFamily="monospace" fontWeight="bold">
              P10: {forecast.p10_hours}h
            </text>

            {/* P50 Marker (Target) */}
            <line x1="400" y1="20" x2="400" y2="180" stroke="#4f46e5" strokeWidth="3" />
            <circle cx="400" cy="30" r="5" fill="#4f46e5" />
            <text x="400" y="15" textAnchor="middle" fill="#4f46e5" fontSize="12" fontFamily="monospace" fontWeight="bold">
              P50: {forecast.p50_hours}h
            </text>

            {/* P80 Marker */}
            <line x1="510" y1="30" x2="510" y2="180" stroke="#d97706" strokeWidth="2" strokeDasharray="4 3" />
            <text x="510" y="24" textAnchor="middle" fill="#d97706" fontSize="11" fontFamily="monospace" fontWeight="bold">
              P80: {forecast.p80_hours}h
            </text>

            {/* P90 Marker */}
            <line x1="600" y1="30" x2="600" y2="180" stroke="#9333ea" strokeWidth="2" strokeDasharray="4 3" />
            <text x="600" y="24" textAnchor="middle" fill="#9333ea" fontSize="11" fontFamily="monospace" fontWeight="bold">
              P90: {forecast.p90_hours}h
            </text>

            {/* Baseline */}
            <line x1="40" y1="180" x2="760" y2="180" stroke="#94a3b8" strokeWidth="1" />
          </svg>
        </div>
      </div>

      {/* Comparison: Bottom-up vs Reference Class */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
          <span>Đối soát Hai Nhánh Độc lập: Bottom-up vs. Reference Class</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50/50 to-white dark:from-indigo-950/30 dark:to-[#0f172a] border border-indigo-200/80 dark:border-indigo-800/60 space-y-2 shadow-xs">
            <div className="text-xs font-bold uppercase text-indigo-800 dark:text-indigo-400">
              Nhánh 1 — Bottom-up WBS Monte Carlo
            </div>
            <div className="text-2xl font-extrabold font-mono text-indigo-700 dark:text-cyan-300">
              {forecast.bottom_up_p50}h
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Tổng hợp từ {version.wbs.length} gói công việc chi tiết. Có tính đến rủi ro đồng biến giữa các vai trò.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-gradient-to-br from-cyan-50/50 to-white dark:from-cyan-950/30 dark:to-[#0f172a] border border-cyan-200/80 dark:border-cyan-800/60 space-y-2 shadow-xs">
            <div className="text-xs font-bold uppercase text-cyan-800 dark:text-cyan-400">
              Nhánh 2 — Reference-Class Median (Lịch sử)
            </div>
            <div className="text-2xl font-extrabold font-mono text-cyan-700 dark:text-cyan-300">
              {forecast.reference_class_p50 ? `${forecast.reference_class_p50}h` : 'Chưa đủ dữ liệu (N < 5)'}
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Dựa trên các dự án tương đồng trong kho dữ liệu lịch sử. Tuyệt đối không tự ý lấy trung bình 70/30 khi có phân kỳ.
            </p>
          </div>
        </div>
      </div>

      {/* Adversarial Critic Section */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            <span>Kết quả Tự phản biện (Adversarial Critic Findings)</span>
          </h2>
          <span className="text-xs font-mono text-slate-500 font-semibold">{critic_findings.length} nhận định</span>
        </div>

        <div className="space-y-3">
          {critic_findings.map((f) => (
            <div
              key={f.finding_id}
              className="p-4 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-200/80 dark:border-slate-800 space-y-2 shadow-xs"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold">
                    {f.finding_id}
                  </span>
                  <span className="text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wide">
                    {f.category}
                  </span>
                </div>
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                    f.verified_by_evidence
                      ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                      : 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
                  }`}
                >
                  {f.verified_by_evidence ? 'Có bằng chứng xác nhận' : 'Giả định kỹ thuật'}
                </span>
              </div>

              <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                {f.claim}
              </p>

              <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5 pt-2 border-t border-slate-200/80 dark:border-slate-800">
                <span className="text-indigo-600 dark:text-cyan-400 font-semibold">Hành động của Engine:</span>
                <span className="font-mono bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-bold">
                  {f.action_taken}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
