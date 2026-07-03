import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const { knowledgeBaseApi, serviceApiMock, antMessage } = vi.hoisted(() => ({
  knowledgeBaseApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  serviceApiMock: {
    knowledgeBase: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
  antMessage: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    useMessage: vi.fn(),
  },
}));

serviceApiMock.knowledgeBase = knowledgeBaseApi;

vi.mock("../../components/knowledge-base", () => ({
  KnowledgeBaseOverview: ({ data, onNavigate, loading }) => (
    <div data-testid="knowledge-overview">
      <div>overview-documents:{data?.documents?.length ?? 0}</div>
      <div>overview-categories:{data?.categories?.length ?? 0}</div>
      <div>{loading ? "overview-loading" : "overview-ready"}</div>
      <button onClick={() => onNavigate("categories")}>去分类管理</button>
    </div>
  ),
  CategoryManager: ({ categories, loading, onRefresh }) => (
    <div data-testid="category-manager">
      <div>categories:{categories?.length ?? 0}</div>
      <div>{loading ? "category-loading" : "category-ready"}</div>
      <button onClick={onRefresh}>刷新分类</button>
    </div>
  ),
  SearchAndFilter: ({ documents, loading }) => (
    <div data-testid="search-filter">
      {loading ? "search-loading" : `search-documents:${documents?.length ?? 0}`}
    </div>
  ),
  DocumentViewer: ({ document }) => (
    <div data-testid="document-viewer">viewer:{document?.title}</div>
  ),
}));

vi.mock("../../services/api/service", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    serviceApi: serviceApiMock,
  };
});

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
  AnimatePresence: ({ children }) => children,
}));

vi.mock("antd", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    message: antMessage,
    Tabs: ({ activeKey, onChange, items = [] }) => {
      const current = items.find((item) => item.key === activeKey) || items[0];
      return (
        <div>
          <div role="tablist">
            {items.map((item) => (
              <button
                key={item.key}
                role="tab"
                aria-selected={item.key === activeKey}
                onClick={() => onChange?.(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div role="tabpanel">{current?.children}</div>
        </div>
      );
    },
  };
});

import KnowledgeBase from "../KnowledgeBase";

describe("KnowledgeBase", () => {
  let originalGetComputedStyle;

  const mockDocuments = [
    {
      id: 1,
      title: "设备操作指南",
      category: "engineering",
      content: "设备调试和操作步骤",
      author_name: "张工",
      created_at: "2026-03-01T10:00:00",
      updated_at: "2026-03-02T10:00:00",
      view_count: 150,
      download_count: 12,
      like_count: 25,
      rating: 4,
      tags: ["设备", "调试"],
      status: "PUBLISHED",
      allow_download: true,
      file_path: "/files/doc-1.pdf",
      file_type: "document",
    },
    {
      id: 2,
      title: "质量检验标准",
      category: "quality",
      content: "来料和过程质量检验标准",
      author_name: "李工",
      created_at: "2026-03-05T10:00:00",
      updated_at: "2026-03-06T10:00:00",
      view_count: 200,
      download_count: 6,
      like_count: 30,
      rating: 5,
      tags: ["质量", "检验"],
      status: "PUBLISHED",
      allow_download: true,
      is_faq: true,
    },
  ];

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
          // ignore jsdom portal style gaps
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
        items: mockDocuments,
        total: 2,
      },
    });
    knowledgeBaseApi.create.mockResolvedValue({ data: { id: 3 } });
    knowledgeBaseApi.update.mockResolvedValue({ data: { id: 1 } });
    knowledgeBaseApi.delete.mockResolvedValue({ data: { success: true } });
    antMessage.useMessage.mockReturnValue([antMessage, <div key="message-holder" data-testid="message-holder" />]);
  });

  afterEach(() => {
    window.getComputedStyle = originalGetComputedStyle;
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <KnowledgeBase />
      </MemoryRouter>,
    );
  }

  it("加载页面时按当前真实参数请求知识库，并渲染页头和概览", async () => {
    renderPage();

    expect(screen.getByText("知识库")).toBeInTheDocument();
    expect(screen.getByText("历史方案、产品知识、工艺知识、竞品情报、模板库")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "创建文档" }).length).toBeGreaterThan(0);

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        keyword: undefined,
        category: undefined,
        status: "published",
        is_faq: undefined,
      });
    });

    expect(screen.getByTestId("knowledge-overview")).toHaveTextContent("overview-documents:2");
    expect(screen.getByTestId("knowledge-overview")).toHaveTextContent("overview-categories:1");
  });

  it("切到分类管理页后会触发重新加载", async () => {
    renderPage();

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole("tab", { name: /分类管理/ }));

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalledTimes(2);
    });
  });

  it("切到文档管理后会展示真实文档数据，并支持搜索过滤", async () => {
    renderPage();

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("tab", { name: /文档管理/ }));

    expect(await screen.findByText("设备操作指南")).toBeInTheDocument();
    expect(screen.getByText("质量检验标准")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("搜索文档标题、内容、标签..."), {
      target: { value: "质量" },
    });

    expect(screen.queryByText("设备操作指南")).not.toBeInTheDocument();
    expect(screen.getByText("质量检验标准")).toBeInTheDocument();
  });

  it("文档管理列表视图下可以删除文档", async () => {
    renderPage();

    await waitFor(() => {
      expect(knowledgeBaseApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("tab", { name: /文档管理/ }));
    fireEvent.click(screen.getAllByRole("radio")[1]);

    const deleteButtons = await screen.findAllByRole("button", { name: "删除" });
    expect(deleteButtons.length).toBeGreaterThan(0);

    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(knowledgeBaseApi.delete).toHaveBeenCalledWith(1);
      expect(antMessage.success).toHaveBeenCalledWith("删除成功");
    });

    await waitFor(() => {
      expect(screen.queryByText("设备操作指南")).not.toBeInTheDocument();
    });
  });

  it("加载失败时会提示错误消息", async () => {
    knowledgeBaseApi.list.mockRejectedValueOnce(new Error("Load failed"));

    renderPage();

    await waitFor(() => {
      expect(antMessage.error).toHaveBeenCalledWith("加载数据失败");
    });
  });
});
