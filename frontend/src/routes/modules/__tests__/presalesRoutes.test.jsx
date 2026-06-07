import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes } from "react-router-dom";
import { PresalesRoutes } from "../presalesRoutes";

vi.mock("../../../pages/PresalesReviewCenter", async () => {
  const { useLocation } = await vi.importActual("react-router-dom");

  return {
    default: function PresalesReviewCenterRouteProbe() {
      const location = useLocation();

      return <div>售前技术支持中心 {location.search}</div>;
    },
  };
});

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
  it("redirects the legacy technical parameter route to the unified center", async () => {
    render(
      <MemoryRouter initialEntries={["/presales/technical-parameters"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持中心 ?tab=parameters")).toBeInTheDocument();
  });

  it.each([
    ["/presales/cost-estimation", "?tab=cost"],
    ["/presales/solutions", "?tab=solutions"],
    ["/bidding", "?tab=bids"],
    ["/presales/templates", "?tab=knowledge"],
    ["/presales-tasks", "?tab=reviews"],
  ])("redirects legacy route %s to the unified center", async (entry, expectedSearch) => {
    render(
      <MemoryRouter initialEntries={[entry]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText(`售前技术支持中心 ${expectedSearch}`)).toBeInTheDocument();
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
