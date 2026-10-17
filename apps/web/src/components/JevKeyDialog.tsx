import React, { useState } from 'react';
import { KeyRound, X } from 'lucide-react';
import { visitorKey } from '../api';
import { useI18n } from '../i18n';

interface JevKeyDialogProps {
  onClose: () => void;
  reason?: string | null;
}

export const JevKeyDialog: React.FC<JevKeyDialogProps> = ({ onClose, reason }) => {
  const { t } = useI18n();
  const [value, setValue] = useState(visitorKey.get());
  const save = (e: React.FormEvent) => {
    e.preventDefault();
    visitorKey.set(value);
    onClose();
  };
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="jev-key-title" className="fixed inset-0 z-[60] bg-slate-900/50 flex items-center justify-center p-4">
      <form onSubmit={save} className="w-full max-w-lg rounded-2xl bg-white dark:bg-[#121829] border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <h2 id="jev-key-title" className="text-lg font-bold flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-violet-600" /> {t('Khóa AI Jev của bạn', 'Your Jev key')}
          </h2>
          <button type="button" onClick={onClose} aria-label={t('Đóng', 'Close')} className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>
        {reason && (
          <p className="text-sm p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-950 dark:text-amber-100">
            {reason}
          </p>
        )}
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {t(
            'Mỗi câu của mô tả đều được AI Jev đọc trước khi tính dự toán. Bạn có thể dùng khóa của riêng mình (jevstation.com hoặc TypeSafe). Khóa chỉ được lưu trong tab trình duyệt này, gửi kèm khi đọc mô tả, và máy chủ không lưu lại.',
            'Jev reads every sentence of the brief before an estimate is produced. You can use your own key (jevstation.com or TypeSafe). The key stays in this browser tab, is sent only when a brief is read, and is not stored on the server.',
          )}
        </p>
        <input
          type="password"
          autoComplete="off"
          aria-label={t('Khóa Jev', 'Jev key')}
          placeholder={t('Dán khóa API Jev', 'Paste a Jev API key')}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 font-mono text-sm"
        />
        <div className="flex flex-wrap justify-end gap-2">
          {visitorKey.get() && (
            <button
              type="button"
              onClick={() => {
                visitorKey.set('');
                onClose();
              }}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 font-bold text-sm cursor-pointer"
            >
              {t('Bỏ khóa', 'Remove key')}
            </button>
          )}
          <button type="submit" className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-sm cursor-pointer">
            {t('Lưu cho phiên này', 'Save for this session')}
          </button>
        </div>
      </form>
    </div>
  );
};
