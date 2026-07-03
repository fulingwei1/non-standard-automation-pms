import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("../../services/api", () => ({
  projectApi: {
    get: vi.fn(),
  },
  progressApi: {
    analytics: {
      getForecast: vi.fn(),
    },
    autoProcess: {
      preview: vi.fn(),
      applyForecast: vi.fn(),
      runCompleteProcess: vi.fn(),
    },
  },
}));

import ProgressForecast from "../ProgressForecast.jsx";
import { projectApi, progressApi } from "../../services/api";

describe("ProgressForecast", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(() => {
      throw new Error("ProgressForecast should use the authenticated API client");
    });
    projectApi.get.mockResolvedValue({
      data: {
        id: 87,
        project_name: "QA 项目",
      },
    });
    progressApi.analytics.getForecast.mockResolvedValue({
      data: {
        project_id: 87,
        project_name: "QA 项目",
        confidence: "LOW",
        current_progress: 0,
        predicted_delay_days: 0,
        tasks: [],
      },
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("loads project details through the authenticated project API client", async () => {
    render(<ProgressForecast projectId={87} />);

    await waitFor(() => {
      expect(projectApi.get).toHaveBeenCalledWith(87);
    });

    expect(global.fetch).not.toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "QA 项目 - 进度预测" })).toBeInTheDocument();
  });
});
