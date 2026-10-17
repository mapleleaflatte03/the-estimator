import React, { useCallback, useEffect, useState } from 'react';
import { PlusCircle, FolderOpen, Sun, Moon, Loader2 } from 'lucide-react';
import type { Project, EstimateVersion, ManualEdits } from './types';
import {
  fetchProjects,
  fetchVersions,
  estimateProject,
  answerClarification,
  recordActuals,
  runBenchmark,
  updateWbs,
} from './api';
import { IntakeScreen } from './components/IntakeScreen';
import { ScopeGraphScreen } from './components/ScopeGraphScreen';
import { EstimationLabScreen } from './components/EstimationLabScreen';
import { ClarificationScreen } from './components/ClarificationScreen';
import { AccuracyLearningScreen } from './components/AccuracyLearningScreen';
import { EvidenceScreen } from './components/EvidenceScreen';

type Tab = 'intake' | 'scope' | 'estimation' | 'clarification' | 'accuracy' | 'evidence';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('intake');
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [versions, setVersions] = useState<EstimateVersion[]>([]);
  const [currentVersion, setCurrentVersion] = useState<EstimateVersion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('parallax_theme');
      if (saved) return saved === 'dark';
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
    localStorage.setItem('parallax_theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const selectProject = useCallback(async (proj: Project) => {
    setCurrentProject(proj);
    setIsLoading(true);
    try {
      let vList = await fetchVersions(proj.project_id);
      if (vList.length === 0) vList = [await estimateProject(proj.project_id)];
      setVersions(vList);
      setCurrentVersion(vList[vList.length - 1]);
      setActiveTab('estimation');
    } catch (err) {
      console.error('Error loading project versions:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchProjects()
      .then((list) => {
        if (cancelled) return;
        setProjects(list);
        if (list.length > 0) selectProject(list[0]);
      })
      .catch((err) => console.error('Error fetching projects:', err));
    return () => {
      cancelled = true;
    };
  }, [selectProject]);

  const withBusy = async (message: string, work: () => Promise<void>) => {
    setIsLoading(true);
    setStatusMessage(message);
    try {
      await work();
    } catch (err) {
      alert(`Có lỗi xảy ra: ${(err as Error).message}`);
    } finally {
      setIsLoading(false);
      setStatusMessage(null);
    }
  };

  const handleProjectCreated = (newProj: Project) =>
    withBusy('AI Jev đang đọc từng câu của mô tả (khoảng 10–30 giây với mô tả mới)…', async () => {
      setProjects((prev) => [newProj, ...prev]);
      setCurrentProject(newProj);
      const v1 = await estimateProject(newProj.project_id);
      setVersions([v1]);
      setCurrentVersion(v1);
      setActiveTab('estimation');
    });

  const handleAnswerClarification = (qId: string, ans: boolean) =>
    withBusy('Đang tính lại dự toán…', async () => {
      if (!currentProject) return;
      const v = await answerClarification(currentProject.project_id, qId, ans);
      setVersions((prev) => [...prev, v]);
      setCurrentVersion(v);
    });

  const handleReestimate = () =>
    withBusy('Đang tính lại dự toán…', async () => {
      if (!currentProject) return;
      const v = await estimateProject(currentProject.project_id);
      setVersions((prev) => [...prev, v]);
      setCurrentVersion(v);
      setActiveTab('estimation');
    });

  const handleUpdateWbs = (edits: ManualEdits) =>
    withBusy('Đang lưu chỉnh sửa và tính lại dự toán…', async () => {
      if (!currentProject) return;
      const v = await updateWbs(currentProject.project_id, edits);
      setVersions((prev) => [...prev, v]);
      setCurrentVersion(v);
    });

  const handleRecordActuals = async (hoursSpent: number, reasons: string[], perRequirement?: Record<string, number>) => {
    if (!currentProject) throw new Error('Chưa chọn dự án');
    const result = await recordActuals(currentProject.project_id, hoursSpent, reasons, perRequirement);
    setProjects((prev) =>
      prev.map((p) => (p.project_id === currentProject.project_id ? { ...p, status: 'actuals_recorded' } : p)),
    );
    return result;
  };

  const openQuestions = currentVersion?.clarifications.filter((q) => q.answer == null).length ?? 0;

  const STEPS: { id: Tab; label: string; badge?: number }[] = [
    { id: 'intake', label: 'Dự án mới' },
    { id: 'estimation', label: 'Dự toán' },
    { id: 'scope', label: 'Công việc' },
    { id: 'clarification', label: 'Câu hỏi', badge: openQuestions },
    { id: 'accuracy', label: 'Giờ thực tế' },
    { id: 'evidence', label: 'Kiểm chứng' },
  ];

  const titleCounts = projects.reduce<Record<string, number>>((acc, p) => {
    acc[p.title] = (acc[p.title] || 0) + 1;
    return acc;
  }, {});
  const projectLabel = (p: Project) =>
    titleCounts[p.title] > 1 ? `${p.title} (${new Date(p.created_at).toLocaleDateString('vi-VN')})` : p.title;

  return (
    <div className="min-h-screen flex flex-col bg-[#f4f6fb] dark:bg-[#090d1a] text-slate-900 dark:text-slate-100 font-sans transition-colors">
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-[#0d1322]/95 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 flex-shrink-0">
            <img src="/parallax_logo.jpg" alt="" className="w-9 h-9 rounded-xl object-cover flex-shrink-0" />
            <span className="font-extrabold tracking-tight max-[399px]:sr-only">PARALLAX</span>
          </div>

          <div className="flex items-center gap-2 min-w-0">
            {projects.length > 0 && (
              <label className="flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm min-w-0">
                <FolderOpen className="w-4 h-4 text-slate-600 dark:text-slate-400 flex-shrink-0" />
                <span className="sr-only">Chọn dự án</span>
                <select
                  value={currentProject?.project_id || ''}
                  onChange={(e) => {
                    const found = projects.find((p) => p.project_id === e.target.value);
                    if (found) selectProject(found);
                  }}
                  className="bg-transparent font-semibold focus:outline-none cursor-pointer min-w-0 w-full max-w-[150px] sm:max-w-[240px] truncate"
                >
                  {projects.map((p) => (
                    <option key={p.project_id} value={p.project_id} className="bg-white dark:bg-slate-900">
                      {projectLabel(p)}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              onClick={() => setActiveTab('intake')}
              aria-label="Dự án mới"
              className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm flex items-center gap-1.5 cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Dự án mới</span>
            </button>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              aria-label={isDarkMode ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối'}
              className="w-9 h-9 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center cursor-pointer"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
            </button>
          </div>
        </div>

        <nav className="border-t border-slate-200/70 dark:border-slate-800" aria-label="Các bước">
          <div className="max-w-6xl mx-auto px-3 sm:px-6 grid grid-cols-3 gap-1 sm:flex sm:overflow-x-auto py-2 scrollbar-none">
            {STEPS.map((step) => {
              const isActive = activeTab === step.id;
              const isDisabled = step.id !== 'intake' && step.id !== 'evidence' && !currentVersion;
              return (
                <button
                  key={step.id}
                  disabled={isDisabled}
                  aria-current={isActive ? 'page' : undefined}
                  onClick={() => setActiveTab(step.id)}
                  className={`px-2 sm:px-3.5 py-1.5 sm:py-2 rounded-xl text-sm whitespace-nowrap flex items-center justify-center sm:justify-start gap-1.5 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                    isActive
                      ? 'bg-indigo-50 dark:bg-slate-800 text-indigo-700 dark:text-cyan-300 font-bold'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60'
                  }`}
                >
                  {step.label}
                  {!!step.badge && (
                    <span className="min-w-5 h-5 px-1.5 rounded-full bg-amber-500 text-white text-[11px] font-bold flex items-center justify-center">
                      {step.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </nav>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {statusMessage && (
          <div role="status" className="mb-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 text-indigo-900 dark:text-indigo-100 text-sm font-semibold flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

        {activeTab === 'intake' && <IntakeScreen onProjectCreated={handleProjectCreated} isLoading={isLoading} />}
        {activeTab === 'scope' && currentVersion && (
          <ScopeGraphScreen version={currentVersion} onSaveEdits={handleUpdateWbs} isLoading={isLoading} />
        )}
        {activeTab === 'estimation' && currentVersion && (
          <EstimationLabScreen
            version={currentVersion}
            projectId={currentProject?.project_id ?? ''}
            onGoToQuestions={() => setActiveTab('clarification')}
          />
        )}
        {activeTab === 'clarification' && currentVersion && (
          <ClarificationScreen
            version={currentVersion}
            versionsHistory={versions}
            onAnswerQuestion={handleAnswerClarification}
            isLoading={isLoading}
          />
        )}
        {activeTab === 'accuracy' && currentVersion && currentProject && (
          <AccuracyLearningScreen
            key={currentProject.project_id}
            version={currentVersion}
            onRecordActuals={handleRecordActuals}
            onReestimate={handleReestimate}
            onOpenEvidence={() => setActiveTab('evidence')}
            isLoading={isLoading}
          />
        )}
        {activeTab === 'evidence' && <EvidenceScreen onRunBenchmark={runBenchmark} />}
      </main>
    </div>
  );
};

export default App;
