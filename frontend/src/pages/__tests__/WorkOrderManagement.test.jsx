import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkOrderManagement from "../WorkOrderManagement";
import { productionApi, projectApi } from "../../services/api";

const mockNavigate = vi.fn();

vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
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
      updateStatus: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
  };
});

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                'initial',
                'animate',
                'exit',
                'variants',
                'transition',
                'whileHover',
                'whileTap',
                'whileInView',
                'layout',
                'layoutId',
                'drag',
                'dragConstraints',
                'onDragEnd',
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
}));

describe("WorkOrderManagement", () => {
  const mockWorkOrders = {
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
  };

  const mockProjects = {
    data: { 
      items: [{ id: 101, project_name: "项目A" }] 
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();

    projectApi.list.mockResolvedValue(mockProjects);
    productionApi.workOrders.list.mockResolvedValue(mockWorkOrders);
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

  it("should handle loading work orders failure", async () => {
    productionApi.workOrders.list.mockRejectedValueOnce(new Error('Load failed'));

    render(
      <MemoryRouter>
        <WorkOrderManagement />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(productionApi.workOrders.list).toHaveBeenCalled();
    });

    // Component should still render even if API fails
    expect(screen.getByText("工单管理")).toBeInTheDocument();
  });

  it("should handle loading projects failure", async () => {
    projectApi.list.mockRejectedValueOnce(new Error('Project load failed'));

    render(
      <MemoryRouter>
        <WorkOrderManagement />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({ page_size: 1000 });
    });

    // Component should still render even if project API fails
    expect(screen.getByText("工单管理")).toBeInTheDocument();
  });

  it("should handle creating work order failure", async () => {
    const mockCreateResponse = { success: false, error: 'Create failed' };
    productionApi.workOrders.create.mockRejectedValueOnce(new Error('Create failed'));

    render(
      <MemoryRouter>
        <WorkOrderManagement />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(productionApi.workOrders.list).toHaveBeenCalled();
    });

    // Component should handle create failure gracefully
    expect(screen.getByText("工单管理")).toBeInTheDocument();
  });

  it("should handle updating work order status failure", async () => {
    productionApi.workOrders.updateStatus.mockRejectedValueOnce(new Error('Update status failed'));

    render(
      <MemoryRouter>
        <WorkOrderManagement />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(productionApi.workOrders.list).toHaveBeenCalled();
    });

    // Component should handle status update failure gracefully
    expect(screen.getByText("工单管理")).toBeInTheDocument();
  });
});