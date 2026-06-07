export function parseAssessmentJsonField(value, fallback) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  if (typeof value !== "string") {
    return value;
  }

  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

export function parseAssessmentObject(value, fallback = null) {
  const parsed = parseAssessmentJsonField(value, fallback);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    return fallback;
  }
  return parsed;
}

export function parseAssessmentList(value) {
  const parsed = parseAssessmentJsonField(value, []);
  return Array.isArray(parsed) ? parsed : [];
}
