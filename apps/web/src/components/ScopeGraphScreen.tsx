import React, { useMemo } from 'react';
import type { EstimateVersion, WorkItem } from '../types';
import { ROLE_COLORS, ROLE_LABELS, card, hours, typicalHours } from '../ui';

interface ScopeGraphScreenProps {
  version: EstimateVersion;
}

const itemHours = (w: WorkItem) => typicalHours(w.optimistic_hours, w.most_likely_hours, w.pessimistic_hours);

export const ScopeGraphScreen: React.FC<ScopeGraphScreenProps> = ({ version }) => {
  const groups = useMemo(() => {
    const byReq = new Map<string, WorkItem[]>();
    version.wbs.forEach((w) => {
      const owner = w.req_ids[0];
      byReq.set(owner, [...(byReq.get(owner) || []), w]);
    });
    const features = version.requirements.filter((r) => r.req_id !== 'REQ-00');
    const foundation = version.requirements.filter((r) => r.req_id === 'REQ-00');
    return [...features, ...foundation].map((req) => ({ req, items: byReq.get(req.req_id) || [] }));
  }, [version]);

  const roleTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    version.wbs.forEach((w) => (totals[w.role] = (totals[w.role] || 0) + itemHours(w)));
    return totals;
  }, [version.wbs]);
  const grandTotal = Object.values(roleTotals).reduce((a, b) => a + b, 0) || 1;
  const featureCount = groups.filter((g) => g.req.req_id !== 'REQ-00' && g.req.in_scope !== false).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Công việc cần làm</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          {featureCount} yêu cầu từ mô tả · {version.wbs.length} công việc · tổng khoảng {hours(grandTotal)} (chưa tính rủi ro)
        </p>
      </div>

      <section className={`${card} p-5 space-y-3`}>
        <div className="flex h-3 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800">
          {Object.entries(roleTotals).map(([role, h]) => (
            <div key={role} className={ROLE_COLORS[role] || 'bg-slate-400'} style={{ width: `${(h / grandTotal) * 100}%` }} />
          ))}
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-700 dark:text-slate-300">
          {Object.entries(roleTotals).map(([role, h]) => (
            <span key={role} className="inline-flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${ROLE_COLORS[role] || 'bg-slate-400'}`} />
              {ROLE_LABELS[role] || role}: {hours(h)}
            </span>
          ))}
        </div>
      </section>

      <div className="space-y-4">
        {groups.map(({ req, items }) => {
          const excluded = req.in_scope === false;
          const total = items.reduce((s, w) => s + itemHours(w), 0);
          const text = req.evidence[0]?.quote ?? req.title;
          return (
            <section key={req.req_id} className={`${card} p-5 ${excluded ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="font-bold leading-snug">{req.req_id === 'REQ-00' ? req.title : text}</h2>
                  {req.req_id === 'REQ-00' && <p className="text-sm text-slate-600 dark:text-slate-400">{req.description}</p>}
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  {!excluded && <span className="font-bold whitespace-nowrap">{hours(total)}</span>}
                  {excluded && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700">Đã bỏ</span>
                  )}
                  {!excluded && req.status === 'assumed' && req.req_id !== 'REQ-00' && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-100">
                      Chưa chắc chắn
                    </span>
                  )}
                </div>
              </div>
              {items.length > 0 && (
                <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
                  {items.map((w) => (
                    <li key={w.item_id} className="py-2 flex items-center justify-between gap-3 text-sm">
                      <span className="flex items-center gap-2 min-w-0">
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${ROLE_COLORS[w.role] || 'bg-slate-400'}`} title={ROLE_LABELS[w.role]} />
                        <span className="text-slate-800 dark:text-slate-200">{w.name}</span>
                      </span>
                      <span className="text-slate-600 dark:text-slate-400 whitespace-nowrap">{hours(itemHours(w))}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
};
