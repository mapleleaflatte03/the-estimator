import React, { useMemo, useState } from 'react';
import { AlertTriangle, Download, FileSpreadsheet, HelpCircle, Sparkles } from 'lucide-react';
import type { EstimateVersion, WorkItem } from '../types';
import { proposalUrl, wbsCsvUrl } from '../api';
import { useI18n } from '../i18n';
import { HOURS_PER_PERSON_WEEK, card, typicalHours } from '../ui';
import { HBarList, RangeBar, type BarRow } from './charts';

interface EstimationLabScreenProps {
  version: EstimateVersion;
  projectId: string;
  onGoToQuestions: () => void;
}

type Currency = 'VND' | 'USD';

const HIDDEN_NOTES = new Set(['scope_breadth', 'quality_gate']);
const X0 = 10;
const X1 = 790;
const Y_BASE = 150;
const Y_TOP = 10;
const itemHours = (w: WorkItem) => typicalHours(w.optimistic_hours, w.most_likely_hours, w.pessimistic_hours);
const shortLabel = (t: string) => (t.length > 60 ? `${t.slice(0, 58).trimEnd()}…` : t);

export const EstimationLabScreen: React.FC<EstimationLabScreenProps> = ({ version, projectId, onGoToQuestions }) => {
  const { lang, locale, t, hours, num } = useI18n();
  const { forecast } = version;
  const [confidence, setConfidence] = useState(80);
  const [currency, setCurrency] = useState<Currency>('VND');
  const [rate, setRate] = useState<Record<Currency, number>>({ VND: 500000, USD: 25 });
  const [people, setPeople] = useState(3);

  const curve = useMemo(() => {
    const pts = new Map<number, number>();
    (forecast.percentile_curve || []).forEach(([p, h]) => pts.set(p, h));
    pts.set(10, forecast.p10_hours);
    pts.set(50, forecast.p50_hours);
    pts.set(80, forecast.p80_hours);
    pts.set(90, forecast.p90_hours);
    return [...pts.entries()].sort((a, b) => a[0] - b[0]);
  }, [forecast]);

  const hoursAt = (pct: number) => {
    if (pct <= curve[0][0]) return curve[0][1];
    for (let i = 1; i < curve.length; i++) {
      if (pct <= curve[i][0]) {
        const [pa, ha] = curve[i - 1];
        const [pb, hb] = curve[i];
        return ha + ((pct - pa) / (pb - pa)) * (hb - ha);
      }
    }
    return curve[curve.length - 1][1];
  };

  const maxPct = curve[curve.length - 1][0];
  const chosen = Math.round(hoursAt(confidence));
  const cost = chosen * rate[currency];
  // Adding people cannot shorten the longest chain of work that must happen in sequence.
  const chainWeeks = ((forecast.critical_path_hours ?? 0) * (forecast.calibration_multiplier ?? 1)) / HOURS_PER_PERSON_WEEK;
  const teamWeeks = chosen / (people * HOURS_PER_PERSON_WEEK);
  const weeks = Math.max(teamWeeks, chainWeeks);
  const chainLimited = chainWeeks > teamWeeks;
  const costParts = (v: number): [string, string] => {
    if (currency === 'USD') return [`$${v.toLocaleString(locale, { maximumFractionDigits: 0 })}`, ''];
    if (v >= 1e9) return [(v / 1e9).toLocaleString(locale, { maximumFractionDigits: 2 }), t('tỷ đồng', 'billion VND')];
    return [(v / 1e6).toLocaleString(locale, { maximumFractionDigits: 1 }), t('triệu đồng', 'million VND')];
  };
  const [costValue, costUnit] = costParts(cost);

  const histogram = forecast.histogram || [];
  const hasChart = histogram.length > 1;
  const hMin = hasChart ? histogram[0].start : 0;
  const hMax = hasChart ? histogram[histogram.length - 1].end : 1;
  const xOf = (h: number) => X0 + ((Math.min(Math.max(h, hMin), hMax) - hMin) / (hMax - hMin || 1)) * (X1 - X0);
  const maxShare = Math.max(...histogram.map((b) => b.share), 1e-9);
  const line = histogram
    .map((b, i) => `${i ? 'L' : 'M'} ${xOf((b.start + b.end) / 2).toFixed(1)},${(Y_BASE - (b.share / maxShare) * (Y_BASE - Y_TOP)).toFixed(1)}`)
    .join(' ');
  const area = hasChart
    ? `M ${xOf((histogram[0].start + histogram[0].end) / 2).toFixed(1)},${Y_BASE} ${line.slice(1)} L ${xOf(
        (histogram[histogram.length - 1].start + histogram[histogram.length - 1].end) / 2,
      ).toFixed(1)},${Y_BASE} Z`
    : '';

  const notes = version.critic_findings.filter((f) => !HIDDEN_NOTES.has(f.category));
  const open = version.clarifications.filter((q) => q.answer == null);
  const hoursAtStake = Math.round(open.reduce((s, q) => s + q.sensitivity_spread_hours, 0));
  const pendingScope = version.requirements
    .filter((r) => r.req_id !== 'REQ-00' && r.in_scope === false)
    .map((r) => ({ req: r, question: version.clarifications.find((q) => q.question_id === `CLAR-${r.req_id}`) }))
    .filter((entry) => entry.question?.answer == null);

  // Where the hours go: one bar per requirement, colour = state (uncertain / AI / foundation).
  const breakdown: BarRow[] = useMemo(() => {
    const byReq = new Map<string, number>();
    version.wbs.forEach((w) => byReq.set(w.req_ids[0], (byReq.get(w.req_ids[0]) || 0) + itemHours(w)));
    return version.requirements
      .filter((r) => r.in_scope !== false && byReq.get(r.req_id))
      .map((r): BarRow => {
        const h = byReq.get(r.req_id) || 0;
        const foundation = r.req_id === 'REQ-00';
        const uncertain = r.status === 'assumed' && !foundation;
        const ai = !!(r.ai_reading?.added_component || r.ai_reading?.flagged_tentative);
        return {
          key: r.req_id,
          label: shortLabel(foundation ? r.title : (r.evidence[0]?.quote ?? r.title)),
          value: h,
          display: hours(h),
          tone: foundation ? 'muted' : uncertain ? 'attention' : 'primary',
          tag: uncertain
            ? { text: t('chưa chốt', 'not committed'), tone: 'attention' as const }
            : r.risk_group === 2
              ? { text: t('dễ vượt giờ', 'likely to overrun'), tone: 'ai' as const }
              : ai
                ? { text: 'AI', tone: 'ai' as const }
                : undefined,
        };
      })
      .sort((a, b) => b.value - a.value);
  }, [version, lang, hours, t]);
  const countedElsewhere = useMemo(() => {
    const owners = new Set(version.wbs.map((w) => w.req_ids[0]));
    return version.requirements.filter(
      (r) => r.req_id !== 'REQ-00' && r.in_scope !== false && !owners.has(r.req_id) && version.wbs.some((w) => w.req_ids.includes(r.req_id)),
    );
  }, [version]);
  const breakdownTotal = breakdown.reduce((s, r) => s + r.value, 0) || 1;
  const topShare = breakdown[0] ? Math.round((breakdown[0].value / breakdownTotal) * 100) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      {open.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border-2 border-amber-300 dark:border-amber-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 text-amber-950 dark:text-amber-100">
            <HelpCircle className="w-6 h-6 flex-shrink-0" />
            <div>
              <div className="font-bold">{t(`Còn ${open.length} câu hỏi chưa trả lời`, `${open.length} ${open.length === 1 ? 'question' : 'questions'} still open`)}</div>
              <div className="text-sm">{t(`Các quyết định này có thể thay đổi phạm vi khoảng ${hours(hoursAtStake)}.`, `These decisions could change the scope by about ${hours(hoursAtStake)}.`)}</div>
            </div>
          </div>
          <button onClick={onGoToQuestions} className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-sm cursor-pointer">
            {t('Trả lời ngay', 'Answer now')}
          </button>
        </div>
      )}

      {/* Most important: the number, its range, and what it means for budget and time */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <section className={`${card} min-w-0 lg:col-span-3 p-5 sm:p-8 border-2 border-indigo-200 dark:border-indigo-900 space-y-3`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">{t('Ước tính khối lượng công việc', 'Estimated effort')}</p>
            {version.reader === 'rules+jev' && (
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-violet-50 dark:bg-violet-950/50 text-violet-700 dark:text-violet-300">
                <Sparkles className="w-3.5 h-3.5" aria-hidden="true" /> {t('Đọc bằng luật + AI', 'Read by rules + AI')}
              </span>
            )}
          </div>
          <p className="flex flex-wrap items-baseline gap-x-2 text-indigo-700 dark:text-indigo-300">
            <span className="text-5xl sm:text-6xl font-extrabold tracking-tight tabular-nums">{num(forecast.p50_hours)}</span>
            <span className="text-xl sm:text-2xl font-bold">{t('giờ', 'hours')}</span>
          </p>
          <RangeBar low={forecast.p10_hours} mid={forecast.p50_hours} high={forecast.p90_hours} plan={chosen} format={(n) => hours(n)} />
          <p className="text-sm text-slate-700 dark:text-slate-300">
            {t(
              `8/10 kịch bản rơi vào khoảng `,
              `8 in 10 outcomes fall between `,
            )}
            <strong>{hours(forecast.p10_hours)}</strong> – <strong>{hours(forecast.p90_hours)}</strong>.
            {forecast.reference_class_p50 != null && t(
              ` Dự án cùng loại đã làm: khoảng ${hours(forecast.reference_class_p50)}.`,
              ` Finished projects of this type: about ${hours(forecast.reference_class_p50)}.`,
            )}
          </p>
          {pendingScope.length > 0 && (
            <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
              {t('Tổng giờ chưa tính các phần khách chưa chốt.', 'This total excludes work the client has not committed to.')}
            </p>
          )}
        </section>

        <section className="min-w-0 lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-1 gap-3">
          <div className="min-w-0 p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border-2 border-amber-300 dark:border-amber-700">
            <div className="text-xs font-bold uppercase tracking-wide text-amber-800 dark:text-amber-300">{t(`Nên dự trù (${confidence}% chắc chắn)`, `Plan for (${confidence}% of outcomes)`)}</div>
            <div className="mt-1 flex flex-wrap items-baseline gap-x-1.5 text-slate-900 dark:text-white">
              <span className="text-3xl font-extrabold tabular-nums">{num(chosen)}</span>
              <span className="text-base font-bold">{t('giờ', 'hours')}</span>
            </div>
          </div>
          <div className="min-w-0 p-4 rounded-2xl bg-white dark:bg-[#121829] border border-slate-200 dark:border-slate-800">
            <div className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-400">{t('Chi phí', 'Cost')}</div>
            <div className="mt-1 flex flex-wrap items-baseline gap-x-1.5">
              <span className="text-2xl font-extrabold tabular-nums break-all">{costValue}</span>
              {costUnit && <span className="text-sm font-bold text-slate-700 dark:text-slate-300">{costUnit}</span>}
            </div>
          </div>
          <div className="min-w-0 p-4 rounded-2xl bg-white dark:bg-[#121829] border border-slate-200 dark:border-slate-800">
            <div className="text-xs font-bold uppercase tracking-wide text-slate-600 dark:text-slate-400">{t(`Thời gian · ${people} người`, `Time · ${people} people`)}</div>
            <div className="mt-1 flex flex-wrap items-baseline gap-x-1.5">
              <span className="text-sm font-bold text-slate-700 dark:text-slate-300">{t('khoảng', 'about')}</span>
              <span className="text-2xl font-extrabold tabular-nums">{Math.max(1, Math.ceil(weeks))}</span>
              <span className="text-sm font-bold text-slate-700 dark:text-slate-300">{t('tuần', 'weeks')}</span>
            </div>
            {chainLimited && <div className="text-xs text-amber-800 dark:text-amber-300 mt-0.5">{t('Có chuỗi việc phải làm nối tiếp, thêm người không nhanh hơn.', 'Some work must happen in sequence, so more people does not make it faster.')}</div>}
          </div>
        </section>
      </div>

      {/* Where the hours go */}
      {breakdown.length > 0 && (
        <section className={`${card} p-6 space-y-4`}>
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-1">
            <h2 className="text-lg font-bold">{t('Giờ công đi vào đâu', 'Where the hours go')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {t('Phần lớn nhất chiếm ', 'The largest part is ')}
              <strong className="text-slate-900 dark:text-white">{topShare}%</strong>
              {t(' tổng giờ (chưa tính rủi ro)', ' of the hours (before risk)')}
            </p>
          </div>
          <HBarList rows={breakdown} />
          {countedElsewhere.length > 0 && (
            <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
              <p>{t(
                'Những câu này nằm trong giờ ở trên và không được cộng thêm:',
                'These sentences are included in the hours above and are not added again:',
              )}</p>
              <ul className="list-disc pl-5 space-y-1">
                {countedElsewhere.map((r) => (
                  <li key={r.req_id} className="break-words">{r.evidence[0]?.quote ?? r.title}</li>
                ))}
              </ul>
            </div>
          )}
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-400">
            <li className="inline-flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" aria-hidden="true" /> {t('chưa chốt', 'not committed')}
            </li>
            <li className="inline-flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" aria-hidden="true" /> {t('đã rõ', 'clear')}
            </li>
            <li className="inline-flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400" aria-hidden="true" /> {t('việc chung (chuẩn bị, kiểm thử)', 'shared work (setup, testing)')}
            </li>
          </ul>
        </section>
      )}

      {pendingScope.length > 0 && (
        <section className={`${card} p-6 space-y-3`}>
          <h2 className="text-lg font-bold">{t('Chờ khách xác nhận', 'Pending client decision')}</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {t('Những phần này chưa nằm trong giờ và chi phí ở trên. Trả lời Có tại trang Câu hỏi để thêm vào dự toán.',
              'These items are excluded from the hours and cost above. Answer Yes on the Questions page to add them.')}
          </p>
          <ul className="space-y-2 text-sm">
            {pendingScope.map(({ req, question }) => (
              <li key={req.req_id} className="flex justify-between gap-3 border-t border-slate-200 dark:border-slate-800 pt-2">
                <span className="break-words">{req.evidence[0]?.quote ?? req.title}</span>
                <span className="font-bold whitespace-nowrap">+{hours(question?.hours_if_true ?? 0)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Planning controls */}
      <section className={`${card} p-6 space-y-5`}>
        <div>
          <h2 className="text-lg font-bold">{t('Lập kế hoạch', 'Planning')}</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">{t('Càng muốn chắc chắn đủ thời gian, càng cần dự trù nhiều giờ hơn.', 'The more sure you want to be, the more hours you should plan for.')}</p>
        </div>

        {hasChart && (
          <div>
            <svg viewBox={`0 0 800 ${Y_BASE}`} preserveAspectRatio="none" className="w-full h-28 sm:h-36" aria-hidden="true">
              <defs>
                <clipPath id="chosenClip">
                  <rect x="0" y="0" width={xOf(chosen)} height={Y_BASE} />
                </clipPath>
              </defs>
              <path d={area} className="fill-slate-200 dark:fill-slate-800" />
              <path d={area} className="fill-indigo-300/70 dark:fill-indigo-500/50" clipPath="url(#chosenClip)" />
              <path d={line} fill="none" className="stroke-indigo-600 dark:stroke-indigo-300" strokeWidth="2" vectorEffect="non-scaling-stroke" />
              <line
                x1={xOf(forecast.p50_hours)}
                x2={xOf(forecast.p50_hours)}
                y1="0"
                y2={Y_BASE}
                className="stroke-indigo-800 dark:stroke-indigo-200"
                strokeDasharray="4 3"
                strokeWidth="1.5"
                vectorEffect="non-scaling-stroke"
              />
              <line x1={xOf(chosen)} x2={xOf(chosen)} y1="0" y2={Y_BASE} className="stroke-amber-500" strokeWidth="3" vectorEffect="non-scaling-stroke" />
            </svg>
            <div className="relative h-6" aria-hidden="true">
              <span
                className="absolute top-1 -translate-x-1/2 whitespace-nowrap text-xs font-bold tabular-nums text-amber-800 dark:text-amber-300"
                style={{ left: `${Math.min(88, Math.max(12, (xOf(chosen) / 800) * 100))}%` }}
              >
                ▲ {hours(chosen)}
              </span>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <label htmlFor="confidence" className="flex justify-between text-sm font-semibold">
            <span>{t('Mức chắc chắn', 'Confidence')}</span>
            <span className="text-amber-800 dark:text-amber-300">{confidence}%</span>
          </label>
          <input
            id="confidence"
            type="range"
            min={50}
            max={maxPct}
            step={5}
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
            <span>{t('Vừa đủ', 'Tight')}</span>
            <span>{t('Rất an toàn', 'Very safe')}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-slate-50 dark:bg-slate-900">
            <label htmlFor="rate" className="text-slate-700 dark:text-slate-300">
              {t('Đơn giá mỗi giờ', 'Rate per hour')}
            </label>
            <span className="flex items-center gap-1.5 min-w-0">
              <input
                id="rate"
                type="number"
                min={0}
                value={rate[currency]}
                onChange={(e) => setRate({ ...rate, [currency]: Number(e.target.value) || 0 })}
                className="w-28 min-w-0 px-2 py-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0b0f1a] text-right tabular-nums"
              />
              <span role="group" aria-label={t('Đơn vị tiền', 'Currency')} className="flex rounded-lg border border-slate-300 dark:border-slate-700 overflow-hidden">
                {(['VND', 'USD'] as Currency[]).map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setCurrency(c)}
                    aria-pressed={currency === c}
                    className={`px-2.5 py-1.5 text-xs font-bold cursor-pointer ${currency === c ? 'bg-indigo-600 text-white' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                  >
                    {c}
                  </button>
                ))}
              </span>
            </span>
          </div>
          <label htmlFor="people" className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-slate-50 dark:bg-slate-900">
            <span className="text-slate-700 dark:text-slate-300">{t('Số người làm', 'People')}</span>
            <input
              id="people"
              type="number"
              min={1}
              max={20}
              value={people}
              onChange={(e) => setPeople(Math.max(1, Number(e.target.value) || 1))}
              className="w-16 px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0b0f1a] text-right"
            />
          </label>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {notes.length > 0 && (
          <section className={`${card} p-5 space-y-2`}>
            <h2 className="font-bold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              {t('Cần lưu ý', 'Watch out')}
            </h2>
            <ul className="space-y-1.5 list-disc pl-5 text-sm text-slate-700 dark:text-slate-300">
              {notes.map((f) => (
                <li key={f.finding_id}>{f.claim}</li>
              ))}
            </ul>
          </section>
        )}
        <section className={`${card} p-5 space-y-3 ${notes.length ? '' : 'md:col-span-2'}`}>
          <div>
            <h2 className="font-bold">{t('Gửi cho khách hàng', 'Send to the client')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('Theo đúng mức chắc chắn, đơn giá và số người đang chọn.', 'Uses the confidence, rate, and team size selected above.')}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <a
              href={proposalUrl(projectId, { confidence, rate: rate[currency], currency, people, lang })}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm inline-flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" /> {t('Tải báo giá', 'Download the quote')}
            </a>
            <a
              href={wbsCsvUrl(projectId, lang)}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 hover:border-indigo-400 font-bold text-sm inline-flex items-center gap-1.5"
            >
              <FileSpreadsheet className="w-4 h-4" /> {t('Bảng công việc (Excel)', 'Work list (Excel)')}
            </a>
          </div>
        </section>
      </div>

      <details className="text-sm text-slate-600 dark:text-slate-400">
        <summary className="cursor-pointer font-semibold">{t('Con số này được tính thế nào?', 'How was this number calculated?')}</summary>
        <p className="mt-2 leading-relaxed">
          {t(
            'Mỗi công việc được ước tính số giờ ít nhất, thường gặp và nhiều nhất. Hệ thống chạy thử 10.000 kịch bản, trong đó mức chênh lệch giữa dự toán và thực tế được lấy từ dữ liệu thật của hơn 10.000 công việc phần mềm đã làm. Khi bạn nhập giờ thực tế của các dự án đã xong, các dự toán sau sẽ tự điều chỉnh theo từng loại dự án',
            'Each piece of work has a low, typical, and high hour figure. The system runs 10,000 outcomes. The spread between an estimate and the actual hours comes from real data on more than 10,000 finished software tasks. When you enter actual hours from finished projects, later estimates adjust by project type',
          )}
          {forecast.calibration_multiplier !== 1 && t(
            ` (hiện đang nhân ×${forecast.calibration_multiplier.toFixed(2)})`,
            ` (currently multiplied by ×${forecast.calibration_multiplier.toFixed(2)})`,
          )}.
          {version.reader === 'rules+jev'
            ? t(
              ' AI Jev đọc từng câu của mô tả như một người ước lượng lâu năm: đây là loại việc gì, khách đã chốt chưa, và việc này có dễ tốn thời gian hơn vẻ ngoài không. Phần AI đánh giá dễ vượt giờ được gắn cờ để xem kỹ; số giờ chỉ được cộng thêm khi giờ thực tế của chính nhóm bạn cho thấy điều đó (kiểm chứng trên dữ liệu thật cho thấy mức chênh không giống nhau giữa các công ty).',
              ' Jev reads every sentence the way a senior estimator would: what kind of work it is, whether the client has committed, and whether it is likely to take longer than it looks. Clauses the AI marks as likely to overrun are flagged for review. Hours are added only when your own team’s actuals show that (measured on real data, the gap is not the same from one company to another).',
            )
            : t(' Phần đọc mô tả dùng luật nhận diện từ khóa.', ' The brief was read with keyword rules.')}
        </p>
      </details>
    </div>
  );
};
