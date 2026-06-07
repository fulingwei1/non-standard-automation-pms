const STAGE_ROUTE_MAP = {
  leads: { path: "/sales/opportunity-center", tab: "leads" },
  opportunities: { path: "/sales/opportunity-center", tab: "opportunities" },
  quotes: { path: "/sales/quotes" },
  contracts: { path: "/sales/contracts" },
};

export function getDateRangeForTimeRange(timeRange, now = new Date()) {
  if (timeRange === "quarter") {
    const quarter = Math.floor(now.getMonth() / 3);
    return {
      startDate: new Date(now.getFullYear(), quarter * 3, 1),
      endDate: new Date(now.getFullYear(), (quarter + 1) * 3, 0),
    };
  }

  if (timeRange === "year") {
    return {
      startDate: new Date(now.getFullYear(), 0, 1),
      endDate: new Date(now.getFullYear(), 11, 31),
    };
  }

  return {
    startDate: new Date(now.getFullYear(), now.getMonth(), 1),
    endDate: new Date(now.getFullYear(), now.getMonth() + 1, 0),
  };
}

export function formatDateParam(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function buildSalesFunnelDrilldownPath(stage, filters = {}) {
  const route = STAGE_ROUTE_MAP[stage];
  if (!route) {
    return null;
  }

  const params = new URLSearchParams();
  if (route.tab) {
    params.set("tab", route.tab);
  }
  params.set("source", "sales_funnel");
  params.set("funnel_stage", stage);

  if (filters.startDate) {
    params.set("start_date", formatDateParam(filters.startDate));
  }
  if (filters.endDate) {
    params.set("end_date", formatDateParam(filters.endDate));
  }
  if (filters.ownerId) {
    params.set("owner_id", String(filters.ownerId));
  }
  if (filters.customerId) {
    params.set("customer_id", String(filters.customerId));
  }
  if (filters.industry) {
    params.set("keyword", String(filters.industry));
  }

  return `${route.path}?${params.toString()}`;
}
