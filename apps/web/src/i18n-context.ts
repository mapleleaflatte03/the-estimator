import { createContext } from 'react';

export type Lang = 'en' | 'vi';
export const I18nContext = createContext<{ lang: Lang; setLang: (lang: Lang) => void }>({
  lang: 'en', setLang: () => {},
});
