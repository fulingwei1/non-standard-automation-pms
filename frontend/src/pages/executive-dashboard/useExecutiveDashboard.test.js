import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { formatCurrency } from "../../lib/utils";
import { reportCenterApi, salesStatisticsApi } from "../../services/api";
import { useExecutiveDashboard } from "./useExecutiveDashboard";

vi.mock("../../services/api", () => ({
  reportCenterApi: {
    getExecutiveDashboard: vi.fn(),
    getDeliveryRate: vi.fn(),
    getUtilization: vi.fn(),
    getHealthDistribution: vi.fn(),
    exportReport: vi.fn(),
  },
  salesStatisticsApi: {
    funnel: vi.fn(),
  },
}));

describe("useExecutiveDashboard RPT-11 KPI cards", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reportCenterApi.getExecutiveDashboard.mockResolvedValue({ data: { data: {} } });
    reportCenterApi.getDeliveryRate.mockResolvedValue({ data: [] });
    reportCenterApi.getUtilization.mockResolvedValue({ data: [] });
    reportCenterApi.getHealthDistribution.mockResolvedValue({ data: {} });
    salesStatisticsApi.funnel.mockResolvedValue({ data: { data: {} } });
  });

  it("uses real revenue and gross profit without Q1 target caps", async () => {
    reportCenterApi.getExecutiveDashboard.mockResolvedValue({
      data: {
        data: {
          summary: {
            total_contract_amount: 80_000_000,
            total_actual_cost: 20_000_000,
            active_projects: 5,
          },
          monthly: {},
          health_distribution: {},
        },
      },
    });

    const { result } = renderHook(() => useExecutiveDashboard());

    await waitFor(() => expect(result.current.loading).toBe(false));

    const revenueCard = result.current.kpiCards.find((card) => card.title === "总营收");
    const grossProfitCard = result.current.kpiCards.find((card) => card.title === "项目毛利");

    expect(revenueCard.value).toBe(formatCurrency(80_000_000));
    expect(revenueCard.change).toContain("达成50.0%");
    expect(revenueCard.subText).toBe("2026目标对比");

    expect(grossProfitCard.value).toBe(formatCurrency(60_000_000));
    expect(grossProfitCard.change).toContain("达成400.0%");
    expect(grossProfitCard.subText).toBe("合同额减实际成本");
    expect(result.current.kpiCards.some((card) => card.title === "净利润")).toBe(false);
  });

  it("binds project and delivery KPIs to available dashboard data instead of missing fields", async () => {
    reportCenterApi.getExecutiveDashboard.mockResolvedValue({
      data: {
        data: {
          summary: {
            total_projects: 12,
            active_projects: 7,
          },
          monthly: {},
          health_distribution: {},
        },
      },
    });
    reportCenterApi.getDeliveryRate.mockResolvedValue({
      data: {
        data: {
          on_time_rate: 87.5,
          on_time_projects: 7,
          total_projects: 8,
        },
      },
    });

    const { result } = renderHook(() => useExecutiveDashboard());

    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() =>
      expect(result.current.deliveryData[0]).toMatchObject({
        rate: 87.5,
        on_time_projects: 7,
        total_projects: 8,
      })
    );

    const projectCard = result.current.kpiCards.find((card) => card.title === "活跃项目");
    const deliveryCard = result.current.kpiCards.find((card) => card.title === "交付准时率");

    expect(projectCard.value).toBe(7);
    expect(projectCard.change).toBe("12");
    expect(projectCard.subText).toBe("项目总数");

    expect(deliveryCard.value).toBe("87.5%");
    expect(deliveryCard.change).toBe("7/8");
    expect(deliveryCard.subText).toBe("按期/总数");
  });

  it("hydrates health, cost, and sales funnel datasets from real API payloads", async () => {
    reportCenterApi.getExecutiveDashboard.mockResolvedValue({
      data: {
        data: {
          summary: {
            total_budget: 100_000_000,
            total_actual_cost: 60_000_000,
          },
          monthly: {},
          health_distribution: {},
        },
      },
    });
    reportCenterApi.getHealthDistribution.mockResolvedValue({
      data: {
        data: {
          H1: 4,
          H2: 2,
        },
      },
    });
    salesStatisticsApi.funnel.mockResolvedValue({
      data: {
        data: {
          leads: 10,
          opportunities: 6,
          quotes: 3,
          contracts: 1,
        },
      },
    });

    const { result } = renderHook(() => useExecutiveDashboard());

    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() => expect(result.current.healthData).toEqual({ H1: 4, H2: 2 }));

    expect(result.current.costData).toEqual([
      { category: "已用预算", amount: 60_000_000 },
      { category: "剩余预算", amount: 40_000_000 },
    ]);
    expect(result.current.salesFunnelData).toEqual([
      { stage: "线索", value: 10 },
      { stage: "商机", value: 6 },
      { stage: "报价", value: 3 },
      { stage: "合同", value: 1 },
    ]);
  });
});
