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
});
