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
});
