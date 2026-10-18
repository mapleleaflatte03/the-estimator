import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, Upload } from 'lucide-react';
import type { Project, SampleBrief } from '../types';
import { createProject, fetchSampleBriefs } from '../api';
import { useI18n } from '../i18n';
import { card } from '../ui';

interface IntakeScreenProps {
  onProjectCreated: (project: Project) => void;
  isLoading: boolean;
}

const inputClass =
  'w-full px-4 py-3 rounded-xl bg-white dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:border-indigo-600 dark:focus:border-cyan-400 focus:ring-2 focus:ring-indigo-500/20 text-sm';

export const IntakeScreen: React.FC<IntakeScreenProps> = ({ onProjectCreated, isLoading }) => {
  const { t, projectTypes } = useI18n();
  const [title, setTitle] = useState('');
  const [projectType, setProjectType] = useState('internal_tool');
  const [briefText, setBriefText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [samples, setSamples] = useState<SampleBrief[]>([]);

  useEffect(() => {
    fetchSampleBriefs()
      .then(setSamples)
      .catch((err) => console.error('Error fetching sample briefs:', err));
  }, []);

  const MAX_FILE_BYTES = 50_000;
  const MAX_BRIEF_CHARS = 50_000;

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (file.size > MAX_FILE_BYTES) {
      setError(t('File quá lớn (tối đa 50 KB). Hãy rút gọn mô tả yêu cầu.', 'That file is too large (50 KB maximum). Shorten the brief.'));
      return;
    }
    const text = (await file.text()).trim();
    if (!text) {
      setError(t('File không có nội dung chữ. Hãy dùng file .txt, .md hoặc .csv.', 'That file has no text. Use a .txt, .md, or .csv file.'));
      return;
    }
    const combined = briefText.trim() ? `${briefText.trim()}\n${text}` : text;
    if (combined.length > MAX_BRIEF_CHARS) {
      setError(t('Mô tả vượt 50.000 ký tự. Hãy giữ các yêu cầu quan trọng nhất.', 'The brief exceeds 50,000 characters. Keep the most important requirements.'));
      return;
    }
    setError(null);
    setBriefText(combined);
    if (!title.trim()) setTitle(file.name.replace(/\.[^.]+$/, ''));
  };

  const applySample = (s: SampleBrief) => {
    setTitle(s.title);
    setProjectType(s.project_type);
    setBriefText(s.brief_text);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !briefText.trim()) {
      setError(t('Vui lòng nhập tên dự án và mô tả.', 'Enter a project name and a brief.'));
      return;
    }
    if (briefText.length > MAX_BRIEF_CHARS) {
      setError(t('Mô tả vượt 50.000 ký tự.', 'The brief exceeds 50,000 characters.'));
      return;
    }
    setError(null);
    try {
      onProjectCreated(
        await createProject({ title: title.trim(), project_type: projectType, brief_text: briefText.trim() }),
      );
    } catch (err) {
      setError((err as Error).message || t('Không kết nối được máy chủ.', 'Could not reach the server.'));
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">{t('Dự án mới', 'New project')}</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          {t(
            'Dán mô tả dự án phần mềm hoặc tự động hóa AI của khách hàng. Hệ thống sẽ chia thành các công việc và lập dự toán nháp để người phụ trách rà soát.',
            'Paste a software or AI automation brief. The system prepares a draft work breakdown and hour estimate for a delivery lead to review.',
          )}
        </p>
      </div>

      <form onSubmit={handleSubmit} className={`${card} p-6 sm:p-8 space-y-5`}>
        {error && (
          <div role="alert" className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 text-sm flex gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2 space-y-1.5">
            <label htmlFor="intake-title" className="text-sm font-semibold">
              {t('Tên dự án', 'Project name')}
            </label>
            <input
              id="intake-title"
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('VD: Ứng dụng đặt lịch bảo trì', 'e.g. Maintenance booking app')}
              className={inputClass}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="intake-type" className="text-sm font-semibold">
              {t('Loại dự án', 'Project type')}
            </label>
            <select id="intake-type" value={projectType} onChange={(e) => setProjectType(e.target.value)} className={`${inputClass} cursor-pointer`}>
              {projectTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between gap-2">
            <label htmlFor="intake-brief" className="text-sm font-semibold">
              {t('Mô tả yêu cầu', 'Brief')}
            </label>
            <label className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-700 dark:text-cyan-300 cursor-pointer hover:underline">
              <Upload className="w-4 h-4" /> {t('Tải file (.txt, .md, .csv)', 'Upload a file (.txt, .md, .csv)')}
              <input type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" onChange={handleFile} className="sr-only" />
            </label>
          </div>
          <textarea
            id="intake-brief"
            value={briefText}
            onChange={(e) => setBriefText(e.target.value)}
            rows={9}
            placeholder={t(
              'Mỗi yêu cầu nên viết trên một dòng, ví dụ:\n- Khách hàng đặt lịch qua điện thoại\n- Gửi tin nhắn nhắc lịch\n- Xuất báo cáo hàng tháng',
              'Put each requirement on its own line, for example:\n- Customers book a slot by phone\n- Send a reminder message\n- Export a monthly report',
            )}
            className={`${inputClass} leading-relaxed`}
            required
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !title || !briefText}
          className="w-full sm:w-auto px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
        >
          {isLoading ? t('Đang tính…', 'Estimating…') : t('Tính dự toán', 'Estimate')}
          {!isLoading && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>

      {samples.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">{t('Chưa có mô tả? Thử một ví dụ:', 'No brief yet? Try a sample:')}</h2>
          <div className="flex flex-wrap gap-2">
            {samples.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => applySample(s)}
                className="px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 text-sm text-left cursor-pointer"
              >
                {s.title}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
