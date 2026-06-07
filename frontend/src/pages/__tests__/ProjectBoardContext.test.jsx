import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import ProjectBoard from "../ProjectBoard";
import { projectApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  projectApi: {
    list: vi.fn(),
    create: vi.fn(),
    recommendTemplates: vi.fn().mockResolvedValue({ data: { recommendations: [] } }),
  },
  milestoneApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get:
        (_, tag) =>
        ({ children, ...props }) => {
          const Tag = typeof tag === "string" ? tag : "div";
          return <Tag {...props}>{children}</Tag>;
        },
    },
  ),
}));

vi.mock("../../components/layout/PageHeader", () => ({
  PageHeader: ({ title, actions }) => (
    <header>
      <h1>{title}</h1>
      {actions}
    </header>
  ),
}));

vi.mock("../../components/board", () => ({
  BoardFilters: ({ filterMode }) => (
    <div data-testid="board-filters" data-filter-mode={filterMode} />
  ),
  BoardColumn: ({ projects = [] }) => (
    <section>
      {projects.map((project) => (
        <div key={project.id}>{project.project_name}</div>
      ))}
    </section>
  ),
}));

vi.mock("../../components/project", () => ({
  ProjectCard: ({ project }) => <div>{project.project_name}</div>,
  ProjectFormStepper: () => null,
}));

vi.mock("../../components/ui/button", () => ({
  Button: ({ children, ...props }) => <button {...props}>{children}</button>,
}));

vi.mock("../../components/ui", () => ({
  ApiIntegrationError: () => <div>接口异常</div>,
  Skeleton: () => <div data-testid="skeleton" />,
  Input: (props) => <input {...props} />,
  Button: ({ children, ...props }) => <button {...props}>{children}</button>,
}));

vi.mock("../../pages/ProjectStageView/components", () => ({
  PipelineView: () => <div>流水线</div>,
}));

vi.mock("../../pages/ProjectStageView/hooks", () => ({
  useStageViews: () => ({
    data: { available_templates: [] },
    pipelineData: null,
    loading: false,
    updateFilters: vi.fn(),
    loadPipelineData: vi.fn(),
    loadTimelineData: vi.fn(),
    loadTreeData: vi.fn(),
  }),
  useStageActions: () => ({}),
}));

vi.mock("../ProjectBoard/MatrixView", () => ({
  default: () => <div>矩阵</div>,
}));

vi.mock("../ProjectBoard/ListView", () => ({
  default: ({ projects = [] }) => (
    <div>
      {projects.map((project) => (
        <div key={project.id}>{project.project_name}</div>
      ))}
    </div>
  ),
}));

vi.mock("../ProjectBoard/ProjectDetailView", () => ({
  default: () => <div>项目详情</div>,
}));

vi.mock("../../hooks/useRoleFilter", () => ({
  useRoleFilter: () => ({
    relevantStages: [],
    isProjectRelevant: () => true,
    isStageRelevant: () => true,
    filterProjects: (projects, mode) => (mode === "all" ? projects : []),
    groupByStage: (projects) =>
      projects.reduce((grouped, project) => {
        const stage = project.stage || "S1";
        grouped[stage] = grouped[stage] || [];
        grouped[stage].push(project);
        return grouped;
      }, {}),
    stageStats: {},
  }),
}));

const renderProjectBoard = () =>
  render(
    <MemoryRouter>
      <ProjectBoard />
    </MemoryRouter>,
  );

describe("ProjectBoard context handoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([
      new URLSearchParams("tab=board&project_id=42&contract_id=9&opportunity_id=2"),
      vi.fn(),
    ]);
    projectApi.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 42,
            project_code: "PRJ-42",
            project_name: "合同转项目",
            stage: "S1",
            health: "H1",
            contract_id: 9,
            opportunity_id: 2,
          },
        ],
      },
    });
  });

  it("passes project, contract, and opportunity context filters to the project list API", async () => {
    renderProjectBoard();

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        project_id: "42",
        contract_id: "9",
        opportunity_id: "2",
      });
    });
  });

  it("shows all projects by default when opened from an exact upstream context", async () => {
    renderProjectBoard();

    const filters = await screen.findByTestId("board-filters");
    expect(filters).toHaveAttribute("data-filter-mode", "all");
    expect(await screen.findByText("合同转项目")).toBeInTheDocument();
  });
});
