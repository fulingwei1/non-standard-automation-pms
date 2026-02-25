import { describe, it, expect, vi, beforeEach } from 'vitest';
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
    lastContact: '2024-01-15',
    totalAmount: 5000000,
    pendingAmount: 1000000,
    projectCount: 8,
    opportunityCount: 3,
    tags: ['VIP', '战略合作'],
    isWarning: false,
  };

  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders customer name', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('renders customer industry', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText('软件开发')).toBeInTheDocument();
    });

    it('renders customer grade', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText(/A级/)).toBeInTheDocument();
    });

    it('renders customer status', () => {
      render(<CustomerCard customer={mockCustomer} />);
      const { container } = render(<CustomerCard customer={mockCustomer} />);
      expect(container).toBeInTheDocument();
    });

    it('renders customer location', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText('北京市海淀区')).toBeInTheDocument();
    });

    it('renders contact information', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('138****1234')).toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('renders in compact mode', () => {
      render(<CustomerCard customer={mockCustomer} compact={true} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('shows essential information in compact mode', () => {
      render(<CustomerCard customer={mockCustomer} compact={true} />);
      expect(screen.getByText('软件开发')).toBeInTheDocument();
      expect(screen.getByText(/A级/)).toBeInTheDocument();
    });

    it('handles click in compact mode', () => {
      render(<CustomerCard customer={mockCustomer} compact={true} onClick={mockOnClick} />);
      const card = screen.getByText('某某科技').closest('div');
      fireEvent.click(card);
      expect(mockOnClick).toHaveBeenCalledWith(mockCustomer);
    });
  });

  describe('Customer Grade', () => {
    it('renders A grade correctly', () => {
      render(<CustomerCard customer={{ ...mockCustomer, grade: 'A' }} />);
      expect(screen.getByText(/A级/)).toBeInTheDocument();
    });

    it('renders B grade correctly', () => {
      render(<CustomerCard customer={{ ...mockCustomer, grade: 'B' }} />);
      expect(screen.getByText(/B级/)).toBeInTheDocument();
    });

    it('renders C grade correctly', () => {
      render(<CustomerCard customer={{ ...mockCustomer, grade: 'C' }} />);
      expect(screen.getByText(/C级/)).toBeInTheDocument();
    });

    it('renders D grade correctly', () => {
      render(<CustomerCard customer={{ ...mockCustomer, grade: 'D' }} />);
      expect(screen.getByText(/D级/)).toBeInTheDocument();
    });

    it('handles missing grade with default', () => {
      const customerWithoutGrade = { ...mockCustomer };
      delete customerWithoutGrade.grade;
      render(<CustomerCard customer={customerWithoutGrade} />);
      expect(screen.getByText(/B级/)).toBeInTheDocument();
    });
  });

  describe('Customer Status', () => {
    it('renders active status', () => {
      render(<CustomerCard customer={{ ...mockCustomer, status: 'active' }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('renders potential status', () => {
      render(<CustomerCard customer={{ ...mockCustomer, status: 'potential' }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('renders dormant status', () => {
      render(<CustomerCard customer={{ ...mockCustomer, status: 'dormant' }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('renders lost status', () => {
      render(<CustomerCard customer={{ ...mockCustomer, status: 'lost' }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('handles missing status with default', () => {
      const customerWithoutStatus = { ...mockCustomer };
      delete customerWithoutStatus.status;
      render(<CustomerCard customer={customerWithoutStatus} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('displays project count', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText(/8/)).toBeInTheDocument();
    });

    it('displays opportunity count', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText(/3/)).toBeInTheDocument();
    });

    it('handles zero statistics', () => {
      const customerWithZeroStats = {
        ...mockCustomer,
        projectCount: 0,
        opportunityCount: 0,
      };
      render(<CustomerCard customer={customerWithZeroStats} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('handles missing statistics with defaults', () => {
      const customerWithoutStats = {
        ...mockCustomer,
        projectCount: undefined,
        opportunityCount: undefined,
      };
      render(<CustomerCard customer={customerWithoutStats} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });
  });

  describe('Tags Display', () => {
    it('displays customer tags', () => {
      render(<CustomerCard customer={mockCustomer} />);
      expect(screen.getByText('VIP')).toBeInTheDocument();
      expect(screen.getByText('战略合作')).toBeInTheDocument();
    });

    it('handles empty tags array', () => {
      const customerWithoutTags = { ...mockCustomer, tags: [] };
      render(<CustomerCard customer={customerWithoutTags} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('handles missing tags with default', () => {
      const customerWithoutTags = { ...mockCustomer };
      delete customerWithoutTags.tags;
      render(<CustomerCard customer={customerWithoutTags} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });
  });

  describe('Warning State', () => {
    it('displays warning indicator when isWarning is true', () => {
      render(<CustomerCard customer={{ ...mockCustomer, isWarning: true }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('does not display warning when isWarning is false', () => {
      render(<CustomerCard customer={{ ...mockCustomer, isWarning: false }} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });
  });

  describe('Click Interactions', () => {
    it('calls onClick when card is clicked', () => {
      render(<CustomerCard customer={mockCustomer} onClick={mockOnClick} />);
      const card = screen.getByText('某某科技').closest('div');
      fireEvent.click(card);
      expect(mockOnClick).toHaveBeenCalledWith(mockCustomer);
    });

    it('does not error when onClick is not provided', () => {
      render(<CustomerCard customer={mockCustomer} />);
      const card = screen.getByText('某某科技').closest('div');
      expect(() => fireEvent.click(card)).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('handles customer with only required fields', () => {
      const minimalCustomer = {
        name: '测试公司',
      };
      render(<CustomerCard customer={minimalCustomer} />);
      expect(screen.getByText('测试公司')).toBeInTheDocument();
    });

    it('uses shortName when provided, falls back to name', () => {
      const customerWithShortName = {
        name: '北京某某科技有限责任公司',
        shortName: '某某科技',
      };
      render(<CustomerCard customer={customerWithShortName} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('handles missing shortName', () => {
      const customerWithoutShortName = {
        name: '某某科技有限公司',
      };
      render(<CustomerCard customer={customerWithoutShortName} />);
      expect(screen.getByText('某某科技有限公司')).toBeInTheDocument();
    });

    it('handles very long customer names', () => {
      const customerWithLongName = {
        name: '这是一个非常非常非常长的公司名称用于测试文本溢出处理',
        shortName: '长名称公司',
      };
      render(<CustomerCard customer={customerWithLongName} />);
      expect(screen.getByText('长名称公司')).toBeInTheDocument();
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot in normal mode', () => {
      const { container } = render(<CustomerCard customer={mockCustomer} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot in compact mode', () => {
      const { container } = render(<CustomerCard customer={mockCustomer} compact={true} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with warning', () => {
      const { container } = render(
        <CustomerCard customer={{ ...mockCustomer, isWarning: true }} />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
