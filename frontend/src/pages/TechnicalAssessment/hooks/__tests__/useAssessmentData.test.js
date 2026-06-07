import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAssessmentData } from "../useAssessmentData";
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

describe("useAssessmentData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  it("clears the current assessment when the selected source has no assessments", async () => {
    const leadAssessment = { id: 11, status: "PENDING", source_type: "LEAD" };
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [leadAssessment],
    });
    technicalAssessmentApi.getOpportunityAssessments.mockResolvedValue({
      data: [],
    });

    const { result, rerender } = renderHook(
      ({ sourceType, sourceId }) => useAssessmentData(sourceType, sourceId),
      { initialProps: { sourceType: "lead", sourceId: "3" } }
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.assessment).toEqual(leadAssessment);

    rerender({ sourceType: "opportunity", sourceId: "8" });
    await waitFor(() => {
      expect(technicalAssessmentApi.getOpportunityAssessments).toHaveBeenCalledWith(8);
      expect(result.current.assessments).toEqual([]);
      expect(result.current.assessment).toBeNull();
    });
  });

  it("applies a lead assessment and reloads the source assessment list", async () => {
    const pendingAssessment = { id: 21, status: "PENDING", source_type: "LEAD" };
    technicalAssessmentApi.getLeadAssessments
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [pendingAssessment] });
    technicalAssessmentApi.applyForLead.mockResolvedValue({
      data: { data: { assessment_id: 21 } },
    });

    const { result } = renderHook(() => useAssessmentData("lead", "4"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.handleApplyAssessment();
    });

    expect(technicalAssessmentApi.applyForLead).toHaveBeenCalledWith(4, {});
    expect(technicalAssessmentApi.getLeadAssessments).toHaveBeenCalledTimes(2);
    expect(result.current.assessment).toEqual(pendingAssessment);
  });

  it("evaluates the currently selected assessment and reloads completed result", async () => {
    const pendingAssessment = { id: 31, status: "PENDING", source_type: "LEAD" };
    const completedAssessment = {
      id: 31,
      status: "COMPLETED",
      source_type: "LEAD",
      total_score: 80,
    };
    technicalAssessmentApi.getLeadAssessments
      .mockResolvedValueOnce({ data: [pendingAssessment] })
      .mockResolvedValueOnce({ data: [completedAssessment] });
    technicalAssessmentApi.evaluate.mockResolvedValue({ data: completedAssessment });

    const { result } = renderHook(() => useAssessmentData("lead", "5"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setRequirementData({ tech_maturity: "mature" });
      result.current.setEnableAI(true);
    });

    await act(async () => {
      await result.current.handleEvaluate();
    });

    expect(technicalAssessmentApi.evaluate).toHaveBeenCalledWith(31, {
      requirement_data: { tech_maturity: "mature" },
      enable_ai: true,
    });
    expect(result.current.assessment).toEqual(completedAssessment);
  });
});
