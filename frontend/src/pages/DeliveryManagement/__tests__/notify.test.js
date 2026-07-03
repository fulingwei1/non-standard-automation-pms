import { describe, expect, it, vi } from "vitest";

import { notifyDelivery } from "../notify";

describe("notifyDelivery", () => {
  it("supports the function-style toast used by existing component tests", () => {
    const toast = vi.fn();

    notifyDelivery(toast, { title: "成功", description: "生成成功" });

    expect(toast).toHaveBeenCalledWith({ title: "成功", description: "生成成功" });
  });

  it("supports the runtime ui toast object API", () => {
    const toast = {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    };

    notifyDelivery(toast, { title: "错误", description: "加载失败", variant: "destructive" });
    notifyDelivery(toast, { title: "提示", description: "暂无数据" });
    notifyDelivery(toast, { title: "成功", description: "已导出" });

    expect(toast.error).toHaveBeenCalledWith("加载失败");
    expect(toast.info).toHaveBeenCalledWith("暂无数据");
    expect(toast.success).toHaveBeenCalledWith("已导出");
  });
});
