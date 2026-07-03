import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../services/api", () => ({
  pmoApi: {
    dashboard: vi.fn().mockResolvedValue({ data: {} }),
  },
  performanceApi: {
    getEvaluationTasks: vi.fn().mockResolvedValue({ data: { items: [] } }),
    getMyPerformance: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

import PerformanceManagement from "./PerformanceManagement.jsx";

describe("PerformanceManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders empty performance stats without visible undefined text", async () => {
    render(<PerformanceManagement />);

    await waitFor(() => {
      expect(screen.getByText("绩效管理")).toBeInTheDocument();
    });

    expect(document.body.textContent).not.toContain("undefined");
  });
});
