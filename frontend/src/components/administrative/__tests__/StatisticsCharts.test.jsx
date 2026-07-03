import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { SimpleLineChart, SimplePieChart } from "../StatisticsCharts";

describe("SimpleLineChart", () => {
  it("uses yKeys and xKey data without rendering NaN SVG coordinates", () => {
    const { container } = render(
      <SimpleLineChart
        data={[
          { month: "Jan", quotes: 0, converted: 0 },
          { month: "Feb", quotes: 6, converted: 3 },
        ]}
        xKey="month"
        yKeys={["quotes", "converted"]}
      />
    );

    expect(screen.getByText("Jan")).toBeInTheDocument();
    expect(screen.getByText("Feb")).toBeInTheDocument();

    const polyline = container.querySelector("polyline");
    expect(polyline?.getAttribute("points")).not.toContain("NaN");

    container.querySelectorAll("circle").forEach((circle) => {
      expect(circle.getAttribute("cx")).not.toContain("NaN");
      expect(circle.getAttribute("cy")).not.toContain("NaN");
    });
  });
});

describe("SimplePieChart", () => {
  it("does not render NaN paths when all slices are zero", () => {
    const { container } = render(
      <SimplePieChart
        data={[
          { name: "已到货", value: 0, color: "#22c55e" },
          { name: "缺料", value: 0, color: "#ef4444" },
        ]}
      />
    );

    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
    expect(container.innerHTML).not.toContain("NaN");
    container.querySelectorAll("path").forEach((path) => {
      expect(path.getAttribute("d")).not.toContain("NaN");
    });
  });
});
