/**
 * ProjectBoard 组件测试
 * 覆盖：页面渲染、项目列表加载、错误态与新建项目按钮
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProjectBoard from "../ProjectBoard/index";
import { projectApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  projectApi: {
    list: vi.fn(),
    getBoard: vi.fn(),
    update: vi.fn(),
    create: vi.fn(),
    recommendTemplates: vi.fn().mockResolvedValue({ data: { recommendations: [] } }),
    createFromTemplate: vi.fn(),
  },
  milestoneApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
  stageViewsApi: {
    getPipeline: vi.fn().mockResolvedValue({ data: { items: [], available_templates: [] } }),
    getTimeline: vi.fn().mockResolvedValue({ data: { items: [] } }),
    getTree: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const invalid = new Set([
          "initial",
          "animate",
          "exit",
          "variants",
          "transition",
          "whileHover",
          "whileTap",
          "whileInView",
          "layout",
          "layoutId",
          "drag",
          "dragConstraints",
          "onDragEnd",
        ]);
        const filtered = Object.fromEntries(
          Object.entries(props).filter(([k]) => !invalid.has(k)),
        );
        const Tag = typeof tag === "string" ? tag : "div";
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

describe("ProjectBoard", () => {
  const mockProjects = [
    {
      id: 1,
      project_code: "PROJ-2024-001",
      project_name: "智能制造系统",
      stage: "S3",
      status: "ST05",
      health: "H1",
      progress_pct: 65,
      pm_name: "张三",
    },
    {
      id: 2,
      project_code: "PROJ-2024-002",
      project_name: "ERP系统升级",
      stage: "S1",
      status: "ST01",
      health: "H2",
      progress_pct: 15,
      pm_name: "李四",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    projectApi.list.mockResolvedValue({
      data: { items: mockProjects, total: 2 },
    });
  });

  const renderPage = () =>
    render(
      <MemoryRouter>
        <ProjectBoard />
      </MemoryRouter>,
    );

  it("renders page header and loads projects on mount", async () => {
    renderPage();

    expect(
      (await screen.findAllByText("项目中心")).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: /新建项目/ }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
    });
  });

  it("shows error state when projectApi.list rejects", async () => {
    projectApi.list.mockRejectedValueOnce(new Error("加载失败"));

    renderPage();

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
    });

    expect(
      await screen.findByRole("button", { name: /重试/ }),
    ).toBeInTheDocument();
  });
});
