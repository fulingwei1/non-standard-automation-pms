import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ContractDetail from "../ContractDetail";
import { contractApi, pmoApi } from "../../services/api";

const mockNavigate = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../services/api", () => ({
  contractApi: {
    get: vi.fn(),
    getPaymentPlans: vi.fn(),
  },
  paymentPlanApi: {
    list: vi.fn(),
  },
  pmoApi: {
    initiations: {
      list: vi.fn(),
      create: vi.fn(),
    },
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const filtered = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                "initial",
                "animate",
                "variants",
                "transition",
                "whileHover",
                "whileTap",
              ].includes(key),
          ),
        );
        const Tag = typeof tag === "string" ? tag : "div";
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
}));

function renderPage(path = "/sales/contracts/42") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/sales/contracts/:id" element={<ContractDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ContractDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    contractApi.get.mockResolvedValue({
      data: {
        id: 42,
        contract_code: "HT2606-042",
        contract_name: "自动化测试设备合同",
        customer_id: 5,
        customer_name: "金凯博客户",
        status: "SIGNED",
        contract_amount: "1000000",
        project_id: 9,
        project_code: "PJ2606-009",
      },
    });
    pmoApi.initiations.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 7,
            contract_no: "HT2606-042",
            status: "APPROVED",
          },
        ],
      },
    });
    contractApi.getPaymentPlans.mockResolvedValue({
      data: [
        {
          id: 1,
          payment_no: 1,
          payment_name: "预付款",
          planned_amount: "300000",
          planned_date: "2099-01-01",
          status: "PENDING",
        },
      ],
    });
  });

  it("shows the contract to PMO to project to payment-plan flow", async () => {
    renderPage();

    expect(await screen.findByText("自动化测试设备合同")).toBeInTheDocument();
    expect(screen.getByText("项目/回款闭环")).toBeInTheDocument();
    expect(screen.getAllByText("立项通过").length).toBeGreaterThan(0);
    expect(screen.getByText("PJ2606-009")).toBeInTheDocument();
    expect(screen.getByText("1 条")).toBeInTheDocument();
    expect(screen.getByText("预付款")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /查看回款/ })).toBeInTheDocument();

    expect(pmoApi.initiations.list).toHaveBeenCalledWith(
      expect.objectContaining({
        contract_no: "HT2606-042",
      }),
    );
    expect(contractApi.getPaymentPlans).toHaveBeenCalledWith("42");
  });

  it("creates a PMO initiation from a signed contract without an existing project", async () => {
    const user = userEvent.setup();
    contractApi.get.mockResolvedValueOnce({
      data: {
        id: 43,
        contract_code: "HT2606-043",
        contract_name: "FCT测试线合同",
        customer_id: 6,
        customer_name: "制造客户",
        status: "SIGNED",
        contract_amount: "800000",
      },
    });
    pmoApi.initiations.list.mockResolvedValue({ data: { items: [] } });
    contractApi.getPaymentPlans.mockResolvedValue({ data: [] });
    pmoApi.initiations.create.mockResolvedValue({
      data: {
        id: 17,
        status: "DRAFT",
      },
    });

    renderPage("/sales/contracts/43");

    const button = await screen.findByRole("button", { name: /发起立项/ });
    await user.click(button);

    await waitFor(() => {
      expect(pmoApi.initiations.create).toHaveBeenCalledWith(
        expect.objectContaining({
          project_name: "FCT测试线合同",
          customer_name: "制造客户",
          customer_id: 6,
          contract_no: "HT2606-043",
          contract_amount: 800000,
        }),
      );
      expect(mockNavigate).toHaveBeenCalledWith("/pmo/initiations/17");
    });
  });
});
