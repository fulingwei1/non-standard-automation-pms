import { describe, expect, it, beforeEach, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useParams, useSearchParams } from "react-router-dom";

import PurchaseRequestNew from "../PurchaseRequestNew";
import ProjectDeliveryScheduleCreate from "../ProjectDeliverySchedule/ScheduleCreate";
import ProjectDeliveryScheduleGantt from "../ProjectDeliverySchedule/ScheduleGantt";
import MaterialReservation from "../inventory/operations/MaterialReservation";
import {
  materialApi,
  machineApi,
  projectApi,
  purchaseApi,
  supplierApi,
} from "../../services/api";
import { projectDeliveryApi } from "../../services/api/projectDelivery";
import InventoryAPI from "../../services/inventory";

vi.mock("../../services/api", () => ({
  materialApi: {
    list: vi.fn(),
  },
  machineApi: {
    list: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
  },
  purchaseApi: {
    requests: {
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
  },
  supplierApi: {
    list: vi.fn(),
  },
}));

vi.mock("../../services/api/projectDelivery", () => ({
  projectDeliveryApi: {
    getSchedules: vi.fn(),
    getGanttData: vi.fn(),
    getConflicts: vi.fn(),
    createSchedule: vi.fn(),
  },
}));

vi.mock("../../services/inventory", () => ({
  default: {
    reserveMaterial: vi.fn(),
    cancelReservation: vi.fn(),
  },
}));

function renderWithRouteContext(element, { params = {}, search = "" } = {}) {
  useParams.mockReturnValue(params);
  useSearchParams.mockReturnValue([new URLSearchParams(search), vi.fn()]);

  return render(
    <MemoryRouter>
      {element}
    </MemoryRouter>
  );
}

describe("execution tail project context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useParams.mockReturnValue({});
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    vi.spyOn(window, "alert").mockImplementation(() => {});
    projectApi.list.mockResolvedValue({
      data: { items: [{ id: 42, project_name: "P42" }] },
    });
    machineApi.list.mockResolvedValue({ data: { items: [] } });
    materialApi.list.mockResolvedValue({ data: { items: [] } });
    supplierApi.list.mockResolvedValue({ data: { items: [] } });
    purchaseApi.requests.create.mockResolvedValue({ data: { id: 1 } });
    projectDeliveryApi.getSchedules.mockResolvedValue([{ id: 7 }]);
    projectDeliveryApi.getGanttData.mockResolvedValue({
      schedule_name: "P42 排产",
      version: "v1",
      tasks: [],
      long_cycle_purchases: [],
      dependencies: [],
    });
    projectDeliveryApi.getConflicts.mockResolvedValue({ has_conflicts: false });
    projectDeliveryApi.createSchedule.mockResolvedValue({ id: 7 });
    InventoryAPI.reserveMaterial.mockResolvedValue({ id: 1 });
  });

  it("defaults a new purchase request to the project context", async () => {
    renderWithRouteContext(
      <PurchaseRequestNew />,
      { search: "project_id=42" }
    );

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 1000,
        project_id: "42",
      });
    });

    await waitFor(() => {
      expect(machineApi.list).toHaveBeenCalledWith(42, {
        page: 1,
        page_size: 100,
      });
    });
  });

  it("creates delivery schedules with the route project context", async () => {
    renderWithRouteContext(
      <ProjectDeliveryScheduleCreate />,
      { params: { projectId: "42" } }
    );

    fireEvent.change(screen.getByPlaceholderText("如：ICT 测试机台项目交付排产计划"), {
      target: { value: "P42 交付计划" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建排产计划" }));

    await waitFor(() => {
      expect(projectDeliveryApi.createSchedule).toHaveBeenCalledWith(
        expect.objectContaining({
          schedule_name: "P42 交付计划",
          project_id: 42,
        })
      );
    });
  });

  it("resolves the delivery gantt schedule from project context", async () => {
    renderWithRouteContext(
      <ProjectDeliveryScheduleGantt />,
      { params: { projectId: "42" } }
    );

    await waitFor(() => {
      expect(projectDeliveryApi.getSchedules).toHaveBeenCalledWith({
        project_id: 42,
      });
    });
    await waitFor(() => {
      expect(projectDeliveryApi.getGanttData).toHaveBeenCalledWith(7);
    });
  });

  it("defaults material reservation creation to the project context", async () => {
    renderWithRouteContext(
      <MaterialReservation />,
      { search: "project_id=42" }
    );

    fireEvent.click(screen.getByRole("button", { name: /创建预留/ }));
    fireEvent.change(screen.getByPlaceholderText("输入物料ID"), {
      target: { value: "1001" },
    });
    fireEvent.change(screen.getByPlaceholderText("输入数量"), {
      target: { value: "3" },
    });
    fireEvent.click(screen.getByRole("button", { name: "确认预留" }));

    await waitFor(() => {
      expect(InventoryAPI.reserveMaterial).toHaveBeenCalledWith(
        expect.objectContaining({
          material_id: 1001,
          quantity: 3,
          project_id: 42,
        })
      );
    });
  });
});
