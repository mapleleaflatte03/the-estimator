import React, { useMemo, useState } from 'react';
import { Pencil, Plus, Sparkles, Trash2, Undo2 } from 'lucide-react';
import type { EstimateVersion, ManualEdits, RequirementNode, WorkItem } from '../types';
import { COMPONENT_LABELS, KIND_LABELS, ROLE_COLORS, ROLE_LABELS, card, hours, typicalHours } from '../ui';

interface ScopeGraphScreenProps {
  version: EstimateVersion;
  onSaveEdits: (edits: ManualEdits) => Promise<void>;
  isLoading: boolean;
}

const itemHours = (w: WorkItem) => typicalHours(w.optimistic_hours, w.most_likely_hours, w.pessimistic_hours);

const aiNotes = (req: RequirementNode): string[] => {
  const a = req.ai_reading;
  if (!a) return [];
  const notes: string[] = [];
  if (a.flagged_tentative) notes.push(`AI: có vẻ khách chưa chốt (${Math.round(a.tentative * 100)}%)`);
  if (a.added_component) notes.push(`AI nhận ra: ${KIND_LABELS[a.kind] ?? a.kind}`);
  if (a.suggested_component) notes.push(`AI gợi ý thêm: ${KIND_LABELS[a.kind] ?? a.kind} (xem Câu hỏi)`);
  if (a.dropped_components?.length)
    notes.push(`AI bỏ phần từ khóa gợi ý nhưng câu không yêu cầu: ${a.dropped_components.map((c) => COMPONENT_LABELS[c] ?? c).join(', ')} (xem Câu hỏi)`);
  const f = req.adjustment_factor ?? 1;
  const learned = Math.abs(f - 1) >= 0.01 ? ` · ${f > 1 ? '+' : '−'}${Math.abs(Math.round((f - 1) * 100))}% giờ, học từ giờ thực tế của nhóm` : '';
  if (req.risk_group === 2 && a.overrun != null)
    notes.push(`AI: dễ tốn hơn vẻ ngoài (${Math.round(a.overrun * 100)}%), nên xem kỹ${learned}`);
  else if (learned) notes.push(learned.slice(3));
  return notes;
};

type Added = NonNullable<ManualEdits['added']>[number] & { dropped?: boolean };
type Draft = { overrides: Record<string, { name?: string; hours?: number }>; removed: string[]; added: Added[] };

// The server numbers user-added items USER-01, USER-02… in the order they were saved.
const userIndex = (id: string) => (id.startsWith('USER-') ? Number(id.slice(5)) - 1 : -1);

const fromVersion = (v: EstimateVersion): Draft => ({
  overrides: { ...(v.manual_edits?.overrides ?? {}) },
  removed: [...(v.manual_edits?.removed ?? [])],
  added: (v.manual_edits?.added ?? []).map(({ name, hours: h, req_id, role }) => ({ name, hours: h, req_id, role })),
});

