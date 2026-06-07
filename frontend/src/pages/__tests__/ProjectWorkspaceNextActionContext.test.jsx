import { describe, expect, it, beforeEach, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useSearchParams } from "react-router-dom";

import MaterialAnalysis from "../MaterialAnalysis";
import ECNManagement from "../ECNManagement";
import InspectionList from "../quality/InspectionList";
import AcceptanceList from "../quality/AcceptanceList";
import { purchaseApi } from "../../services/api";
import { ecnBomApi } from "../../services/api/ecnBom";
import { qualityApi } from "../../services/api/quality";
import { acceptanceApi } from "../../services/api/acceptance";

vi.mock("../../components/material-analysis", () => ({
  MaterialStatsOverview: () => <div>材料统计</div>,
}));

vi.mock("../../components/ui/select", () => ({
  Select: ({ value, onValueChange, children }) => (
    <select
      value={value ?? ""}
      onChange={(event) => onValueChange?.(event.target.value)}
    >
      {children}
    </select>
  ),
  SelectTrigger: ({ children }) => <>{children}</>,
  SelectValue: ({ placeholder }) => (
    placeholder ? <option value="">{placeholder}</option> : null
  ),
  SelectContent: ({ children }) => <>{children}</>,
  SelectItem: ({ value, children }) => <option value={value}>{children}</option>,
}));

vi.mock("../../services/api", () => ({
  purchaseApi: {
    kitRate: {
      dashboard: vi.fn(),
      getProjectMaterialStatus: vi.fn(),
      unified: vi.fn(),
      trend: vi.fn(),
    },
  },
}));

vi.mock("../../services/api/ecnBom", () => ({
  ecnBomApi: {
    list: vi.fn(),
    create: vi.fn(),
    getImpact: vi.fn(),
    applyToBom: vi.fn(),
  },
}));

vi.mock("../../services/api/quality", () => ({
  qualityApi: {
    inspection: {
      list: vi.fn(),
    },
  },
}));

vi.mock("../../services/api/acceptance", () => ({
  acceptanceApi: {
    orders: {
      list: vi.fn(),
    },
  },
}));

const renderAt = (element, path) => {
  const url = new URL(path, "http://localhost");
  useSearchParams.mockReturnValue([url.searchParams, vi.fn()]);
  return render(<MemoryRouter initialEntries={[path]}>{element}</MemoryRouter>);
};

describe("project workspace next-action context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    purchaseApi.kitRate.dashboard.mockResolvedValue({
      data: {
        projects: [
          {
            project_id: 42,
            project_code: "PRJ-42",
            project_name: "合同转项目",
            total_items: 10,
            fulfilled_items: 6,
            shortage_items: 4,
            kit_rate: 60,
          },
        ],
      },
    });
    purchaseApi.kitRate.getProjectMaterialStatus.mockResolvedValue({ data: { materials: [] } });
    purchaseApi.kitRate.unified.mockResolvedValue({ data: {} });
    ecnBomApi.list.mockResolvedValue({ data: { items: [], total: 0 } });
    ecnBomApi.create.mockResolvedValue({ data: { id: 1 } });
    qualityApi.inspection.list.mockResolvedValue({ data: { items: [], total: 0 } });
    acceptanceApi.orders.list.mockResolvedValue({ data: { items: [], total: 0 } });
  });

  it("scopes material analysis to the project context", async () => {
    renderAt(<MaterialAnalysis />, "/material-analysis?project_id=42");

    await waitFor(() => {
      expect(purchaseApi.kitRate.dashboard).toHaveBeenCalledWith({
        project_id: "42",
      });
    });
  });

  it("scopes ECN list and defaults creation to the project context", async () => {
    renderAt(<ECNManagement />, "/ecn?project_id=42");

    await waitFor(() => {
      expect(ecnBomApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ project_id: "42" }),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /新建 ECN/ }));
    expect(screen.getByText("项目 42")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("简要描述变更内容"), {
      target: { value: "夹具结构变更" },
    });
    const changeTypeField = screen.getByText("变更类型 *").closest("div");
    fireEvent.change(within(changeTypeField).getByRole("combobox"), {
      target: { value: "设计变更" },
    });
    fireEvent.change(screen.getByPlaceholderText("详细描述变更原因、内容和范围"), {
      target: { value: "客户验收标准变化" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(ecnBomApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          affected_projects: [42],
        }),
      );
    });
  });

  it("scopes quality inspections to the project context", async () => {
    renderAt(<InspectionList />, "/quality/inspections?project_id=42");

    await waitFor(() => {
      expect(qualityApi.inspection.list).toHaveBeenCalledWith(
        expect.objectContaining({ project_id: "42" }),
      );
    });
  });

  it("scopes acceptance orders to the project context", async () => {
    renderAt(<AcceptanceList />, "/quality/acceptance?project_id=42");

    await waitFor(() => {
      expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
        expect.objectContaining({ project_id: "42" }),
      );
    });
  });
});
