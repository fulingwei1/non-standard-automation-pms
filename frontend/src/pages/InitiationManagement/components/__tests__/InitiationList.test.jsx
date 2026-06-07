import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InitiationList } from "../InitiationList";

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

describe("InitiationList", () => {
  it("shows approval actions for submitted initiations", async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn();
    const onReject = vi.fn();

    render(
      <InitiationList
        loading={false}
        error={null}
        initiations={[
          {
            id: 17,
            application_no: "LX260607001",
            project_name: "FCT 测试线立项",
            customer_name: "制造客户",
            contract_amount: 800000,
            applicant_name: "销售",
            apply_time: "2026-06-07T10:00:00",
            status: "SUBMITTED",
          },
        ]}
        total={1}
        page={1}
        pageSize={20}
        setPage={vi.fn()}
        onRetry={vi.fn()}
        onViewDetail={vi.fn()}
        onViewProject={vi.fn()}
        onSubmitReview={vi.fn()}
        onApprove={onApprove}
        onReject={onReject}
      />,
    );

    await user.click(screen.getByRole("button", { name: "审批通过" }));
    await user.click(screen.getByRole("button", { name: "驳回" }));

    expect(onApprove).toHaveBeenCalledWith(17);
    expect(onReject).toHaveBeenCalledWith(17);
  });

  it("shows presale handover and PM risk before approval", () => {
    render(
      <InitiationList
        loading={false}
        error={null}
        initiations={[
          {
            id: 18,
            application_no: "LX260607002",
            project_name: "FCT 测试线立项",
            customer_name: "制造客户",
            contract_amount: 800000,
            applicant_name: "销售",
            apply_time: "2026-06-07T10:00:00",
            status: "SUBMITTED",
            presale_handover_context: {
              presale_solution: {
                id: 88,
                name: "PMO售前交接方案",
                estimated_cost: 90000,
                suggested_price: 150000,
              },
              presale_ticket: {
                id: 51,
                ticket_no: "PST-051",
                actual_hours: 12.5,
                assessment_status: "COMPLETED",
                current_assessment_id: 701,
                pm_involvement_required: true,
                pm_involvement_risk_level: "高",
                pm_involvement_risk_factors: ["金额高", "交期紧"],
                pm_assigned: false,
              },
              technical_assessment: {
                current: {
                  id: 701,
                  status: "COMPLETED",
                  total_score: 82,
                  decision: "RECOMMEND",
                },
                risks: {
                  total: 1,
                  items: [
                    {
                      id: 801,
                      risk_title: "交期压缩风险",
                      risk_description: "交付周期偏紧，项目启动后需要 PM 提前排产",
                      risk_level: "HIGH",
                      status: "OPEN",
                    },
                  ],
                },
              },
              baseline_cost: {
                presale_estimated_cost: 90000,
              },
              handover_status: {
                ready: true,
                missing: [],
              },
            },
          },
        ]}
        total={1}
        page={1}
        pageSize={20}
        setPage={vi.fn()}
        onRetry={vi.fn()}
        onViewDetail={vi.fn()}
        onViewProject={vi.fn()}
        onSubmitReview={vi.fn()}
        onApprove={vi.fn()}
        onReject={vi.fn()}
      />,
    );

    expect(screen.getByText("售前交接包")).toBeInTheDocument();
    expect(screen.getByText("PMO售前交接方案")).toBeInTheDocument();
    expect(screen.getByText("PST-051")).toBeInTheDocument();
    expect(screen.getByText("12.5 小时")).toBeInTheDocument();
    expect(screen.getByText("PM提前介入")).toBeInTheDocument();
    expect(screen.getByText("高风险")).toBeInTheDocument();
    expect(screen.getByText("金额高、交期紧")).toBeInTheDocument();
    expect(screen.getByText("PM未分配")).toBeInTheDocument();
    expect(screen.getByText("技术评估")).toBeInTheDocument();
    expect(screen.getByText("82 分")).toBeInTheDocument();
    expect(screen.getByText("交期压缩风险")).toBeInTheDocument();
  });
});