export const ScopeGraphScreen: React.FC<ScopeGraphScreenProps> = ({ version, onSaveEdits, isLoading }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Draft>(() => fromVersion(version));
  const [newItem, setNewItem] = useState<Record<string, { name: string; hours: string }>>({});

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
  const reqTotals = groups.map(({ req, items }) => (req.in_scope === false ? 0 : items.reduce((t, w) => t + itemHours(w), 0)));
  const maxReq = Math.max(...reqTotals, 1);
  const biggestFeature = groups.reduce(
    (best, g, i) => (g.req.req_id !== 'REQ-00' && reqTotals[i] > (best.h ?? -1) ? { id: g.req.req_id, h: reqTotals[i] } : best),
    { id: '', h: -1 as number },
  ).id;
  const featureCount = groups.filter((g) => g.req.req_id !== 'REQ-00' && g.req.in_scope !== false).length;
  const editCount =
    Object.keys(version.manual_edits?.overrides ?? {}).length +
    (version.manual_edits?.removed?.length ?? 0) +
    (version.manual_edits?.added?.length ?? 0);

  const startEditing = () => {
    setDraft(fromVersion(version));
    setNewItem({});
    setEditing(true);
  };

  const patchAdded = (idx: number, patch: Partial<Added>) =>
    setDraft((d) => ({ ...d, added: d.added.map((a, i) => (i === idx ? { ...a, ...patch } : a)) }));

  const setHours = (id: string, value: string) => {
    const h = Number(value);
    const idx = userIndex(id);
    if (idx >= 0) return h > 0 && patchAdded(idx, { hours: h });
    setDraft((d) => ({ ...d, overrides: { ...d.overrides, [id]: { ...d.overrides[id], hours: h > 0 ? h : undefined } } }));
  };
  const setName = (id: string, value: string) => {
    const idx = userIndex(id);
    if (idx >= 0) return value && patchAdded(idx, { name: value });
    setDraft((d) => ({ ...d, overrides: { ...d.overrides, [id]: { ...d.overrides[id], name: value || undefined } } }));
  };
  const isRemoved = (id: string) => {
    const idx = userIndex(id);
    return idx >= 0 ? !!draft.added[idx]?.dropped : draft.removed.includes(id);
  };
  const toggleRemove = (id: string) => {
    const idx = userIndex(id);
    if (idx >= 0) return patchAdded(idx, { dropped: !draft.added[idx]?.dropped });
    setDraft((d) => ({ ...d, removed: d.removed.includes(id) ? d.removed.filter((x) => x !== id) : [...d.removed, id] }));
  };
  const addItem = (reqId: string) => {
    const n = newItem[reqId];
    const h = Number(n?.hours);
    if (!n?.name?.trim() || !(h > 0)) return;
    setDraft((d) => ({ ...d, added: [...d.added, { name: n.name.trim(), hours: h, req_id: reqId, role: 'Backend' }] }));
    setNewItem((s) => ({ ...s, [reqId]: { name: '', hours: '' } }));
  };

  const save = async () => {
    const overrides = Object.fromEntries(
      Object.entries(draft.overrides).filter(([, v]) => v && (v.hours || v.name)),
    );
    const added = draft.added.filter((a) => !a.dropped).map(({ name, hours: h, req_id, role }) => ({ name, hours: h, req_id, role }));
    await onSaveEdits({ overrides, removed: draft.removed, added });
    setEditing(false);
  };

  const inputClass =
    'px-2 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0b0f1a] text-sm';

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Công việc cần làm</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            {featureCount} yêu cầu từ mô tả · {version.wbs.length} công việc · tổng khoảng {hours(grandTotal)} (chưa tính rủi ro)
            {editCount > 0 && ` · ${editCount} chỉnh sửa tay`}
          </p>
        </div>
        {!editing ? (
          <button
            type="button"
            onClick={startEditing}
            className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:border-indigo-400 font-bold text-sm inline-flex items-center gap-1.5 cursor-pointer"
          >
            <Pencil className="w-4 h-4" /> Chỉnh sửa
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 font-bold text-sm cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={save}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm disabled:opacity-50 cursor-pointer"
            >
              Lưu & tính lại
            </button>
          </div>
        )}
      </div>

      {editing && (
        <p className="text-sm text-slate-700 dark:text-slate-300 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-xl p-3">
          Sửa số giờ hoặc tên, bỏ việc không cần, hoặc thêm việc mới. Chỉnh sửa được giữ lại cả khi bạn trả lời câu hỏi sau này.
        </p>
      )}

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
          const notes = aiNotes(req);
          const savedAdds = version.manual_edits?.added?.length ?? 0;
          const pendingAdds = editing ? draft.added.slice(savedAdds).filter((a) => a.req_id === req.req_id && !a.dropped) : [];
          return (
            <section key={req.req_id} className={`${card} p-5 ${excluded ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="font-bold leading-snug break-words">{req.req_id === 'REQ-00' ? req.title : text}</h2>
                  {req.req_id === 'REQ-00' && <p className="text-sm text-slate-600 dark:text-slate-400">{req.description}</p>}
                  {notes.map((note) => (
                    <p key={note} className="mt-1 flex items-start gap-1 text-xs font-semibold text-violet-700 dark:text-violet-300">
                      <Sparkles className="w-3.5 h-3.5 flex-shrink-0 mt-px" /> {note}
                    </p>
                  ))}
                </div>
                <div className="flex flex-col items-end gap-1 flex-shrink-0">
                  {!excluded && (
                    <span className={`whitespace-nowrap ${req.req_id === biggestFeature ? 'text-xl font-extrabold text-indigo-700 dark:text-indigo-300' : 'font-bold'}`}>
                      {hours(total)}
                    </span>
                  )}
                  {req.req_id === biggestFeature && !excluded && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-indigo-600 text-white">Tốn nhiều giờ nhất</span>
                  )}
                  {excluded && <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700">Đã bỏ</span>}
                  {!excluded && req.status === 'assumed' && req.req_id !== 'REQ-00' && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-100">
                      Chưa chắc chắn
                    </span>
                  )}
                </div>
              </div>

              {!excluded && total > 0 && (
                <div className="mt-2 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden" aria-hidden="true">
                  <div
                    className={`h-full rounded-full ${
                      req.req_id === 'REQ-00' ? 'bg-slate-400' : req.status === 'assumed' ? 'bg-amber-500' : 'bg-indigo-600 dark:bg-indigo-400'
                    }`}
                    style={{ width: `${(total / maxReq) * 100}%` }}
                  />
                </div>
              )}
              {items.length > 0 && (
                <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
                  {items.map((w) => {
                    const removed = isRemoved(w.item_id);
                    const edited = !!version.manual_edits?.overrides?.[w.item_id] || w.basis?.includes('user');
                    return (
                      <li
                        key={w.item_id}
                        className={`py-2 flex gap-x-3 gap-y-1.5 text-sm ${editing ? 'flex-col sm:flex-row sm:items-start' : 'items-start justify-between'}`}
                      >
                        <span className="flex items-start gap-2 min-w-0 flex-1">
                          <span
                            className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${ROLE_COLORS[w.role] || 'bg-slate-400'}`}
                            title={ROLE_LABELS[w.role]}
                          />
                          {editing ? (
                            <textarea
                              aria-label={`Tên công việc ${w.name}`}
                              defaultValue={draft.overrides[w.item_id]?.name ?? w.name}
                              onChange={(e) => setName(w.item_id, e.target.value)}
                              disabled={removed}
                              rows={Math.min(3, Math.max(1, Math.ceil((draft.overrides[w.item_id]?.name ?? w.name).length / 45)))}
                              className={`${inputClass} flex-1 min-w-0 resize-y leading-snug field-sizing-content ${removed ? 'line-through opacity-50' : ''}`}
                            />
                          ) : (
                            <span className="min-w-0 break-words text-slate-800 dark:text-slate-200">
                              {w.name}
                              {edited && <span className="ml-1.5 text-xs text-slate-600 dark:text-slate-400">(đã chỉnh)</span>}
                            </span>
                          )}
                        </span>
                        {editing ? (
                          <span className="flex items-center gap-1.5 flex-shrink-0 pl-4 sm:pl-0">
                            <input
                              type="number"
                              min={1}
                              aria-label={`Số giờ ${w.name}`}
                              defaultValue={draft.overrides[w.item_id]?.hours ?? itemHours(w)}
                              onChange={(e) => setHours(w.item_id, e.target.value)}
                              disabled={removed}
                              className={`${inputClass} w-20 text-right`}
                            />
                            <span className="text-slate-600 dark:text-slate-400">giờ</span>
                            {(req.req_id !== 'REQ-00' || w.item_id.startsWith('USER-')) && (
                              <button
                                type="button"
                                onClick={() => toggleRemove(w.item_id)}
                                aria-label={removed ? `Giữ lại ${w.name}` : `Bỏ ${w.name}`}
                                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
                              >
                                {removed ? <Undo2 className="w-4 h-4" /> : <Trash2 className="w-4 h-4 text-rose-600" />}
                              </button>
                            )}
                          </span>
                        ) : (
                          <span className="text-slate-600 dark:text-slate-400 whitespace-nowrap">{hours(itemHours(w))}</span>
                        )}
                      </li>
                    );
                  })}
                  {pendingAdds.map((a, i) => (
                    <li key={`new-${i}`} className="py-2 flex flex-wrap items-start justify-between gap-x-3 text-sm text-indigo-800 dark:text-cyan-300">
                      <span className="min-w-0 break-words">+ {a.name}</span>
                      <span className="whitespace-nowrap">{hours(a.hours)} (chưa lưu)</span>
                    </li>
                  ))}
                </ul>
              )}

              {editing && !excluded && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input
                    aria-label="Tên công việc mới"
                    placeholder="Thêm công việc…"
                    value={newItem[req.req_id]?.name ?? ''}
                    onChange={(e) => setNewItem((s) => ({ ...s, [req.req_id]: { name: e.target.value, hours: s[req.req_id]?.hours ?? '' } }))}
                    className={`${inputClass} flex-1 min-w-40`}
                  />
                  <input
                    type="number"
                    min={1}
                    aria-label="Số giờ công việc mới"
                    placeholder="giờ"
                    value={newItem[req.req_id]?.hours ?? ''}
                    onChange={(e) => setNewItem((s) => ({ ...s, [req.req_id]: { name: s[req.req_id]?.name ?? '', hours: e.target.value } }))}
                    className={`${inputClass} w-20 text-right`}
                  />
                  <button
                    type="button"
                    onClick={() => addItem(req.req_id)}
                    className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-sm font-semibold inline-flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-4 h-4" /> Thêm
                  </button>
                </div>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
};
