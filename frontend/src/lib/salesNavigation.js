export const SALES_WORKSTATION_PATH = "/sales/workstation";
export const SALES_OPPORTUNITY_CENTER_PATH = "/sales/opportunity-center";

const listTabs = {
  customers: "customers",
  leads: "leads",
  opportunities: "opportunities",
};

export function buildSalesOpportunityCenterPath(tab = "opportunities", params = {}) {
  const searchParams = new URLSearchParams();
  const normalizedTab = listTabs[tab] || listTabs.opportunities;
  searchParams.set("tab", normalizedTab);

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    searchParams.set(key, String(value));
  });

  return `${SALES_OPPORTUNITY_CENTER_PATH}?${searchParams.toString()}`;
}

export const SALES_CUSTOMER_LIST_PATH = buildSalesOpportunityCenterPath("customers");
export const SALES_LEAD_LIST_PATH = buildSalesOpportunityCenterPath("leads");
export const SALES_OPPORTUNITY_LIST_PATH =
  buildSalesOpportunityCenterPath("opportunities");

export function buildTechnicalAssessmentPath(sourceType, sourceId) {
  const normalizedType =
    String(sourceType || "").toLowerCase() === "opportunity"
      ? "opportunity"
      : "lead";
  return `/sales/assessments/${normalizedType}/${sourceId}`;
}
