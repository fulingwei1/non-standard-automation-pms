import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import BudgetManagement from "../BudgetManagement";
import GanttDependency from "../GanttDependency";
import TaskCenter from "../TaskCenter";
import TimeCostMarginFlow from "../TimeCostMarginFlow";
import {
  costApi,
  ganttDependencyApi,
  projectApi,
  taskCenterApi,
} from "../../services/api";

vi.mock("../../services/api", () => ({
  projectApi: {
    list: vi.fn(),
    getTimesheetSummary: vi.fn(),
  },
  costApi: {
    getProjectSummary: vi.fn(),
  },
  ganttDependencyApi: {
    getGantt: vi.fn(),
    getCriticalPath: vi.fn(),
    createDependency: vi.fn(),
    deleteDependency: vi.fn(),
  },
  taskCenterApi: {
    getMyTasks: vi.fn(),
    updateTask: vi.fn(),
    completeTask: vi.fn(),
  },
  progressApi: {
    tasks: {
      updateProgress: vi.fn(),
    },
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get:
        (_, tag) =>
        ({ children, ...props }) => {
          const ignored = new Set([
            "initial",
            "animate",
            "exit",
            "variants",
            "transition",
            "whileHover",
            "whileTap",
            "layout",
          ]);
          const filtered = Object.fromEntries(
            Object.entries(props).filter(([key]) => !ignored.has(key)),
          );
          const Tag = typeof tag === "string" ? tag : "div";
          return <Tag {...filtered}>{children}</Tag>;
        },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearchParams: vi.fn(),
  };
});

const mockProject = {
  id: 42,
  project_code: "PRJ-42",
  project_name: "合同转项目",
  stage: "S1",
  health: "H1",
  budget_amount: 100000,
  actual_cost: 20000,
  contract_amount: 180000,
  contract_id: 9,
  opportunity_id: 2,
};

const renderWithRouter = (ui) => render(<MemoryRouter>{ui}</MemoryRouter>);

describe("Project management downstream context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem(
      "user",
      JSON.stringify({ id: 1, username: "admin", role: "admin" }),
    );
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=planning&project_id=42&contract_id=9&opportunity_id=2"),
      vi.fn(),
    ]);
    projectApi.list.mockResolvedValue({
      data: { items: [mockProject], total: 1 },
    });
    costApi.getProjectSummary.mockResolvedValue({
      data: { total_cost: 20000 },
    });
    projectApi.getTimesheetSummary.mockResolvedValue({
      data: { total_hours: 16, record_count: 2, pending_sync_count: 0 },
    });
    ganttDependencyApi.getGantt.mockResolvedValue({
      data: { tasks: [], dependencies: [] },
    });
    ganttDependencyApi.getCriticalPath.mockResolvedValue({
      data: { critical_path_task_ids: [], total_duration_days: 0 },
    });
    taskCenterApi.getMyTasks.mockResolvedValue({
      data: { items: [] },
    });
  });

  it("passes upstream context to budget project loading", async () => {
    renderWithRouter(<BudgetManagement embedded />);

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 8,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
    expect(costApi.getProjectSummary).not.toHaveBeenCalled();
  });

  it("passes upstream context to time-cost-margin project loading", async () => {
    renderWithRouter(<TimeCostMarginFlow embedded />);

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
    await waitFor(() => {
      expect(projectApi.getTimesheetSummary).toHaveBeenCalledWith(42, {});
    });
  });

  it("passes upstream context to task gantt project loading", async () => {
    renderWithRouter(<GanttDependency />);

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 200,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });

  it("passes upstream project context to task center loading", async () => {
    renderWithRouter(<TaskCenter />);

    await waitFor(() => {
      expect(taskCenterApi.getMyTasks).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: "42",
        }),
      );
    });
  });
});
