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

  it("keeps the handoff solution selected by the presale entry path", async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      source: { type: "opportunity", id: 2 },
      ticket: {
        id: 501,
        title: "售前支持申请",
        customer_name: "华南电子",
        estimated_amount: 420000,
      },
      solutions: {
        items: [
          {
            id: 88,
            name: "入口选中的方案",
            customer_name: "华南电子",
            suggested_price: 460000,
            estimated_cost: 320000,
            requirement_summary: "选中方案的交接范围",
            estimated_hours: 20,
          },
          {
            id: 99,
            name: "上下文默认方案",
            customer_name: "华南电子",
            suggested_price: 999999,
            estimated_cost: 888888,
            requirement_summary: "不应覆盖入口方案",
            estimated_hours: 120,
          },
        ],
        total: 2,
      },
      costing: {
        baseline: {
          solution_id: 99,
          solution_name: "上下文默认方案",
          suggested_price: 999999,
          estimated_cost: 888888,
        },
      },
      assessment: {
        requirementDetail: {
          requirement_summary: "客户现场约束已澄清",
        },
        risks: {
          items: [],
          total: 0,
        },
      },
    });

    renderPage(
      "?handoff=presale&opportunity_id=2&ticket_id=501&solution_id=88&project_name=备用项目&customer_name=备用客户",
    );

    expect(await screen.findByDisplayValue("入口选中的方案")).toBeInTheDocument();
    expect(screen.getByDisplayValue("460000")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("999999")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(pmoApi.initiations.create).toHaveBeenCalledWith(
        expect.objectContaining({
          project_name: "入口选中的方案",
          contract_amount: 460000,
          technical_solution_id: 88,
          estimated_hours: 20,
        }),
      );
    });
  });

  it("prefills a PMO initiation from contract handoff params", async () => {
    renderPage(
      "?handoff=contract&project_name=FCT%E6%B5%8B%E8%AF%95%E7%BA%BF%E5%90%88%E5%90%8C&customer_name=%E5%88%B6%E9%80%A0%E5%AE%A2%E6%88%B7&contract_no=HT2606-043&contract_amount=800000&required_end_date=2026-10-20&requirement_summary=%E5%AE%A2%E6%88%B7%E9%9C%80%E8%A6%81FCT%E6%B5%8B%E8%AF%95%E7%BA%BF%EF%BC%8C%E5%90%ABMES%E6%8E%A5%E5%8F%A3",
    );

    expect(presaleWorkbenchApi.loadContext).not.toHaveBeenCalled();
    expect(await screen.findByDisplayValue("FCT测试线合同")).toBeInTheDocument();
    expect(screen.getByDisplayValue("制造客户")).toBeInTheDocument();
    expect(screen.getByDisplayValue("HT2606-043")).toBeInTheDocument();
    expect(screen.getByDisplayValue("800000")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2026-10-20")).toBeInTheDocument();
    expect(screen.getByDisplayValue("客户需要FCT测试线，含MES接口")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(pmoApi.initiations.create).toHaveBeenCalledWith(
        expect.objectContaining({
          project_name: "FCT测试线合同",
          customer_name: "制造客户",
          contract_no: "HT2606-043",
          contract_amount: "800000",
          required_end_date: "2026-10-20",
          requirement_summary: "客户需要FCT测试线，含MES接口",
        }),
      );
    });
  });
});
