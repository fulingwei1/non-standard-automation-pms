import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter, MemoryRouter, Routes } from "react-router-dom";
import { ProjectRoutes } from "../projectRoutes";
import { buildProjectManagementCenterSearch } from "../projectRedirects";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("../../../components/common/ProtectedRoute", () => ({
  ProjectReviewProtectedRoute: ({ children }) => children,
}));

vi.mock("../../../pages/ProjectManagementCenter", async () => {
  const { useLocation } = await vi.importActual("react-router-dom");

  return {
    default: function ProjectManagementCenterRouteProbe() {
      const location = useLocation();

      return <div>项目管理中心 {location.search}</div>;
    },
  };
});

vi.mock("../../../pages/ProjectDetail", () => ({
  default: () => <div>项目详情页</div>,
}));

describe("ProjectRoutes project management center compatibility", () => {
  it("builds unified center redirects while preserving legacy filters", () => {
    expect(
      buildProjectManagementCenterSearch("board", "?view=list&owner=me", {
        view: "pipeline",
      }),
    ).toBe("?tab=board&view=pipeline&owner=me");
  });

  it.each([
    ["/project/dashboard-center", "?tab=dashboard"],
    ["/project/cost-center", "?tab=cost"],
    ["/gantt-resource", "?tab=planning"],
    ["/ai-project-tools", "?tab=ai"],
    ["/project-closing", "?tab=closing"],
    ["/progress-tracking/reports", "?tab=tracking&trackingTab=reports"],
  ])("redirects legacy project entry %s to the unified center", async (entry, expectedSearch) => {
    render(
      <MemoryRouter initialEntries={[entry]}>
        <Routes>{ProjectRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText(`项目管理中心 ${expectedSearch}`)).toBeInTheDocument();
  });

  it("preserves filters when redirecting the legacy project board route", async () => {
    window.history.pushState({}, "", "/board?view=list&owner=me");

    render(
      <BrowserRouter>
        <Routes>{ProjectRoutes()}</Routes>
      </BrowserRouter>,
    );

    expect(
      await screen.findByText("项目管理中心 ?tab=board&view=list&owner=me"),
    ).toBeInTheDocument();
  });

  it("keeps project detail routes as deep links", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/123"]}>
        <Routes>{ProjectRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("项目详情页")).toBeInTheDocument();
    expect(screen.queryByText(/项目管理中心/)).not.toBeInTheDocument();
  });
});
