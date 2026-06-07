import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import * as Router from "react-router-dom";
import { ProjectRoutes } from "../projectRoutes";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("../../../components/common/ProtectedRoute", () => ({
  ProjectReviewProtectedRoute: ({ children }) => children,
}));

vi.mock("../../../pages/PresalesTasks", () => ({
  default: () => <div>项目侧售前工单旧视图</div>,
}));

function LocationProbe() {
  const location = Router.useLocation();

  return <div>售前技术支持中心 {location.search}</div>;
}

describe("ProjectRoutes presales task compatibility", () => {
  it("redirects project presales tasks to the unified review tab and preserves filters", async () => {
    window.history.pushState({}, "", "/project-presales-tasks?projectId=42&status=assigned");

    render(
      <Router.BrowserRouter>
        <Router.Routes>
          {ProjectRoutes()}
          <Router.Route path="/presales/technical-solutions" element={<LocationProbe />} />
        </Router.Routes>
      </Router.BrowserRouter>,
    );

    expect(
      await screen.findByText("售前技术支持中心 ?tab=reviews&project_id=42&status=assigned"),
    ).toBeInTheDocument();
    expect(screen.queryByText("项目侧售前工单旧视图")).not.toBeInTheDocument();
  });
});
