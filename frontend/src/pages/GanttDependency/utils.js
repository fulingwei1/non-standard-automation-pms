export function extractPayload(response) {
  return response?.formatted ?? response?.data?.data ?? response?.data ?? response;
}

export function normalizeProjects(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  if (Array.isArray(payload?.list)) {
    return payload.list;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items;
  }
  return [];
}

export function parseDate(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

export function diffDays(start, end) {
  const ms = end.getTime() - start.getTime();
  return Math.round(ms / (1000 * 60 * 60 * 24));
}

export function getTaskBarPlacement(task, timelineRange) {
  const start = parseDate(task.plan_start) || timelineRange.startDate;
  const rawEnd = parseDate(task.plan_end) || start;
  const end = rawEnd < start ? start : rawEnd;
  const startOffset = Math.max(0, diffDays(timelineRange.startDate, start));
  const duration = Math.max(1, diffDays(start, end) + 1);
  const leftPct = (startOffset / timelineRange.totalDays) * 100;
  const widthPct = Math.max((duration / timelineRange.totalDays) * 100, 1.5);
  return {
    leftPct,
    widthPct,
    endPct: Math.min(leftPct + widthPct, 100),
  };
}
