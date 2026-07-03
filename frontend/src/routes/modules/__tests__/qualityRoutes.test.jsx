import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes } from "react-router-dom";
import { QualityRoutes } from "../qualityRoutes";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return actual;
});

vi.mock("../../../components/common/ProtectedRoute", () => ({
  ProtectedRoute: ({ children }) => children,
  QualityProtectedRoute: ({ children }) => children,
}));

vi.mock("../../../pages/quality/IssueDetail", () => ({
  default: () => <div>通用问题详情</div>,
}));

vi.mock("../../../pages/quality/QualityIssues", () => ({
  default: () => <div>质量问题列表</div>,
}));

vi.mock("../../../pages/quality/AcceptanceDetail", () => ({
  default: () => <div>验收详情</div>,
}));

vi.mock("../../../pages/quality/AcceptanceList", () => ({
  default: () => <div>验收列表</div>,
}));

describe("QualityRoutes issue detail compatibility", () => {
  it("mounts issue detail on the cross-module /issues/:id deep link", async () => {
    render(
      <MemoryRouter initialEntries={["/issues/47"]}>
        <Routes>{QualityRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("通用问题详情")).toBeInTheDocument();
  });

  it("does not treat the quality issue new route as an issue id", async () => {
    render(
      <MemoryRouter initialEntries={["/quality/issues/new"]}>
        <Routes>{QualityRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("质量问题列表")).toBeInTheDocument();
  });

  it("does not treat the quality acceptance new route as an acceptance id", async () => {
    render(
      <MemoryRouter initialEntries={["/quality/acceptance/new"]}>
        <Routes>{QualityRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("验收列表")).toBeInTheDocument();
  });
});
