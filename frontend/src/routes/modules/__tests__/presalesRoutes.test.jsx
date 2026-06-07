import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes } from "react-router-dom";
import { PresalesRoutes } from "../presalesRoutes";

vi.mock("../../../pages/TechnicalParameterManagement", () => ({
  default: () => <div>技术参数模板路由已挂载</div>,
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
});
