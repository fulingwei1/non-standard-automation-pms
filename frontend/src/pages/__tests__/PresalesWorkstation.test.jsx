import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesWorkstation from "../PresalesWorkstation";

const apiMocks = vi.hoisted(() => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      updateProgress: vi.fn(),
      complete: vi.fn(),
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
    vi.spyOn(window, "alert").mockImplementation(() => {});
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

  it("completes the presale ticket when saving feasibility assessment", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue({
      tickets: {
        items: [
          {
            id: 51,
            ticket_no: "PS-051",
            title: "电池包可行性评估",
            ticket_type: "FEASIBILITY_ASSESSMENT",
            urgency: "NORMAL",
            customer_name: "金凯博客户",
            applicant_name: "张销售",
            status: "PROCESSING",
            opportunity_id: 41,
            description: "客户要求新增检测站",
          },
        ],
        total: 1,
      },
      solutions: { items: [], total: 0 },
      tenders: { items: [], total: 0 },
      opportunities: { items: [], total: 0 },
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
    apiMocks.presaleApi.tickets.update.mockResolvedValue({ data: { id: 51 } });
    apiMocks.presaleApi.tickets.complete.mockResolvedValue({ data: { id: 51 } });
    apiMocks.presaleApi.tickets.updateProgress.mockResolvedValue({ data: { id: 51 } });

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText("电池包可行性评估"));
    fireEvent.click(screen.getAllByText("5 - 优秀")[0]);

    const textboxes = screen.getAllByRole("textbox");
    fireEvent.change(textboxes[0], { target: { value: "建议进入报价" } });
    fireEvent.change(textboxes[1], { target: { value: "周期风险可控" } });
    fireEvent.change(textboxes[2], { target: { value: "采用标准测试平台" } });

    fireEvent.click(screen.getByRole("button", { name: /提交评估/ }));

    await waitFor(() => {
      expect(apiMocks.presaleApi.tickets.complete).toHaveBeenCalledWith(51, {
        completion_note: expect.stringContaining("可行性评估已完成"),
      });
    });
    expect(apiMocks.presaleApi.tickets.complete.mock.calls[0][1].completion_note)
      .toContain("建议进入报价");
    expect(apiMocks.presaleApi.tickets.updateProgress).not.toHaveBeenCalled();
  });

  it("completes the presale ticket when submitting cost estimation", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue({
      tickets: {
        items: [
          {
            id: 61,
            ticket_no: "PS-061",
            title: "电池包成本核算",
            ticket_type: "COST_ESTIMATE",
            urgency: "NORMAL",
            customer_id: 7,
            customer_name: "金凯博客户",
            applicant_name: "张销售",
            status: "PROCESSING",
            opportunity_id: 41,
            description: "核算夹治具和电气成本",
          },
        ],
        total: 1,
      },
      solutions: { items: [], total: 0 },
      tenders: { items: [], total: 0 },
      opportunities: { items: [], total: 0 },
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
    apiMocks.presaleApi.solutions.list.mockResolvedValue({ data: { items: [], total: 0 } });
    apiMocks.presaleApi.tickets.get.mockResolvedValue({
      data: {
        id: 61,
        customer_id: 7,
        opportunity_id: 41,
      },
    });
    apiMocks.presaleApi.solutions.create.mockResolvedValue({ data: { id: 71 } });
    apiMocks.presaleApi.tickets.complete.mockResolvedValue({ data: { id: 61 } });
    apiMocks.presaleApi.tickets.updateProgress.mockResolvedValue({ data: { id: 61 } });

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText("电池包成本核算"));
    fireEvent.change(screen.getAllByPlaceholderText("0.00")[0], {
      target: { value: "12" },
    });
    fireEvent.click(screen.getByRole("button", { name: /提交成本估算/ }));

    await waitFor(() => {
      expect(apiMocks.presaleApi.tickets.complete).toHaveBeenCalledWith(61, {
        completion_note: expect.stringContaining("成本估算已完成"),
      });
    });
    expect(apiMocks.presaleApi.tickets.complete.mock.calls[0][1].completion_note)
      .toContain("建议报价");
    expect(apiMocks.presaleApi.tickets.updateProgress).not.toHaveBeenCalled();
  });
});
