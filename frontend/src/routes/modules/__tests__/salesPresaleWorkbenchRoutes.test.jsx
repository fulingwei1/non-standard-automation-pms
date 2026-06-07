import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter, MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { SalesRoutes } from "../salesRoutes";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("../../../pages/SalesDashboard", () => ({
  default: () => <div>销售仪表盘</div>,
}));

vi.mock("../../../pages/SalesPresaleWorkbench", () => ({
  default: () => <div>销售侧售前旧视图</div>,
}));

vi.mock("../../../pages/PresalesTasks", () => ({
  default: () => <div>销售侧售前工单旧视图</div>,
}));

function LocationProbe() {
  const location = useLocation();

  return <div>售前技术支持中心 {location.search}</div>;
}

describe("SalesRoutes presales workbench compatibility", () => {
  it("redirects the sales presale workbench route to the unified presales entry", async () => {
    render(
      <MemoryRouter initialEntries={["/sales/presale-workbench"]}>
        <Routes>
          {SalesRoutes()}
          <Route path="/presales/workbench" element={<div>售前技术支持工作台</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持工作台")).toBeInTheDocument();
  });

  it("redirects the plural sales presales workbench route to the unified presales entry", async () => {
    render(
      <MemoryRouter initialEntries={["/sales/presales-workbench"]}>
        <Routes>
          {SalesRoutes()}
          <Route path="/presales/workbench" element={<div>售前技术支持工作台</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持工作台")).toBeInTheDocument();
  });

  it("redirects sales presales tasks to the unified review tab and preserves filters", async () => {
    window.history.pushState({}, "", "/sales/presales-tasks?type=review&status=reviewing");

    render(
      <BrowserRouter>
        <Routes>
          {SalesRoutes()}
          <Route
            path="/presales/technical-solutions"
            element={<LocationProbe />}
          />
        </Routes>
      </BrowserRouter>,
    );

    expect(await screen.findByText(/售前技术支持中心/)).toBeInTheDocument();
    expect(screen.queryByText("销售侧售前工单旧视图")).not.toBeInTheDocument();
  });
});
