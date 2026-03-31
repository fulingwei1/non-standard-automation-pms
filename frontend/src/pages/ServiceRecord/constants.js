export const serviceTypeConfigs = {
    installation: { label: '安装调试', icon: 'Wrench', color: 'bg-blue-500' },
    repair: { label: '维修', icon: 'Tool', color: 'bg-amber-500' },
    maintenance: { label: '保养', icon: 'Settings', color: 'bg-emerald-500' },
    training: { label: '培训', icon: 'GraduationCap', color: 'bg-purple-500' },
    consultation: { label: '咨询', icon: 'MessageSquare', color: 'bg-cyan-500' },
};

export const serviceStatusConfigs = {
    pending: { label: '待处理', color: 'bg-slate-500' },
    scheduled: { label: '已排期', color: 'bg-blue-500' },
    in_progress: { label: '进行中', color: 'bg-amber-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};

export const INITIAL_FORM_DATA = {
  service_type: "CONSULTATION",
  project_name: "",
  customer_name: "",
  service_location: "",
  service_date: "",
  service_start_time: "",
  service_end_time: "",
  service_engineer: "",
  customer_contact: "",
  customer_phone: "",
  service_content: "",
  service_result: "",
  photos: [],
};
