import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesWorkstation from "../PresalesWorkstation";

const apiMocks = vi.hoisted(() => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      updateProgress: vi.fn(),
    },
    solutions: {
      list: vi.fn(),
      update: vi.fn(),
      create: vi.fn(),
    },
    tenders: {
      list: vi.fn(),
    },
  },
  opportunityApi: {
    list: vi.fn(),
  },
  presaleWorkbenchApi: {
    loadOverview: vi.fn(),
  },
}));

vi.mock("../../services/api", () => apiMocks);

describe("PresalesWorkstation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not replace failed live tickets with demo tasks", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockRejectedValue(new Error("Network Error"));

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Network Error/)).toBeInTheDocument();
    expect(screen.queryByText("新能源电池测试方案")).not.toBeInTheDocument();
    expect(screen.queryByText("汽车电子成本核算")).not.toBeInTheDocument();
  });

  it("loads execution data through the presale workbench aggregate endpoint", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue({
      tickets: {
        items: [
          {
            id: 11,
            ticket_no: "PS-011",
            title: "电池包测试方案",
            ticket_type: "SOLUTION",
            urgency: "URGENT",
            customer_name: "金凯博客户",
            applicant_name: "张销售",
            status: "PROCESSING",
          },
        ],
        total: 1,
      },
      solutions: {
        items: [
          {
            id: 21,
            ticket_id: 11,
            name: "电池包 FCT 方案",
            status: "DRAFT",
            customer_name: "金凯博客户",
            estimated_cost: 180000,
            updated_at: "2026-06-01T00:00:00",
          },
        ],
        total: 1,
      },
      tenders: {
        items: [
          {
            id: 31,
            tender_name: "电池包产线投标",
            customer_name: "金凯博客户",
            result: "PENDING",
            budget_amount: 360000,
          },
        ],
        total: 1,
      },
      opportunities: {
        items: [
          {
            id: 41,
            opp_name: "电池包测试线商机",
            customer_name: "金凯博客户",
            stage: "QUALIFICATION",
            est_amount: 580000,
            probability: 70,
            owner_name: "李销售",
          },
        ],
        total: 1,
      },
      templates: {
        assessment: { items: [], total: 0 },
        technical: { items: [], total: 0 },
      },
      funnel: {
        summary: {},
        health: {},
        conversion: {},
        dwellAlerts: { items: [], total: 0 },
      },
      meta: { failures: [] },
    });

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    expect(await screen.findByText("电池包测试方案")).toBeInTheDocument();
    expect(screen.getByText("电池包 FCT 方案")).toBeInTheDocument();
    expect(screen.getByText("电池包产线投标")).toBeInTheDocument();
    expect(screen.getByText("电池包测试线商机")).toBeInTheDocument();
    expect(apiMocks.presaleWorkbenchApi.loadOverview).toHaveBeenCalledTimes(1);
    expect(apiMocks.presaleApi.tickets.list).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.solutions.list).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.tenders.list).not.toHaveBeenCalled();
    expect(apiMocks.opportunityApi.list).not.toHaveBeenCalled();
  });
});
