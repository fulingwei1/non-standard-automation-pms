import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Shipments from "../Shipments";

const { businessSupportApiMock, quoteDeliveryApiMock } = vi.hoisted(() => ({
  businessSupportApiMock: {
    deliveryOrders: {
      statistics: vi.fn(),
    },
  },
  quoteDeliveryApiMock: {
    upcoming: vi.fn(),
    overdue: vi.fn(),
  },
}));

vi.mock("../../services/api", () => ({
  businessSupportApi: businessSupportApiMock,
}));

vi.mock("../../services/api/sales", () => ({
  quoteDeliveryApi: quoteDeliveryApiMock,
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get:
        (_, tag) =>
        ({ children, ...props }) => {
          const ignored = new Set(["initial", "animate", "transition"]);
          const filtered = Object.fromEntries(
            Object.entries(props).filter(([key]) => !ignored.has(key)),
          );
          const Tag = typeof tag === "string" ? tag : "div";
          return <Tag {...filtered}>{children}</Tag>;
        },
    },
  ),
}));

const renderPage = () =>
  render(
    <MemoryRouter>
      <Shipments />
    </MemoryRouter>,
  );

describe("Shipments", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    businessSupportApiMock.deliveryOrders.statistics.mockResolvedValue({
      data: {
        data: {
          pending_shipments: 0,
          shipped_today: 0,
          in_transit: 0,
          delivered_this_week: 0,
          on_time_shipping_rate: 0,
          avg_shipping_time: 0,
          total_orders: 0,
        },
      },
    });
    quoteDeliveryApiMock.upcoming.mockResolvedValue({ data: { data: { items: [] } } });
    quoteDeliveryApiMock.overdue.mockResolvedValue({ data: { data: { items: [] } } });
  });

  it("renders zero shipment statistics as 0 instead of unknown", async () => {
    renderPage();

    await waitFor(() => {
      expect(businessSupportApiMock.deliveryOrders.statistics).toHaveBeenCalled();
    });

    expect(screen.queryByText("unknown")).not.toBeInTheDocument();
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(4);
  });
});
