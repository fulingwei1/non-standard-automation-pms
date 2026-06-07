import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import AIProjectTools from "../AIProjectTools";
import MilestoneManagement from "../MilestoneManagement";
import ProjectHealthMonitor from "../ProjectHealthMonitor";
import ScheduleBoard from "../ScheduleBoard";
import WBSTemplateManagement from "../WBSTemplateManagement";
import { milestoneApi, progressApi, projectApi } from "../../services/api";
import { materialReadinessApi } from "../../services/api/materialReadiness";

const routeState = vi.hoisted(() => ({
  pathname: "/project/management-center",
  search: "?tab=ai&project_id=42&contract_id=9&opportunity_id=2",
  params: {},
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useLocation: () => ({
      pathname: routeState.pathname,
      search: routeState.search,
      hash: "",
      state: null,
      key: "test",
    }),
    useNavigate: () => vi.fn(),
    useParams: () => routeState.params,
    useSearchParams: () => [
      new URLSearchParams(routeState.search),
      vi.fn(),
    ],
  };
});

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

vi.mock("../../components/schedule-board", () => ({
  StatsCards: () => <div>排期统计</div>,
  ViewControls: () => <div>视图切换</div>,
  StageColumn: () => <div>阶段列</div>,
  ScheduleGanttView: () => <div>甘特</div>,
  ScheduleCalendarView: () => <div>日历</div>,
  ResourceHeatMap: () => <div>资源热力</div>,
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(),
}));

vi.mock("../../services/api/materialReadiness", () => ({
  materialReadinessApi: {
    getBatchKitRate: vi.fn(),
  },
}));

vi.mock("../../services/api", () => ({
  projectApi: {
    list: vi.fn(),
    get: vi.fn(),
  },
  milestoneApi: {
    list: vi.fn(),
    listAll: vi.fn(),
    create: vi.fn(),
  },
  progressApi: {
    reports: {
      getSummary: vi.fn(),
    },
    wbsTemplates: {
      list: vi.fn(),
      getTasks: vi.fn(),
      create: vi.fn(),
    },
    projects: {
      initWBS: vi.fn(),
    },
  },
  marginPredictionApi: {},
}));

const upstreamSearch = "?tab=ai&project_id=42&contract_id=9&opportunity_id=2";

const mockProject = {
  id: 42,
  project_code: "PRJ-42",
  project_name: "合同转项目",
  customer_name: "测试客户",
  stage: "S3",
  health: "H1",
  contract_id: 9,
  opportunity_id: 2,
};

function renderAt(element, path = `/project/management-center${upstreamSearch}`) {
  const url = new URL(path, "https://example.test");
  routeState.pathname = url.pathname;
  routeState.search = url.search;
  routeState.params = {};
  return render(<MemoryRouter initialEntries={[path]}>{element}</MemoryRouter>);
}

describe("Project management child pages context handoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    projectApi.list.mockResolvedValue({
      data: { items: [mockProject], total: 1 },
    });
    projectApi.get.mockResolvedValue({ data: mockProject });
    milestoneApi.list.mockResolvedValue({ data: [] });
    milestoneApi.listAll.mockResolvedValue({ data: { items: [] } });
    progressApi.reports.getSummary.mockResolvedValue({ data: {} });
    progressApi.wbsTemplates.list.mockResolvedValue({ data: { items: [] } });
    materialReadinessApi.getBatchKitRate.mockResolvedValue({
      data: { kit_rates: { 42: { rate: 80, status: "warning" } } },
    });
  });

  it("scopes AI project tools project loading to upstream project context", async () => {
    renderAt(<AIProjectTools embedded searchParamName="aiTab" />);

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 100,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });

  it("scopes project health monitor to upstream project context", async () => {
    renderAt(<ProjectHealthMonitor embedded />);

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 100,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });

  it("scopes schedule board project loading to upstream project context", async () => {
    renderAt(<ScheduleBoard />, "/project/management-center?tab=tracking&trackingTab=schedule&project_id=42&contract_id=9&opportunity_id=2");

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 100,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });

  it("scopes global milestone project and milestone loading to upstream project context", async () => {
    renderAt(<MilestoneManagement />, "/project/management-center?tab=tracking&trackingTab=milestones&project_id=42&contract_id=9&opportunity_id=2");

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 200,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
    await waitFor(() => {
      expect(milestoneApi.listAll).toHaveBeenCalledWith(
        expect.objectContaining({ project_id: "42" }),
      );
    });
  });

  it("scopes WBS initialization project choices to upstream project context", async () => {
    renderAt(<WBSTemplateManagement />, "/project/management-center?tab=tracking&trackingTab=wbs&project_id=42&contract_id=9&opportunity_id=2");

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 1000,
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });
});
