import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { materialApiMock, purchaseApiMock, toastMock } = vi.hoisted(() => ({
  materialApiMock: {
    list: vi.fn(),
    create: vi.fn(),
    categories: {
      list: vi.fn(),
    },
  },
  purchaseApiMock: {
    orders: {
      list: vi.fn(),
      getItems: vi.fn(),
    },
  },
  toastMock: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../../services/api', () => ({
  materialApi: materialApiMock,
  purchaseApi: purchaseApiMock,
}));

vi.mock('../../components/ui/toast', () => ({
  toast: toastMock,
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                'initial',
                'animate',
                'exit',
                'variants',
                'transition',
                'whileHover',
                'whileTap',
                'whileInView',
                'layout',
                'layoutId',
                'drag',
                'dragConstraints',
                'onDragEnd',
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

vi.mock('../MaterialTracking/MaterialRow', () => ({
  default: ({ material, onView }) => (
    <div data-testid={`material-row-${material.id}`}>
      <div>{material.name}</div>
      <div>{material.code}</div>
      <div>{material.status}</div>
      <div>{material.totalQuantity}</div>
      <div>{material.arrivedQuantity}</div>
      <div>{material.nextAction}</div>
      <button onClick={() => onView(material)}>查看物料</button>
    </div>
  ),
}));

vi.mock('../MaterialTracking/CreateMaterialDialog', () => ({
  default: ({ categories, onClose, onSuccess }) => (
    <div data-testid="create-material-dialog">
      <div>categories:{categories.length}</div>
      <button onClick={onClose}>关闭新建</button>
      <button onClick={onSuccess}>创建成功</button>
    </div>
  ),
}));

import MaterialTracking from '../MaterialTracking';

describe('MaterialTracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    materialApiMock.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            material_code: 'MAT-001',
            material_name: '钢板',
            category_name: '原材料',
            standard_price: 100,
          },
          {
            id: 2,
            material_code: 'MAT-002',
            material_name: '螺栓',
            category_name: '标准件',
            standard_price: 50,
          },
        ],
      },
    });

    materialApiMock.create.mockResolvedValue({ data: { success: true } });
    materialApiMock.categories.list.mockResolvedValue({
      data: {
        items: [{ id: 1, category_name: '原材料' }],
      },
    });

    purchaseApiMock.orders.list.mockResolvedValue({
      data: {
        items: [
          { id: 11, order_no: 'PO-001' },
          { id: 12, order_no: 'PO-002' },
        ],
      },
    });

    purchaseApiMock.orders.getItems
      .mockResolvedValueOnce({
        data: {
          items: [
            { id: 101, material_code: 'MAT-001', quantity: 500, received_quantity: 500, order_no: 'PO-001' },
          ],
        },
      })
      .mockResolvedValueOnce({
        data: {
          items: [
            { id: 102, material_code: 'MAT-002', quantity: 1000, received_quantity: 0, order_no: 'PO-002' },
          ],
        },
      });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <MaterialTracking />
      </MemoryRouter>,
    );
  }

  it('默认会按真实参数加载物料、采购单和分类，并渲染统计与列表', async () => {
    renderPage();

    await waitFor(() => {
      expect(materialApiMock.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        keyword: undefined,
        is_active: true,
      });
      expect(purchaseApiMock.orders.list).toHaveBeenCalledWith({ page: 1, page_size: 100 });
      expect(purchaseApiMock.orders.getItems).toHaveBeenCalledWith(11);
      expect(purchaseApiMock.orders.getItems).toHaveBeenCalledWith(12);
      expect(materialApiMock.categories.list).toHaveBeenCalled();
    });

    expect(screen.getByText('物料跟踪')).toBeInTheDocument();
    expect(screen.getByText('实时监控物料采购、到货和使用状态')).toBeInTheDocument();
    expect(screen.getByText('物料总数')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByTestId('material-row-1')).toHaveTextContent('钢板');
    expect(screen.getByTestId('material-row-1')).toHaveTextContent('fully-arrived');
    expect(screen.getByTestId('material-row-1')).toHaveTextContent('按需领取');
    expect(screen.getByTestId('material-row-2')).toHaveTextContent('螺栓');
    expect(screen.getByTestId('material-row-2')).toHaveTextContent('not-arrived');
    expect(screen.getByTestId('material-row-2')).toHaveTextContent('等待到货');
  });

  it('搜索输入会按关键字重新请求并过滤列表', async () => {
    renderPage();

    await waitFor(() => {
      expect(materialApiMock.list).toHaveBeenCalledTimes(1);
    });

    fireEvent.change(screen.getByPlaceholderText('搜索物料名、物料码、供应商...'), {
      target: { value: '螺栓' },
    });

    await waitFor(() => {
      expect(materialApiMock.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        keyword: '螺栓',
        is_active: true,
      });
    });
  });

  it('状态按钮会切换前端过滤结果', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('material-row-1')).toBeInTheDocument();
      expect(screen.getByTestId('material-row-2')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '未到货' }));

    await waitFor(() => {
      expect(screen.queryByTestId('material-row-1')).not.toBeInTheDocument();
      expect(screen.getByTestId('material-row-2')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '全部状态' }));

    await waitFor(() => {
      expect(screen.getByTestId('material-row-1')).toBeInTheDocument();
      expect(screen.getByTestId('material-row-2')).toBeInTheDocument();
    });
  });

  it('点击新建物料会打开弹窗，成功后关闭并提示成功', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '新建物料' })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: '新建物料' }));

    expect(await screen.findByTestId('create-material-dialog')).toHaveTextContent('categories:1');

    fireEvent.click(screen.getByRole('button', { name: '创建成功' }));

    await waitFor(() => {
      expect(screen.queryByTestId('create-material-dialog')).not.toBeInTheDocument();
      expect(toastMock.success).toHaveBeenCalledWith('物料创建成功');
    });
  });

  it('加载失败时会显示错误信息', async () => {
    materialApiMock.list.mockRejectedValueOnce(new Error('Load failed'));

    renderPage();

    expect(await screen.findByText('Load failed')).toBeInTheDocument();
  });
});
