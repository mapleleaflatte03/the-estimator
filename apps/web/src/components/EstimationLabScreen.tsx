import React, { useState, useMemo } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ShieldAlert,
  Info,
  CheckCircle2,
  DollarSign,
  Sliders,
  Zap,
  TrendingUp,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Layers,
} from 'lucide-react';
import type { EstimateVersion, CriticFinding } from '../types';

interface EstimationLabScreenProps {
  version: EstimateVersion;
}

type Currency = 'USD' | 'VND';
type ShockMode = 'nominal' | 'api_drift' | 'scope_volatility' | 'tech_unknown';

export const EstimationLabScreen: React.FC<EstimationLabScreenProps> = ({ version }) => {
  const { forecast, critic_findings } = version;

  // Interactive Quantile Scrubber state (from P10 to P95)
  const [scrubberPct, setScrubberPct] = useState<number>(50);

  // Systemic Shock mode
  const [shockMode, setShockMode] = useState<ShockMode>('nominal');

  // Budget Modeler state
  const [currency, setCurrency] = useState<Currency>('USD');
  const [hourlyRateUSD, setHourlyRateUSD] = useState<number>(75);
  const [hourlyRateVND, setHourlyRateVND] = useState<number>(1850000);

  // Critic category filter & expanded state
  const [criticCategoryFilter, setCriticCategoryFilter] = useState<string>('all');
  const [expandedFindings, setExpandedFindings] = useState<Record<string, boolean>>({});

  // Multiplier from shock mode
  const shockMultiplier = useMemo(() => {
    switch (shockMode) {
      case 'api_drift':
        return 1.15;
      case 'scope_volatility':
        return 1.25;
      case 'tech_unknown':
        return 1.4;
      case 'nominal':
      default:
        return 1.0;
    }
  }, [shockMode]);

  // Dynamic adjusted quantiles based on shock mode
  const adjustedP10 = Math.round(forecast.p10_hours);
  const adjustedP50 = Math.round(forecast.p50_hours * (1 + (shockMultiplier - 1) * 0.4));
  const adjustedP80 = Math.round(forecast.p80_hours * (1 + (shockMultiplier - 1) * 0.85));
  const adjustedP90 = Math.round(forecast.p90_hours * shockMultiplier);

  // Interpolate hours at current scrubberPct
  const interpolatedHours = useMemo(() => {
    if (scrubberPct <= 10) return adjustedP10;
    if (scrubberPct <= 50) {
      const ratio = (scrubberPct - 10) / 40;
      return Math.round(adjustedP10 + ratio * (adjustedP50 - adjustedP10));
    }
    if (scrubberPct <= 80) {
      const ratio = (scrubberPct - 50) / 30;
      return Math.round(adjustedP50 + ratio * (adjustedP80 - adjustedP50));
    }
    const ratio = Math.min(1, (scrubberPct - 80) / 15);
    return Math.round(adjustedP80 + ratio * (adjustedP90 - adjustedP80));
  }, [scrubberPct, adjustedP10, adjustedP50, adjustedP80, adjustedP90]);

  // Budget calculations
  const effectiveRate = currency === 'USD' ? hourlyRateUSD : hourlyRateVND;
  const targetBudget = interpolatedHours * effectiveRate;
  const p50Budget = adjustedP50 * effectiveRate;
  const contingencyBufferHours = Math.max(0, interpolatedHours - adjustedP50);
  const contingencyBufferCost = contingencyBufferHours * effectiveRate;

  // Format currency helper
  const formatCost = (amount: number) => {
    if (currency === 'USD') {
      return `$${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
    }
    return `${amount.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} ₫`;
  };

  // SVG Coordinates calculation for dynamic curve
  // Width 800, Height 200
  const p10X = 220;
  const p50X = 400;
  const p80X = 540 + (shockMultiplier - 1) * 60;
  const p90X = 640 + (shockMultiplier - 1) * 80;

  // Scrubber X position in SVG viewBox
  const scrubberX = useMemo(() => {
    if (scrubberPct <= 10) return p10X;
    if (scrubberPct <= 50) {
      const ratio = (scrubberPct - 10) / 40;
      return p10X + ratio * (p50X - p10X);
    }
    if (scrubberPct <= 80) {
      const ratio = (scrubberPct - 50) / 30;
      return p50X + ratio * (p80X - p50X);
    }
    const ratio = Math.min(1, (scrubberPct - 80) / 15);
    return p80X + ratio * (p90X - p80X);
  }, [scrubberPct, p10X, p50X, p80X, p90X]);

  // Filter critic findings
  const filteredFindings = critic_findings.filter((f) => {
    if (criticCategoryFilter === 'all') return true;
    return f.category === criticCategoryFilter;
  });

  const toggleFindingExpand = (id: string) => {
    setExpandedFindings((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Cockpit Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 text-cyan-300 dark:bg-cyan-950/80 dark:border dark:border-cyan-800/80 text-[11px] font-mono font-bold tracking-wider mb-2">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>ESTIMATION INTELLIGENCE COCKPIT &bull; MONTE CARLO N=10,000</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Mô phỏng Phân phối Xác suất & Điều phối Rủi ro
          </h1>
          <p className="text-slate-600 dark:text-slate-400 text-sm max-w-2xl mt-1 leading-relaxed">
            Thay thế con số chính xác giả định bằng phân phối Beta-PERT đa biến. Trượt thanh Scrubbing để định lượng cam kết ngân sách và đệm an toàn theo khẩu vị rủi ro.
          </p>
        </div>

        {/* Shock Preset Controls */}
        <div className="flex flex-col items-end gap-1.5 self-stretch md:self-auto">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <Zap className="w-3 h-3 text-amber-500" /> Cú sốc tương quan hệ thống:
          </span>
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-900 p-1 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
            <button
              onClick={() => setShockMode('nominal')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                shockMode === 'nominal'
                  ? 'bg-white dark:bg-slate-800 text-indigo-700 dark:text-cyan-300 font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Chuẩn (1.0x)
            </button>
            <button
              onClick={() => setShockMode('api_drift')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                shockMode === 'api_drift'
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              API Lệch (+15%)
            </button>
            <button
              onClick={() => setShockMode('scope_volatility')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                shockMode === 'scope_volatility'
                  ? 'bg-rose-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Scope Biến động (+25%)
            </button>
          </div>
        </div>
      </div>

      {/* Divergence Warning if exists */}
      {forecast.divergence_warning && (
        <div className="p-4 rounded-xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-3 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block text-amber-950 dark:text-amber-100">
              Cảnh báo phân kỳ / Tham chiếu lịch sử độc lập:
            </span>
            <span className="leading-relaxed">{forecast.divergence_warning}</span>
          </div>
        </div>
      )}

      {/* Bento Grid: Interactive Scrubber & Dynamic Curve (Top 8 cols) + Budget Modeler (Top 4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Interactive Distribution & Scrubber */}
        <div className="lg:col-span-8 space-y-6">
          {/* Probability Distribution Card */}
          <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-5">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                  <span>Phân phối Xác suất Beta-PERT &bull; Correlated Tail</span>
                </h2>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Đường cong mật độ xác suất hoàn thành đúng hạn &bull; 10.000 lần mô phỏng
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  Mean: <strong className="text-indigo-600 dark:text-cyan-400">{forecast.mean_hours}h</strong>
                </span>
                <span className="text-xs font-mono px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                  Std: <strong className="text-amber-600 dark:text-amber-400">&plusmn;{forecast.std_hours}h</strong>
                </span>
              </div>
            </div>

            {/* Dynamic SVG Probability Curve */}
            <div className="w-full bg-slate-50/90 dark:bg-[#0b0f1a] rounded-xl p-4 border border-slate-200/80 dark:border-slate-800/80 overflow-hidden relative">
              <svg viewBox="0 0 800 220" className="w-full h-44 select-none">
                <defs>
                  <linearGradient id="curveBaseGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.02" />
                  </linearGradient>
                  <linearGradient id="scrubberFillGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.4" />
                    <stop offset="70%" stopColor="#06b6d4" stopOpacity="0.45" />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.5" />
                  </linearGradient>
                  <clipPath id="scrubberClip">
                    <rect x="0" y="0" width={scrubberX} height="220" />
                  </clipPath>
                </defs>

                {/* Grid guidelines */}
                <line x1="50" y1="190" x2="750" y2="190" stroke="#94a3b8" strokeWidth="1" strokeOpacity="0.4" />
                <line x1="50" y1="130" x2="750" y2="130" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="3 3" strokeOpacity="0.3" />
                <line x1="50" y1="70" x2="750" y2="70" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="3 3" strokeOpacity="0.3" />

                {/* Base Distribution Curve Area */}
                <path
                  d={`M 50,190 Q ${p10X - 40},190 ${p10X},145 Q ${p10X + 80},70 ${p50X},35 Q ${p80X - 50},60 ${p80X},135 Q ${p90X},175 750,190 Z`}
                  fill="url(#curveBaseGradient)"
                />

                {/* Shaded Cumulative Confidence Area (Clipped to scrubberX) */}
                <path
                  d={`M 50,190 Q ${p10X - 40},190 ${p10X},145 Q ${p10X + 80},70 ${p50X},35 Q ${p80X - 50},60 ${p80X},135 Q ${p90X},175 750,190 Z`}
                  fill="url(#scrubberFillGradient)"
                  clipPath="url(#scrubberClip)"
                />

                {/* Distribution Stroke Outline */}
                <path
                  d={`M 50,190 Q ${p10X - 40},190 ${p10X},145 Q ${p10X + 80},70 ${p50X},35 Q ${p80X - 50},60 ${p80X},135 Q ${p90X},175 750,190`}
                  fill="none"
                  stroke="#4f46e5"
                  strokeWidth="2.5"
                  className="dark:stroke-cyan-400 transition-all duration-300"
                />

                {/* P10 Marker */}
                <line x1={p10X} y1="45" x2={p10X} y2="190" stroke="#059669" strokeWidth="1.5" strokeDasharray="3 3" />
                <text x={p10X} y="38" textAnchor="middle" fill="#059669" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  P10: {adjustedP10}h
                </text>

                {/* P50 Marker (Target Baseline) */}
                <line x1={p50X} y1="28" x2={p50X} y2="190" stroke="#4f46e5" strokeWidth="2" strokeDasharray="4 2" />
                <text x={p50X} y="22" textAnchor="middle" fill="#4f46e5" fontSize="11" fontFamily="monospace" fontWeight="bold">
                  P50: {adjustedP50}h
                </text>

                {/* P80 Marker */}
                <line x1={p80X} y1="45" x2={p80X} y2="190" stroke="#d97706" strokeWidth="1.5" strokeDasharray="3 3" />
                <text x={p80X} y="38" textAnchor="middle" fill="#d97706" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  P80: {adjustedP80}h
                </text>

                {/* P90 Marker */}
                <line x1={p90X} y1="55" x2={p90X} y2="190" stroke="#e11d48" strokeWidth="1.5" strokeDasharray="3 3" />
                <text x={p90X} y="48" textAnchor="middle" fill="#e11d48" fontSize="10" fontFamily="monospace" fontWeight="bold">
                  P90: {adjustedP90}h
                </text>

                {/* DYNAMIC SCRUBBER CURSOR */}
                <line
                  x1={scrubberX}
                  y1="10"
                  x2={scrubberX}
                  y2="190"
                  stroke="#06b6d4"
                  strokeWidth="3"
                  className="transition-all duration-75"
                />
                <circle
                  cx={scrubberX}
                  cy="16"
                  r="6"
                  fill="#06b6d4"
                  stroke="#ffffff"
                  strokeWidth="2"
                  className="shadow-md"
                />
              </svg>

              {/* Scrubber Tooltip Badge */}
              <div
                className="absolute top-2 transform -translate-x-1/2 pointer-events-none transition-all duration-75 hidden sm:block"
                style={{ left: `${(scrubberX / 800) * 100}%` }}
              >
                <div className="bg-slate-900 text-white text-[11px] font-mono px-2.5 py-1 rounded-md shadow-lg border border-cyan-400 font-bold whitespace-nowrap">
                  P{scrubberPct}: {interpolatedHours}h ({scrubberPct}% tự tin)
                </div>
              </div>
            </div>

            {/* Tactile Scrubber Range Slider Control */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-indigo-600 dark:text-cyan-400" />
                  <span>Kéo thanh Scrubber để chọn Mức độ Tự tin (Percentile Confidence):</span>
                </span>
                <span className="font-mono text-xs font-extrabold text-indigo-700 dark:text-cyan-400 bg-indigo-50 dark:bg-slate-800 px-2.5 py-1 rounded-lg border border-indigo-200 dark:border-slate-700">
                  P{scrubberPct} &bull; {interpolatedHours} Giờ Công
                </span>
              </div>

              <input
                type="range"
                min="10"
                max="95"
                step="1"
                value={scrubberPct}
                onChange={(e) => setScrubberPct(parseInt(e.target.value, 10))}
                className="w-full h-2.5 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600 dark:accent-cyan-400"
              />

              {/* Quick Jump Buttons */}
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1">
                <button
                  onClick={() => setScrubberPct(10)}
                  className={`hover:text-emerald-600 transition-colors cursor-pointer ${scrubberPct === 10 ? 'font-bold text-emerald-600 underline' : ''}`}
                >
                  P10 ({adjustedP10}h)
                </button>
                <button
                  onClick={() => setScrubberPct(25)}
                  className={`hover:text-indigo-600 transition-colors cursor-pointer ${scrubberPct === 25 ? 'font-bold text-indigo-600 underline' : ''}`}
                >
                  P25
                </button>
                <button
                  onClick={() => setScrubberPct(50)}
                  className={`hover:text-indigo-600 transition-colors cursor-pointer ${scrubberPct === 50 ? 'font-bold text-indigo-600 underline' : ''}`}
                >
                  P50 Target ({adjustedP50}h)
                </button>
                <button
                  onClick={() => setScrubberPct(75)}
                  className={`hover:text-amber-600 transition-colors cursor-pointer ${scrubberPct === 75 ? 'font-bold text-amber-600 underline' : ''}`}
                >
                  P75
                </button>
                <button
                  onClick={() => setScrubberPct(80)}
                  className={`hover:text-amber-600 transition-colors cursor-pointer ${scrubberPct === 80 ? 'font-bold text-amber-600 underline' : ''}`}
                >
                  P80 An toàn ({adjustedP80}h)
                </button>
                <button
                  onClick={() => setScrubberPct(90)}
                  className={`hover:text-rose-600 transition-colors cursor-pointer ${scrubberPct === 90 ? 'font-bold text-rose-600 underline' : ''}`}
                >
                  P90 ({adjustedP90}h)
                </button>
              </div>
            </div>
          </div>

          {/* Quantile Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div
              onClick={() => setScrubberPct(10)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                scrubberPct === 10
                  ? 'border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/50 dark:bg-emerald-950/40 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-[#121829] hover:border-emerald-300'
              }`}
            >
              <div className="text-[10px] font-mono font-bold uppercase text-emerald-700 dark:text-emerald-400">
                P10 (Lạc quan)
              </div>
              <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-300 font-mono mt-1">
                {adjustedP10}h
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Không blocker</div>
            </div>

            <div
              onClick={() => setScrubberPct(50)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                scrubberPct === 50
                  ? 'border-indigo-600 dark:border-cyan-400 ring-2 ring-indigo-500/20 dark:ring-cyan-500/20 bg-indigo-50/50 dark:bg-indigo-950/40 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-[#121829] hover:border-indigo-300'
              }`}
            >
              <div className="text-[10px] font-mono font-bold uppercase text-indigo-700 dark:text-cyan-400 flex items-center justify-between">
                <span>P50 (Chuẩn)</span>
                <span className="text-[9px] bg-indigo-600 text-white px-1.5 py-0.2 rounded font-bold">TARGET</span>
              </div>
              <div className="text-2xl font-extrabold text-slate-900 dark:text-white font-mono mt-1">
                {adjustedP50}h
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Trung vị cam kết</div>
            </div>

            <div
              onClick={() => setScrubberPct(80)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                scrubberPct === 80
                  ? 'border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/50 dark:bg-amber-950/40 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-[#121829] hover:border-amber-300'
              }`}
            >
              <div className="text-[10px] font-mono font-bold uppercase text-amber-700 dark:text-amber-400">
                P80 (An toàn)
              </div>
              <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-300 font-mono mt-1">
                {adjustedP80}h
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Đệm dự phòng rủi ro</div>
            </div>

            <div
              onClick={() => setScrubberPct(90)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                scrubberPct === 90
                  ? 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-50/50 dark:bg-rose-950/40 shadow-sm'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-[#121829] hover:border-rose-300'
              }`}
            >
              <div className="text-[10px] font-mono font-bold uppercase text-rose-700 dark:text-rose-400">
                P90 (Tail Risk)
              </div>
              <div className="text-2xl font-extrabold text-rose-600 dark:text-rose-300 font-mono mt-1">
                {adjustedP90}h
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Trục trặc tích hợp API</div>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Financial Budget Modeler & Contract Decision Engine */}
        <div className="lg:col-span-4 space-y-6">
          <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Mô hình Ngân sách Tài chính</span>
              </h2>

              {/* Currency Toggle */}
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs">
                <button
                  onClick={() => setCurrency('USD')}
                  className={`px-2 py-0.5 rounded-md font-mono text-[11px] font-bold transition-all cursor-pointer ${
                    currency === 'USD' ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-white shadow-xs' : 'text-slate-500'
                  }`}
                >
                  USD ($)
                </button>
                <button
                  onClick={() => setCurrency('VND')}
                  className={`px-2 py-0.5 rounded-md font-mono text-[11px] font-bold transition-all cursor-pointer ${
                    currency === 'VND' ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-white shadow-xs' : 'text-slate-500'
                  }`}
                >
                  VND (₫)
                </button>
              </div>
            </div>

            {/* Hourly Rate Control */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
                <span>Đơn giá giờ công hỗn hợp:</span>
                <span className="font-mono text-slate-900 dark:text-white font-bold">
                  {formatCost(effectiveRate)} / giờ
                </span>
              </div>

              {/* Rate Presets */}
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => {
                    if (currency === 'USD') setHourlyRateUSD(50);
                    else setHourlyRateVND(1200000);
                  }}
                  className="px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-mono text-center hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  Junior ({currency === 'USD' ? '$50' : '1.2M'})
                </button>
                <button
                  onClick={() => {
                    if (currency === 'USD') setHourlyRateUSD(75);
                    else setHourlyRateVND(1850000);
                  }}
                  className="px-2 py-1.5 rounded-lg border border-indigo-300 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-950/40 text-[11px] font-mono text-center text-indigo-800 dark:text-cyan-300 font-bold cursor-pointer"
                >
                  Standard ({currency === 'USD' ? '$75' : '1.85M'})
                </button>
                <button
                  onClick={() => {
                    if (currency === 'USD') setHourlyRateUSD(110);
                    else setHourlyRateVND(2700000);
                  }}
                  className="px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-mono text-center hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 cursor-pointer"
                >
                  Lead ({currency === 'USD' ? '$110' : '2.7M'})
                </button>
              </div>
            </div>

            {/* Target Budget Summary Box */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950 text-white space-y-3 shadow-md">
              <div className="flex items-center justify-between text-[11px] text-slate-300 uppercase tracking-wider font-mono">
                <span>Ngân sách tại P{scrubberPct}:</span>
                <span className="text-cyan-400 font-bold">{interpolatedHours} GIỜ</span>
              </div>
              <div className="text-3xl font-extrabold font-mono text-white tracking-tight">
                {formatCost(targetBudget)}
              </div>

              {/* Contingency breakdown */}
              <div className="pt-2 border-t border-slate-700/80 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300">Đệm dự phòng (+{contingencyBufferHours}h):</span>
                <span className="text-amber-400 font-bold">+{formatCost(contingencyBufferCost)}</span>
              </div>
            </div>

            {/* Contract Recommendation Advice based on scrubberPct */}
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200 dark:border-slate-800 text-xs space-y-1.5">
              <div className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <FileCheck className="w-3.5 h-3.5 text-indigo-600 dark:text-cyan-400" />
                <span>Khuyến nghị Điều khoản Hợp đồng:</span>
              </div>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                {scrubberPct < 50 && (
                  <span className="text-rose-600 dark:text-rose-400 font-medium">
                    ⚠️ Mức rủi ro cao: Chỉ phù hợp với hợp đồng Time &amp; Materials hoặc giai đoạn Proof of Concept (PoC).
                  </span>
                )}
                {scrubberPct >= 50 && scrubberPct <= 75 && (
                  <span className="text-indigo-700 dark:text-cyan-300 font-medium">
                    🎯 Cân bằng lý tưởng: Khuyến nghị chốt hợp đồng Milestone-based với điều khoản Change Request nếu bên thứ ba trễ hẹn.
                  </span>
                )}
                {scrubberPct > 75 && (
                  <span className="text-emerald-700 dark:text-emerald-400 font-medium">
                    🛡️ Hợp đồng Fixed-Price an toàn: Mức dự phòng bảo đảm biên độ lợi nhuận gộp &gt; 25% ngay cả khi có phát sinh kỹ thuật.
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Reference Class Historical Comparison Card */}
          <div className="modern-card p-5 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <BarChart3 className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Đối soát Nhánh Độc lập</span>
            </h3>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200/70 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Bottom-up WBS</div>
                <div className="text-base font-extrabold text-indigo-700 dark:text-cyan-300 mt-0.5">
                  {forecast.bottom_up_p50}h
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-[#0b0f1a] border border-slate-200/70 dark:border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Reference Class</div>
                <div className="text-base font-extrabold text-cyan-700 dark:text-cyan-400 mt-0.5">
                  {forecast.reference_class_p50 ? `${forecast.reference_class_p50}h` : 'N < 5 (Chờ mẫu)'}
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
              Hai nhánh chạy song song độc lập. Nghiêm cấm hòa trộn 70/30 khi phát hiện phân kỳ vượt ngưỡng &gt;15%.
            </p>
          </div>
        </div>
      </div>

      {/* Adversarial Critic Bento Section */}
      <div className="modern-card p-6 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600 dark:text-rose-400" />
              <span>Kết quả Tự Phản Biện Đối Kháng (Adversarial Critic)</span>
            </h2>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Hệ thống tự chất vấn các giả định lạc quan vô căn cứ hoặc các hạng mục WBS bị bỏ sót
            </div>
          </div>

          {/* Category Filter Chips */}
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/90 p-1 rounded-xl text-xs">
            <button
              onClick={() => setCriticCategoryFilter('all')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                criticCategoryFilter === 'all' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Tất cả ({critic_findings.length})
            </button>
            <button
              onClick={() => setCriticCategoryFilter('unsupported_optimism')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                criticCategoryFilter === 'unsupported_optimism' ? 'bg-rose-600 text-white font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Lạc quan vô căn cứ
            </button>
            <button
              onClick={() => setCriticCategoryFilter('missing_wbs_item')}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                criticCategoryFilter === 'missing_wbs_item' ? 'bg-amber-600 text-white font-bold shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Hạng mục WBS thiếu
            </button>
          </div>
        </div>

        {/* Critic Findings List */}
        <div className="space-y-3">
          {filteredFindings.map((f) => {
            const isExpanded = !!expandedFindings[f.finding_id];

            return (
              <div
                key={f.finding_id}
                className="p-4.5 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-200/80 dark:border-slate-800 space-y-3 transition-all shadow-xs"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-bold">
                      {f.finding_id}
                    </span>
                    <span className="text-xs font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wide">
                      {f.category}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                        f.verified_by_evidence
                          ? 'bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                          : 'bg-amber-50 dark:bg-amber-950/80 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
                      }`}
                    >
                      {f.verified_by_evidence ? 'Có căn cứ tài liệu' : 'Giả định kỹ thuật'}
                    </span>

                    <button
                      onClick={() => toggleFindingExpand(f.finding_id)}
                      className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                  {f.claim}
                </p>

                {/* Engine Action Badge */}
                <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-2 pt-2 border-t border-slate-200/80 dark:border-slate-800">
                  <span className="text-indigo-600 dark:text-cyan-400 font-semibold">Hành động của Engine:</span>
                  <span className="font-mono bg-white dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-bold text-[11px]">
                    {f.action_taken}
                  </span>
                </div>

                {/* Expanded Supporting Evidence if any */}
                {isExpanded && f.supporting_evidence && f.supporting_evidence.length > 0 && (
                  <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1.5 animate-fadeIn">
                    <div className="text-[10px] uppercase font-bold text-slate-500">Bằng chứng liên kết:</div>
                    {f.supporting_evidence.map((ev, i) => (
                      <div key={i} className="text-xs text-slate-700 dark:text-slate-300 font-mono italic">
                        &ldquo;{ev.quote}&rdquo; &mdash;{' '}
                        <span className="text-indigo-600 dark:text-cyan-400 font-sans font-semibold">
                          {ev.source_doc}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
