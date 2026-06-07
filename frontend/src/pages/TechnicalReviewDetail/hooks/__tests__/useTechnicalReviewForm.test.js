import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTechnicalReviewForm } from "../useTechnicalReviewForm";
import { projectApi, technicalReviewApi, userApi } from "../../../../services/api";

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
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
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    userApi.list.mockResolvedValue({ data: { items: [] } });
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
});
