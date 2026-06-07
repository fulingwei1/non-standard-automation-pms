import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import SalesPresaleWorkbench from "../SalesPresaleWorkbench";

const presaleWorkbenchApiMock = vi.hoisted(() => ({
  loadOverview: vi.fn(),
}));

vi.mock("../../services/api", () => ({
  presaleWorkbenchApi: presaleWorkbenchApiMock,
}));

describe("SalesPresaleWorkbench", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleWorkbenchApiMock.loadOverview.mockResolvedValue({
      tickets: { items: [], total: 0 },
      solutions: { items: [], total: 0 },
      templates: {
        assessment: { items: [], total: 0 },
        technical: {
          items: [{ id: 4, name: "FCT 技术参数模板" }],
          total: 1,
        },
      },
      funnel: {
        summary: {
          leads: 0,
          opportunities: 0,
          quotes: 0,
          contracts: 0,
        },
        health: {
          overall_health: { score: 80, level: "GOOD" },
          key_metrics: { target_coverage: 100 },
        },
        dwellAlerts: { items: [], total: 0 },
        conversion: { stages: [] },
      },
      meta: { failures: [] },
    });
  });

  it("provides a direct entry to technical parameter templates", async () => {
    render(
      <MemoryRouter>
        <SalesPresaleWorkbench />
      </MemoryRouter>,
    );

    expect(await screen.findByText("FCT 技术参数模板")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /管理技术参数/ })).toHaveAttribute(
      "href",
      "/presales/technical-parameters",
    );
  });
});
