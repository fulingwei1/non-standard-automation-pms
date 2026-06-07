import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";
import { useTechnicalReviewForm } from "../useTechnicalReviewForm";
import { projectApi, technicalReviewApi, userApi } from "../../../../services/api";

const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useSearchParams: vi.fn(),
  };
});

vi.mock("../../../../services/api", () => ({
  technicalReviewApi: {
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    createIssue: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
  },
  userApi: {
    list: vi.fn(),
  },
}));

describe("useTechnicalReviewForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigateSpy.mockClear();
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    userApi.list.mockResolvedValue({ data: { items: [] } });
    technicalReviewApi.create.mockResolvedValue({ data: { id: 7 } });
    technicalReviewApi.get.mockResolvedValue({
      data: {
        id: 7,
        review_type: "PDR",
        review_name: "合同转项目 PDR",
        project_id: 42,
        equipment_id: null,
        scheduled_date: "2026-06-07T09:00:00",
        location: "会议室",
        meeting_type: "ONSITE",
        host_id: 1,
        presenter_id: 1,
        recorder_id: 1,
        participants: [],
        materials: [],
        checklist_records: [],
        issues: [],
      },
    });
    technicalReviewApi.createIssue.mockResolvedValue({ data: { id: 11 } });
  });

  it("treats the static new route without reviewId as create mode", async () => {
    const { result } = renderHook(() => useTechnicalReviewForm(undefined));

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
      expect(userApi.list).toHaveBeenCalled();
    });

    expect(result.current.isNew).toBe(true);
    expect(result.current.loading).toBe(false);
    expect(technicalReviewApi.get).not.toHaveBeenCalled();
  });

  it("defaults the new review project from the project context query", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42"),
      vi.fn(),
    ]);

    const { result } = renderHook(() => useTechnicalReviewForm("new"));

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
      expect(userApi.list).toHaveBeenCalled();
    });

    expect(result.current.isNew).toBe(true);
    expect(result.current.formData.project_id).toBe("42");
    expect(technicalReviewApi.get).not.toHaveBeenCalled();
  });

  it("returns to the scoped technical review list after creating from project presale context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42&ticket_id=91&opportunity_id=2"),
      vi.fn(),
    ]);

    const { result } = renderHook(() => useTechnicalReviewForm("new"));

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
      expect(userApi.list).toHaveBeenCalled();
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(technicalReviewApi.create).toHaveBeenCalledWith(
      expect.objectContaining({ project_id: "42" }),
    );
    expect(navigateSpy).toHaveBeenCalledWith(
      "/technical-reviews?project_id=42&ticket_id=91&opportunity_id=2",
    );
  });

  it("creates a review issue and refreshes the review detail", async () => {
    const { result } = renderHook(() => useTechnicalReviewForm("7"));

    await waitFor(() => {
      expect(technicalReviewApi.get).toHaveBeenCalledWith("7");
    });

    await act(async () => {
      await result.current.handleCreateIssue({
        review_id: 7,
        issue_level: "B",
        category: "设计风险",
        description: "夹具定位方案需要复核",
        suggestion: "补充定位销校核",
        assignee_id: 3,
        deadline: "2026-06-20",
      });
    });

    expect(technicalReviewApi.createIssue).toHaveBeenCalledWith(
      "7",
      expect.objectContaining({
        review_id: 7,
        issue_level: "B",
        category: "设计风险",
        description: "夹具定位方案需要复核",
        suggestion: "补充定位销校核",
        assignee_id: 3,
        deadline: "2026-06-20",
      }),
    );
    expect(technicalReviewApi.get).toHaveBeenCalledTimes(2);
    expect(result.current.issueDialog.open).toBe(false);
  });
});
