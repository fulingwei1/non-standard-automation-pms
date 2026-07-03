import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";
import { confirmAction } from "@/lib/confirmAction";
import { useProductionPlanList } from "../useProductionPlanList";
import { productionApi, projectApi } from "../../../../services/api";

vi.mock("react-router-dom", () => ({
  useSearchParams: vi.fn(),
}));

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(),
}));

vi.mock("../../../../services/api", () => ({
  productionApi: {
    productionPlans: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      submit: vi.fn(),
      approve: vi.fn(),
      publish: vi.fn(),
    },
    workshops: {
      list: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

describe("useProductionPlanList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    productionApi.workshops.list.mockResolvedValue({ data: { items: [] } });
    productionApi.productionPlans.list.mockResolvedValue({ data: { items: [] } });
    productionApi.productionPlans.submit.mockResolvedValue({ data: { code: 200 } });
    productionApi.productionPlans.approve.mockResolvedValue({ data: { code: 200 } });
    productionApi.productionPlans.publish.mockResolvedValue({ data: { code: 200 } });
    confirmAction.mockResolvedValue(true);
  });

  it("scopes production plans and defaults new plans by project context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42"),
      vi.fn(),
    ]);

    const { result } = renderHook(() => useProductionPlanList());

    await waitFor(() => {
      expect(productionApi.productionPlans.list).toHaveBeenCalledWith({
        project_id: "42",
      });
    });

    expect(result.current.filterProject).toBe("42");
    expect(result.current.newPlan.project_id).toBe(42);
  });

  it("submits draft plans for approval and refreshes the list", async () => {
    const { result } = renderHook(() => useProductionPlanList());

    await waitFor(() => {
      expect(productionApi.productionPlans.list).toHaveBeenCalled();
    });

    await act(async () => {
      await result.current.handleSubmitPlan(7);
    });

    expect(confirmAction).toHaveBeenCalledWith("确认提交此生产计划审批？");
    expect(productionApi.productionPlans.submit).toHaveBeenCalledWith(7);
    expect(productionApi.productionPlans.list).toHaveBeenCalledTimes(2);
  });

  it("approves and rejects submitted plans through the real approval API", async () => {
    const { result } = renderHook(() => useProductionPlanList());

    await waitFor(() => {
      expect(productionApi.productionPlans.list).toHaveBeenCalled();
    });

    await act(async () => {
      await result.current.handleApprovePlan(8, true);
    });
    await act(async () => {
      await result.current.handleApprovePlan(8, false);
    });

    expect(productionApi.productionPlans.approve).toHaveBeenNthCalledWith(1, 8, {
      approved: true,
    });
    expect(productionApi.productionPlans.approve).toHaveBeenNthCalledWith(2, 8, {
      approved: false,
    });
  });
});
