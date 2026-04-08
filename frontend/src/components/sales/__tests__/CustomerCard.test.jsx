import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CustomerCard from '../CustomerCard';

describe('CustomerCard', () => {
  const mockCustomer = {
    id: 1,
    name: '某某科技有限公司',
    shortName: '某某科技',
    grade: 'A',
    status: 'active',
    industry: '软件开发',
    location: '北京市海淀区',
    contactPerson: '张三',
    phone: '138****1234',
    email: 'zhangsan@example.com',
    lastContact: '2024-01-15',
    totalAmount: 5000000,
    pendingAmount: 1000000,
    projectCount: 8,
    opportunityCount: 3,
    tags: ['VIP', '战略合作'],
    isWarning: false,
  };

  const mockOnClick = vi.fn();
  const mockOpen = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
    mockOpen.mockClear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-04-05T00:00:00Z'));
    vi.stubGlobal('open', mockOpen);
    window.open = mockOpen;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  describe('基本渲染', () => {
    it('渲染客户核心信息', () => {
      render(<CustomerCard customer={mockCustomer} />);

      expect(screen.getByText('某某科技')).toBeInTheDocument();
      expect(screen.getByText(/A级/)).toBeInTheDocument();
      expect(screen.getByText('软件开发')).toBeInTheDocument();
      expect(screen.getByText('北京市海淀区')).toBeInTheDocument();
      expect(screen.getByText('张三')).toBeInTheDocument();
    });

    it('渲染价值、状态和联系提醒', () => {
      render(<CustomerCard customer={mockCustomer} />);

      expect(screen.getByText('高价值')).toBeInTheDocument();
      expect(screen.getByText('活跃')).toBeInTheDocument();
      expect(screen.getAllByText('81天未联系').length).toBeGreaterThan(0);
    });

    it('渲染统计信息', () => {
      render(<CustomerCard customer={mockCustomer} />);

      expect(screen.getByText('500万')).toBeInTheDocument();
      expect(screen.getByText('100万')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('项目')).toBeInTheDocument();
      expect(screen.getByText('商机')).toBeInTheDocument();
    });

    it('渲染标签', () => {
      render(<CustomerCard customer={mockCustomer} />);

      expect(screen.getByText('VIP')).toBeInTheDocument();
      expect(screen.getByText('战略合作')).toBeInTheDocument();
    });
  });

  describe('紧凑模式', () => {
    it('渲染紧凑模式必要信息', () => {
      render(<CustomerCard customer={mockCustomer} compact />);

      expect(screen.getByText('某某科技')).toBeInTheDocument();
      expect(screen.getByText('软件开发')).toBeInTheDocument();
      expect(screen.getByText(/A级/)).toBeInTheDocument();
      expect(screen.getByText('3个商机')).toBeInTheDocument();
    });

    it('紧凑模式点击卡片会触发 onClick', () => {
      render(<CustomerCard customer={mockCustomer} compact onClick={mockOnClick} />);

      fireEvent.click(screen.getByText('某某科技'));
      expect(mockOnClick).toHaveBeenCalledWith(mockCustomer);
    });
  });

  describe('等级和状态', () => {
    it('支持不同客户等级', () => {
      const { rerender } = render(<CustomerCard customer={{ ...mockCustomer, grade: 'B' }} />);
      expect(screen.getByText(/B级/)).toBeInTheDocument();

      rerender(<CustomerCard customer={{ ...mockCustomer, grade: 'C' }} />);
      expect(screen.getByText(/C级/)).toBeInTheDocument();

      rerender(<CustomerCard customer={{ ...mockCustomer, grade: 'D' }} />);
      expect(screen.getByText(/D级/)).toBeInTheDocument();
    });

    it('缺少等级时默认显示 B 级', () => {
      const customerWithoutGrade = { ...mockCustomer };
      delete customerWithoutGrade.grade;

      render(<CustomerCard customer={customerWithoutGrade} />);
      expect(screen.getByText(/B级/)).toBeInTheDocument();
    });

    it('支持不同客户状态', () => {
      const { rerender } = render(<CustomerCard customer={{ ...mockCustomer, status: 'potential' }} />);
      expect(screen.getByText('潜在')).toBeInTheDocument();

      rerender(<CustomerCard customer={{ ...mockCustomer, status: 'dormant' }} />);
      expect(screen.getByText('沉睡')).toBeInTheDocument();

      rerender(<CustomerCard customer={{ ...mockCustomer, status: 'lost' }} />);
      expect(screen.getByText('流失')).toBeInTheDocument();
    });

    it('缺少状态时默认显示活跃', () => {
      const customerWithoutStatus = { ...mockCustomer };
      delete customerWithoutStatus.status;

      render(<CustomerCard customer={customerWithoutStatus} />);
      expect(screen.getByText('活跃')).toBeInTheDocument();
    });
  });

  describe('默认值和边界情况', () => {
    it('只传最少字段时使用默认展示', () => {
      render(<CustomerCard customer={{ name: '测试公司' }} />);

      expect(screen.getByText('测试公司')).toBeInTheDocument();
      expect(screen.getByText(/B级/)).toBeInTheDocument();
      expect(screen.getByText('未分类')).toBeInTheDocument();
      expect(screen.getByText('未设置联系人')).toBeInTheDocument();
      expect(screen.getByText('待开发')).toBeInTheDocument();
      expect(screen.getByText('从未联系')).toBeInTheDocument();
    });

    it('没有 shortName 时回退到 name', () => {
      render(<CustomerCard customer={{ name: '某某科技有限公司' }} />);
      expect(screen.getByText('某某科技有限公司')).toBeInTheDocument();
    });

    it('统计值为 0 时仍正常显示', () => {
      render(
        <CustomerCard
          customer={{
            ...mockCustomer,
            totalAmount: 0,
            pendingAmount: 0,
            projectCount: 0,
            opportunityCount: 0,
          }}
        />
      );

      expect(screen.getAllByText('0').length).toBeGreaterThan(0);
      expect(screen.getByText('待开发')).toBeInTheDocument();
    });

    it('标签超过 3 个时显示 +n', () => {
      render(
        <CustomerCard
          customer={{
            ...mockCustomer,
            tags: ['VIP', '战略合作', '重点客户', '年度大客户'],
          }}
        />
      );

      expect(screen.getByText('VIP')).toBeInTheDocument();
      expect(screen.getByText('战略合作')).toBeInTheDocument();
      expect(screen.getByText('重点客户')).toBeInTheDocument();
      expect(screen.getByText('+1')).toBeInTheDocument();
    });
  });

  describe('交互', () => {
    it('点击卡片会触发 onClick', () => {
      render(<CustomerCard customer={mockCustomer} onClick={mockOnClick} />);

      fireEvent.click(screen.getByText('某某科技'));
      expect(mockOnClick).toHaveBeenCalledWith(mockCustomer);
    });

    it('点击电话按钮会打开 tel 且不触发卡片 onClick', () => {
      render(<CustomerCard customer={mockCustomer} onClick={mockOnClick} />);

      fireEvent.click(screen.getByTitle('拨打 138****1234'));
      expect(mockOpen).toHaveBeenCalledWith('tel:138****1234');
      expect(mockOnClick).not.toHaveBeenCalled();
    });

    it('点击邮件按钮会打开 mailto 且不触发卡片 onClick', () => {
      render(<CustomerCard customer={mockCustomer} onClick={mockOnClick} />);

      fireEvent.click(screen.getByTitle('发送邮件 zhangsan@example.com'));
      expect(mockOpen).toHaveBeenCalledWith('mailto:zhangsan@example.com');
      expect(mockOnClick).not.toHaveBeenCalled();
    });

    it('点击记录沟通按钮会触发 onClick', () => {
      render(<CustomerCard customer={mockCustomer} onClick={mockOnClick} />);

      fireEvent.click(screen.getByTitle('记录沟通'));
      expect(mockOnClick).toHaveBeenCalledWith(mockCustomer);
    });
  });

  describe('预警态', () => {
    it('预警客户会带预警样式', () => {
      const { container } = render(
        <CustomerCard customer={{ ...mockCustomer, isWarning: true }} />
      );

      expect(container.firstChild).toHaveClass('border-amber-500/30');
    });

    it('非预警客户不带预警边框', () => {
      const { container } = render(
        <CustomerCard customer={{ ...mockCustomer, isWarning: false }} />
      );

      expect(container.firstChild).not.toHaveClass('border-amber-500/30');
    });
  });
});
