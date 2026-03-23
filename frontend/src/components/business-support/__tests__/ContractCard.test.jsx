import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ContractCard } from '../ContractCard';

// Mock contract data
const mockContract = {
  id: 'CONTRACT-001',
  projectName: '测试项目',
  customerName: '测试客户',
  contractAmount: 1000000,
  paidAmount: 500000,
  paymentProgress: 50,
  health: 'good',
  invoiceStatus: 'complete',
  invoiceCount: 3,
  acceptanceStatus: 'completed',
  paymentStages: [
    { type: '首付款', amount: 300000, status: 'paid' },
    { type: '进度款', amount: 200000, status: 'paid' },
    { type: '尾款', amount: 500000, status: 'pending' },
  ],
};

describe('ContractCard', () => {
  describe('Basic Rendering', () => {
    it('renders contract basic information', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('测试项目')).toBeInTheDocument();
      expect(screen.getByText('测试客户')).toBeInTheDocument();
      expect(screen.getByText('CONTRACT-001')).toBeInTheDocument();
    });

    it('renders contract amount', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getAllByText(/1,000,000/).length).toBeGreaterThanOrEqual(1);
    });

    it('renders payment progress', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('回款进度')).toBeInTheDocument();
    });

    it('displays paid stages count', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('2/3 款已到账')).toBeInTheDocument();
    });
  });

  describe('Payment Stages', () => {
    it('renders all payment stages', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('首付款')).toBeInTheDocument();
      expect(screen.getByText('进度款')).toBeInTheDocument();
      expect(screen.getByText('尾款')).toBeInTheDocument();
    });

    it('displays paid stage status', () => {
      render(<ContractCard contract={mockContract} />);

      const paidBadges = screen.getAllByText('已到账');
      expect(paidBadges).toHaveLength(2);
    });

    it('displays pending stage status', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('待回款')).toBeInTheDocument();
    });

    it('displays overdue stage status', () => {
      const contractWithOverdue = {
        ...mockContract,
        paymentStages: [
          ...mockContract.paymentStages,
          { type: '延期款', amount: 100000, status: 'overdue' },
        ],
      };

      render(<ContractCard contract={contractWithOverdue} />);

      expect(screen.getByText('已逾期')).toBeInTheDocument();
    });
  });

  describe('Health Status', () => {
    it('displays good health status', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('正常')).toBeInTheDocument();
    });

    it('displays warning health status', () => {
      const warningContract = { ...mockContract, health: 'warning' };
      render(<ContractCard contract={warningContract} />);

      expect(screen.getByText('有风险')).toBeInTheDocument();
    });

    it('displays danger health status', () => {
      const dangerContract = { ...mockContract, health: 'danger' };
      render(<ContractCard contract={dangerContract} />);

      expect(screen.getByText('阻塞')).toBeInTheDocument();
    });
  });

  describe('Invoice and Acceptance Status', () => {
    it('displays invoice status when complete', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText('发票: 3张')).toBeInTheDocument();
    });

    it('displays completed acceptance status', () => {
      render(<ContractCard contract={mockContract} />);

      expect(screen.getByText(/验收.*已完成/)).toBeInTheDocument();
    });

    it('displays in-progress acceptance status', () => {
      const contract = { ...mockContract, acceptanceStatus: 'in_progress' };
      render(<ContractCard contract={contract} />);

      expect(screen.getByText(/验收.*进行中/)).toBeInTheDocument();
    });

    it('displays pending acceptance status', () => {
      const contract = { ...mockContract, acceptanceStatus: 'pending' };
      render(<ContractCard contract={contract} />);

      expect(screen.getByText(/验收.*待验收/)).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('shows action buttons by default', () => {
      render(
        <ContractCard
          contract={mockContract}
          onViewDetails={() => {}}
          onEdit={() => {}}
          onDownload={() => {}}
        />
      );

      expect(screen.getByTitle('查看详情')).toBeInTheDocument();
      expect(screen.getByTitle('编辑')).toBeInTheDocument();
      expect(screen.getByTitle('下载')).toBeInTheDocument();
    });

    it('hides actions when showActions is false', () => {
      render(<ContractCard contract={mockContract} showActions={false} />);

      expect(screen.queryByTitle('查看详情')).not.toBeInTheDocument();
      expect(screen.queryByTitle('编辑')).not.toBeInTheDocument();
      expect(screen.queryByTitle('下载')).not.toBeInTheDocument();
    });

    it('calls onViewDetails when view button is clicked', () => {
      const handleView = vi.fn();
      render(
        <ContractCard contract={mockContract} onViewDetails={handleView} />
      );

      const viewButton = screen.getByTitle('查看详情');
      fireEvent.click(viewButton);

      expect(handleView).toHaveBeenCalledWith(mockContract);
    });

    it('calls onEdit when edit button is clicked', () => {
      const handleEdit = vi.fn();
      render(<ContractCard contract={mockContract} onEdit={handleEdit} />);

      const editButton = screen.getByTitle('编辑');
      fireEvent.click(editButton);

      expect(handleEdit).toHaveBeenCalledWith(mockContract);
    });

    it('calls onDownload when download button is clicked', () => {
      const handleDownload = vi.fn();
      render(
        <ContractCard contract={mockContract} onDownload={handleDownload} />
      );

      const downloadButton = screen.getByTitle('下载');
      fireEvent.click(downloadButton);

      expect(handleDownload).toHaveBeenCalledWith(mockContract);
    });

    it('handles missing action handlers gracefully', () => {
      render(<ContractCard contract={mockContract} />);

      const viewButton = screen.getByTitle('查看详情');
      expect(() => fireEvent.click(viewButton)).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('handles contract with no payment stages', () => {
      const contract = { ...mockContract, paymentStages: [] };
      render(<ContractCard contract={contract} />);

      expect(screen.getByText('0/0 款已到账')).toBeInTheDocument();
    });

    it('handles contract with all paid stages', () => {
      const contract = {
        ...mockContract,
        paymentStages: [
          { type: '首付款', amount: 300000, status: 'paid' },
          { type: '尾款', amount: 700000, status: 'paid' },
        ],
      };
      render(<ContractCard contract={contract} />);

      expect(screen.getByText('2/2 款已到账')).toBeInTheDocument();
    });

    it('handles zero payment progress', () => {
      const contract = {
        ...mockContract,
        paidAmount: 0,
        paymentProgress: 0,
      };
      render(<ContractCard contract={contract} />);

      expect(screen.getByText(/0.*1,000,000/)).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for contract in good health', () => {
      const { container } = render(<ContractCard contract={mockContract} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for contract with warning', () => {
      const { container } = render(
        <ContractCard contract={{ ...mockContract, health: 'warning' }} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for contract in danger', () => {
      const { container } = render(
        <ContractCard contract={{ ...mockContract, health: 'danger' }} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot without actions', () => {
      const { container } = render(
        <ContractCard contract={mockContract} showActions={false} />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
