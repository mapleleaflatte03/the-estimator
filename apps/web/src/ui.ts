export const ROLE_LABELS: Record<string, string> = {
  Backend: 'Máy chủ',
  Frontend: 'Giao diện',
  QA: 'Kiểm thử',
  DevOps: 'Triển khai',
};

export const ROLE_COLORS: Record<string, string> = {
  Backend: 'bg-indigo-600',
  Frontend: 'bg-cyan-500',
  QA: 'bg-emerald-500',
  DevOps: 'bg-purple-500',
};

export const PROJECT_TYPES: { value: string; label: string }[] = [
  { value: 'internal_tool', label: 'Phần mềm quản lý nội bộ' },
  { value: 'api_integration', label: 'Kết nối bán hàng / thương mại điện tử' },
  { value: 'ai_workflow', label: 'Trợ lý AI / chatbot' },
  { value: 'field_service', label: 'Ứng dụng điện thoại / hiện trường' },
  { value: 'custom_software', label: 'Khác' },
];

export const hours = (n: number) => `${Math.round(n).toLocaleString('vi-VN')} giờ`;

/** PERT mean of a three-point estimate, rounded to whole hours. */
export const typicalHours = (o: number, m: number, p: number) => Math.round((o + 4 * m + p) / 6);

export const card = 'rounded-2xl bg-white dark:bg-[#121829] border border-slate-200 dark:border-slate-800 shadow-sm';

export const KIND_LABELS: Record<string, string> = {
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
};

export const HOURS_PER_PERSON_WEEK = 32;
