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

describe("QualityRoutes issue detail compatibility", () => {
  it("mounts issue detail on the cross-module /issues/:id deep link", async () => {
    render(
      <MemoryRouter initialEntries={["/issues/47"]}>
        <Routes>{QualityRoutes()}</Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("通用问题详情")).toBeInTheDocument();
  });
});
