import React, { useState } from 'react';
import {
  Sparkles,
  FileText,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Database,
  ShoppingCart,
  Bot,
  Laptop,
  Compass,
} from 'lucide-react';
import type { Project } from '../types';

interface IntakeScreenProps {
  onProjectCreated: (project: Project) => void;
  isLoading: boolean;
}

const SAMPLE_BRIEFS = [
  {
    id: 'pm',
    title: 'Cổng Quản lý Dự án & Phê duyệt Ngân sách',
    type: 'internal_tool',
    icon: Laptop,
    domainLabel: 'Internal Tool',
    complexity: 'Trung bình (6.5/10)',
    text: `Dự án: Xây dựng Cổng thông tin Quản lý Dự án & Phê duyệt Ngân sách Doanh nghiệp.
1. Xác thực người dùng: Bắt buộc hỗ trợ Single Sign-On (SSO) qua Okta / Google Workspace cho toàn bộ 500 nhân sự.
2. Quản lý dự án: Cho phép tạo dự án, phân rã công việc WBS, gán người phụ trách, theo dõi tiến độ theo thời gian thực.
3. Báo cáo & Thống kê: Dashboard trực quan hiển thị KPI, biểu đồ Gantt tiến độ, và xuất báo cáo PDF/Excel hàng tuần.
4. Tích hợp: Doanh nghiệp hiện có hệ thống legacy ERP lưu trữ số liệu kế toán. Cần xem xét khả năng đồng bộ hai chiều nhưng chưa có tài liệu kỹ thuật về API của ERP.
5. Bảo mật: Phân quyền đa cấp (Admin, Project Manager, Member, Viewer) kèm audit log ghi nhận mọi thay đổi.`,
  },
  {
    id: 'ecomm',
    title: 'Hệ thống Đồng bộ Đơn hàng & Tồn kho Đa sàn',
    type: 'api_integration',
    icon: ShoppingCart,
    domainLabel: 'E-Commerce Sync',
    complexity: 'Nâng cao (7.2/10)',
    text: `Dự án: Hệ thống Tích hợp & Đồng bộ Đơn hàng - Tồn kho Đa kênh Thương mại Điện tử.
1. Kết nối kênh bán: Tích hợp API của Shopee, Lazada, TikTok Shop và Shopify để đồng bộ tồn kho tức thời (real-time).
2. Webhook & Sự kiện: Tiếp nhận webhook đơn hàng mới, cập nhật trạng thái giao dịch và tự động khóa tồn kho chống bán vượt.
3. Xử lý tải cao: Hệ thống phải chịu tải tối thiểu 500 yêu cầu/giây trong các đợt flash sale lớn mà không bị nghẽn đơn.
4. Báo cáo đối soát: Bảng điều khiển đối soát doanh thu, phí sàn và cảnh báo đơn hàng lỗi đồng bộ.
5. Tích hợp thanh toán và hệ thống legacy ERP cũ để kết chuyển chứng từ cuối ngày.`,
  },
  {
    id: 'rag',
    title: 'Trợ lý AI Hỗ trợ Khách hàng & Điều phối Ticket RAG',
    type: 'ai_workflow',
    icon: Bot,
    domainLabel: 'AI & RAG Pipeline',
    complexity: 'Đặc thù (7.8/10)',
    text: `Dự án: Trợ lý AI Hỗ trợ Khách hàng và Điều phối Ticket Thông minh.
1. Tri thức nền tảng: Xây dựng pipeline RAG (Retrieval-Augmented Generation) nạp tài liệu hướng dẫn kỹ thuật PDF, Notion và FAQ.
2. Tìm kiếm vector: Sử dụng PostgreSQL pgvector để lưu trữ và truy vấn tương đồng ngữ nghĩa câu hỏi khách hàng.
3. Trả lời tự động: Chatbot AI phản hồi thắc mắc khách hàng với trích dẫn nguồn tài liệu tham khảo chính xác.
4. Báo cáo & Giám sát: Dashboard trực quan thống kê tỷ lệ giải quyết câu hỏi và đánh giá độ chính xác của AI.
5. Tích hợp kênh: Hỗ trợ tích hợp live-chat widget nhúng website và kênh Slack nội bộ công ty.`,
  },
];

