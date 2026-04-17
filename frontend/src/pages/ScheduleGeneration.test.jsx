import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../services/api", () => ({
  scheduleGenerationApi: {
    generateBothModes: vi.fn(),
    saveSchedule: vi.fn(),
  },
}));

import ScheduleGeneration from "./ScheduleGeneration.jsx";
import { scheduleGenerationApi } from "../services/api";

function renderPage(route = "/projects/1/schedule-generation") {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/projects/:id/schedule-generation" element={<ScheduleGeneration />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ScheduleGeneration page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  it("uses the route project id when generating schedules", async () => {
    scheduleGenerationApi.generateBothModes.mockResolvedValue({
      data: {
        normal_mode: { total_days: 10, overall_efficiency: 1, ai_boost_factor: 1, mode_name: "正常", start_date: "2026-01-01", end_date: "2026-01-10", phases: {} },
        intensive_mode: { total_days: 8, overall_efficiency: 1, mode_name: "高强度", phases: {} },
        comparison: { time_saved: 2, time_saved_percentage: 20 },
      },
    });

    renderPage();

    await waitFor(() => {
      expect(scheduleGenerationApi.generateBothModes).toHaveBeenCalledWith("1");
    });

    expect(screen.queryByText("生成失败")).not.toBeInTheDocument();
  });
});
