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

function appendContextParam(params, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    params.set(key, String(value));
  }
}

function getFirstValue(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

export function buildTechnicalAssessmentPath(sourceType, sourceId, context = {}) {
  const normalizedType =
    String(sourceType || "").toLowerCase() === "opportunity"
      ? "opportunity"
      : "lead";
  const params = new URLSearchParams();
  appendContextParam(
    params,
    "assessment_id",
    getFirstValue(context.assessmentId, context.assessment_id),
  );
  appendContextParam(
    params,
    "ticket_id",
    getFirstValue(
      context.presaleTicketId,
      context.presale_ticket_id,
      context.ticketId,
      context.ticket_id,
    ),
  );
  if (normalizedType === "opportunity") {
    appendContextParam(params, "lead_id", getFirstValue(context.leadId, context.lead_id));
  }
  appendContextParam(params, "project_id", getFirstValue(context.projectId, context.project_id));

  const query = params.toString();
  return `/sales/assessments/${normalizedType}/${sourceId}${query ? `?${query}` : ""}`;
}
