import { render, screen } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectManagementCenter from "../ProjectManagementCenter";

const permissionMock = vi.hoisted(() => ({
  hasPermission: vi.fn(() => true),
  hasAnyPermission: vi.fn(() => true),
}));

vi.mock("../../hooks/usePermission", () => ({
  usePermission: () => permissionMock,
}));

vi.mock("../ProjectBoard", () => ({
  default: () => <div>项目看板</div>,
}));

vi.mock("../ProjectDashboardCenter", () => ({
  default: () => <div>项目驾驶舱</div>,
}));

vi.mock("../TaskCenter", () => ({
  default: () => <div>任务中心</div>,
}));

vi.mock("../GanttAndResource", () => ({
  default: () => <div>计划资源</div>,
}));

vi.mock("../ProjectCostCenter", () => ({
  default: () => <div>项目成本</div>,
}));

vi.mock("../ProjectClosing", () => ({
  default: () => <div>项目收尾</div>,
}));

vi.mock("../AIProjectTools", () => ({
  default: () => <div>AI工具</div>,
}));

vi.mock("../ScheduleBoard", () => ({
  default: () => <div>排期看板</div>,
}));

vi.mock("../ProgressReport", () => ({
  default: () => <div>进度报告</div>,
}));

vi.mock("../MilestoneManagement", () => ({
  default: () => <div>里程碑</div>,
}));

vi.mock("../WBSTemplateManagement", () => ({
  default: () => <div>WBS模板</div>,
}));

describe("ProjectManagementCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    permissionMock.hasPermission.mockReturnValue(true);
    permissionMock.hasAnyPermission.mockReturnValue(true);
  });

  it("offers a project presales handover tab with unified presales links preserving context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams(
        "tab=presales&project_id=42&ticket_id=91&opportunity_id=2&lead_id=2026",
      ),
      vi.fn(),
    ]);

    render(
      <MemoryRouter
        initialEntries={[
          "/project/management-center?tab=presales&project_id=42&ticket_id=91&opportunity_id=2&lead_id=2026",
        ]}
      >
        <ProjectManagementCenter />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "售前" })).toBeInTheDocument();
    expect(await screen.findByText("售前交接")).toBeInTheDocument();

    expect(screen.getByRole("link", { name: /工单看板/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&ticket_id=91&lead_id=2026&opportunity_id=2&project_id=42",
    );
    expect(screen.getByRole("link", { name: /需求调研/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=surveys&ticket_id=91&lead_id=2026&opportunity_id=2&project_id=42",
    );
    expect(screen.getByRole("link", { name: /方案管理/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=solutions&ticket_id=91&lead_id=2026&opportunity_id=2&project_id=42",
    );
    expect(screen.getByRole("link", { name: /项目交接包/ })).toHaveAttribute(
      "href",
      "/projects/42/workspace?ticket_id=91&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });
});
