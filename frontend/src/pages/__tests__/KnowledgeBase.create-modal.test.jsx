import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const { knowledgeBaseApi, serviceApiMock } = vi.hoisted(() => {
  const knowledgeBaseApi = {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  };

  return {
    knowledgeBaseApi,
    serviceApiMock: {
      knowledgeBase: knowledgeBaseApi,
    },
  };
});

vi.mock("../../services/api/service", () => ({
  serviceApi: serviceApiMock,
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === "string" ? tag : "div";
        const filteredProps = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                "initial",
                "animate",
                "exit",
                "variants",
                "transition",
                "whileHover",
                "whileTap",
                "whileInView",
                "layout",
                "layoutId",
                "drag",
                "dragConstraints",
                "onDragEnd",
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
}));

import KnowledgeBase from "../KnowledgeBase";

describe("KnowledgeBase create modal", () => {
  let originalGetComputedStyle;

  beforeEach(() => {
    vi.clearAllMocks();
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = vi.fn((element) => {
      if (typeof originalGetComputedStyle === "function") {
        try {
          return originalGetComputedStyle(element);
        } catch (_error) {
          // jsdom does not implement pseudo element styles used by Ant Design portal locking.
        }
      }

      return {
        getPropertyValue: () => "",
        overflow: "auto",
        overflowX: "auto",
        overflowY: "auto",
      };
    });

    knowledgeBaseApi.list.mockResolvedValue({
      data: {
        items: [],
        total: 0,
      },
    });

    knowledgeBaseApi.create.mockResolvedValue({
      data: {
        id: 1001,
        title: "新建知识文档",
        category: "engineering",
        content: "知识内容",
        tags: ["调试", "SOP"],
        status: "published",
        author_name: "测试用户",
        is_faq: false,
        is_featured: false,
        allow_download: true,
        created_at: "2026-03-16T10:00:00",
        updated_at: "2026-03-16T10:00:00",
      },
    });
  });

  afterEach(() => {
    window.getComputedStyle = originalGetComputedStyle;
  });

  it("点击创建文档后会打开表单弹窗", async () => {
    render(
      <MemoryRouter>
        <KnowledgeBase />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "创建文档" })[0]);

    const dialog = await screen.findByRole("dialog");

    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("创建文档")).toBeInTheDocument();
    expect(within(dialog).getByLabelText("文档标题")).toBeInTheDocument();
  });

  it("提交创建表单后会调用创建接口", async () => {
    render(
      <MemoryRouter>
        <KnowledgeBase />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "创建文档" })[0]);

    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("文档标题"), {
      target: { value: "新建知识文档" },
    });
    fireEvent.change(within(dialog).getByLabelText("标签"), {
      target: { value: "调试, SOP" },
    });
    fireEvent.change(within(dialog).getByLabelText("内容"), {
      target: { value: "知识内容" },
    });

    fireEvent.click(within(dialog).getByRole("button", { name: /创\s*建/ }));

    await waitFor(() => {
      expect(knowledgeBaseApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "新建知识文档",
          category: "engineering",
          content: "知识内容",
          tags: ["调试", "SOP"],
          status: "published",
        }),
      );
    });
  });
});
