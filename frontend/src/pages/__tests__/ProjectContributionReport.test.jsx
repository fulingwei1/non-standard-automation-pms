import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ProjectContributionReport from "../ProjectContributionReport";
import { projectContributionApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  projectContributionApi: {
    getReport: vi.fn(),
    calculate: vi.fn(),
    rateMember: vi.fn(),
  },
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => ({ id: "42" }),
  };
});

vi.mock("../../components/project/ContributionChart", () => ({
  default: ({ contributions }) => (
    <div data-testid="contribution-chart">{contributions.length}</div>
  ),
}));

const reportPayload = {
  project_id: 42,
  period: null,
  total_members: 1,
  total_task_count: 3,
  total_hours: 12.5,
  total_bonus: 1000,
  contributions: [
    {
      user_id: 7,
      user_name: "Alice",
      period: "pr30222",
      task_count: 3,
      actual_hours: 12.5,
      deliverable_count: 2,
      issue_resolved: 1,
      bonus_amount: 1000,
      contribution_score: 8.5,
      pm_rating: 4,
    },
  ],
  top_contributors: [
    {
      user_id: 7,
      user_name: "Alice",
      period: "pr30222",
      contribution_score: 8.5,
    },
  ],
};

describe("ProjectContributionReport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    projectContributionApi.getReport.mockResolvedValue({ data: reportPayload });
    projectContributionApi.calculate.mockResolvedValue({ data: { code: 200 } });
    projectContributionApi.rateMember.mockResolvedValue({ data: { code: 200 } });
  });

  it("loads all periods by default instead of forcing the current month", async () => {
    render(<ProjectContributionReport />);

    await waitFor(() => {
      expect(projectContributionApi.getReport).toHaveBeenCalledWith("42", {});
    });
    expect(screen.getAllByText(/全部周期/).length).toBeGreaterThan(0);
    expect(screen.getByText("pr30222")).toBeInTheDocument();
  });

  it("calculates the selected period and refreshes the report", async () => {
    render(<ProjectContributionReport />);

    await waitFor(() => {
      expect(screen.getAllByText("Alice").length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText("统计周期"), {
      target: { value: "2026-06" },
    });
    fireEvent.click(screen.getByRole("button", { name: "计算贡献" }));

    await waitFor(() => {
      expect(projectContributionApi.calculate).toHaveBeenCalledWith("42", "2026-06");
    });
    expect(projectContributionApi.getReport).toHaveBeenLastCalledWith("42", {
      period: "2026-06",
    });
  });

  it("rates a contribution row using the row period", async () => {
    render(<ProjectContributionReport />);

    await waitFor(() => {
      expect(screen.getAllByText("Alice").length).toBeGreaterThan(0);
    });
    fireEvent.change(screen.getByLabelText("PM评分-Alice"), {
      target: { value: "5" },
    });

    await waitFor(() => {
      expect(projectContributionApi.rateMember).toHaveBeenCalledWith("42", 7, {
        period: "pr30222",
        pm_rating: 5,
      });
    });
  });
});
