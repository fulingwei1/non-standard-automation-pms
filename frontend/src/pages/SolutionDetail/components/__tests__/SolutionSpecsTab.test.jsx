import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SolutionSpecsTab } from "../SolutionSpecsTab";

describe("SolutionSpecsTab", () => {
  it("renders technical parameters written back from a template estimate", () => {
    render(
      <SolutionSpecsTab
        solution={{
          techSpecs: {
            productInfo: {},
            capacity: { uph: 0, cycleTime: 0, dailyOutput: 0, channels: 0 },
            testItems: [],
            testStandards: [],
            environment: {},
            technicalParameters: [
              { key: "test_station_count", label: "测试工位数", value: "4", unit: "个" },
              { key: "cycle_time", label: "节拍时间", value: "18", unit: "秒" },
            ],
          },
        }}
      />,
    );

    expect(screen.getByText("技术参数")).toBeInTheDocument();
    expect(screen.getByText("测试工位数")).toBeInTheDocument();
    expect(screen.getByText("4 个")).toBeInTheDocument();
    expect(screen.getByText("节拍时间")).toBeInTheDocument();
    expect(screen.getByText("18 秒")).toBeInTheDocument();
  });
});
