import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import GaugeChart from "../GaugeChart";

vi.mock("@ant-design/plots", () => ({
  Gauge: (props) => (
    <div
      data-testid="ant-gauge"
      data-props={JSON.stringify(props, (_key, value) =>
        typeof value === "function" ? value() : value
      )}
    />
  ),
}));

const getGaugeProps = () =>
  JSON.parse(screen.getByTestId("ant-gauge").getAttribute("data-props"));

describe("GaugeChart", () => {
  it("passes normalized gauge data through the current @ant-design/plots children API", () => {
    render(<GaugeChart value={82} title="整体健康度" unit="%" />);

    const props = getGaugeProps();
    expect(props.percent).toBeUndefined();
    expect(props.children[0].type).toBe("gauge");
    expect(props.children[0].data).toMatchObject({
      target: 0.82,
      total: 1,
    });
    expect(props.children[0].style.textContent).toBe("82%");
  });

  it("clamps invalid or out-of-range values before rendering", () => {
    render(<GaugeChart value={Number.NaN} min={0} max={100} unit="%" />);
    expect(getGaugeProps().children[0].data.target).toBe(0);
    expect(getGaugeProps().children[0].style.textContent).toBe("0%");
  });
});
