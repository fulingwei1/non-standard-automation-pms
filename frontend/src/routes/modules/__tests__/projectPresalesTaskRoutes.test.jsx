import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
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
  const location = useLocation();

  return <div>售前技术支持中心 {location.search}</div>;
}

describe("ProjectRoutes presales task compatibility", () => {
  it("redirects project presales tasks to the unified review tab and preserves filters", async () => {
    window.history.pushState({}, "", "/project-presales-tasks?projectId=42&status=assigned");

    render(
      <BrowserRouter>
        <Routes>
          {ProjectRoutes()}
          <Route path="/presales/technical-solutions" element={<LocationProbe />} />
        </Routes>
      </BrowserRouter>,
    );

    expect(await screen.findByText(/售前技术支持中心/)).toBeInTheDocument();
    expect(screen.queryByText("项目侧售前工单旧视图")).not.toBeInTheDocument();
  });
});
