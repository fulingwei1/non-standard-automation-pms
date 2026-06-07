import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useParams, useSearchParams } from "react-router-dom";
import TechnicalAssessment from "../TechnicalAssessment";
import { technicalAssessmentApi } from "../../services/api";

vi.mock("../../services/api", () => ({
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
    expect(screen.getByText("技术维度")).toBeInTheDocument();
    expect(screen.getByText("18 / 20")).toBeInTheDocument();
    expect(screen.getByText("推荐立项")).toBeInTheDocument();
    expect(screen.getByText("PM 提前确认排产资源")).toBeInTheDocument();
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
});
