import React, { useCallback, useEffect, useState } from 'react';
import { PlusCircle, FolderOpen, Sun, Moon, Loader2, KeyRound } from 'lucide-react';
import type { Project, EstimateVersion, ManualEdits } from './types';
import {
  fetchProjects,
  createProject,
  fetchVersions,
  estimateProject,
  answerClarification,
  recordActuals,
  runBenchmark,
  updateWbs,
  ApiError,
  visitorKey,
} from './api';
import { JevKeyDialog } from './components/JevKeyDialog';
import { loadSavedProject, saveProject, type SavedActuals, type SavedProject } from './recovery';
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
  const [keyDialog, setKeyDialog] = useState<{ open: boolean; reason?: string | null }>({ open: false });
  const [orphan, setOrphan] = useState<SavedProject | null>(null);
  const [savedActuals, setSavedActuals] = useState<{ id: string; actuals: SavedActuals } | null>(null);
  const [hasKey, setHasKey] = useState(() => !!visitorKey.get());
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
      setVersions([]);
      setCurrentVersion(null);
      if (err instanceof ApiError && err.status === 503) setKeyDialog({ open: true, reason: err.message });
      else console.error('Error loading project versions:', err);
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
        const saved = loadSavedProject();
        const stillThere = saved != null && list.some((p) => p.project_id === saved.server_project_id);
        setOrphan(saved && !stillThere ? saved : null);
        if (list.length > 0) selectProject(list[0]);
      })
      .catch((err) => console.error('Error fetching projects:', err));
    return () => {
      cancelled = true;
    };
  }, [selectProject]);

  useEffect(() => {
    if (!currentProject || !currentVersion) return;
    // A restart left a brief in this browser. Do not overwrite it with some other project the server still has.
    if (orphan && orphan.brief_text !== currentProject.brief_text) return;
    const prev = loadSavedProject();
    saveProject({
      title: currentProject.title,
      project_type: currentProject.project_type,
      brief_text: currentProject.brief_text,
      documents: currentProject.documents,
      server_project_id: currentProject.project_id,
      answers: Object.entries(currentVersion.clarification_answers).map(([question_id, answer]) => ({
        question_id,
        answer,
      })),
      edits: currentVersion.manual_edits ?? null,
      actuals:
        savedActuals?.id === currentProject.project_id
          ? savedActuals.actuals
          : prev?.server_project_id === currentProject.project_id
            ? (prev.actuals ?? null)
            : null,
      saved_at: new Date().toISOString(),
    });
  }, [currentProject, currentVersion, savedActuals, orphan]);

  const withBusy = async (message: string, work: () => Promise<void>) => {
    setIsLoading(true);
    setStatusMessage(message);
    try {
      await work();
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) setKeyDialog({ open: true, reason: err.message });
      else alert(`Có lỗi xảy ra: ${(err as Error).message}`);
    } finally {
      setIsLoading(false);
      setStatusMessage(null);
    }
  };

  const handleProjectCreated = (newProj: Project) =>
    withBusy('AI Jev đang đọc từng câu của mô tả (khoảng 20 giây với mô tả mới)…', async () => {
      setOrphan(null);
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
    setSavedActuals({ id: currentProject.project_id, actuals: { hours: hoursSpent, reasons, perRequirement } });
    setProjects((prev) =>
      prev.map((p) => (p.project_id === currentProject.project_id ? { ...p, status: 'actuals_recorded' } : p)),
    );
    return result;
  };

  const handleRestore = () =>
    withBusy('Đang đọc lại mô tả bằng Jev và khôi phục dự án trên máy này…', async () => {
      const saved = loadSavedProject();
      if (!saved) {
        setOrphan(null);
        return;
      }
      const project = await createProject({
        title: saved.title,
        project_type: saved.project_type,
        brief_text: saved.brief_text,
        documents: saved.documents,
      });
      let version = await estimateProject(project.project_id);
      const skipped: string[] = [];
      for (const item of saved.answers) {
        try {
          version = await answerClarification(project.project_id, item.question_id, item.answer);
        } catch (err) {
          if (err instanceof ApiError && err.status === 400) {
            skipped.push(item.question_id);
            continue;
          }
          throw err;
        }
      }
      const edits = saved.edits;
      const hasEdits = !!edits && (
        (edits.removed?.length ?? 0) > 0
        || (edits.added?.length ?? 0) > 0
        || Object.keys(edits.overrides ?? {}).length > 0
      );
      if (hasEdits && edits) version = await updateWbs(project.project_id, edits);
      if (saved.actuals) {
        await recordActuals(project.project_id, saved.actuals.hours, saved.actuals.reasons, saved.actuals.perRequirement);
        setSavedActuals({ id: project.project_id, actuals: saved.actuals });
        project.status = 'actuals_recorded';
      }
      const vList = await fetchVersions(project.project_id);
      setProjects((prev) => [project, ...prev.filter((p) => p.project_id !== project.project_id)]);
      setCurrentProject(project);
      setVersions(vList.length ? vList : [version]);
      setCurrentVersion(vList.length ? vList[vList.length - 1] : version);
      setOrphan(null);
      setActiveTab('estimation');
      if (skipped.length) {
        alert(`Đã khôi phục dự toán. ${skipped.length} câu trả lời không còn khớp câu hỏi mới và được bỏ qua.`);
      }
    });

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
              onClick={() => setKeyDialog({ open: true })}
              aria-label="Khóa AI Jev"
              title={hasKey ? 'Đang dùng khóa Jev của bạn' : 'Dùng khóa Jev của bạn'}
              className={`w-9 h-9 rounded-xl border flex items-center justify-center cursor-pointer ${
                hasKey
                  ? 'bg-violet-50 dark:bg-violet-950/50 border-violet-300 dark:border-violet-700 text-violet-700 dark:text-violet-300'
                  : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
              }`}
            >
              <KeyRound className="w-4 h-4" />
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

        {orphan && (
          <div className="mb-6 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-amber-950 dark:text-amber-100">
            <p className="text-sm font-semibold">
              Máy chủ vừa khởi động lại và quên dự án «{orphan.title}». Bản mô tả vẫn nằm trong trình duyệt này.
            </p>
            <button
              type="button"
              onClick={handleRestore}
              disabled={isLoading}
              className="mt-3 px-3 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-bold cursor-pointer"
            >
              Đọc lại bằng Jev và khôi phục
            </button>
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
      {keyDialog.open && (
        <JevKeyDialog
          reason={keyDialog.reason}
          onClose={() => {
            setKeyDialog({ open: false });
            setHasKey(!!visitorKey.get());
            // A brief that could not be read yet is read again right away with the new key.
            if (visitorKey.get() && currentProject && !currentVersion) handleReestimate();
          }}
        />
      )}
    </div>
  );
};

export default App;
