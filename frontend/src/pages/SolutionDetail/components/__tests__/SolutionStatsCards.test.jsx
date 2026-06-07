import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SolutionStatsCards } from "../SolutionStatsCards";

const baseSolution = {
  customer: "华南电子",
  deviceTypeName: "FCT",
  amount: 18,
  deadline: "2026-06-30",
  progress: 35,
};

describe("SolutionStatsCards", () => {
  it("formats solution amount in business-friendly units", () => {
    const { rerender } = render(<SolutionStatsCards solution={baseSolution} />);

    expect(screen.getByText("¥18万")).toBeInTheDocument();

    rerender(<SolutionStatsCards solution={{ ...baseSolution, amount: 0.0001 }} />);

    expect(screen.getByText("¥1元")).toBeInTheDocument();
    expect(screen.queryByText("¥0.0001万")).not.toBeInTheDocument();
  });
});
