import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { useSearchParams } from "react-router-dom";

import CostAccounting from "../CostAccounting";
import { useCostAccounting } from "../CostAccounting/hooks";
import { costApi } from "../../services/api/projects.js";

vi.mock("../CostAccounting/hooks", () => ({
  useCostAccounting: vi.fn(),
}));

vi.mock("../../services/api/projects.js", () => ({
  costApi: {
    create: vi.fn(),
  },
}));

describe("CostAccounting", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams("project_id=7"), vi.fn()]);
    useCostAccounting.mockReturnValue({
      costs: [],
      setFilters: vi.fn(),
      loadCosts: vi.fn().mockResolvedValue(undefined),
    });
    costApi.create.mockResolvedValue({ data: { id: 99 } });
  });

  it("submits a manual cost record for the project context", async () => {
    render(<CostAccounting />);

    fireEvent.click(screen.getByRole("button", { name: /录入成本/ }));

    const dialog = screen.getByRole("dialog");
    const [projectSelect, typeSelect] = within(dialog).getAllByRole("combobox");

    expect(within(projectSelect).getByRole("option", { name: "项目 #7" })).toBeInTheDocument();

    fireEvent.change(projectSelect, { target: { value: "7" } });
    fireEvent.change(typeSelect, { target: { value: "MATERIAL" } });
    fireEvent.change(within(dialog).getByPlaceholderText("请输入金额"), {
      target: { value: "1234.56" },
    });
    fireEvent.change(dialog.querySelector('input[type="date"]'), {
      target: { value: "2026-07-03" },
    });
    fireEvent.change(within(dialog).getByPlaceholderText("请输入成本描述..."), {
      target: { value: "按钮流成本" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "保存" }));

    await waitFor(() => {
      expect(costApi.create).toHaveBeenCalledWith(7, {
        project_id: 7,
        cost_type: "MATERIAL",
        cost_category: "OTHER",
        amount: 1234.56,
        tax_amount: 0,
        description: "按钮流成本",
        cost_date: "2026-07-03",
      });
    });
    expect(useCostAccounting().loadCosts).toHaveBeenCalled();
  });
});
