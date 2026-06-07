import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import BiddingDetail from "../BiddingDetail";
import { presaleApi } from "../../services/api";

const navigateMock = vi.hoisted(() => vi.fn());
const routeState = vi.hoisted(() => ({
  params: { id: "7" },
  location: {
    pathname: "/bidding/7",
    search: "?type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
  },
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: () => routeState.params,
    useNavigate: () => navigateMock,
    useLocation: () => routeState.location,
  };
});

vi.mock("../../services/api", () => ({
  presaleApi: {
    tenders: {
      get: vi.fn(),
    },
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = typeof tag === "string" ? tag : "div";
        return ({ children, ...props }) => {
          const motionProps = new Set([
            "initial",
            "animate",
            "exit",
            "variants",
            "transition",
            "whileHover",
            "whileTap",
            "layout",
          ]);
          const domProps = Object.fromEntries(
            Object.entries(props).filter(([key]) => !motionProps.has(key)),
          );
          return <Tag {...domProps}>{children}</Tag>;
        };
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

describe("BiddingDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    routeState.params = { id: "7" };
    routeState.location = {
      pathname: "/bidding/7",
      search: "?type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    };
    presaleApi.tenders.get.mockResolvedValue({
      data: {
        id: 7,
        ticket_id: 501,
        lead_id: 2026,
        opportunity_id: 2,
        project_id: 42,
        tender_no: "BID-2026-007",
        tender_name: "线索阶段投标",
        customer_name: "重点客户",
        budget_amount: 900000,
        result: "PREPARING",
      },
    });
  });

  it("keeps sales support context when returning from a failed detail load", async () => {
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    presaleApi.tenders.get.mockRejectedValueOnce({
      response: { data: { detail: "投标记录不存在" } },
    });

    try {
      render(<BiddingDetail />);

      expect(await screen.findByText("投标记录不存在")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "返回投标中心" }));

      expect(navigateMock).toHaveBeenCalledWith(
        "/presales/technical-solutions?tab=bids&type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
      );
    } finally {
      consoleErrorSpy.mockRestore();
    }
  });

  it("keeps tender response context when returning from a loaded detail", async () => {
    routeState.location = {
      pathname: "/bidding/7",
      search: "",
    };

    render(<BiddingDetail />);

    expect(await screen.findByText("线索阶段投标")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "返回投标中心" }));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=bids&type=support&ticket_id=501&lead_id=2026&opportunity_id=2&project_id=42",
    );
  });

  it("loads tender detail by route id", async () => {
    render(<BiddingDetail />);

    await waitFor(() => {
      expect(presaleApi.tenders.get).toHaveBeenCalledWith("7");
    });
  });
});
