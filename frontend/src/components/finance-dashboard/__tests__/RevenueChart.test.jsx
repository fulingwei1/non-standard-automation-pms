import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RevenueChart } from "../RevenueChart";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
}));

describe("RevenueChart", () => {
  it("renders empty states when revenue data is not available yet", () => {
    expect(() => render(<RevenueChart />)).not.toThrow();

    expect(screen.getByText("收入概览")).toBeInTheDocument();
    expect(screen.getByText("暂无收入趋势数据")).toBeInTheDocument();
  });
});