export const IntakeScreen: React.FC<IntakeScreenProps> = ({ onProjectCreated, isLoading }) => {
  const [title, setTitle] = useState('');
  const [projectType, setProjectType] = useState('internal_tool');
  const [briefText, setBriefText] = useState('');
  const [docName, setDocName] = useState('brief.txt');
  const [error, setError] = useState<string | null>(null);

  const handleApplySample = (sample: typeof SAMPLE_BRIEFS[0]) => {
    setTitle(sample.title);
    setProjectType(sample.type);
    setBriefText(sample.text);
    setDocName('brief.txt');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !briefText.trim()) {
      setError('Vui lòng nhập tên dự án và nội dung yêu cầu.');
      return;
    }
    setError(null);
    try {
      const documents: Record<string, string> = {
        'brief.txt': briefText.trim(),
      };
      const res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          project_type: projectType,
          brief_text: briefText.trim(),
          documents,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Lỗi khi tạo dự án');
      }
      const createdProject: Project = await res.json();
      onProjectCreated(createdProject);
    } catch (err: any) {
      setError(err.message || 'Không thể kết nối đến API backend.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* 21st.dev Style Asymmetric Bento Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Bento Cell 1: Core Value Proposition & Mission Statement (8 Cols) */}
        <div className="lg:col-span-8 modern-card p-6 sm:p-8 lg:p-9 bg-gradient-to-br from-white via-indigo-50/20 to-slate-50 dark:from-[#131b2e] dark:via-[#101726] dark:to-[#0d1322] border border-slate-200/90 dark:border-slate-800 shadow-md flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-indigo-500/10 via-violet-500/5 to-transparent rounded-bl-full pointer-events-none" />

          <div className="space-y-4 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/80 dark:border-indigo-800/80 text-indigo-700 dark:text-cyan-300 text-xs font-mono font-bold tracking-wider shadow-xs">
              <span className="w-2 h-2 rounded-full bg-indigo-600 dark:bg-cyan-400 animate-pulse" />
              <span>PARALLAX CYBERNETICS // SELF-CALIBRATING ESTIMATION ENGINE</span>
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight leading-tight">
              Dự toán Phần mềm Khoa học Dựa trên Bằng chứng
            </h1>

            <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed max-w-2xl">
              Không dựa trên trực giác chủ quan hay câu chữ AI mơ hồ. Hệ thống bóc tách các yêu cầu có trích dẫn nguồn chuẩn xác 100%, xây dựng đồ thị WBS phi chu trình và kiểm nghiệm bằng 10.000 lượt mô phỏng xác suất Monte Carlo trước khi đưa ra cam kết thương mại.
            </p>

            <div className="pt-2 flex flex-wrap gap-2.5 text-xs font-semibold">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200/70 dark:border-emerald-800/50 shadow-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                100% Verbatim Citation
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-800 dark:text-indigo-300 border border-indigo-200/70 dark:border-indigo-800/50 shadow-xs">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                Monte Carlo Beta-PERT
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-50 dark:bg-cyan-950/40 text-cyan-800 dark:text-cyan-300 border border-cyan-200/70 dark:border-cyan-800/50 shadow-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
                Acyclic WBS DAG (0 Cycles)
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-50 dark:bg-purple-950/40 text-purple-800 dark:text-purple-300 border border-purple-200/70 dark:border-purple-800/50 shadow-xs">
                <CheckCircle2 className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                Strict Holdout MAE Gate
              </span>
            </div>
          </div>

          <div className="pt-6 mt-6 border-t border-slate-200/60 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>Dành cho Giám đốc Kỹ thuật (CTO), Head of Delivery và Project Estimators</span>
            <span className="font-mono font-bold text-indigo-600 dark:text-cyan-400">v2.4 Engine Release</span>
          </div>
        </div>

        {/* Bento Cell 2: 3D Holographic Evidence Radar Card (4 Cols) */}
        <div className="lg:col-span-4 modern-card p-5 sm:p-6 bg-gradient-to-b from-white to-slate-100/60 dark:from-[#111827] dark:to-[#0b0f1a] border border-slate-200/90 dark:border-slate-800 shadow-md flex flex-col justify-between group">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                CYBERNETIC COCKPIT HUD
              </span>
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold border border-emerald-200 dark:border-emerald-800">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                CALIBRATED
              </span>
            </div>

            <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700/80 relative shadow-inner bg-slate-950">
              <img
                src="/parallax_hero.jpg"
                alt="PARALLAX AI Evidence Network"
                className="w-full h-36 object-cover object-center group-hover:scale-105 transition-transform duration-500 opacity-90"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />
              <div className="absolute bottom-2.5 left-3 right-3 flex items-center justify-between text-[10px] text-white font-mono font-semibold">
                <span>Monte Carlo Runs</span>
                <span className="text-cyan-300">10,000 Iterations</span>
              </div>
            </div>
          </div>

          <div className="space-y-2 pt-4">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500 dark:text-slate-400">Historical Holdout Priors:</span>
              <strong className="text-slate-900 dark:text-white">16 Seeded Projects</strong>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500 dark:text-slate-400">Systemic Correlation Shock:</span>
              <strong className="text-indigo-600 dark:text-cyan-400">&mu; = -0.5&sigma;&sup2;, &sigma; = 0.35</strong>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500 dark:text-slate-400">Holdout Error Gate:</span>
              <strong className="text-emerald-600 dark:text-emerald-400">Strict MAE Guard</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 21st.dev Style Golden Briefs Bento Grid with SVG Complexity Meters */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Thư viện Kịch bản Kiểm thử Chuẩn (Golden Briefs Benchmark)</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              3 bộ tài liệu thực tế đã được gán nhãn thực nghiệm để đối soát độ chính xác của mô hình
            </p>
          </div>
          <span className="text-xs font-mono bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg text-slate-600 dark:text-slate-300 font-semibold hidden sm:inline-block">
            3 BENCHMARK PRESETS
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {SAMPLE_BRIEFS.map((s) => {
            const Icon = s.icon;
            // Thematic styling & SVG meter configuration
            const styleMap: Record<string, {
              cardBg: string;
              badgeBg: string;
              badgeText: string;
              badgeBorder: string;
              actionText: string;
              borderHover: string;
              ringColor: string;
              meterValue: number;
              tags: string[];
            }> = {
              pm: {
                cardBg: 'bg-gradient-to-b from-white to-blue-50/30 dark:from-[#111827] dark:to-[#0e1626]',
                badgeBg: 'bg-blue-50 dark:bg-blue-950/80',
                badgeText: 'text-blue-700 dark:text-blue-300',
                badgeBorder: 'border-blue-200 dark:border-blue-800',
                actionText: 'text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300',
                borderHover: 'hover:border-blue-400 dark:hover:border-blue-500/80 hover:shadow-blue-500/10',
                ringColor: '#2563EB',
                meterValue: 65,
                tags: ['SSO Okta', 'Legacy ERP', 'Gantt WBS', 'Audit Logs'],
              },
              ecomm: {
                cardBg: 'bg-gradient-to-b from-white to-emerald-50/30 dark:from-[#0f1d1d] dark:to-[#0a1518]',
                badgeBg: 'bg-emerald-50 dark:bg-emerald-950/80',
                badgeText: 'text-emerald-700 dark:text-emerald-300',
                badgeBorder: 'border-emerald-200 dark:border-emerald-800',
                actionText: 'text-emerald-600 dark:text-emerald-400 group-hover:text-emerald-700 dark:group-hover:text-emerald-300',
                borderHover: 'hover:border-emerald-400 dark:hover:border-emerald-500/80 hover:shadow-emerald-500/10',
                ringColor: '#059669',
                meterValue: 72,
                tags: ['500 req/s', 'Shopee API', 'TikTok Shop', 'Anti-Oversell'],
              },
              rag: {
                cardBg: 'bg-gradient-to-b from-white to-purple-50/30 dark:from-[#19132d] dark:to-[#110d22]',
                badgeBg: 'bg-purple-50 dark:bg-purple-950/80',
                badgeText: 'text-purple-700 dark:text-purple-300',
                badgeBorder: 'border-purple-200 dark:border-purple-800',
                actionText: 'text-purple-600 dark:text-purple-400 group-hover:text-purple-700 dark:group-hover:text-purple-300',
                borderHover: 'hover:border-purple-400 dark:hover:border-purple-500/80 hover:shadow-purple-500/10',
                ringColor: '#9333EA',
                meterValue: 78,
                tags: ['pgvector', 'PDF/Notion RAG', 'Slack Bot', 'Citation Strict'],
              },
            };

            const config = styleMap[s.id] || styleMap.pm;

            return (
              <div
                key={s.id}
                onClick={() => handleApplySample(s)}
                className={`modern-card modern-card-interactive p-6 cursor-pointer ${config.cardBg} border border-slate-200/90 dark:border-slate-800 flex flex-col justify-between group shadow-sm transition-all duration-200 hover:scale-[1.015] ${config.borderHover}`}
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg ${config.badgeBg} ${config.badgeText} font-bold text-[11px] border ${config.badgeBorder} shadow-xs`}>
                      <Icon className="w-3.5 h-3.5" />
                      {s.domainLabel}
                    </span>

                    {/* Circular SVG Complexity Gauge */}
                    <div className="flex items-center gap-2">
                      <div className="relative w-8 h-8 flex items-center justify-center">
                        <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                          <path
                            className="text-slate-200 dark:text-slate-800"
                            strokeWidth="3.5"
                            stroke="currentColor"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path
                            stroke={config.ringColor}
                            strokeWidth="3.5"
                            strokeDasharray={`${config.meterValue}, 100`}
                            strokeLinecap="round"
                            fill="none"
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                        </svg>
                        <span className="absolute text-[9px] font-mono font-extrabold text-slate-800 dark:text-slate-200">
                          {config.meterValue}%
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 font-bold">Risk</span>
                    </div>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:underline transition-colors leading-snug">
                    {s.title}
                  </h3>

                  <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 leading-relaxed">
                    {s.text}
                  </p>

                  {/* Architecture Tags */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {config.tags.map((t) => (
                      <span
                        key={t}
                        className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100/80 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 border border-slate-200/60 dark:border-slate-700/60"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className={`pt-4 flex items-center justify-between text-xs font-bold ${config.actionText} border-t border-slate-100 dark:border-slate-800/90 mt-4`}>
                  <span>Nạp kịch bản này vào Studio</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Ingestion Cockpit Studio Form */}
      <form onSubmit={handleSubmit} className="modern-card p-6 sm:p-8 lg:p-9 bg-white dark:bg-[#121829] border border-slate-200/90 dark:border-slate-800 shadow-lg space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600 dark:text-cyan-400" />
              <span>Studio Tiếp nhận Yêu cầu Dự án (Evidence Ingestion Studio)</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Dán brief thô, hợp đồng, email yêu cầu hoặc RFC kỹ thuật. PARALLAX sẽ tự động bóc tách WBS và kiểm tra trích dẫn.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-indigo-700 dark:text-cyan-400 bg-indigo-50 dark:bg-slate-800/90 border border-indigo-200/60 dark:border-slate-700 px-2.5 py-1 rounded-lg">
              STAGE 01 // COCKPIT
            </span>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs sm:text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Project Title Input (8 Cols) */}
          <div className="lg:col-span-8 space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Tên dự án cam kết <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="VD: Cổng thông tin Quản lý Dự án & Phê duyệt Ngân sách Doanh nghiệp"
              className="w-full px-4 py-3 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-cyan-500/20 text-sm transition-all"
              required
            />
          </div>

          {/* Domain Type Selector (4 Cols) */}
          <div className="lg:col-span-4 space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Phân loại Reference Class
            </label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-cyan-500/20 text-sm transition-all cursor-pointer font-medium"
            >
              <option value="internal_tool">Hệ thống nội bộ / Quản trị (Internal Tool)</option>
              <option value="api_integration">Tích hợp API / E-Commerce Đa sàn</option>
              <option value="ai_workflow">AI Workflow / RAG Pipeline &amp; Vector</option>
              <option value="custom_software">Phần mềm đặc thù khác</option>
            </select>
          </div>
        </div>

        {/* Text Area for Requirements Ingest */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-2">
              <span>Nội dung Yêu cầu Kỹ thuật / Client Brief</span>
              <span className="text-rose-500">*</span>
            </label>
            <div className="flex items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              <span>{briefText.split('\n').filter(Boolean).length} dòng</span>
              <span>&bull;</span>
              <span>{briefText.length} ký tự</span>
            </div>
          </div>

          <textarea
            value={briefText}
            onChange={(e) => setBriefText(e.target.value)}
            rows={9}
            placeholder="Dán toàn bộ nội dung tài liệu yêu cầu, email, specs, hoặc ghi chú cuộc họp tại đây..."
            className="w-full p-4.5 rounded-2xl bg-slate-50/80 dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 dark:focus:ring-cyan-500/20 text-sm font-mono leading-relaxed transition-all"
            required
          />
        </div>

        {/* Footer Actions */}
        <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <span className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <Database className="w-4 h-4 text-indigo-500 dark:text-cyan-400" /> Lưu trữ phiên bản bất biến (v1, v2) — không ghi đè dữ liệu gốc.
          </span>

          <button
            type="submit"
            disabled={isLoading || !title || !briefText}
            className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-sm tracking-wide shadow-lg shadow-indigo-600/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2.5 cursor-pointer hover:translate-y-[-1px]"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Đang phân tích &amp; tạo WBS Monte Carlo...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Kích hoạt Engine Bóc tách &amp; Mô phỏng WBS &rarr;</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
