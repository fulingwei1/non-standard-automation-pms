import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAssessmentData } from "../useAssessmentData";
import { presaleWorkbenchApi, technicalAssessmentApi } from "../../../../services/api";

vi.mock("../../../../services/api", () => ({
  presaleWorkbenchApi: {
    loadContext: vi.fn(),
  },
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
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: { requirementDetail: null },
    });
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

  it("selects the assessment requested by query context when loading a source list", async () => {
    const olderAssessment = { id: 31, status: "COMPLETED", source_type: "LEAD" };
    const ticketAssessment = { id: 701, status: "PENDING", source_type: "LEAD" };
    technicalAssessmentApi.getLeadAssessments.mockResolvedValue({
      data: [olderAssessment, ticketAssessment],
    });

    const { result } = renderHook(() =>
      useAssessmentData("lead", "21", "701")
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.assessments).toEqual([olderAssessment, ticketAssessment]);
    expect(result.current.assessment).toEqual(ticketAssessment);
  });

  it("prefills requirement data from the presale workbench context when opened from a ticket", async () => {
    const ticketAssessment = { id: 702, status: "PENDING", source_type: "OPPORTUNITY" };
    technicalAssessmentApi.getOpportunityAssessments.mockResolvedValue({
      data: [ticketAssessment],
    });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: {
        requirementDetail: {
          id: 301,
          lead_id: 21,
          has_sow: true,
          requirement_maturity: 4,
          cycle_time_seconds: 12.5,
          workstation_count: 2,
          target_object_type: "电源模块",
        },
      },
    });

    const { result } = renderHook(() =>
      useAssessmentData("opportunity", "2", "702", "93")
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "opportunity",
      sourceId: 2,
      presaleTicketId: 93,
    });
    expect(result.current.requirementData).toEqual(
      expect.objectContaining({
        source_type: "opportunity",
        source_id: 2,
        requirement_detail_id: 301,
        lead_id: 21,
        has_sow: true,
        hasSOW: true,
        requirement_maturity: 4,
        requirementMaturity: 4,
        cycle_time_seconds: 12.5,
        takt_time_s: 12.5,
        workstation_count: 2,
        target_object_type: "电源模块",
      }),
    );
  });

  it("prefills requirement data from opportunity context even without a ticket", async () => {
    const pendingAssessment = { id: 703, status: "PENDING", source_type: "OPPORTUNITY" };
    technicalAssessmentApi.getOpportunityAssessments.mockResolvedValue({
      data: [pendingAssessment],
    });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      assessment: {
        requirementDetail: {
          id: 302,
          lead_id: 22,
          has_interface_doc: true,
          cycle_time_seconds: 9.5,
          target_object_type: "PCBA",
        },
      },
      collaboration: {
        openItems: { items: [{ id: 901 }], total: 1, blocking_count: 1 },
        requirementFreezes: { items: [{ id: 902 }], total: 1 },
        aiClarifications: { items: [{ id: 903 }], total: 1 },
      },
    });

    const { result } = renderHook(() =>
      useAssessmentData("opportunity", "8", "703")
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: "opportunity",
      sourceId: 8,
    });
    expect(result.current.requirementData).toEqual(
      expect.objectContaining({
        source_type: "opportunity",
        source_id: 8,
        requirement_detail_id: 302,
        lead_id: 22,
        has_interface_doc: true,
        cycle_time_seconds: 9.5,
        target_object_type: "PCBA",
      }),
    );
    expect(result.current.collaboration.openItems.blocking_count).toBe(1);
    expect(result.current.collaboration.requirementFreezes.total).toBe(1);
    expect(result.current.collaboration.aiClarifications.total).toBe(1);
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
