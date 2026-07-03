import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../services/api", () => ({
  projectReviewApi: {
    getPopularBestPractices: vi.fn().mockResolvedValue({
      data: {
        success: true,
        code: 200,
        message: "获取热门最佳实践成功",
        data: { items: [], total: 0, page: 1, page_size: 10 },
      },
    }),
    recommendBestPractices: vi.fn().mockResolvedValue({
      data: { recommendations: [] },
    }),
    getProjectBestPracticeRecommendations: vi.fn(),
    applyBestPractice: vi.fn(),
  },
  projectApi: {
    get: vi.fn(),
  },
}));

import BestPracticeRecommendations from "./BestPracticeRecommendations.jsx";
import { projectReviewApi } from "../services/api";

describe("BestPracticeRecommendations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("unwraps paginated popular practices before rendering", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/best-practices/recommend"]}>
        <Routes>
          <Route
            path="/projects/best-practices/recommend"
            element={<BestPracticeRecommendations />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(projectReviewApi.getPopularBestPractices).toHaveBeenCalled();
      expect(screen.getByText("最佳实践推荐")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("热门实践"));

    await waitFor(() => {
      expect(screen.getByText("暂无热门最佳实践")).toBeInTheDocument();
    });
  });
});
