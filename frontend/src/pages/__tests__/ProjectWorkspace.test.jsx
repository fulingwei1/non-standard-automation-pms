import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProjectWorkspace from "../ProjectWorkspace";
import { projectWorkspaceApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  projectWorkspaceApi: {
    getWorkspace: vi.fn(),
  },
}));

vi.mock("../../components/project/ProjectBonusPanel", () => ({
  default: () => <div>奖金面板</div>,
}));

vi.mock("../../components/project/ProjectMeetingPanel", () => ({
  default: () => <div>会议面板</div>,
}));

vi.mock("../../components/project/ProjectIssuePanel", () => ({
  default: () => <div>问题面板</div>,
}));

vi.mock("../../components/project/SolutionLibrary", () => ({
  default: () => <div>解决方案库</div>,
}));

describe("ProjectWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sales and presale handover context in the overview", async () => {
    projectWorkspaceApi.getWorkspace.mockResolvedValue({
      data: {
        project: {
          id: 1,
          project_name: "FCT整线项目",
          project_code: "PRJ-001",
          progress_pct: 20,
          health: "H1",
          contract_amount: 580000,
        },
        team: [],
        tasks: [],
        bonus: {},
        meetings: {},
        issues: {},
        solutions: {},
        documents: [],
        handover_context: {
          contract: {
            contract_code: "CT-001",
            total_amount: 580000,
          },
          opportunity: {
            opp_code: "OPP-001",
            opp_name: "电源测试线商机",
          },
          quote: {
            quote_code: "QT-001",
            version: {
              cost_total: 360000,
              total_price: 580000,
              gross_margin: 37.93,
            },
          },
          presale_solutions: [
            {
              solution_no: "SOL-001",
              name: "FCT测试方案",
              estimated_cost: 355000,
              suggested_price: 580000,
            },
          ],
          baseline_cost: {
            quote_cost_total: 360000,
            presale_estimated_cost: 355000,
          },
          handover_status: {
            ready: true,
            missing: [],
          },
        },
      },
    });

    render(
      <MemoryRouter initialEntries={["/projects/1/workspace"]}>
        <Routes>
          <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("项目交接包")).toBeInTheDocument();
    expect(screen.getByText("CT-001")).toBeInTheDocument();
    expect(screen.getByText("OPP-001")).toBeInTheDocument();
    expect(screen.getByText("QT-001")).toBeInTheDocument();
    expect(screen.getByText("FCT测试方案")).toBeInTheDocument();
    expect(screen.getByText(/[¥￥]360,000.00/)).toBeInTheDocument();
  });
});
