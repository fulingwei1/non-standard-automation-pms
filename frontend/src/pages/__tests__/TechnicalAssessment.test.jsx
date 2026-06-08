import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useParams, useSearchParams } from "react-router-dom";
import TechnicalAssessment from "../TechnicalAssessment";
import { presaleWorkbenchApi, technicalAssessmentApi } from "../../services/api";

vi.mock("react-router-dom", () => ({
  useParams: vi.fn(),
  useSearchParams: vi.fn(),
  Link: ({ to, children, ...props }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("../../services/api", () => ({
  presaleWorkbenchApi: {
    loadContext: vi.fn(),
    getAssessmentTemplates: vi.fn(),
  },
  technicalAssessmentApi: {
    getLeadAssessments: vi.fn(),
    getOpportunityAssessments: vi.fn(),
    applyForLead: vi.fn(),
    applyForOpportunity: vi.fn(),
    evaluate: vi.fn(),
  },
}));

describe("TechnicalAssessment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: { requirementDetail: null },
    });
    presaleWorkbenchApi.getAssessmentTemplates.mockResolvedValue({
      data: { data: { items: [] } },
    });
    useParams.mockReturnValue({ sourceType: "lead", sourceId: "21" });
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
  });

  it("renders completed assessment results when JSON fields are already parsed", async () => {
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [
        {
          id: 701,
          source_type: "LEAD",
          source_id: 21,
          status: "COMPLETED",
          total_score: 82,
          dimension_scores: {
            technology: 18,
            business: 16,
            resource: 15,
            delivery: 17,
            customer: 16,
          },
          decision: "RECOMMEND",
          risks: [
            {
              dimension: "delivery",
              level: "MEDIUM",
              description: "交付周期偏紧，项目启动后需要 PM 提前排产",
            },
          ],
          similar_cases: [],
          conditions: ["PM 提前确认排产资源"],
        },
      ],
    });

    render(<TechnicalAssessment />);

    expect(await screen.findByText("评估结果")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "线索管理" })).toHaveAttribute(
      "href",
      "/sales/leads",
    );
    expect(screen.getByText("技术维度")).toBeInTheDocument();
    expect(screen.getByText("18 / 20")).toBeInTheDocument();
    expect(screen.getByText("推荐立项")).toBeInTheDocument();
    expect(screen.getByText("PM 提前确认排产资源")).toBeInTheDocument();
  });

  it("shows template item scores for completed template-based assessments", async () => {
    presaleWorkbenchApi.getAssessmentTemplates.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              id: 31,
              template_name: "非标自动化标准评估模板",
              version: "V1.0",
              is_default: true,
            },
          ],
        },
      },
    });
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [
        {
          id: 706,
          source_type: "LEAD",
          source_id: 21,
          status: "COMPLETED",
          total_score: 85,
          template_id: 31,
          dimension_scores: {
            technology: 20,
            business: 16,
            resource: 15,
            delivery: 17,
            customer: 17,
          },
          item_scores: JSON.stringify([
            {
              item_id: 1,
              item_code: "tech_maturity",
              item_name: "技术成熟度",
              dimension: "technology",
              score: 10,
              max_score: 10,
              weight: 1,
              value: "mature",
            },
          ]),
          decision: "RECOMMEND",
          risks: [],
          similar_cases: [],
          conditions: [],
        },
      ],
    });

    render(<TechnicalAssessment />);

    expect(await screen.findByText("评估项得分")).toBeInTheDocument();
    expect(screen.getByText("技术成熟度")).toBeInTheDocument();
    expect(screen.getByText("10 / 10")).toBeInTheDocument();
    expect(screen.getByText("非标自动化标准评估模板 V1.0")).toBeInTheDocument();
  });

  it("submits structured requirement fields without editing raw JSON", async () => {
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [
        {
          id: 702,
          source_type: "LEAD",
          source_id: 21,
          status: "PENDING",
          total_score: null,
        },
      ],
    });
    technicalAssessmentApi.evaluate.mockResolvedValue({
      data: {
        id: 702,
        source_type: "LEAD",
        source_id: 21,
        status: "COMPLETED",
        total_score: 86,
        dimension_scores: JSON.stringify({
          technology: 18,
          business: 18,
          resource: 16,
          delivery: 17,
          customer: 17,
        }),
        risks: "[]",
        similar_cases: "[]",
        conditions: "[]",
      },
    });

    render(<TechnicalAssessment />);

    fireEvent.change(await screen.findByLabelText("技术成熟度"), {
      target: { value: "mature" },
    });
    fireEvent.change(screen.getByLabelText("预算状态"), {
      target: { value: "confirmed" },
    });
    fireEvent.click(screen.getByLabelText("有客户SOW/URS"));
    fireEvent.click(screen.getByRole("button", { name: "执行评估" }));

    await waitFor(() => {
      expect(technicalAssessmentApi.evaluate).toHaveBeenCalledWith(702, {
        requirement_data: expect.objectContaining({
          tech_maturity: "mature",
          budget_status: "confirmed",
          has_sow: true,
        }),
        enable_ai: false,
      });
    });
  });

  it("passes the default assessment template when applying a new assessment", async () => {
    presaleWorkbenchApi.getAssessmentTemplates.mockResolvedValue({
      data: {
        data: {
          items: [
            { id: 41, template_name: "默认技术评估模板", is_default: true },
            { id: 42, template_name: "改造项目评估模板", is_default: false },
          ],
        },
      },
    });
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({ data: [] });
    technicalAssessmentApi.applyForLead.mockResolvedValue({
      data: { data: { assessment_id: 900 } },
    });

    render(<TechnicalAssessment />);

    const templateSelect = await screen.findByLabelText("评估模板");
    expect(templateSelect).toHaveValue("41");
    fireEvent.click(screen.getByRole("button", { name: "申请技术评估" }));

    await waitFor(() => {
      expect(technicalAssessmentApi.applyForLead).toHaveBeenCalledWith(21, {
        template_id: 41,
      });
    });
  });

  it("passes the selected assessment template when evaluating a pending assessment", async () => {
    presaleWorkbenchApi.getAssessmentTemplates.mockResolvedValue({
      data: {
        data: {
          items: [
            { id: 51, template_name: "标准设备模板", is_default: true },
            { id: 52, template_name: "软件项目模板", is_default: false },
          ],
        },
      },
    });
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [
        {
          id: 707,
          source_type: "LEAD",
          source_id: 21,
          status: "PENDING",
          total_score: null,
        },
      ],
    });
    technicalAssessmentApi.evaluate.mockResolvedValue({
      data: {
        id: 707,
        source_type: "LEAD",
        source_id: 21,
        status: "COMPLETED",
        total_score: 88,
        template_id: 52,
        dimension_scores: JSON.stringify({
          technology: 18,
          business: 18,
          resource: 17,
          delivery: 17,
          customer: 18,
        }),
        risks: "[]",
        similar_cases: "[]",
        conditions: "[]",
        item_scores: "[]",
      },
    });

    render(<TechnicalAssessment />);

    const templateSelect = await screen.findByLabelText("评估模板");
    expect(templateSelect).toHaveValue("51");
    fireEvent.change(templateSelect, { target: { value: "52" } });
    fireEvent.change(screen.getByLabelText("技术成熟度"), {
      target: { value: "mature" },
    });
    fireEvent.click(screen.getByRole("button", { name: "执行评估" }));

    await waitFor(() => {
      expect(technicalAssessmentApi.evaluate).toHaveBeenCalledWith(707, {
        requirement_data: expect.objectContaining({
          tech_maturity: "mature",
        }),
        enable_ai: false,
        template_id: 52,
      });
    });
  });

  it("shows presale collaboration context links from the workbench context", async () => {
    useParams.mockReturnValue({ sourceType: "opportunity", sourceId: "8" });
    useSearchParams.mockReturnValue([
      new URLSearchParams("ticket_id=501&project_id=42"),
      vi.fn(),
    ]);
    technicalAssessmentApi.getOpportunityAssessments.mockResolvedValue({
      data: [
        {
          id: 704,
          source_type: "OPPORTUNITY",
          source_id: 8,
          status: "PENDING",
          total_score: null,
        },
      ],
    });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: { requirementDetail: null },
      collaboration: {
        openItems: { items: [{ id: 1 }], total: 2, blocking_count: 1 },
        requirementFreezes: { items: [{ id: 2 }], total: 1 },
        aiClarifications: { items: [{ id: 3 }], total: 1 },
      },
    });

    render(<TechnicalAssessment />);

    expect(await screen.findByText("售前协作上下文")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "商机管理" })).toHaveAttribute(
      "href",
      "/sales/opportunities",
    );
    expect(screen.getByText("2 项未决，1 项阻塞")).toBeInTheDocument();
    expect(screen.getByText("1 项需求冻结")).toBeInTheDocument();
    expect(screen.getByText("1 轮AI澄清")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /查看未决事项/ })).toHaveAttribute(
      "href",
      "/sales/opportunity/8/open-items?ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看需求冻结/ })).toHaveAttribute(
      "href",
      "/sales/opportunity/8/requirement-freezes?ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看AI澄清/ })).toHaveAttribute(
      "href",
      "/sales/opportunity/8/ai-clarifications?ticket_id=501&project_id=42",
    );
  });

  it("keeps collaboration entrypoints visible before collaboration records exist", async () => {
    useParams.mockReturnValue({ sourceType: "leads", sourceId: "21" });
    useSearchParams.mockReturnValue([
      new URLSearchParams("ticket_id=501&lead_id=12&project_id=42"),
      vi.fn(),
    ]);
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [
        {
          id: 705,
          source_type: "LEAD",
          source_id: 21,
          status: "PENDING",
          total_score: null,
        },
      ],
    });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: { requirementDetail: null },
      collaboration: {
        openItems: { items: [], total: 0, blocking_count: 0 },
        requirementFreezes: { items: [], total: 0 },
        aiClarifications: { items: [], total: 0 },
      },
    });

    render(<TechnicalAssessment />);

    expect(await screen.findByText("售前协作上下文")).toBeInTheDocument();
    expect(screen.getByText("0 项未决，0 项阻塞")).toBeInTheDocument();
    expect(screen.getByText("暂无协作记录，可从这里进入创建未决事项、需求冻结或AI澄清。")).toBeInTheDocument();
    expect(technicalAssessmentApi.getLeadAssessments).toHaveBeenCalledWith(21);
    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "lead",
      sourceId: 21,
      presaleTicketId: 501,
    });
    expect(screen.getByRole("link", { name: /查看未决事项/ })).toHaveAttribute(
      "href",
      "/sales/lead/21/open-items?ticket_id=501&lead_id=12&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看需求冻结/ })).toHaveAttribute(
      "href",
      "/sales/lead/21/requirement-freezes?ticket_id=501&lead_id=12&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看AI澄清/ })).toHaveAttribute(
      "href",
      "/sales/lead/21/ai-clarifications?ticket_id=501&lead_id=12&project_id=42",
    );
  });
});
