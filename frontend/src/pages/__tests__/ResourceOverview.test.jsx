import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ResourceOverview from "../ResourceOverview";
import { resourceOverviewApi } from "../../services/api/resourceOverview";

vi.mock("framer-motion", () => ({
  AnimatePresence: ({ children }) => <>{children}</>,
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = typeof tag === "string" ? tag : "div";
        return ({ children, variants: _variants, initial: _initial, animate: _animate, ...props }) => (
          <Tag {...props}>{children}</Tag>
        );
      },
    },
  ),
}));

vi.mock("../../components/layout", () => ({
  PageHeader: ({ title, subtitle }) => (
    <div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  ),
}));

vi.mock("../../components/common/ConflictRecommendations", () => ({
  default: () => <div>conflict recommendations</div>,
}));

vi.mock("../../services/api/resourceOverview", () => ({
  resourceOverviewApi: {
    list: vi.fn(),
  },
}));

describe("ResourceOverview", () => {
  it("renders PMO aggregate resource data when no allocation timeline rows exist", async () => {
    resourceOverviewApi.list.mockResolvedValue({
      data: {
        total_resources: 12,
        allocated_resources: 0,
        available_resources: 12,
        overloaded_resources: 0,
        employees_with_conflicts: 0,
        total_conflicts: 0,
        avg_utilization: 0,
        employees: [],
        by_department: [
          {
            department_id: 1,
            department_name: "研发部",
            total_resources: 8,
            allocated_resources: 0,
            available_resources: 8,
          },
        ],
      },
    });

    render(<ResourceOverview />);

    expect(await screen.findByText("资源总数")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByText("暂无资源分配数据")).toBeTruthy();
    expect(screen.getAllByText("研发部").length).toBeGreaterThan(0);
    expect(screen.getByText("总数 8")).toBeTruthy();
    expect(resourceOverviewApi.list).toHaveBeenCalledWith({ only_assigned: true });
  });
});
