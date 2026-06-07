import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SolutionCostTab } from "../SolutionCostTab";

describe("SolutionCostTab", () => {
  it("renders backend cost breakdown items", () => {
    render(
      <SolutionCostTab
        costEstimate={{
          solution_id: 88,
          total_cost: 120000,
          suggested_price: 240000,
          breakdown: [
            {
              id: 1,
              category: "硬件",
              item_name: "PXI机箱",
              unit: "套",
              quantity: 1,
              unit_price: 80000,
              amount: 80000,
            },
            {
              id: 2,
              category: "治具",
              item_name: "FCT治具",
              unit: "套",
              quantity: 2,
              unit_price: 20000,
              amount: 40000,
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("PXI机箱")).toBeInTheDocument();
    expect(screen.getByText("FCT治具")).toBeInTheDocument();
    expect(screen.getByText("硬件")).toBeInTheDocument();
    expect(screen.getByText("治具")).toBeInTheDocument();
    expect(screen.getByText("1套")).toBeInTheDocument();
    expect(screen.getAllByText("¥80,000")).toHaveLength(1);
    expect(screen.getAllByText("¥40,000")).toHaveLength(1);
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("offers a cost-estimation entry when the solution has no cost estimate", async () => {
    const onCreateEstimate = vi.fn();
    const user = userEvent.setup();

    render(
      <SolutionCostTab
        costEstimate={null}
        solution={{ id: 88, name: "华南电子FCT方案" }}
        onCreateEstimate={onCreateEstimate}
      />,
    );

    await user.click(screen.getByRole("button", { name: "去做成本估算" }));

    expect(onCreateEstimate).toHaveBeenCalledWith({
      id: 88,
      name: "华南电子FCT方案",
    });
  });
});
