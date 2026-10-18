import React, { createContext, useContext, useEffect, useState } from 'react';

export type Lang = 'en' | 'vi';

const STORAGE_KEY = 'parallax_lang';

type Labels = {
  roles: Record<string, string>;
  projectTypes: { value: string; label: string }[];
  kinds: Record<string, string>;
  components: Record<string, string>;
  risks: string[];
};

const VI: Labels = {
  roles: { Backend: 'Máy chủ', Frontend: 'Giao diện', QA: 'Kiểm thử', DevOps: 'Triển khai' },
  projectTypes: [
    { value: 'internal_tool', label: 'Phần mềm quản lý nội bộ' },
    { value: 'api_integration', label: 'Kết nối bán hàng / thương mại điện tử' },
    { value: 'ai_workflow', label: 'Trợ lý AI / chatbot' },
    { value: 'field_service', label: 'Ứng dụng điện thoại / hiện trường' },
    { value: 'custom_software', label: 'Dự án phần mềm khác' },
  ],
  kinds: {
    auth: 'đăng nhập',
    permissions_audit: 'phân quyền & lịch sử thay đổi',
    reporting: 'báo cáo',
    file_export: 'xuất file',
    data_import: 'nhập dữ liệu',
    notification: 'thông báo',
    scheduling: 'lịch & phân công',
    mobile_app: 'ứng dụng điện thoại',
    offline_sync: 'dùng khi mất mạng',
    external_integration: 'kết nối hệ thống khác',
    payment: 'thanh toán',
    ai_assistant: 'AI',
    search: 'tìm kiếm',
    workflow_approval: 'quy trình & duyệt',
    performance: 'chịu tải',
    maps_location: 'bản đồ & vị trí',
    data_management: 'quản lý dữ liệu',
    other: 'khác',
  },
  components: {
    auth: 'đăng nhập', rbac: 'phân quyền', audit: 'lịch sử thay đổi', integration: 'kết nối hệ thống khác',
    reporting: 'báo cáo', export: 'xuất file', import: 'nhập file', migration: 'chuyển dữ liệu cũ',
    notification: 'thông báo', scheduling: 'lịch & phân công', mobile: 'điện thoại', offline: 'dùng khi mất mạng',
    realtime: 'cập nhật tức thời', performance: 'chịu tải', ai: 'AI', rag: 'tìm kiếm tài liệu', search: 'tìm kiếm',
    payment: 'thanh toán', workflow: 'quy trình & trạng thái', files: 'ảnh & file', maps: 'bản đồ',
    widget: 'khung nhúng website', i18n: 'nhiều ngôn ngữ', security: 'bảo mật', crud: 'quản lý dữ liệu',
    generic: 'chưa phân loại', foundation: 'việc chung',
  },
  risks: ['ít rủi ro', 'rủi ro vừa', 'dễ vượt giờ'],
};

const EN: Labels = {
  roles: { Backend: 'Server', Frontend: 'Interface', QA: 'Testing', DevOps: 'Deployment' },
  projectTypes: [
    { value: 'internal_tool', label: 'Internal business software' },
    { value: 'api_integration', label: 'Sales / commerce connection' },
    { value: 'ai_workflow', label: 'AI assistant / chatbot' },
    { value: 'field_service', label: 'Phone / field app' },
    { value: 'custom_software', label: 'Other software project' },
  ],
  kinds: {
    auth: 'sign-in',
    permissions_audit: 'permissions & change history',
    reporting: 'reports',
    file_export: 'file export',
    data_import: 'data import',
    notification: 'notifications',
    scheduling: 'scheduling & assignment',
    mobile_app: 'phone app',
    offline_sync: 'works offline',
    external_integration: 'connection to another system',
    payment: 'payments',
    ai_assistant: 'AI',
    search: 'search',
    workflow_approval: 'workflow & approval',
    performance: 'load',
    maps_location: 'maps & location',
    data_management: 'data management',
    other: 'other',
  },
  components: {
    auth: 'sign-in', rbac: 'permissions', audit: 'change history', integration: 'connection to another system',
    reporting: 'reports', export: 'file export', import: 'file import', migration: 'moving old data',
    notification: 'notifications', scheduling: 'scheduling & assignment', mobile: 'phone', offline: 'works offline',
    realtime: 'live updates', performance: 'load', ai: 'AI', rag: 'document search', search: 'search',
    payment: 'payments', workflow: 'workflow & status', files: 'images & files', maps: 'maps',
    widget: 'website embed', i18n: 'several languages', security: 'security', crud: 'data management',
    generic: 'unclassified', foundation: 'shared work',
  },
  risks: ['low risk', 'medium risk', 'likely to overrun'],
};

type Ctx = { lang: Lang; setLang: (lang: Lang) => void };

const I18nContext = createContext<Ctx>({ lang: 'en', setLang: () => {} });

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem(STORAGE_KEY) === 'vi' ? 'vi' : 'en'));
  const setLang = (next: Lang) => {
    localStorage.setItem(STORAGE_KEY, next);
    setLangState(next);
  };
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return <I18nContext.Provider value={{ lang, setLang }}>{children}</I18nContext.Provider>;
};

export function useI18n() {
  const { lang, setLang } = useContext(I18nContext);
  const labels = lang === 'vi' ? VI : EN;
  const locale = lang === 'vi' ? 'vi-VN' : 'en-US';
  const t = (vi: string, en: string) => (lang === 'en' ? en : vi);
  const hours = (n: number) => `${Math.round(n).toLocaleString(locale)} ${t('giờ', 'hours')}`;
  const hours1 = (n: number) =>
    `${n.toLocaleString(locale, { maximumFractionDigits: 1 })} ${t('giờ', 'hours')}`;
  const num = (n: number, digits = 0) =>
    n.toLocaleString(locale, digits ? { maximumFractionDigits: digits } : { maximumFractionDigits: 0 });
  const pct = (v: unknown, digits = 1) => `${Number(v).toLocaleString(locale, { maximumFractionDigits: digits })}%`;
  return { lang, setLang, locale, t, hours, hours1, num, pct, ...labels };
}
