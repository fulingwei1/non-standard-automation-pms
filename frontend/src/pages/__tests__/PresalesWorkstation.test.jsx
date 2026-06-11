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
  technicalAssessmentApi: {
    applyForLead: vi.fn(),
    applyForOpportunity: vi.fn(),
    evaluate: vi.fn(),
  },
}));

vi.mock("../../services/api", () => apiMocks);

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

function createOverview(overrides = {}) {
  return {
    tickets: { items: [], total: 0 },
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
    ...overrides,
  };
}

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

  it("preserves upstream support context in execution workbench technical links", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue(createOverview());

    render(
      <MemoryRouter
        initialEntries={[
          "/presales/workbench/execution?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
        ]}
      >
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("link", { name: "新建方案" })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: "新建调研" })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=surveys&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看全部/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /方案中心/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(
      screen
        .getAllByRole("link", { name: "全部" })
        .some(
          (link) =>
            link.getAttribute("href") ===
            "/presales/technical-solutions?tab=bids&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
        ),
    ).toBe(true);
    expect(screen.getByRole("link", { name: "上传文档" })).toHaveAttribute(
      "href",
      "/documents",
    );
    expect(screen.getByRole("link", { name: "知识库" })).toHaveAttribute(
      "href",
      "/knowledge-base",
    );
  });

  it("saves opportunity feasibility assessment through the formal technical assessment flow", async () => {
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
    apiMocks.technicalAssessmentApi.applyForOpportunity.mockResolvedValue({
      data: { data: { assessment_id: 901 } },
    });
    apiMocks.technicalAssessmentApi.evaluate.mockResolvedValue({
      data: { id: 901, status: "COMPLETED" },
    });
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
      expect(apiMocks.technicalAssessmentApi.evaluate).toHaveBeenCalled();
    });
    expect(apiMocks.technicalAssessmentApi.applyForOpportunity).toHaveBeenCalledWith(41, {
      presale_ticket_id: 51,
    });
    expect(apiMocks.technicalAssessmentApi.evaluate).toHaveBeenCalledWith(901, {
      requirement_data: expect.objectContaining({
        source_type: "OPPORTUNITY",
        source_id: 41,
        presale_ticket_id: 51,
        task_title: "电池包可行性评估",
        recommendation: "建议进入报价",
        risk_analysis: "周期风险可控",
        technical_notes: "采用标准测试平台",
      }),
      enable_ai: false,
    });
    expect(apiMocks.presaleApi.tickets.update).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.tickets.complete).not.toHaveBeenCalled();
    expect(apiMocks.technicalAssessmentApi.applyForLead).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.tickets.updateProgress).not.toHaveBeenCalled();
  });

  it("saves lead-stage feasibility assessment through the formal technical assessment flow", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue({
      tickets: {
        items: [
          {
            id: 52,
            ticket_no: "PS-052",
            title: "线索阶段可行性评估",
            ticket_type: "FEASIBILITY_ASSESSMENT",
            urgency: "NORMAL",
            customer_name: "线索客户",
            applicant_name: "张销售",
            status: "PROCESSING",
            lead_id: 2026,
            description: "客户还未转商机，先判断技术路线",
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
    apiMocks.technicalAssessmentApi.applyForLead.mockResolvedValue({
      data: { data: { assessment_id: 902 } },
    });
    apiMocks.technicalAssessmentApi.evaluate.mockResolvedValue({
      data: { id: 902, status: "COMPLETED" },
    });

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText("线索阶段可行性评估"));
    fireEvent.click(screen.getAllByText("5 - 优秀")[0]);

    const textboxes = screen.getAllByRole("textbox");
    fireEvent.change(textboxes[0], { target: { value: "建议继续需求调研" } });
    fireEvent.change(textboxes[1], { target: { value: "样品风险待确认" } });
    fireEvent.change(textboxes[2], { target: { value: "先按标准平台预研" } });

    fireEvent.click(screen.getByRole("button", { name: /提交评估/ }));

    await waitFor(() => {
      expect(apiMocks.technicalAssessmentApi.evaluate).toHaveBeenCalled();
    });
    expect(apiMocks.technicalAssessmentApi.applyForLead).toHaveBeenCalledWith(2026, {
      presale_ticket_id: 52,
    });
    expect(apiMocks.technicalAssessmentApi.evaluate).toHaveBeenCalledWith(902, {
      requirement_data: expect.objectContaining({
        source_type: "LEAD",
        source_id: 2026,
        presale_ticket_id: 52,
        task_title: "线索阶段可行性评估",
        recommendation: "建议继续需求调研",
      }),
      enable_ai: false,
    });
    expect(apiMocks.presaleApi.tickets.update).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.tickets.complete).not.toHaveBeenCalled();
    expect(apiMocks.technicalAssessmentApi.applyForOpportunity).not.toHaveBeenCalled();
  });

  it("creates the cost baseline with project context when submitting cost estimation", async () => {
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
            project_id: 91,
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
        project_id: 91,
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
    expect(apiMocks.presaleApi.solutions.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "电池包成本核算",
        ticket_id: 61,
        opportunity_id: 41,
        customer_id: 7,
        project_id: 91,
        estimated_cost: 120000,
      }),
    );
    expect(apiMocks.presaleApi.tickets.complete.mock.calls[0][1].completion_note)
      .toContain("建议报价");
    expect(apiMocks.presaleApi.tickets.updateProgress).not.toHaveBeenCalled();
  });

  it("keeps task context when writing cost baseline back to an existing solution", async () => {
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
            project_id: 91,
            description: "已有方案补充成本基线",
          },
        ],
        total: 1,
      },
      solutions: {
        items: [
          {
            id: 71,
            ticket_id: 61,
            name: "电池包 FCT 方案",
            status: "DRAFT",
            updated_at: "2026-06-01T00:00:00",
          },
        ],
        total: 1,
      },
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
    apiMocks.presaleApi.solutions.update.mockResolvedValue({ data: { id: 71 } });
    apiMocks.presaleApi.tickets.complete.mockResolvedValue({ data: { id: 61 } });

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
      expect(apiMocks.presaleApi.solutions.update).toHaveBeenCalledWith(71, {
        ticket_id: 61,
        customer_id: 7,
        opportunity_id: 41,
        project_id: 91,
        estimated_cost: 120000,
        suggested_price: 156000,
        cost_breakdown: {
          mechanical: 120000,
          electrical: 0,
          software: 0,
          standard: 0,
          labor: 0,
          other: 0,
          notes: "",
        },
      });
    });
    expect(apiMocks.presaleApi.solutions.create).not.toHaveBeenCalled();
    expect(apiMocks.presaleApi.tickets.get).not.toHaveBeenCalled();
  });

  it("creates the cost baseline for a lead-stage cost ticket without opportunity context", async () => {
    apiMocks.presaleWorkbenchApi.loadOverview.mockResolvedValue({
      tickets: {
        items: [
          {
            id: 62,
            ticket_no: "PS-062",
            title: "线索阶段成本核算",
            ticket_type: "COST_ESTIMATE",
            urgency: "NORMAL",
            customer_id: 8,
            customer_name: "线索客户",
            applicant_name: "张销售",
            status: "PROCESSING",
            lead_id: 2026,
            description: "还没有转商机，先核算夹治具成本",
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
        id: 62,
        customer_id: 8,
        lead_id: 2026,
      },
    });
    apiMocks.presaleApi.solutions.create.mockResolvedValue({ data: { id: 72 } });
    apiMocks.presaleApi.tickets.complete.mockResolvedValue({ data: { id: 62 } });
    apiMocks.presaleApi.tickets.updateProgress.mockResolvedValue({ data: { id: 62 } });

    render(
      <MemoryRouter>
        <PresalesWorkstation />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText("线索阶段成本核算"));
    fireEvent.change(screen.getAllByPlaceholderText("0.00")[0], {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /提交成本估算/ }));

    await waitFor(() => {
      expect(apiMocks.presaleApi.tickets.complete).toHaveBeenCalledWith(62, {
        completion_note: expect.stringContaining("成本估算已完成"),
      });
    });
    expect(apiMocks.presaleApi.solutions.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "线索阶段成本核算",
        ticket_id: 62,
        lead_id: 2026,
        customer_id: 8,
        estimated_cost: 90000,
        cost_breakdown: {
          mechanical: 90000,
          electrical: 0,
          software: 0,
          standard: 0,
          labor: 0,
          other: 0,
          notes: "",
        },
      }),
    );
    expect(apiMocks.presaleApi.solutions.create.mock.calls[0][0])
      .not.toHaveProperty("opportunity_id");
    expect(apiMocks.presaleApi.tickets.updateProgress).not.toHaveBeenCalled();
  });
});
