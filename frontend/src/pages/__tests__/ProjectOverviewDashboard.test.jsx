import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ProjectOverviewDashboard from "../ProjectOverviewDashboard";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("ProjectOverviewDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockResolvedValue({
      json: vi.fn().mockResolvedValue({
        production: {},
        procurement: {},
        delivery: {},
        after_sales: {
          warranty: { is_expired: false, days_remaining: 90 },
          support_tickets: {},
          field_services: {},
          spare_parts: {},
          satisfaction: {},
          sla: {},
          maintenance: {},
        },
      }),
    });
  });

  it("navigates downstream module cards with project context", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/42/overview-dashboard"]}>
        <Routes>
          <Route
            path="/projects/:projectId/overview-dashboard"
            element={<ProjectOverviewDashboard />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await screen.findByText("项目总览");

    fireEvent.click(screen.getByText(/生产状态/));
    expect(mockNavigate).toHaveBeenCalledWith("/production-plans?project_id=42");

    fireEvent.click(screen.getByText(/采购状态/));
    expect(mockNavigate).toHaveBeenCalledWith("/material-demands?project_id=42");
  });
});
