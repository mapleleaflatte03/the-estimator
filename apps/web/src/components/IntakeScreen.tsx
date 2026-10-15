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
    <div className="max-w-6xl mx-auto space-y-8 animate-fadeIn">
      {/* Hero Visual Card with Generated Artwork */}
      <div className="modern-card overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 items-center">
          <div className="lg:col-span-7 p-6 sm:p-8 lg:p-10 space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-semibold tracking-wide">
              <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span>EVIDENCE-DRIVEN ESTIMATION INTELLIGENCE</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
              Dự toán phần mềm dựa trên bằng chứng & Tự hiệu chỉnh
            </h1>
            <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed">
              PARALLAX AI không chỉ tạo văn bản báo giá. Hệ thống bóc tách các yêu cầu có trích dẫn nguồn, phát hiện câu hỏi quan trọng nhất để giảm sai số và mô phỏng xác suất Monte Carlo trước khi đưa ra cam kết.
            </p>

            <div className="pt-2 flex flex-wrap gap-4 text-xs font-medium text-slate-600 dark:text-slate-400">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>100% Trích dẫn nguồn verbatim</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                <span>Monte Carlo Beta-PERT P10-P90</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>Active Clarification (EVI)</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 p-4 sm:p-6 flex justify-center">
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-slate-200/80 dark:border-slate-700/80 max-h-[300px] w-full">
              <img
                src="/parallax_hero.jpg"
                alt="PARALLAX AI Evidence Network"
                className="w-full h-full object-cover object-center"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/40 via-transparent to-transparent pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Load Golden Briefs */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-2">
            <Compass className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span>Chọn nhanh bộ Brief kiểm thử chuẩn (Golden Briefs)</span>
          </span>
          <span className="text-xs text-slate-500">3 kịch bản được gán nhãn thực nghiệm</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {SAMPLE_BRIEFS.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.id}
                onClick={() => handleApplySample(s)}
                className="modern-card modern-card-interactive p-5 cursor-pointer bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between group"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 font-semibold text-[11px] border border-indigo-200 dark:border-indigo-800">
                      <Icon className="w-3.5 h-3.5" />
                      {s.domainLabel}
                    </span>
                    <span className="text-[10px] text-slate-600 dark:text-slate-300 font-mono font-medium">{s.complexity}</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-cyan-400 transition-colors">
                    {s.title}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-3 leading-relaxed">
                    {s.text}
                  </p>
                </div>

                <div className="pt-4 flex items-center justify-between text-xs font-semibold text-indigo-600 dark:text-cyan-400 border-t border-slate-100 dark:border-slate-800/80 mt-3">
                  <span>Nạp kịch bản này</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Intake Form */}
      <form onSubmit={handleSubmit} className="modern-card p-6 sm:p-8 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <span>Nạp thông tin yêu cầu dự án mới</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Nhập brief thô từ khách hàng để AI bóc tách Scope Graph và WBS có trích dẫn nguồn.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
            STAGE 01 / INTAKE
          </span>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs sm:text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Tên dự án <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="VD: Cổng thông tin Quản lý Dự án & Phê duyệt Ngân sách"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 text-sm transition-colors"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Phân loại domain
            </label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 text-sm transition-colors cursor-pointer"
            >
              <option value="internal_tool">Hệ thống nội bộ / Quản trị (Internal Tool)</option>
              <option value="api_integration">Tích hợp API / E-Commerce</option>
              <option value="ai_workflow">AI Workflow / RAG Pipeline</option>
              <option value="custom_software">Phần mềm đặc thù khác</option>
            </select>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Văn bản Brief / Yêu cầu kỹ thuật <span className="text-rose-500">*</span>
            </label>
            <span className="text-[11px] text-slate-400 font-mono">
              {briefText.length} ký tự
            </span>
          </div>
          <textarea
            value={briefText}
            onChange={(e) => setBriefText(e.target.value)}
            rows={8}
            placeholder="Dán toàn bộ nội dung tài liệu yêu cầu, email, specs, hoặc ghi chú cuộc họp tại đây..."
            className="w-full p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 text-sm font-mono leading-relaxed transition-colors"
            required
          />
        </div>

        <div className="pt-2 flex items-center justify-between">
          <span className="text-xs text-slate-500 flex items-center gap-1.5">
            <Database className="w-4 h-4 text-slate-400" /> Lưu trữ phiên bản bất biến (v1, v2) — không ghi đè dữ liệu gốc.
          </span>

          <button
            type="submit"
            disabled={isLoading || !title || !briefText}
            className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 dark:bg-cyan-500 dark:hover:bg-cyan-400 text-white dark:text-slate-950 font-bold text-sm tracking-wide shadow-lg shadow-indigo-600/20 dark:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white dark:border-slate-950 border-t-transparent rounded-full animate-spin" />
                <span>Đang phân tích & tạo WBS...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Bóc tách Evidence & Ước tính WBS &rarr;</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
