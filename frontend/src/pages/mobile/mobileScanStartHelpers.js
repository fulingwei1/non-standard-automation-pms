export const OFFLINE_START_QUEUE_KEY = "mobile.scanStart.offlineStartQueue.v1";

const readStorageQueue = (storage) => {
  try {
    const raw = storage?.getItem?.(OFFLINE_START_QUEUE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_error) {
    return [];
  }
};

const writeStorageQueue = (storage, queue) => {
  if (!storage) {
    return;
  }
  if (queue.length === 0) {
    storage.removeItem?.(OFFLINE_START_QUEUE_KEY);
    return;
  }
  storage.setItem?.(OFFLINE_START_QUEUE_KEY, JSON.stringify(queue));
};

export const readOfflineStartQueue = (storage = window.localStorage) =>
  readStorageQueue(storage);

export const enqueueOfflineStartWorkReport = (
  workOrder,
  reportNote = "",
  storage = window.localStorage,
  now = () => new Date(),
) => {
  const queuedAt = now().toISOString();
  const item = {
    client_id: `offline-start-${workOrder.id}-${queuedAt}`,
    work_order_id: workOrder.id,
    work_order_no: workOrder.work_order_no,
    task_name: workOrder.task_name,
    report_note: reportNote,
    queued_at: queuedAt,
  };
  const queue = readStorageQueue(storage);
  const alreadyQueued = queue.some((queued) => queued.client_id === item.client_id);
  writeStorageQueue(storage, alreadyQueued ? queue : [...queue, item]);
  return item;
};

export const flushOfflineStartWorkReports = async (
  startApi,
  storage = window.localStorage,
) => {
  const queue = readStorageQueue(storage);
  const remaining = [];
  let synced = 0;

  for (const item of queue) {
    try {
      await startApi({
        work_order_id: item.work_order_id,
        report_note: item.report_note || "",
        offline_client_id: item.client_id,
        offline_queued_at: item.queued_at,
      });
      synced += 1;
    } catch (_error) {
      remaining.push(item);
    }
  }

  writeStorageQueue(storage, remaining);
  return {
    attempted: queue.length,
    synced,
    remaining: remaining.length,
  };
};

export const isLikelyOfflineStartError = (
  error,
  navigatorLike = window.navigator,
) => {
  if (navigatorLike?.onLine === false) {
    return true;
  }
  if (error?.code === "ERR_NETWORK" || error?.message === "Network Error") {
    return true;
  }
  return !error?.response;
};

export const hasBarcodeDetector = (windowLike = window) =>
  typeof windowLike?.BarcodeDetector === "function";

export const isIOSUserAgent = (navigatorLike = window.navigator) => {
  const userAgent = navigatorLike?.userAgent || "";
  const platform = navigatorLike?.platform || "";
  return /iPad|iPhone|iPod/i.test(userAgent) || (
    /Mac/i.test(platform) && navigatorLike?.maxTouchPoints > 1
  );
};

export const getCameraScanUnavailableMessage = (
  windowLike = window,
  navigatorLike = window.navigator,
) => {
  if (hasBarcodeDetector(windowLike)) {
    return "";
  }
  if (isIOSUserAgent(navigatorLike)) {
    return "iOS 浏览器暂不支持页面内自动识别二维码，请用系统相机打开工单码，或在此页手动输入/粘贴工单号。";
  }
  return "当前浏览器不支持页面内自动扫码，请手动输入/粘贴工单号。";
};
