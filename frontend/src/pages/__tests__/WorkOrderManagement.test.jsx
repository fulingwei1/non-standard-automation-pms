import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkOrderManagement from "../WorkOrderManagement";
import { productionApi, projectApi } from "../../services/api";

const mockNavigate = vi.fn();

vi.mock("../../services/api", () => ({
  productionApi: {
    workOrders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      assign: vi.fn(),
      start: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      complete: vi.fn(),
      getProgress: vi.fn(),
      getReports: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("WorkOrderManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    projectApi.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ id: 101, project_name: "项目A" }],
        },
      },
    });

    productionApi.workOrders.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 1,
              work_order_no: "WO-001",
              task_name: "装配电机",
              material_name: "伺服电机",
              plan_qty: 12,
              completed_qty: 4,
              status: "PENDING",
              priority: "HIGH",
            },
          ],
        },
      },
    });
  });

  it("renders and loads wrapped work-order data without crashing", async () => {
    render(
      <MemoryRouter>
        <WorkOrderManagement />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText("搜索工单号、任务名称...")).toHaveValue("");

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({ page_size: 1000 });
      expect(productionApi.workOrders.list).toHaveBeenCalled();
    });

    expect(screen.getByText("工单管理")).toBeInTheDocument();
    expect(screen.getByText("WO-001")).toBeInTheDocument();
    expect(screen.getByText("装配电机")).toBeInTheDocument();
  });
});
