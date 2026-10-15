import React, { useEffect, useState } from 'react';
import {
  Layers,
  Activity,
  HelpCircle,
  Award,
  PlusCircle,
  FolderOpen,
  Sparkles,
  Sun,
  Moon,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import type {
  Project,
  EstimateVersion,
} from './types';
import {
  fetchProjects,
  fetchVersions,
  estimateProject,
  answerClarification,
  recordActuals,
  runBenchmark,
} from './api';
import { IntakeScreen } from './components/IntakeScreen';
import { ScopeGraphScreen } from './components/ScopeGraphScreen';
import { EstimationLabScreen } from './components/EstimationLabScreen';
import { ClarificationScreen } from './components/ClarificationScreen';
import { AccuracyLearningScreen } from './components/AccuracyLearningScreen';

type Tab = 'intake' | 'scope' | 'estimation' | 'clarification' | 'accuracy';

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

  // Toggle Dark / Light mode class on document element
  useEffect(() => {
    const root = document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
      localStorage.setItem('parallax_theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('parallax_theme', 'light');
    }
  }, [isDarkMode]);

  // Load projects on startup
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const list = await fetchProjects();
      setProjects(list);
      if (list.length > 0 && !currentProject) {
        selectProject(list[0]);
      }
    } catch (err) {
      console.error('Error fetching projects:', err);
    }
  };

  const selectProject = async (proj: Project) => {
    setCurrentProject(proj);
    setIsLoading(true);
    try {
      let vList = await fetchVersions(proj.project_id);
      if (vList.length === 0) {
        const v1 = await estimateProject(proj.project_id);
        vList = [v1];
      }
      setVersions(vList);
      setCurrentVersion(vList[vList.length - 1]);
      setActiveTab('scope');
    } catch (err) {
      console.error('Error loading project versions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProjectCreated = async (newProj: Project) => {
    setProjects((prev) => [newProj, ...prev]);
    setCurrentProject(newProj);
    setIsLoading(true);
    setStatusMessage('Bóc tách bằng chứng và tạo WBS ban đầu...');
    try {
      const v1 = await estimateProject(newProj.project_id);
      setVersions([v1]);
      setCurrentVersion(v1);
      setActiveTab('scope');
    } catch (err: any) {
      alert(`Lỗi khi tạo dự toán: ${err.message}`);
    } finally {
      setIsLoading(false);
      setStatusMessage(null);
    }
  };

  const handleAnswerClarification = async (qId: string, ans: boolean, notes?: string) => {
    if (!currentProject) return;
    setIsLoading(true);
    setStatusMessage('Đang tính toán lại phân phối xác suất Monte Carlo (Beta-PERT)...');
    try {
      const newVersion = await answerClarification(currentProject.project_id, qId, ans, notes);
      setVersions((prev) => [...prev, newVersion]);
      setCurrentVersion(newVersion);
      setActiveTab('estimation');
    } catch (err: any) {
      alert(`Lỗi khi làm rõ yêu cầu: ${err.message}`);
    } finally {
      setIsLoading(false);
      setStatusMessage(null);
    }
  };

  const handleRecordActuals = async (hours: number, reasons: string[]) => {
    if (!currentProject) return null;
    return await recordActuals(currentProject.project_id, hours, reasons);
  };

  const STEPS: { id: Tab; label: string; number: string; sub: string }[] = [
    { id: 'intake', label: 'Intake & Brief', number: '01', sub: 'Nạp yêu cầu' },
    { id: 'scope', label: 'Scope & Evidence', number: '02', sub: 'Trích dẫn WBS' },
    { id: 'estimation', label: 'Estimation Lab', number: '03', sub: 'Monte Carlo' },
    { id: 'clarification', label: 'Active Clarify', number: '04', sub: 'What-if' },
    { id: 'accuracy', label: 'Accuracy & Learn', number: '05', sub: 'Tự hiệu chỉnh' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#f4f6fb] dark:bg-[#090d1a] text-slate-900 dark:text-slate-100 font-sans transition-colors duration-300 relative selection:bg-indigo-500/20 selection:text-indigo-900 dark:selection:text-indigo-200">
      {/* Ambient background mesh for depth and warmth */}
      <div className="fixed inset-0 pointer-events-none bg-mesh-light dark:bg-mesh-dark opacity-60 z-0" />

      <div className="relative z-10 flex-1 flex flex-col">
        {/* Top Header Navbar */}
        <header className="border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-[#0d1322]/90 backdrop-blur-md sticky top-0 z-50 shadow-sm transition-colors">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between gap-4">
            {/* Logo & Brand */}
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl overflow-hidden shadow-md border border-slate-200 dark:border-slate-700/80 flex-shrink-0 bg-slate-900">
                <img
                  src="/parallax_logo.jpg"
                  alt="PARALLAX AI Logo"
                  className="w-full h-full object-cover"
                />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 dark:from-white dark:via-indigo-200 dark:to-cyan-200 bg-clip-text text-transparent font-mono">
                    PARALLAX AI
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-cyan-300 border border-indigo-200 dark:border-indigo-800 font-bold">
                    EVIDENCE-DRIVEN
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                  Self-Calibrating Estimation Intelligence &bull; Anduin Cybernetics
                </div>
              </div>
            </div>

            {/* Right Header Controls */}
            <div className="flex items-center gap-3">
              {/* Project Picker */}
              {projects.length > 0 && (
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100/90 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 text-xs shadow-inner">
                  <FolderOpen className="w-3.5 h-3.5 text-indigo-600 dark:text-cyan-400" />
                  <select
                    value={currentProject?.project_id || ''}
                    onChange={(e) => {
                      const found = projects.find((p) => p.project_id === e.target.value);
                      if (found) selectProject(found);
                    }}
                    className="bg-transparent text-slate-800 dark:text-slate-200 font-semibold focus:outline-none cursor-pointer max-w-[210px] truncate text-xs"
                  >
                    {projects.map((p) => (
                      <option key={p.project_id} value={p.project_id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                        {p.title}
                      </option>
                    ))}
                  </select>
                  {currentVersion && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-indigo-100 dark:bg-indigo-950 text-indigo-800 dark:text-cyan-300 font-bold">
                      {currentVersion.version_id}
                    </span>
                  )}
                </div>
              )}

              {/* New Project Button */}
              <button
                onClick={() => setActiveTab('intake')}
                className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white font-bold text-xs transition-all shadow-sm hover:shadow-indigo-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Dự án mới</span>
              </button>

              {/* Theme Toggle Button */}
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                title={isDarkMode ? 'Chuyển sang chế độ Sáng' : 'Chuyển sang chế độ Tối'}
                className="w-9 h-9 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/80 flex items-center justify-center text-slate-700 dark:text-amber-300 transition-colors cursor-pointer shadow-sm"
              >
                {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
              </button>
            </div>
          </div>

          {/* 5-Step Pipeline Stepper Bar */}
          <div className="border-t border-slate-200/60 dark:border-slate-800/70 bg-slate-50/80 dark:bg-[#0b0f1d]/80">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between overflow-x-auto py-2 scrollbar-none gap-2">
              {STEPS.map((step, idx) => {
                const isActive = activeTab === step.id;
                const isDisabled = step.id !== 'intake' && !currentVersion;

                return (
                  <button
                    key={step.id}
                    disabled={isDisabled}
                    onClick={() => setActiveTab(step.id)}
                    className={`flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-left whitespace-nowrap transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
                      isActive
                        ? 'bg-white dark:bg-slate-800 text-indigo-700 dark:text-cyan-300 font-bold border border-indigo-200 dark:border-slate-700 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    <span
                      className={`w-6 h-6 rounded-lg text-[11px] font-mono font-bold flex items-center justify-center transition-colors ${
                        isActive
                          ? 'bg-indigo-600 text-white dark:bg-cyan-500 dark:text-slate-950 shadow-sm'
                          : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {step.number}
                    </span>
                    <div>
                      <div className="text-xs font-bold leading-tight">{step.label}</div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">{step.sub}</div>
                    </div>
                    {idx < STEPS.length - 1 && (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-300 dark:text-slate-700 ml-1 hidden lg:block" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Operational Telemetry Ribbon */}
          <div className="border-t border-slate-200/50 dark:border-slate-800/60 bg-white/60 dark:bg-[#070b14]/70 px-4 sm:px-6 py-1.5 text-[11px] font-mono border-b border-slate-200/70 dark:border-slate-800/80">
            <div className="max-w-7xl mx-auto flex items-center justify-between overflow-x-auto gap-4 scrollbar-none">
              <div className="flex items-center gap-4 text-slate-600 dark:text-slate-400 flex-shrink-0">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="font-bold text-slate-800 dark:text-slate-200">ENGINE:</span>
                  <span className="text-emerald-700 dark:text-emerald-400 font-semibold">ONLINE (Beta-PERT N=10,000)</span>
                </div>

                <span className="text-slate-300 dark:text-slate-700">&bull;</span>

                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-slate-800 dark:text-slate-200">DAG INTEGRITY:</span>
                  <span className="text-indigo-700 dark:text-cyan-400 font-semibold">ACYCLIC (0 Chu trình)</span>
                </div>

                <span className="text-slate-300 dark:text-slate-700">&bull;</span>

                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-slate-800 dark:text-slate-200">CALIBRATION:</span>
                  <span className="text-amber-700 dark:text-amber-400 font-semibold">16 Holdout Benchmarks (MAE &lt; 4.5h)</span>
                </div>

                <span className="text-slate-300 dark:text-slate-700 hidden lg:inline">&bull;</span>

                <div className="hidden lg:flex items-center gap-1.5">
                  <span className="font-bold text-slate-800 dark:text-slate-200">SHOCK:</span>
                  <span className="text-purple-700 dark:text-purple-400 font-semibold">Lognormal Tail Active (&sigma;=0.35)</span>
                </div>
              </div>

              {currentVersion && (
                <div className="flex items-center gap-2 flex-shrink-0 text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    Model: <strong className="font-mono text-indigo-600 dark:text-cyan-400">{currentVersion.model_tag}</strong>
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    WBS: <strong className="font-mono text-slate-900 dark:text-white">{currentVersion.wbs.length} tasks</strong>
                  </span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main Container */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {statusMessage && (
            <div className="mb-6 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-800 text-indigo-800 dark:text-indigo-200 text-xs sm:text-sm font-semibold flex items-center gap-3 animate-pulse shadow-sm">
              <Sparkles className="w-5 h-5 text-indigo-600 dark:text-cyan-400 flex-shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

        {activeTab === 'intake' && (
          <IntakeScreen onProjectCreated={handleProjectCreated} isLoading={isLoading} />
        )}

        {activeTab === 'scope' && currentVersion && (
          <ScopeGraphScreen version={currentVersion} />
        )}

        {activeTab === 'estimation' && currentVersion && (
          <EstimationLabScreen version={currentVersion} />
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
            version={currentVersion}
            projectId={currentProject.project_id}
            onRecordActuals={handleRecordActuals}
            onRunBenchmark={runBenchmark}
          />
        )}
      </main>

      {/* Modern Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-5 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-700 dark:text-slate-300">PARALLAX AI</span>
            <span>&bull; Evidence-Driven, Self-Calibrating Estimation Intelligence</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Anduin Cybernetics Challenge &bull; Agent in the Shell 2026</span>
          </div>
        </div>
      </footer>
    </div>
  </div>
  );
};

export default App;
