import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProductionPlanList from "../ProductionPlanList";
import WorkReportList from "../WorkReportList";
import ProductionExceptionList from "../ProductionExceptionList";
import WorkerManagement from "../WorkerManagement";
import CapacityAnalysis from "../CapacityAnalysis";
import AssemblyKitBoard from "../AssemblyKitBoard";
import { productionApi, projectApi } from "../../services/api";
import { assemblyKitApi } from "../../services/api/production";

const mockNavigate = vi.fn();

vi.mock("../../services/api", () => ({
  productionApi: {
    workshops: {
      list: vi.fn(),
    },
    productionPlans: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      publish: vi.fn(),
    },
    workReports: {
      list: vi.fn(),
      get: vi.fn(),
      approve: vi.fn(),
    },
    exceptions: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      handle: vi.fn(),
      close: vi.fn(),
    },
    workers: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    capacity: {
      oee: vi.fn(),
      bottlenecks: vi.fn(),
      trend: vi.fn(),
      forecast: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

vi.mock("../../services/api/production", async () => {
  const actual = await vi.importActual("../../services/api/production");
  return {
    ...actual,
    assemblyKitApi: {
      dashboard: vi.fn(),
      getShortageAlerts: vi.fn(),
      getAnalysisDetail: vi.fn(),
      generateSuggestions: vi.fn(),
      acceptSuggestion: vi.fn(),
      rejectSuggestion: vi.fn(),
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

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(async (action) => action?.()),
}));

function renderPage(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("production module smoke", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    projectApi.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ id: 88, project_name: "项目Alpha", name: "项目Alpha" }],
        },
      },
    });

    productionApi.workshops.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ id: 3, workshop_name: "总装一车间" }],
        },
      },
    });

    productionApi.productionPlans.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 11,
              plan_no: "PP-001",
              plan_name: "三月装配排产",
              project_name: "项目Alpha",
              workshop_name: "总装一车间",
              plan_start_date: "2026-03-15",
              plan_end_date: "2026-03-20",
              status: "DRAFT",
              plan_type: "WEEKLY",
            },
          ],
        },
      },
    });

    productionApi.workReports.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 21,
              report_no: "WR-001",
              work_order_no: "WO-001",
              worker_name: "王师傅",
              report_type: "PROGRESS",
              status: "PENDING",
              report_date: "2026-03-15",
              reported_hours: 6,
              completed_qty: 8,
            },
          ],
        },
      },
    });

    productionApi.exceptions.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 31,
              exception_no: "EX-001",
              title: "装配缺料",
              exception_type: "MATERIAL",
              exception_level: "HIGH",
              status: "OPEN",
              project_name: "项目Alpha",
              report_time: "2026-03-15 08:00:00",
            },
          ],
        },
      },
    });

    productionApi.workers.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 41,
              worker_code: "WK-001",
              worker_name: "李工",
              phone: "13800000000",
              skill_level: "ADVANCED",
              is_active: true,
            },
          ],
        },
      },
    });

    productionApi.capacity.oee.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ equipment_id: 1, equipment_name: "装配线A", total_output: 10000, avg_oee: 91.2 }],
        },
      },
    });
    productionApi.capacity.bottlenecks.mockResolvedValue({
      data: {
        success: true,
        data: {
          equipment_bottlenecks: [{ equipment_name: "装配线A", utilization_rate: 96, total_downtime: 180, avg_oee: 91, suggestion: "补充工装" }],
          workstation_bottlenecks: [{ workstation_name: "工位1", total_hours: 12, work_order_count: 3, suggestion: "优化工序" }],
          low_efficiency_workers: [{ worker_name: "李工", avg_efficiency: 76, suggestion: "安排培训" }],
        },
      },
    });
    productionApi.capacity.trend.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ period: "W11", avg_oee: 89.5 }],
        },
      },
    });
    productionApi.capacity.forecast.mockResolvedValue({
      data: {
        success: true,
        data: {
          forecast_values: [{ forecast_value: 12000, upper_bound: 12800, lower_bound: 11300 }],
          model_info: { r_squared: 0.88 },
          summary: { confidence_level: "88" },
        },
      },
    });

    assemblyKitApi.dashboard.mockResolvedValue({
      data: {
        success: true,
        data: {
          stats: {
            total_projects: 5,
            can_start_count: 3,
            avg_kit_rate: 82,
            avg_blocking_rate: 18,
          },
          stage_stats: [
            { stage_code: "FRAME", stage_name: "钣金", ready_count: 2, blocked_count: 1, total_count: 3, readiness_rate: 66 },
          ],
          alert_summary: { L1: 1, L2: 0, L3: 2, L4: 1 },
          recent_analyses: [
            { id: 1, readiness_id: 1, project_name: "项目Alpha", readiness_no: "AR-001", overall_readiness: 82 },
          ],
          pending_suggestions: [
            {
              id: 1,
              project_name: "项目Alpha",
              suggestion_type: "CAN_START",
              suggested_start_date: "2026-03-16",
              priority_score: 92,
              current_kit_rate: 88,
            },
          ],
        },
      },
    });
    assemblyKitApi.getShortageAlerts.mockResolvedValue({
      data: {
        success: true,
        data: {
          total: 1,
          items: [{ shortage_id: 1, project_name: "项目Alpha", level: "L1", material_name: "伺服电机", shortage_qty: 2 }],
        },
      },
    });
  });

  it("renders production plans with wrapped list data", async () => {
    renderPage(<ProductionPlanList />);

    await waitFor(() => expect(productionApi.productionPlans.list).toHaveBeenCalled());

    expect(screen.getByText("生产计划管理")).toBeInTheDocument();
    expect(screen.getByText("PP-001")).toBeInTheDocument();
    expect(screen.getByText("三月装配排产")).toBeInTheDocument();
  });

  it("renders work reports with wrapped list data", async () => {
    renderPage(<WorkReportList />);

    await waitFor(() => expect(productionApi.workReports.list).toHaveBeenCalled());

    expect(screen.getByText("报工管理")).toBeInTheDocument();
    expect(screen.getByText("WR-001")).toBeInTheDocument();
    expect(screen.getByText("王师傅")).toBeInTheDocument();
  });

  it("renders production exceptions with wrapped list data", async () => {
    renderPage(<ProductionExceptionList />);

    await waitFor(() => expect(productionApi.exceptions.list).toHaveBeenCalled());

    expect(screen.getByText("生产异常管理")).toBeInTheDocument();
    expect(screen.getByText("EX-001")).toBeInTheDocument();
    expect(screen.getByText("装配缺料")).toBeInTheDocument();
  });

  it("renders workers with wrapped list data", async () => {
    renderPage(<WorkerManagement />);

    await waitFor(() => expect(productionApi.workers.list).toHaveBeenCalled());

    expect(screen.getByText("工人管理")).toBeInTheDocument();
    expect(screen.getByText("WK-001")).toBeInTheDocument();
    expect(screen.getByText("李工")).toBeInTheDocument();
  });

  it("renders capacity analysis and calls capacity APIs", async () => {
    renderPage(<CapacityAnalysis />);

    await waitFor(() => {
      expect(productionApi.capacity.oee).toHaveBeenCalled();
      expect(productionApi.capacity.bottlenecks).toHaveBeenCalled();
      expect(productionApi.capacity.trend).toHaveBeenCalled();
      expect(productionApi.capacity.forecast).toHaveBeenCalled();
    });

    expect(screen.getByText("产能分析")).toBeInTheDocument();
    expect(screen.getByText("平均产能利用率")).toBeInTheDocument();
    expect(screen.getAllByText("装配线A").length).toBeGreaterThan(0);
  });

  it("renders assembly kit board with wrapped dashboard data", async () => {
    renderPage(<AssemblyKitBoard />);

    await waitFor(() => {
      expect(assemblyKitApi.dashboard).toHaveBeenCalled();
      expect(assemblyKitApi.getShortageAlerts).toHaveBeenCalled();
    });

    expect(screen.getByText("装配齐套看板")).toBeInTheDocument();
    expect(screen.getAllByText("项目Alpha").length).toBeGreaterThan(0);
    expect(screen.getByText("可立即开工")).toBeInTheDocument();
  });
});
