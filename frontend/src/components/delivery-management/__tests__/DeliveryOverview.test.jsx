import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DeliveryOverview from "../DeliveryOverview";

vi.mock("../../administrative/StatisticsCharts", () => ({
  MonthlyTrendChart: () => <div data-testid="monthly-trend-chart" />,
}));

describe("DeliveryOverview", () => {
  it("renders zero delivered count as 0 instead of unknown", () => {
    render(
      <DeliveryOverview
        data={[
          { status: "pending", priority: "normal" },
          { status: "preparing", priority: "normal" },
        ]}
        statistics={{ on_time_shipping_rate: 0 }}
      />,
    );

    expect(screen.queryByText("unknown")).not.toBeInTheDocument();
    expect(screen.getByText("已送达 0 / 2（取消 0）")).toBeInTheDocument();
  });
});
