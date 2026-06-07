import { describe, expect, it } from "vitest";
import {
  buildSalesFunnelDrilldownPath,
  formatDateParam,
  getDateRangeForTimeRange,
} from "./drilldown";

describe("sales funnel drilldown", () => {
  it("builds canonical quote detail drilldown URL with active filters", () => {
    const path = buildSalesFunnelDrilldownPath("quotes", {
      startDate: new Date("2026-06-01T00:00:00Z"),
      endDate: new Date("2026-06-30T00:00:00Z"),
      ownerId: 12,
      customerId: 34,
      industry: "ICT",
    });

    expect(path).toBe(
      "/sales/quotes?source=sales_funnel&funnel_stage=quotes&start_date=2026-06-01&end_date=2026-06-30&owner_id=12&customer_id=34&keyword=ICT",
    );
  });

  it("routes lead and opportunity drilldowns back into the opportunity center tabs", () => {
    expect(buildSalesFunnelDrilldownPath("leads", {})).toBe(
      "/sales/opportunity-center?tab=leads&source=sales_funnel&funnel_stage=leads",
    );
    expect(buildSalesFunnelDrilldownPath("opportunities", {})).toBe(
      "/sales/opportunity-center?tab=opportunities&source=sales_funnel&funnel_stage=opportunities",
    );
  });

  it("returns null for unknown stages instead of navigating to a dead page", () => {
    expect(buildSalesFunnelDrilldownPath("unknown")).toBeNull();
  });

  it("calculates quarter date range", () => {
    const { startDate, endDate } = getDateRangeForTimeRange(
      "quarter",
      new Date("2026-06-07T12:00:00Z"),
    );

    expect(formatDateParam(startDate)).toBe("2026-04-01");
    expect(formatDateParam(endDate)).toBe("2026-06-30");
  });
});
