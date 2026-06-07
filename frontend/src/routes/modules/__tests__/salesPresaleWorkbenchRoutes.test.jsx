import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SalesRoutes } from "../salesRoutes";

vi.mock("../../../pages/SalesDashboard", () => ({
  default: () => <div>销售仪表盘</div>,
}));

vi.mock("../../../pages/SalesPresaleWorkbench", () => ({
  default: () => <div>销售侧售前旧视图</div>,
}));

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
});
