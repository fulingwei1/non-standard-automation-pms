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
      "/presales/technical-solutions?tab=parameters",
    );
    expect(screen.getByRole("link", { name: /售前任务/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews",
    );
    expect(
      screen
        .getAllByRole("link", { name: /查看全部/ })
        .some((link) => link.getAttribute("href") === "/presales/technical-solutions?tab=reviews"),
    ).toBe(true);
  });

  it("links recent tickets and solutions back into their sales support context", async () => {
    presaleWorkbenchApiMock.loadOverview.mockResolvedValueOnce({
      tickets: {
        items: [
          {
            id: 501,
            ticket_no: "PST-501",
            title: "FCT 线体评估",
            status: "IN_PROGRESS",
            lead_id: 2026,
            opportunity_id: 2,
            project_id: 42,
          },
        ],
        total: 1,
      },
      solutions: {
        items: [
          {
            id: 88,
            name: "FCT 自动化方案",
            status: "DRAFT",
            ticket_id: 501,
            lead_id: 2026,
            opportunity_id: 2,
            project_id: 42,
          },
        ],
        total: 1,
      },
      templates: {
        assessment: { items: [], total: 0 },
        technical: { items: [], total: 0 },
      },
      funnel: {
        summary: { leads: 0, opportunities: 0, quotes: 0, contracts: 0 },
        health: {
          overall_health: { score: 80, level: "GOOD" },
          key_metrics: { target_coverage: 100 },
        },
        dwellAlerts: { items: [], total: 0 },
        conversion: { stages: [] },
      },
      meta: { failures: [] },
    });

    render(
      <MemoryRouter>
        <SalesPresaleWorkbench />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("link", { name: /PST-501/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
    expect(screen.getByRole("link", { name: /FCT 自动化方案/ })).toHaveAttribute(
      "href",
      "/solutions/88?ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });
});
