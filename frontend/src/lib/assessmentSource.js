export function normalizeAssessmentSourceType(sourceType) {
  const value = String(sourceType || "").trim().toLowerCase();
  if (value === "lead" || value === "leads") {
    return "lead";
  }
  if (value === "opportunity" || value === "opportunities") {
    return "opportunity";
  }
  return value;
}

export function isLeadAssessmentSource(sourceType) {
  return normalizeAssessmentSourceType(sourceType) === "lead";
}

export function getAssessmentSourceListPath(sourceType) {
  return isLeadAssessmentSource(sourceType)
    ? "/sales/leads"
    : "/sales/opportunities";
}
