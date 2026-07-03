/**
 * AutofillBar 组件与 mergeAutofill 合并逻辑测试
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import AutofillBar, { mergeAutofill } from "../AutofillBar";
import api from "../../../services/api";

vi.mock("../../../services/api", () => ({
  default: { post: vi.fn() },
}));

describe("mergeAutofill", () => {
  it("只填空位，不覆盖用户已填的值", () => {
    const prev = { opp_name: "已填名称", equipment_type: "" };
    const fields = { opp_name: "AI名称", equipment_type: "视觉检测" };
    expect(mergeAutofill(prev, fields)).toEqual({
      opp_name: "已填名称",
      equipment_type: "视觉检测",
    });
  });

  it("忽略表单中不存在的键，数字转字符串", () => {
    const prev = { est_amount: "" };
    const fields = { est_amount: 1200000, unknown_key: "x" };
    const next = mergeAutofill(prev, fields);
    expect(next).toEqual({ est_amount: "1200000" });
  });

  it("递归合并嵌套 requirement，空值/0 不写入", () => {
    const prev = {
      requirement: { product_object: "", ct_seconds: "9" },
      est_amount: "",
    };
    const fields = {
      requirement: { product_object: "PCB", ct_seconds: "18" },
      est_amount: 0,
    };
    expect(mergeAutofill(prev, fields)).toEqual({
      requirement: { product_object: "PCB", ct_seconds: "9" },
      est_amount: "",
    });
  });
});

describe("AutofillBar", () => {
  it("提交线索后调用 autofill 接口并回填字段", async () => {
    api.post.mockResolvedValueOnce({
      data: { data: { fields: { customer_name: "比克动力" } } },
    });
    const onFill = vi.fn();
    render(<AutofillBar formType="customer" onFill={onFill} />);

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "深圳做锂电池PACK的比克动力" },
    });
    fireEvent.click(screen.getByRole("button", { name: "AI 填充" }));

    await waitFor(() => expect(onFill).toHaveBeenCalledWith({ customer_name: "比克动力" }));
    expect(api.post).toHaveBeenCalledWith("/ai-copilot/autofill", {
      form_type: "customer",
      hint: "深圳做锂电池PACK的比克动力",
    });
  });

  it("接口失败时展示错误提示且不回填", async () => {
    api.post.mockRejectedValueOnce(new Error("boom"));
    const onFill = vi.fn();
    render(<AutofillBar formType="opportunity" onFill={onFill} />);

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "一句话线索" } });
    fireEvent.click(screen.getByRole("button", { name: "AI 填充" }));

    await waitFor(() =>
      expect(screen.getByText("AI 填充失败，请稍后重试")).toBeInTheDocument()
    );
    expect(onFill).not.toHaveBeenCalled();
  });

  it("线索太短时按钮禁用", () => {
    render(<AutofillBar formType="customer" onFill={vi.fn()} />);
    expect(screen.getByRole("button", { name: "AI 填充" })).toBeDisabled();
  });

  it("带 defaultHint 时自动执行填充（命令栏动作入口）", async () => {
    api.post.mockResolvedValueOnce({
      data: { data: { fields: { opp_name: "宁德时代视觉检测" } } },
    });
    const onFill = vi.fn();
    render(
      <AutofillBar
        formType="opportunity"
        onFill={onFill}
        defaultHint="给宁德时代做视觉检测，预算120万"
      />
    );

    await waitFor(() =>
      expect(onFill).toHaveBeenCalledWith({ opp_name: "宁德时代视觉检测" })
    );
    expect(api.post).toHaveBeenCalledWith("/ai-copilot/autofill", {
      form_type: "opportunity",
      hint: "给宁德时代做视觉检测，预算120万",
    });
    // 线索同步进输入框，用户可改后手动再填
    expect(screen.getByRole("textbox")).toHaveValue("给宁德时代做视觉检测，预算120万");
  });
});
