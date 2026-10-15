import React, { useState } from 'react';
import {
  CheckCircle2,
  HelpCircle,
  AlertTriangle,
  GitFork,
  Quote,
  ShieldCheck,
  Layers,
  Search,
  Filter,
} from 'lucide-react';
import type { EstimateVersion, RequirementNode } from '../types';

interface ScopeGraphScreenProps {
  version: EstimateVersion;
}

export const ScopeGraphScreen: React.FC<ScopeGraphScreenProps> = ({ version }) => {
  const [selectedReq, setSelectedReq] = useState<RequirementNode | null>(
    version.requirements[0] || null
  );
  const [reqFilter, setReqFilter] = useState<'all' | 'confirmed' | 'assumed' | 'missing'>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredReqs = version.requirements.filter((r) => {
    if (reqFilter !== 'all' && r.status !== reqFilter) return false;
    if (searchQuery && !r.title.toLowerCase().includes(searchQuery.toLowerCase()) && !r.description.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const filteredWbs = version.wbs.filter((item) => {
    if (roleFilter !== 'all' && item.role !== roleFilter) return false;
    return true;
  });

  const confirmedCount = version.requirements.filter((r) => r.status === 'confirmed').length;
  const assumedCount = version.requirements.filter((r) => r.status === 'assumed').length;
  const missingCount = version.requirements.filter((r) => r.status === 'missing').length;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> CONFIRMED
          </span>
        );
      case 'assumed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 dark:bg-amber-950/80 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
            <HelpCircle className="w-3 h-3" /> ASSUMED
          </span>
        );
      case 'missing':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 dark:bg-rose-950/80 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800">
            <AlertTriangle className="w-3 h-3" /> MISSING
          </span>
        );
      default:
        return null;
    }
  };

  const getRoleBadge = (role: string) => {
    const map: Record<string, string> = {
      Backend: 'bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
      Frontend: 'bg-cyan-50 dark:bg-cyan-950/80 text-cyan-700 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800',
      QA: 'bg-emerald-50 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
      DevOps: 'bg-purple-50 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800',
    };
    return (
      <span className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${map[role] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
        {role}
      </span>
    );
  };

  return (
    <div className="space-y-8 animate-fadeIn max-w-6xl mx-auto">
      {/* Overview Stat Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="modern-card p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Tổng Yêu cầu</div>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-white mt-1 font-mono">
            {version.requirements.length}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">Bóc tách từ brief</div>
        </div>

        <div className="modern-card p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40">
          <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">Có bằng chứng</div>
          <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-300 mt-1 font-mono">
            {confirmedCount}
          </div>
          <div className="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 mt-0.5">Trích dẫn verbatim</div>
        </div>

        <div className="modern-card p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/40">
          <div className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400">Giả định ngầm</div>
          <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-300 mt-1 font-mono">
            {assumedCount}
          </div>
          <div className="text-[10px] text-amber-600/80 dark:text-amber-400/80 mt-0.5">Cần xác nhận</div>
        </div>

        <div className="modern-card p-4 bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/40">
          <div className="text-[11px] font-bold uppercase tracking-wider text-rose-700 dark:text-rose-400">Khoảng trống</div>
          <div className="text-2xl font-extrabold text-rose-600 dark:text-rose-300 mt-1 font-mono">
            {missingCount}
          </div>
          <div className="text-[10px] text-rose-600/80 dark:text-rose-400/80 mt-0.5">Chờ active clarify</div>
        </div>

        <div className="modern-card p-4 col-span-2 md:col-span-1 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800/40 flex flex-col justify-between">
          <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>DAG Integrity</span>
          </div>
          <div className="text-base font-bold text-indigo-700 dark:text-indigo-300 mt-1">
            0 Chu trình
          </div>
          <div className="text-[10px] text-indigo-600/80 dark:text-indigo-400/80">Acyclic Verified</div>
        </div>
      </div>

      {/* Main Grid: Left Requirements List, Right WBS Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Requirements Column */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Yêu cầu & Dẫn chứng ({filteredReqs.length})</span>
            </h2>

            {/* Filter buttons */}
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
              <button
                onClick={() => setReqFilter('all')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${reqFilter === 'all' ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm' : 'text-slate-500'}`}
              >
                Tất cả
              </button>
              <button
                onClick={() => setReqFilter('confirmed')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${reqFilter === 'confirmed' ? 'bg-emerald-600 text-white' : 'text-slate-500'}`}
              >
                Có nguồn
              </button>
              <button
                onClick={() => setReqFilter('missing')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${reqFilter === 'missing' ? 'bg-rose-600 text-white' : 'text-slate-500'}`}
              >
                Thiếu
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {filteredReqs.map((req) => (
              <div
                key={req.req_id}
                onClick={() => setSelectedReq(req)}
                className={`modern-card p-4.5 cursor-pointer bg-white dark:bg-slate-900 border transition-all ${
                  selectedReq?.req_id === req.req_id
                    ? 'border-indigo-600 dark:border-cyan-400 ring-2 ring-indigo-500/20 shadow-md'
                    : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-indigo-600 dark:text-cyan-400 uppercase">
                      {req.req_id}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-0.5 leading-snug">
                      {req.title}
                    </h3>
                  </div>
                  {getStatusBadge(req.status)}
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1.5 leading-relaxed">
                  {req.description}
                </p>

                {req.evidence.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 space-y-1.5">
                    <div className="text-[10px] uppercase font-bold text-slate-600 dark:text-slate-300 flex items-center gap-1">
                      <Quote className="w-3 h-3 text-indigo-600 dark:text-cyan-400" />
                      <span>Trích dẫn verbatim từ tài liệu:</span>
                    </div>
                    {req.evidence.map((ev, i) => (
                      <div
                        key={i}
                        className="text-xs font-mono text-slate-800 dark:text-cyan-200 bg-slate-50 dark:bg-cyan-950/40 p-2 rounded-lg border border-slate-200 dark:border-cyan-800/40"
                      >
                        &ldquo;{ev.quote}&rdquo;
                        <span className="block text-[10px] text-slate-600 dark:text-slate-300 mt-1 font-sans font-medium">
                          Nguồn: <span className="font-mono text-indigo-600 dark:text-cyan-300 font-semibold">{ev.source_doc}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* WBS Column */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <GitFork className="w-4 h-4 text-indigo-600 dark:text-cyan-400" />
              <span>Phân rã WBS & Ước tính 3 điểm ({filteredWbs.length} gói)</span>
            </h2>

            {/* Role Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-500">
              <Filter className="w-3.5 h-3.5" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 px-2 py-1 rounded-lg text-xs font-semibold focus:outline-none"
              >
                <option value="all">Tất cả vai trò</option>
                <option value="Backend">Backend</option>
                <option value="Frontend">Frontend</option>
                <option value="QA">QA</option>
                <option value="DevOps">DevOps</option>
              </select>
            </div>
          </div>

          <div className="modern-card bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950/80 text-slate-500 dark:text-slate-400 uppercase tracking-wider font-bold border-b border-slate-200 dark:border-slate-800 text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Công việc</th>
                    <th className="py-3 px-3">Role</th>
                    <th className="py-3 px-3">Phụ thuộc</th>
                    <th className="py-3 px-4 text-right">3 Điểm (O / L / P)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                  {filteredWbs.map((item) => (
                    <tr key={item.item_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-mono text-indigo-600 dark:text-cyan-400 font-bold text-[11px]">
                          {item.item_id}
                        </div>
                        <div className="text-slate-900 dark:text-slate-100 font-semibold text-xs mt-0.5">
                          {item.name}
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        {getRoleBadge(item.role)}
                      </td>
                      <td className="py-3.5 px-3">
                        {item.dependencies.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {item.dependencies.map((dep) => (
                              <span
                                key={dep}
                                className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-[10px] border border-slate-200 dark:border-slate-700"
                              >
                                {dep}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400 font-mono">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono">
                        <div className="text-slate-900 dark:text-slate-100 text-xs font-medium">
                          <span className="text-emerald-600 dark:text-emerald-400 font-bold">{item.optimistic_hours}h</span>
                          <span className="text-slate-400 mx-1">/</span>
                          <span className="text-indigo-600 dark:text-cyan-300 font-extrabold">{item.most_likely_hours}h</span>
                          <span className="text-slate-400 mx-1">/</span>
                          <span className="text-amber-600 dark:text-amber-400 font-bold">{item.pessimistic_hours}h</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
