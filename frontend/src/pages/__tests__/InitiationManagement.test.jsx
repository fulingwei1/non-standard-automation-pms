import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import InitiationManagement from "../InitiationManagement";
import { pmoApi, presaleWorkbenchApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  pmoApi: {
    initiations: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      submit: vi.fn(),
      approve: vi.fn(),
      reject: vi.fn(),
      projectManagers: vi.fn(),
    },
  },
  presaleWorkbenchApi: {
    loadContext: vi.fn(),
  },
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy({}, {
    get: (_, tag) => {
      const Tag = typeof tag === "string" ? tag : "div";
      return ({ children, ...props }) => {
        const motionProps = new Set([
          "initial",
          "animate",
          "variants",
          "transition",
          "whileHover",
          "whileTap",
        ]);
        const domProps = Object.fromEntries(
          Object.entries(props).filter(([key]) => !motionProps.has(key)),
        );
        return <Tag {...domProps}>{children}</Tag>;
      };
    },
  }),
}));

const navigateMock = vi.fn();

function renderPage(search) {
  useParams.mockReturnValue({});
  useNavigate.mockReturnValue(navigateMock);
  useLocation.mockReturnValue({
    pathname: "/pmo/initiations",
    search,
    hash: "",
    state: null,
  });
  return render(<InitiationManagement />);
}

describe("InitiationManagement presale handoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    navigateMock.mockClear();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    pmoApi.initiations.list.mockResolvedValue({ data: { items: [], total: 0 } });
    pmoApi.initiations.get.mockResolvedValue({
      data: {
        id: 18,
        project_name: "聚合上下文方案",
        presale_handover_context: {},
      },
    });
    pmoApi.initiations.create.mockResolvedValue({ data: { id: 18 } });
    presaleWorkbenchApi.loadContext.mockResolvedValue({
      source: { type: "opportunity", id: 2 },
      ticket: {
        id: 501,
        title: "售前支持申请",
        customer_name: "华南电子",
        description: "客户需要电源测试线",
        estimated_amount: 420000,
        estimated_hours: 18,
      },
      solutions: {
        items: [
          {
            id: 88,
            name: "聚合上下文方案",
            customer_name: "华南电子",
            suggested_price: 460000,
            estimated_cost: 320000,
            requirement_summary: "自动化测试线、扫码追溯、节拍 8 秒",
            estimated_hours: 20,
          },
        ],
        total: 1,
      },
      costing: {
        baseline: {
          solution_id: 88,
          solution_name: "聚合上下文方案",
          suggested_price: 460000,
          estimated_cost: 320000,
        },
      },
      assessment: {
        requirementDetail: {
          requirement_summary: "客户现场约束已澄清",
        },
        risks: {
          items: [{ risk_title: "交期压缩风险" }],
          total: 1,
        },
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("prefills a PMO initiation from presale workbench context", async () => {
    renderPage(
      "?handoff=presale&opportunity_id=2&ticket_id=501&solution_id=88&project_name=备用项目&customer_name=备用客户",
    );

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: "opportunity",
        sourceId: 2,
        presaleTicketId: 501,
      });
    });

    expect(await screen.findByDisplayValue("聚合上下文方案")).toBeInTheDocument();
    expect(screen.getByDisplayValue("华南电子")).toBeInTheDocument();
    expect(screen.getByDisplayValue("460000")).toBeInTheDocument();
    expect(screen.getByDisplayValue("客户现场约束已澄清")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(pmoApi.initiations.create).toHaveBeenCalledWith(
        expect.objectContaining({
          project_name: "聚合上下文方案",
          customer_name: "华南电子",
          contract_amount: 460000,
          technical_solution_id: 88,
          requirement_summary: "客户现场约束已澄清",
          estimated_hours: 20,
          risk_assessment: "交期压缩风险",
        }),
      );
    });
    expect(navigateMock).toHaveBeenCalledWith("/pmo/initiations/18");
  });
});
