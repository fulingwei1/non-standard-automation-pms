import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useLeadAssessment } from "../useLeadAssessment";
import { technicalAssessmentApi } from "../../../../services/api";

vi.mock("../../../../services/api", () => ({
  technicalAssessmentApi: {
    getLeadAssessments: vi.fn(),
    applyForLead: vi.fn(),
    evaluate: vi.fn(),
  },
}));

describe("useLeadAssessment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not call obsolete list endpoint when no lead id is provided", async () => {
    const { result } = renderHook(() => useLeadAssessment());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(technicalAssessmentApi.getLeadAssessments).not.toHaveBeenCalled();
    expect(result.current.assessments).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("loads lead assessments from the real lead-specific endpoint", async () => {
    const assessments = [{ id: 41, status: "PENDING" }];
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({ data: assessments });

    const { result } = renderHook(() => useLeadAssessment("12"));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(technicalAssessmentApi.getLeadAssessments).toHaveBeenCalledWith(12);
    expect(result.current.assessments).toEqual(assessments);
  });

  it("submits a lead assessment through the real evaluate endpoint", async () => {
    const pendingAssessment = [{ id: 41, status: "PENDING" }];
    technicalAssessmentApi.getLeadAssessments
      .mockResolvedValueOnce({ data: pendingAssessment })
      .mockResolvedValueOnce({ data: [{ id: 41, status: "COMPLETED" }] });
    technicalAssessmentApi.evaluate.mockResolvedValue({
      data: { id: 41, status: "COMPLETED" },
    });

    const { result } = renderHook(() => useLeadAssessment("12"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    let submitResult;
    await act(async () => {
      submitResult = await result.current.submitAssessment(41, {
        tech_maturity: "mature",
      });
    });

    expect(submitResult).toEqual({ success: true });
    expect(technicalAssessmentApi.evaluate).toHaveBeenCalledWith(41, {
      requirement_data: { tech_maturity: "mature" },
      enable_ai: false,
    });
  });
});
