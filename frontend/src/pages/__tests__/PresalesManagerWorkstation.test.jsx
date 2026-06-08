import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesManagerWorkstation from "../PresalesManagerWorkstation";

const dashboardDataMock = vi.hoisted(() => ({
  useDashboardData: vi.fn(),
}));

vi.mock("../PresalesManagerWorkstation/hooks/useDashboardData", () => dashboardDataMock);

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

describe("PresalesManagerWorkstation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dashboardDataMock.useDashboardData.mockReturnValue({
      loading: false,
      error: null,
      overallStats: {
        teamSize: 2,
        activeSolutions: 1,
        pendingReview: 1,
        activeBids: 1,
        urgentBids: 1,
        monthlyOutput: 1200000,
        monthlyTarget: 1500000,
        achievementRate: 80,
        solutionQuality: 92,
      },
      teamPerformance: [
        {
          id: 1,
          name: "售前工程师",
          role: "售前技术工程师",
          activeSolutions: 2,
          completedThisMonth: 1,
          pendingReview: 1,
          avgQuality: 90,
          status: "excellent",
        },
      ],
      pendingReviews: [
        {
          id: 88,
          title: "FCT 自动化方案",
          customer: "金凯博客户",
          author: "售前工程师",
          version: "V1.0",
          submitTimeLabel: "06-08 10:00",
          amount: 1200000,
          priority: "high",
          daysWaiting: 2,
        },
      ],
      ongoingSolutions: [
        {
          id: 88,
          name: "FCT 自动化方案",
          customer: "金凯博客户",
          author: "售前工程师",
          version: "V1.0",
          status: "评审中",
          statusColor: "bg-amber-500",
          progress: 80,
          amount: 1200000,
          deadline: "06-30",
        },
      ],
      biddingProjects: [
        {
          id: 301,
          name: "CVTE 投标项目",
          customer: "CVTE",
          daysLeft: 5,
          status: "准备中",
          statusColor: "bg-amber-500",
          amount: 3000000,
          responsible: "售前工程师",
          progress: 60,
        },
      ],
    });
  });

  it("preserves upstream support context in manager workbench technical links", () => {
    render(
      <MemoryRouter
        initialEntries={[
          "/presales/workbench/manager?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
        ]}
      >
        <PresalesManagerWorkstation />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: /查看详情/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /方案中心/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: /查看全部方案/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
    expect(screen.getByRole("link", { name: "全部" })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=bids&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );
  });
});
