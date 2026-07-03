import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import useDeliveryManagement from "../useDeliveryManagement";
import { businessSupportApi } from "../../../services/api";

const routeState = vi.hoisted(() => ({
  pathname: "/pmc/delivery-orders",
  params: {},
  search: "project_id=42",
}));
const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", () => ({
  useNavigate: () => navigateSpy,
  useParams: () => routeState.params,
  useLocation: () => ({
    pathname: routeState.pathname,
    search: routeState.search ? `?${routeState.search}` : "",
  }),
  useSearchParams: () => [new URLSearchParams(routeState.search), vi.fn()],
}));

vi.mock("../../../components/ui", () => ({
  toast: vi.fn(),
}));

vi.mock("../../../services/api", () => ({
  businessSupportApi: {
    deliveryOrders: {
      list: vi.fn(),
      statistics: vi.fn(),
    },
  },
}));

describe("useDeliveryManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    routeState.pathname = "/pmc/delivery-orders";
    routeState.params = {};
    routeState.search = "project_id=42";
    businessSupportApi.deliveryOrders.list.mockResolvedValue({
      data: { code: 200, data: { items: [] } },
    });
    businessSupportApi.deliveryOrders.statistics.mockResolvedValue({
      data: { code: 200, data: {} },
    });
  });

  it("loads delivery orders within the upstream project context", async () => {
    renderHook(() => useDeliveryManagement());

    await waitFor(() => {
      expect(businessSupportApi.deliveryOrders.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 200,
        project_id: "42",
      });
    });
  });

  it("keeps project context when returning from nested delivery views", async () => {
    routeState.pathname = "/pmc/delivery-orders/9";
    routeState.params = { id: "9" };
    const { result } = renderHook(() => useDeliveryManagement());

    act(() => {
      result.current.handleBack();
    });

    expect(navigateSpy).toHaveBeenCalledWith("/pmc/delivery-orders?project_id=42");
  });

  it("opens the plan tab for the delivery plan menu route", async () => {
    routeState.pathname = "/pmc/delivery-plan";
    routeState.search = "";

    const { result } = renderHook(() => useDeliveryManagement());

    expect(result.current.activeTab).toBe("plan");
    await waitFor(() => {
      expect(businessSupportApi.deliveryOrders.list).toHaveBeenCalled();
    });
  });

  it("filters in-transit menu route to shipped or in-transit deliveries", async () => {
    routeState.search = "status=in_transit";
    businessSupportApi.deliveryOrders.list.mockResolvedValue({
      data: {
        code: 200,
        data: {
          items: [
            {
              id: 1,
              delivery_no: "DO-SHIP",
              order_no: "SO-SHIP",
              delivery_status: "shipped",
            },
            {
              id: 2,
              delivery_no: "DO-RECEIVED",
              order_no: "SO-RECEIVED",
              delivery_status: "received",
            },
          ],
        },
      },
    });

    const { result } = renderHook(() => useDeliveryManagement());

    await waitFor(() => {
      expect(result.current.filteredDeliveries).toHaveLength(1);
    });
    expect(result.current.filteredDeliveries[0].deliveryNo).toBe("DO-SHIP");
    expect(result.current.activeTab).toBe("tracking");
  });
});
