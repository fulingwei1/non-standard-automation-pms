import { describe, expect, it } from "vitest";
import { getStatusStyle } from "../constants";

describe("SolutionDetail status styles", () => {
  it("maps backend review statuses to Chinese labels", () => {
    expect(getStatusStyle("review")).toMatchObject({ text: "评审中" });
    expect(getStatusStyle("approved")).toMatchObject({ text: "已通过" });
    expect(getStatusStyle("rejected")).toMatchObject({ text: "已驳回" });
  });
});
