import React, { useState, useEffect } from 'react';
import {
  Award,
  BarChart,
  Clock,
  RotateCcw,
  ShieldCheck,
  AlertOctagon,
  CheckCircle2,
  TrendingDown,
  Database,
  Search,
  Filter,
  Layers,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { BenchmarkMetrics, EstimateVersion, HistoricalCase } from '../types';
import { fetchHistoricalCases } from '../api';

interface AccuracyLearningScreenProps {
  version: EstimateVersion;
  projectId: string;
  onRecordActuals: (actualHours: number, reasons: string[]) => Promise<any>;
  onRunBenchmark: () => Promise<BenchmarkMetrics>;
}

export const AccuracyLearningScreen: React.FC<AccuracyLearningScreenProps> = ({
  version,
  projectId,
  onRecordActuals,
  onRunBenchmark,
}) => {
  const [actualHours, setActualHours] = useState('');
  const [reason, setReason] = useState('');
  const [actualResult, setActualResult] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [benchmarkMetrics, setBenchmarkMetrics] = useState<BenchmarkMetrics | null>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);

  // Historical cases explorer
  const [historicalCases, setHistoricalCases] = useState<HistoricalCase[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingCases, setIsLoadingCases] = useState(false);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    setIsLoadingCases(true);
    try {
      const data = await fetchHistoricalCases();
      setHistoricalCases(data);
    } catch (err) {
      console.error('Error fetching historical cases:', err);
    } finally {
      setIsLoadingCases(false);
    }
  };

  const handleActualsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const hours = parseFloat(actualHours);
    if (isNaN(hours) || hours <= 0) return;
    setIsSubmitting(true);
    try {
      const res = await onRecordActuals(hours, reason ? [reason] : []);
      setActualResult(res);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBenchmarkRun = async () => {
    setIsRunningBenchmark(true);
    try {
      const res = await onRunBenchmark();
      setBenchmarkMetrics(res);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  // Filter historical cases
  const filteredCases = historicalCases.filter((c) => {
    if (selectedDomain !== 'all' && c.domain.toLowerCase() !== selectedDomain.toLowerCase()) return false;
    if (searchQuery && !c.title.toLowerCase().includes(searchQuery.toLowerCase()) && !c.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 text-emerald-400 dark:bg-emerald-950/80 dark:border dark:border-emerald-800 text-[11px] font-mono font-bold tracking-wider">
          <Award className="w-3.5 h-3.5 text-emerald-400" />
          <span>CONTINUOUS SELF-CALIBRATION & EMPIRICAL BENCHMARK</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Độ chính xác & Vòng lặp Tự hiệu chỉnh
        </h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm max-w-2xl mx-auto leading-relaxed">
          Giải quyết yêu cầu &ldquo;become more accurate over time&rdquo;. Khi dự án hoàn thành, nạp actuals để đối soát với dự toán ban đầu (v1). Nếu mô hình hiệu chỉnh mới làm tăng sai số (MAE), hệ thống sẽ từ chối cập nhật.
        </p>
      </div>

      {/* Grid: Actuals Ingestion & Benchmark Suite */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Actuals Recording Card */}
        <div className="modern-card p-6 sm:p-7 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 space-y-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Ghi nhận Giờ công Thực tế (Actuals)</span>
            </h2>
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-cyan-400 border border-slate-200 dark:border-slate-700 font-bold">
              So sánh baseline v1
            </span>
          </div>

          <form onSubmit={handleActualsSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Tổng giờ công thực tế hoàn thành (Hours) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.5"
                min="1"
                value={actualHours}
                onChange={(e) => setActualHours(e.target.value)}
                placeholder="VD: 185"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-cyan-500/20 transition-all"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Ghi chú nguyên nhân sai lệch (nếu có)
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                placeholder="VD: API bên thứ ba thay đổi cấu trúc webhook, cần 15 giờ refactor..."
                className="w-full px-4 py-2 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white text-xs focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-cyan-500/20 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !actualHours}
              className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-cyan-300 dark:bg-cyan-400 dark:hover:bg-cyan-300 dark:text-slate-950 font-bold text-xs tracking-wide transition-all shadow-sm disabled:opacity-50 cursor-pointer font-mono"
            >
              {isSubmitting ? 'Đang phân tích...' : 'Lưu Actuals & Phân tích Sai lệch'}
            </button>
          </form>

          {/* Feedback Card */}
          {actualResult && (
            <div className="p-4.5 rounded-2xl bg-slate-50/90 dark:bg-[#0b0f1a] border border-slate-200/90 dark:border-slate-800 space-y-3 animate-fadeIn">
              <div className="text-xs font-bold text-indigo-700 dark:text-cyan-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Báo cáo sai lệch so với Baseline v1:</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-white dark:bg-slate-900/80 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Dự toán P50 v1:</span>
                  <span className="font-mono font-extrabold text-slate-900 dark:text-white text-sm">
                    {actualResult.estimated_p50}h
                  </span>
                </div>
                <div className="bg-white dark:bg-slate-900/80 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Thực tế thi công:</span>
                  <span className="font-mono font-extrabold text-slate-900 dark:text-white text-sm">
                    {actualResult.actual_hours}h
                  </span>
                </div>
                <div className="bg-white dark:bg-slate-900/80 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Chênh lệch tuyệt đối:</span>
                  <span className="font-mono font-extrabold text-amber-600 dark:text-amber-400 text-sm">
                    {actualResult.delta_hours}h
                  </span>
                </div>
                <div className="bg-white dark:bg-slate-900/80 p-2.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 block text-[11px]">Sai số tương đối:</span>
                  <span className="font-mono font-extrabold text-amber-600 dark:text-amber-400 text-sm">
                    {actualResult.percentage_error}%
                  </span>
                </div>
              </div>

              <div className="pt-1">
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                    actualResult.inside_p10_p90
                      ? 'bg-emerald-50 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
                      : 'bg-rose-50 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                  }`}
                >
                  {actualResult.inside_p10_p90 ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                      <span>Actuals nằm trọn trong khoảng tin cậy P10-P90 ({version.forecast.p10_hours}h - {version.forecast.p90_hours}h)</span>
                    </>
                  ) : (
                    <>
                      <AlertOctagon className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
                      <span>Actuals vượt ngoài khoảng P10-P90 &bull; Kích hoạt Re-weighting</span>
                    </>
                  )}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Benchmark Suite Card */}
        <div className="modern-card p-6 sm:p-7 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 space-y-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <BarChart className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Bộ kiểm định tự động (Benchmark Suite)</span>
            </h2>
            <button
              onClick={handleBenchmarkRun}
              disabled={isRunningBenchmark}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-emerald-400 dark:bg-emerald-500 dark:hover:bg-emerald-400 dark:text-slate-950 text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50 shadow-sm font-mono"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isRunningBenchmark ? 'animate-spin' : ''}`} />
              <span>{isRunningBenchmark ? 'Đang tính...' : 'Chạy Benchmark'}</span>
            </button>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            Đo lường sai số định lượng trên 16 dự án lịch sử holdout theo các tiêu chuẩn khoa học quốc tế (PMI, Jørgensen, Derek Jones).
          </p>

          {benchmarkMetrics ? (
            <div className="space-y-3 animate-fadeIn">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200 dark:border-slate-800 shadow-xs">
                  <div className="text-slate-600 dark:text-slate-400 font-bold uppercase text-[10px]">MAE (Sai lệch tuyệt đối TB)</div>
                  <div className="text-xl font-extrabold font-mono text-indigo-700 dark:text-cyan-300 mt-0.5">
                    {benchmarkMetrics.mae} giờ
                  </div>
                  <div className="text-[10px] text-slate-500">Mean Absolute Error</div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200 dark:border-slate-800 shadow-xs">
                  <div className="text-slate-600 dark:text-slate-400 font-bold uppercase text-[10px]">MdAPE (Sai số trung vị)</div>
                  <div className="text-xl font-extrabold font-mono text-cyan-700 dark:text-cyan-300 mt-0.5">
                    {benchmarkMetrics.mdape}%
                  </div>
                  <div className="text-[10px] text-slate-500">Median Abs % Error</div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200 dark:border-slate-800 shadow-xs">
                  <div className="text-slate-600 dark:text-slate-400 font-bold uppercase text-[10px]">WAPE (Tỷ lệ tổng sai số)</div>
                  <div className="text-xl font-extrabold font-mono text-purple-700 dark:text-purple-300 mt-0.5">
                    {benchmarkMetrics.wape}%
                  </div>
                  <div className="text-[10px] text-slate-500">Weighted Abs % Error</div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200 dark:border-slate-800 shadow-xs">
                  <div className="text-slate-600 dark:text-slate-400 font-bold uppercase text-[10px]">PRED(25) (% sai số &le; 25%)</div>
                  <div className="text-xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {benchmarkMetrics.pred_25}%
                  </div>
                  <div className="text-[10px] text-slate-500">Tỷ lệ dự đoán chuẩn xác</div>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/80 flex items-center justify-between text-xs shadow-xs">
                <div>
                  <div className="text-emerald-900 dark:text-emerald-200 font-bold text-sm">
                    Độ phủ khoảng (Interval Coverage): {benchmarkMetrics.interval_coverage}%
                  </div>
                  <div className="text-emerald-800/80 dark:text-emerald-400 text-[11px] font-medium mt-0.5">
                    Độ rộng khoảng dự báo trung bình: {benchmarkMetrics.mean_interval_width}h ({benchmarkMetrics.n_cases} dự án)
                  </div>
                </div>
                <ShieldCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-dashed border-slate-300 dark:border-slate-800 text-center text-xs text-slate-500">
              Nhấn nút &ldquo;Chạy Benchmark&rdquo; phía trên để tính toán MAE, MdAPE, WAPE và Coverage trên tập holdout.
            </div>
          )}
        </div>
      </div>

      {/* Seeded Historical Holdout Projects Explorer */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Kho Dữ liệu Lịch sử Holdout (16 Seeded Reference Projects)</span>
            </h2>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Cơ sở dữ liệu thực nghiệm dùng cho định giá lớp tham chiếu (Reference-Class Forecasting)
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
              {['all', 'Fintech', 'Security', 'Integration'].map((dom) => (
                <button
                  key={dom}
                  onClick={() => setSelectedDomain(dom)}
                  className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                    selectedDomain === dom
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs font-bold'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  {dom === 'all' ? 'Tất cả' : dom}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table of cases */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/90 dark:bg-[#0b0f1a] text-slate-600 dark:text-slate-400 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 text-[11px]">
              <tr>
                <th className="py-2.5 px-3">Mã &amp; Tên dự án</th>
                <th className="py-2.5 px-3">Lĩnh vực</th>
                <th className="py-2.5 px-3">Số Task</th>
                <th className="py-2.5 px-3">Độ phức tạp</th>
                <th className="py-2.5 px-3 text-right">Giờ công thực tế</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 font-mono">
              {filteredCases.slice(0, 8).map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3">
                    <span className="font-bold text-indigo-600 dark:text-cyan-400 mr-2">{c.case_id}</span>
                    <span className="font-sans text-slate-800 dark:text-slate-200 font-semibold">{c.title}</span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] border border-slate-200 dark:border-slate-700">
                      {c.domain}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">{c.task_count} tasks</td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-1.5">
                      <div className="w-16 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 dark:bg-cyan-400 rounded-full"
                          style={{ width: `${Math.round(c.complexity_score * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-500">{c.complexity_score}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-right font-bold text-slate-900 dark:text-white">
                    {c.actual_hours}h
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodological Integrity Alert */}
      <div className="modern-card p-5 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 border-l-4 border-l-indigo-600 dark:border-l-cyan-400 flex items-start gap-3.5 text-xs text-slate-600 dark:text-slate-300 shadow-sm">
        <AlertOctagon className="w-5 h-5 text-indigo-600 dark:text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold text-slate-900 dark:text-white block mb-0.5 text-xs">
            Nguyên tắc bảo toàn tính trung thực nghiên cứu:
          </span>
          Không cho phép ghi đè dự toán ban đầu bằng kết quả mới để quảng cáo độ chính xác ảo. Quá trình hiệu chỉnh tự động (Calibration Gate) chỉ phê duyệt tham số mới khi chứng minh được mức cải thiện MAE trên tập Validation độc lập, bảo vệ uy tín kỹ thuật của dự án.
        </div>
      </div>
    </div>
  );
};
