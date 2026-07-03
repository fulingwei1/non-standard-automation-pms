import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QuoteCreateEdit from "../QuoteCreateEdit";
import QuoteItemsTable from "../QuoteCreateEdit/QuoteItemsTable";
import { opportunityApi, quoteApi } from "../../services/api";

const navigateMock = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../services/api", () => ({
  opportunityApi: {
    list: vi.fn(),
  },
  quoteApi: {
    create: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    recalculateCost: vi.fn(),
  },
}));

vi.mock("../QuoteCreateEdit/AiSidebarPanel", () => ({
  default: () => <aside>AI智能定价</aside>,
}));

describe("QuoteCreateEdit presale solution context", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    navigateMock.mockClear();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    opportunityApi.list.mockResolvedValue({
      data: {
        data: {
          items: [
            {
              id: 2,
              customer_id: 1,
              opp_code: "OP-002",
              opp_name: "FCT测试线商机",
            },
          ],
        },
      },
    });
    quoteApi.create.mockResolvedValue({ data: { id: 9 } });
  });

  it("creates a quote from presale solution context without manual quote items", async () => {
    render(
      <MemoryRouter
        initialEntries={[
          "/sales/quotes/create?opportunity_id=2&customer_id=1&lead_id=7&project_id=9&solution_id=88&ticket_id=501",
        ]}
      >
        <QuoteCreateEdit />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(opportunityApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => {
      expect(quoteApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          opportunity_id: 2,
          customer_id: 1,
          lead_id: 7,
          project_id: 9,
          solution_id: 88,
          presale_ticket_id: 501,
          version: expect.objectContaining({
            items: [],
          }),
        }),
      );
    });
    expect(window.alert).toHaveBeenCalledWith("创建成功");
    expect(navigateMock).toHaveBeenCalledWith("/sales/quotes");
  });
});

describe("QuoteItemsTable validation hints", () => {
  it("marks quantity and unit price inputs as positive-only values", () => {
    const { container } = render(
      <QuoteItemsTable
        items={[
          {
            item_name: "自动化测试平台",
            qty: 1,
            unit_price: 1000,
            cost: 600,
          },
        ]}
        onAddItem={vi.fn()}
        onRemoveItem={vi.fn()}
        onItemChange={vi.fn()}
      />,
    );

    const numberInputs = container.querySelectorAll('input[type="number"]');

    expect(numberInputs[0]).toHaveAttribute("min", "0.01");
    expect(numberInputs[0]).toHaveAttribute("step", "0.01");
    expect(numberInputs[1]).toHaveAttribute("min", "0.01");
    expect(numberInputs[1]).toHaveAttribute("step", "0.01");
  });
});
