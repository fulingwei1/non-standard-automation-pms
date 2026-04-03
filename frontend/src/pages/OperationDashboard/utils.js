export const formatTimeAgo = (value) => {
  if (!value) { return ""; }
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) { return value; }
  const diff = Date.now() - target.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) { return "刚刚"; }
  if (diff < hour) { return `${Math.max(1, Math.floor(diff / minute))}分钟前`; }
  if (diff < day) { return `${Math.floor(diff / hour)}小时前`; }
  if (diff < 30 * day) { return `${Math.floor(diff / day)}天前`; }
  return target.toLocaleDateString("zh-CN");
};

export const formatAmountInWan = (value) => {
  const amount = Number(value || 0);
  if (amount <= 0) { return "¥0"; }
  const wan = amount / 10000;
  if (wan >= 1) {
    return `¥${wan.toFixed(wan >= 100 ? 0 : 1)}万`;
  }
  return `¥${amount.toFixed(2)}`;
};

export const buildDateRange = (range) => {
  const end = new Date();
  const start = new Date(end);
  const days = range === "week" ? 7 : range === "quarter" ? 90 : 30;
  start.setDate(end.getDate() - days + 1);
  const toISODate = (date) => date.toISOString().slice(0, 10);
  return { start_date: toISODate(start), end_date: toISODate(end) };
};

export const buildMonthlyTrend = (projects, months = 6) => {
  const now = new Date();
  const buckets = [];
  for (let i = months - 1; i >= 0; i -= 1) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    buckets.push({ key, label: `${date.getMonth() + 1}月`, amount: 0 });
  }
  const bucketMap = new Map((buckets || []).map((bucket) => [bucket.key, bucket]));
  (projects || []).forEach((project) => {
    const dateValue = project.planned_end_date || project.contract_date;
    if (!dateValue) { return; }
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) { return; }
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const bucket = bucketMap.get(key);
    if (bucket) {
      bucket.amount += Number(project.contract_amount || 0);
    }
  });
  return (buckets || []).map((bucket) => ({
    month: bucket.label,
    revenue: Math.round(bucket.amount / 10000),
  }));
};
