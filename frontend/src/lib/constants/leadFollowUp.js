export const FOLLOW_UP_TYPES = [
  { value: "CALL", label: "电话" },
  { value: "EMAIL", label: "邮件" },
  { value: "VISIT", label: "拜访" },
  { value: "MEETING", label: "会议" },
  { value: "OTHER", label: "其他" },
];

export const LEAD_QUICK_FOLLOW_UP_TEMPLATES = [
  {
    key: "contacted_waiting_quote",
    label: "已联系，待报价",
    shortLabel: "待报价",
    follow_up_type: "CALL",
    content: "已与客户取得联系，已确认初步需求，待发送报价单。",
    next_action: "整理需求并发送报价单",
  },
  {
    key: "quote_sent_waiting_feedback",
    label: "已报价，待反馈",
    shortLabel: "待反馈",
    follow_up_type: "EMAIL",
    content: "报价资料已发送给客户，待客户内部评审反馈。",
    next_action: "回访客户确认报价反馈",
  },
  {
    key: "need_technical_support",
    label: "需技术支援",
    shortLabel: "技术支援",
    follow_up_type: "MEETING",
    content: "客户提出技术细节问题，需安排售前工程师协同支持。",
    next_action: "协调售前工程师并安排技术沟通",
  },
  {
    key: "onsite_visit_planned",
    label: "待拜访",
    shortLabel: "约拜访",
    follow_up_type: "VISIT",
    content: "已与客户初步沟通，计划安排现场拜访进一步澄清需求。",
    next_action: "确认拜访时间与参与人员",
  },
];
