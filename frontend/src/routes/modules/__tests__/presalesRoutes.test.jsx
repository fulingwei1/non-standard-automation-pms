import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import * as Router from "react-router-dom";
import { PresalesRoutes } from "../presalesRoutes";
import { buildPresalesCenterSearch } from "../presalesRedirects";

const { BrowserRouter, MemoryRouter, Routes } = Router;

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("../../../pages/PresalesReviewCenter", async () => {
  const { useLocation } = await vi.importActual("react-router-dom");

  return {
    default: function PresalesReviewCenterRouteProbe() {
      const location = useLocation();

      return <div>售前技术支持中心 {location.search}</div>;
    },
  };
});

vi.mock("../../../components/sales/AdvantageProducts", () => ({
  default: () => <div>优势产品入口</div>,
}));

vi.mock("../../../pages/PresalesWorkstation", () => ({
  default: () => <div>售前执行旧视图</div>,
}));

vi.mock("../../../pages/PresalesManagerWorkstation", () => ({
  default: () => <div>售前经理旧视图</div>,
}));

vi.mock("../../../pages/PresalesWorkbench", async () => {
  const { useLocation } = await vi.importActual("react-router-dom");

  return {
    default: function PresalesWorkbenchRouteProbe() {
      const location = useLocation();

      return (
        <div>
          <span>售前技术支持工作台 {location.search}</span>
          <span>销售协同</span>
          <span>售前执行</span>
          <span>经理调度</span>
        </div>
      );
    },
  };
});

vi.mock("../../../hooks/usePermission", () => ({
  usePermission: () => ({
    hasPermission: () => false,
    isLoading: false,
    isSuperuser: false,
  }),
}));

describe("PresalesRoutes", () => {
  it("preserves legacy filter params when building unified center redirects", () => {
    expect(buildPresalesCenterSearch("reviews", "?type=review&status=reviewing")).toBe(
      "?tab=reviews&type=review&status=reviewing",
    );
  });

  it("normalizes legacy camelCase context params when building unified redirects", () => {
    expect(
      buildPresalesCenterSearch(
        "reviews",
        "?projectId=42&opportunityId=2&ticketId=501&leadId=7",
      ),
    ).toBe("?tab=reviews&project_id=42&opportunity_id=2&ticket_id=501&lead_id=7");
  });

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

  it("preserves filters when redirecting the legacy presales task route", async () => {
    window.history.pushState({}, "", "/presales-tasks?type=review&status=reviewing");

    render(
      <BrowserRouter>
        <Routes>{PresalesRoutes()}</Routes>
      </BrowserRouter>,
    );

    expect(
      await screen.findByText("售前技术支持中心 ?tab=reviews&type=review&status=reviewing"),
    ).toBeInTheDocument();
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

  it("mounts the advantage products page as a reachable presales route", async () => {
    render(
      <MemoryRouter initialEntries={["/presales/advantage-products"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("优势产品入口")).toBeInTheDocument();
  });

  it("redirects the legacy presales workbench route to the unified entry", async () => {
    render(
      <MemoryRouter initialEntries={["/presales-workbench"]}>
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("售前技术支持工作台")).toBeInTheDocument();
  });

  it("preserves context params when redirecting the legacy presales workbench route", async () => {
    render(
      <MemoryRouter
        initialEntries={[
          "/presales-workbench?leadId=2026&opportunityId=2&ticketId=501&projectId=42",
        ]}
      >
        <Routes>{PresalesRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(
      await screen.findByText(
        "售前技术支持工作台 ?lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
      ),
    ).toBeInTheDocument();
  });
});
