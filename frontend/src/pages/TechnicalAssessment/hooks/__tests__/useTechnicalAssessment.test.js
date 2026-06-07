import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useTechnicalAssessment } from "../useTechnicalAssessment";
import { technicalAssessmentApi } from "../../../../services/api";

vi.mock("../../../../services/api", () => ({
  technicalAssessmentApi: {
    getLeadAssessments: vi.fn(),
    getOpportunityAssessments: vi.fn(),
    applyForLead: vi.fn(),
    applyForOpportunity: vi.fn(),
    evaluate: vi.fn(),
  },
}));

describe("useTechnicalAssessment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads assessments from the source-specific lead endpoint", async () => {
    const leadAssessments = [{ id: 7, status: "PENDING" }];
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: leadAssessments,
    });

    const { result } = renderHook(() => useTechnicalAssessment("lead", "12"));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(technicalAssessmentApi.getLeadAssessments).toHaveBeenCalledWith(12);
    expect(result.current.assessments).toEqual(leadAssessments);
    expect(result.current.error).toBeNull();
  });

  it("loads assessments from unified paginated API responses", async () => {
    const pendingAssessment = { id: 17, status: "PENDING", source_type: "OPPORTUNITY" };
    technicalAssessmentApi.getOpportunityAssessments.mockResolvedValue({
      data: {
        code: 0,
        data: { items: [pendingAssessment], total: 1 },
      },
      formatted: { items: [pendingAssessment], total: 1 },
    });

    const { result } = renderHook(() =>
      useTechnicalAssessment("opportunity", "9")
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(technicalAssessmentApi.getOpportunityAssessments).toHaveBeenCalledWith(9);
    expect(result.current.assessments).toEqual([pendingAssessment]);
    expect(result.current.error).toBeNull();
  });

  it("applies an opportunity assessment and reloads the same source", async () => {
    const appliedAssessment = [{ id: 21, status: "PENDING" }];
    technicalAssessmentApi.getOpportunityAssessments
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: appliedAssessment });
    technicalAssessmentApi.applyForOpportunity.mockResolvedValue({
      data: { data: { assessment_id: 21 } },
    });

    const { result } = renderHook(() =>
      useTechnicalAssessment("opportunity", "9")
    );
    await waitFor(() => expect(result.current.loading).toBe(false));

    let applyResult;
    await act(async () => {
      applyResult = await result.current.createAssessment({ evaluator_id: 3 });
    });

    expect(applyResult).toEqual({ success: true });
    expect(technicalAssessmentApi.applyForOpportunity).toHaveBeenCalledWith(9, {
      evaluator_id: 3,
    });
    expect(technicalAssessmentApi.getOpportunityAssessments).toHaveBeenCalledTimes(2);
    expect(result.current.assessments).toEqual(appliedAssessment);
  });

  it("submits evaluation through the real evaluate endpoint", async () => {
    const pendingAssessment = [{ id: 7, status: "PENDING" }];
    const completedAssessment = [{ id: 7, status: "COMPLETED" }];
    technicalAssessmentApi.getLeadAssessments
      .mockResolvedValueOnce({ data: pendingAssessment })
      .mockResolvedValueOnce({ data: completedAssessment });
    technicalAssessmentApi.evaluate.mockResolvedValue({
      data: completedAssessment[0],
    });

    const { result } = renderHook(() => useTechnicalAssessment("lead", "12"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    let submitResult;
    await act(async () => {
      submitResult = await result.current.submitAssessment(7, {
        requirement_data: { tech_maturity: "mature" },
        enable_ai: true,
      });
    });

    expect(submitResult).toEqual({ success: true });
    expect(technicalAssessmentApi.evaluate).toHaveBeenCalledWith(7, {
      requirement_data: { tech_maturity: "mature" },
      enable_ai: true,
    });
    expect(result.current.assessments).toEqual(completedAssessment);
  });
});
