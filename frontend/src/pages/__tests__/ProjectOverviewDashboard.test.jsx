import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ProjectOverviewDashboard from "../ProjectOverviewDashboard";
import { projectApi } from "../../services/api";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../services/api", () => ({
  projectApi: {
    createWorkOrdersFromWbs: vi.fn(),
    createPurchaseRequestsFromBom: vi.fn(),
    createDeliverySchedule: vi.fn(),
    transferToAfterSales: vi.fn(),
  },
}));

describe("ProjectOverviewDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
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

  it("runs downstream data flow actions for the current project", async () => {
    projectApi.createWorkOrdersFromWbs.mockResolvedValue({ data: { message: "ok" } });
    projectApi.createPurchaseRequestsFromBom.mockResolvedValue({ data: { message: "ok" } });
    projectApi.createDeliverySchedule.mockResolvedValue({ data: { message: "ok" } });
    projectApi.transferToAfterSales.mockResolvedValue({ data: { message: "ok" } });

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

    fireEvent.click(screen.getByRole("button", { name: /WBS→生产工单/ }));
    await waitFor(() => {
      expect(projectApi.createWorkOrdersFromWbs).toHaveBeenCalledWith("42");
    });

    fireEvent.click(screen.getByRole("button", { name: /BOM→采购申请/ }));
    await waitFor(() => {
      expect(projectApi.createPurchaseRequestsFromBom).toHaveBeenCalledWith("42");
    });

    fireEvent.click(screen.getByRole("button", { name: /里程碑→交付计划/ }));
    await waitFor(() => {
      expect(projectApi.createDeliverySchedule).toHaveBeenCalledWith("42");
    });

    fireEvent.click(screen.getByRole("button", { name: /验收→售后/ }));
    await waitFor(() => {
      expect(projectApi.transferToAfterSales).toHaveBeenCalledWith("42");
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(5);
    });
  });
});
