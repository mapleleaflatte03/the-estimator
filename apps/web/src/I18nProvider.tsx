import React, { useEffect, useState } from 'react';
import { I18nContext, type Lang } from './i18n-context';

const STORAGE_KEY = 'parallax_lang';

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Lang>(() => {
    try { return localStorage.getItem(STORAGE_KEY) === 'vi' ? 'vi' : 'en'; } catch { return 'en'; }
  });
  const setLang = (next: Lang) => {
    try { localStorage.setItem(STORAGE_KEY, next); } catch { /* tab-local only */ }
    setLangState(next);
  };
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return <I18nContext.Provider value={{ lang, setLang }}>{children}</I18nContext.Provider>;
};
