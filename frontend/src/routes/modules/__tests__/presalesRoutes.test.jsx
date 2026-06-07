import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes } from "react-router-dom";
import { PresalesRoutes } from "../presalesRoutes";

vi.mock("../../../pages/TechnicalParameterManagement", () => ({
  default: () => <div>技术参数模板路由已挂载</div>,
}));

vi.mock("../../../pages/PresalesWorkstation", () => ({
  default: () => <div>售前执行旧视图</div>,
}));

vi.mock("../../../pages/PresalesManagerWorkstation", () => ({
  default: () => <div>售前经理旧视图</div>,
}));

vi.mock("../../../hooks/usePermission", () => ({
  usePermission: () => ({
    hasPermission: () => false,
    isLoading: false,
    isSuperuser: false,
  }),
}));

describe("PresalesRoutes", () => {
  it("mounts the technical parameter management page", async () => {
    render(
      <MemoryRouter initialEntries={["/presales/technical-parameters"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("技术参数模板路由已挂载")).toBeInTheDocument();
  });

  it("mounts the unified presales workbench as the primary entry", async () => {
    render(
      <MemoryRouter initialEntries={["/presales/workbench"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持工作台")).toBeInTheDocument();
    expect(screen.getByText("销售协同")).toBeInTheDocument();
    expect(screen.getByText("售前执行")).toBeInTheDocument();
    expect(screen.getByText("经理调度")).toBeInTheDocument();
  });

  it("redirects the legacy presales workbench route to the unified entry", async () => {
    render(
      <MemoryRouter initialEntries={["/presales-workbench"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持工作台")).toBeInTheDocument();
  });
});
