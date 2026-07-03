import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAcceptanceExecutionPage } from "../useAcceptanceExecutionPage";
import { acceptanceApi } from "../../../../services/api";

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../../services/api", () => ({
  acceptanceApi: {
    orders: {
      get: vi.fn(),
      getItems: vi.fn(),
      updateItem: vi.fn(),
      complete: vi.fn(),
    },
    issues: {
      list: vi.fn(),
      create: vi.fn(),
    },
  },
}));

describe("useAcceptanceExecutionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    acceptanceApi.orders.get.mockResolvedValue({
      data: { id: 7, order_no: "SAT-QA-001", status: "IN_PROGRESS" },
    });
    acceptanceApi.orders.getItems.mockResolvedValue({ data: [] });
    acceptanceApi.issues.list.mockResolvedValue({ data: [] });
  });

  it("defaults a pending check item to PASSED when opening the result dialog", async () => {
    const { result } = renderHook(() => useAcceptanceExecutionPage("7"));

    await waitFor(() => {
      expect(acceptanceApi.orders.getItems).toHaveBeenCalledWith("7");
    });

    act(() => {
      result.current.openItemDialog({
        id: 11,
        item_name: "QA electrical check",
        result_status: "PENDING",
        actual_value: "",
        deviation: "",
        remark: "",
      });
    });

    expect(result.current.itemResult.result_status).toBe("PASSED");
  });

  it("preserves a non-pending saved result when reopening the dialog", async () => {
    const { result } = renderHook(() => useAcceptanceExecutionPage("7"));

    await waitFor(() => {
      expect(acceptanceApi.orders.getItems).toHaveBeenCalledWith("7");
    });

    act(() => {
      result.current.openItemDialog({
        id: 12,
        item_name: "QA mechanical check",
        result_status: "FAILED",
        actual_value: "NG",
        deviation: "Noise",
        remark: "Needs adjustment",
      });
    });

    expect(result.current.itemResult).toEqual(
      expect.objectContaining({
        result_status: "FAILED",
        actual_value: "NG",
        deviation: "Noise",
        remark: "Needs adjustment",
      }),
    );
  });
});
