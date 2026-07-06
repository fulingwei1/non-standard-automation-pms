import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NotificationCenter from "../NotificationCenter";

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  list: vi.fn(),
  getUnreadCount: vi.fn(),
  markRead: vi.fn(),
  readAll: vi.fn(),
  deleteNotification: vi.fn(),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

vi.mock("../../services/api", () => ({
  notificationApi: {
    list: mocks.list,
    getUnreadCount: mocks.getUnreadCount,
    markRead: mocks.markRead,
    readAll: mocks.readAll,
    delete: mocks.deleteNotification,
  },
}));

vi.mock("../../components/layout", () => ({
  PageHeader: ({ title, description }) => (
    <header>
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  ),
}));

vi.mock("../../components/ui", () => ({
  ApiIntegrationError: ({ onRetry }) => (
    <button type="button" onClick={onRetry}>
      API Error
    </button>
  ),
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = tag;
        return ({ children, ...props }) => {
          const {
            animate: _animate,
            exit: _exit,
            initial: _initial,
            layout: _layout,
            variants: _variants,
            whileHover: _whileHover,
            ...rest
          } = props;
          return <Tag {...rest}>{children}</Tag>;
        };
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

vi.mock("lucide-react", () => {
  const Icon = ({ "data-testid": testId, ...props }) => (
    <span data-testid={testId || "icon"} {...props} />
  );
  return {
    AlertTriangle: Icon,
    ArrowRight: Icon,
    Bell: Icon,
    Calendar: Icon,
    Check: Icon,
    CheckCheck: Icon,
    Clock: Icon,
    FileText: Icon,
    Filter: Icon,
    Info: Icon,
    Package: Icon,
    Search: Icon,
    Trash2: Icon,
    Users: Icon,
  };
});

describe("NotificationCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            notification_type: "ALERT",
            title: "紧急通知",
            content: "设备异常",
            is_read: false,
            priority: "HIGH",
            created_at: "2026-07-05T08:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
        pages: 1,
      },
    });
    mocks.getUnreadCount.mockResolvedValue({
      data: {
        code: 200,
        message: "获取未读数量成功",
        data: { unread_count: 6 },
      },
    });
  });

  it("uses the unified unread-count response shape for page stats", async () => {
    render(
      <MemoryRouter>
        <NotificationCenter />
      </MemoryRouter>,
    );

    expect(await screen.findByText("您有 6 条未读通知")).toBeInTheDocument();
    expect(screen.getAllByText("未读")[0].nextElementSibling).toHaveTextContent("6");
  });
});
