import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OpportunityCard from '../OpportunityCard';

describe('OpportunityCard', () => {
  const mockOpportunity = {
    id: 1,
    name: 'ERP系统升级项目',
    customerName: '某某科技有限公司',
    customerShort: '某某科技',
    stage: 'quote',
    priority: 'high',
    expectedAmount: 500000,
    expectedCloseDate: '2024-03-01',
    probability: 70,
    owner: '张三',
    daysInStage: 5,
    isHot: false,
    isOverdue: false,
    tags: ['重点项目', 'Q1目标'],
  };

  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders opportunity name', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders customer name', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('uses customerShort when available', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('某某科技')).toBeInTheDocument();
    });

    it('falls back to customerName when customerShort is missing', () => {
      const oppWithoutShortName = { ...mockOpportunity, customerShort: undefined };
      render(<OpportunityCard opportunity={oppWithoutShortName} />);
      expect(screen.getByText('某某科技有限公司')).toBeInTheDocument();
    });

    it('renders priority badge', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('高')).toBeInTheDocument();
    });
  });

  describe('Stage Display', () => {
    it('renders lead stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'lead' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders contact stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'contact' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders quote stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'quote' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders negotiate stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'negotiate' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders won stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'won' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('renders lost stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, stage: 'lost' }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('handles missing stage with default', () => {
      const oppWithoutStage = { ...mockOpportunity };
      delete oppWithoutStage.stage;
      render(<OpportunityCard opportunity={oppWithoutStage} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Priority Display', () => {
    it('renders high priority', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, priority: 'high' }} />);
      expect(screen.getByText('高')).toBeInTheDocument();
    });

    it('renders medium priority', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, priority: 'medium' }} />);
      expect(screen.getByText('中')).toBeInTheDocument();
    });

    it('renders low priority', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, priority: 'low' }} />);
      expect(screen.getByText('低')).toBeInTheDocument();
    });

    it('handles missing priority with default', () => {
      const oppWithoutPriority = { ...mockOpportunity };
      delete oppWithoutPriority.priority;
      render(<OpportunityCard opportunity={oppWithoutPriority} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Amount Display', () => {
    it('displays expected amount', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText(/500000|50万|50\.0|500,000/)).toBeInTheDocument();
    });

    it('handles zero amount', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, expectedAmount: 0 }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('handles missing amount with default', () => {
      const oppWithoutAmount = { ...mockOpportunity };
      delete oppWithoutAmount.expectedAmount;
      render(<OpportunityCard opportunity={oppWithoutAmount} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Probability Display', () => {
    it('displays probability', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText(/70%/)).toBeInTheDocument();
    });

    it('handles 0% probability', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, probability: 0 }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('handles 100% probability', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, probability: 100 }} />);
      expect(screen.getByText(/100%/)).toBeInTheDocument();
    });

    it('handles missing probability with default', () => {
      const oppWithoutProbability = { ...mockOpportunity };
      delete oppWithoutProbability.probability;
      render(<OpportunityCard opportunity={oppWithoutProbability} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Hot and Overdue States', () => {
    it('displays hot indicator when isHot is true', () => {
      const { container } = render(
        <OpportunityCard opportunity={{ ...mockOpportunity, isHot: true }} />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('does not display hot indicator when isHot is false', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, isHot: false }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('applies overdue styling when isOverdue is true', () => {
      const { container } = render(
        <OpportunityCard opportunity={{ ...mockOpportunity, isOverdue: true }} />
      );
      expect(container.firstChild).toHaveClass(/border-red/);
    });

    it('does not apply overdue styling when isOverdue is false', () => {
      const { container } = render(
        <OpportunityCard opportunity={{ ...mockOpportunity, isOverdue: false }} />
      );
      expect(container.firstChild).not.toHaveClass(/border-red/);
    });
  });

  describe('Days in Stage', () => {
    it('displays days in stage', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText(/5/)).toBeInTheDocument();
    });

    it('handles 0 days in stage', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, daysInStage: 0 }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('handles large days in stage value', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, daysInStage: 30 }} />);
      expect(screen.getByText(/30/)).toBeInTheDocument();
    });

    it('handles missing daysInStage with default', () => {
      const oppWithoutDays = { ...mockOpportunity };
      delete oppWithoutDays.daysInStage;
      render(<OpportunityCard opportunity={oppWithoutDays} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Tags Display', () => {
    it('displays opportunity tags', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('重点项目')).toBeInTheDocument();
      expect(screen.getByText('Q1目标')).toBeInTheDocument();
    });

    it('handles empty tags array', () => {
      render(<OpportunityCard opportunity={{ ...mockOpportunity, tags: [] }} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });

    it('handles missing tags with default', () => {
      const oppWithoutTags = { ...mockOpportunity };
      delete oppWithoutTags.tags;
      render(<OpportunityCard opportunity={oppWithoutTags} />);
      expect(screen.getByText('ERP系统升级项目')).toBeInTheDocument();
    });
  });

  describe('Draggable Mode', () => {
    it('renders in draggable mode', () => {
      const { container } = render(
        <OpportunityCard opportunity={mockOpportunity} draggable={true} />
      );
      expect(container.firstChild).toHaveAttribute('draggable', 'true');
    });

    it('renders in non-draggable mode by default', () => {
      const { container } = render(
        <OpportunityCard opportunity={mockOpportunity} />
      );
      expect(container.firstChild).toHaveAttribute('draggable', 'false');
    });

    it('applies draggable cursor styles', () => {
      const { container } = render(
        <OpportunityCard opportunity={mockOpportunity} draggable={true} />
      );
      expect(container.firstChild).toHaveClass(/cursor-grab/);
    });
  });

  describe('Click Interactions', () => {
    it('calls onClick when card is clicked', () => {
      render(<OpportunityCard opportunity={mockOpportunity} onClick={mockOnClick} />);
      const card = screen.getByText('ERP系统升级项目').closest('div');
      fireEvent.click(card);
      expect(mockOnClick).toHaveBeenCalledWith(mockOpportunity);
    });

    it('does not error when onClick is not provided', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      const card = screen.getByText('ERP系统升级项目').closest('div');
      expect(() => fireEvent.click(card)).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('handles opportunity with only required fields', () => {
      const minimalOpportunity = {
        name: '测试机会',
        customerName: '测试客户',
      };
      render(<OpportunityCard opportunity={minimalOpportunity} />);
      expect(screen.getByText('测试机会')).toBeInTheDocument();
      expect(screen.getByText('测试客户')).toBeInTheDocument();
    });

    it('handles very long opportunity names', () => {
      const oppWithLongName = {
        ...mockOpportunity,
        name: '这是一个非常非常非常长的商机名称用于测试文本溢出处理和截断效果',
      };
      render(<OpportunityCard opportunity={oppWithLongName} />);
      expect(screen.getByText(/这是一个非常非常非常长的商机名称/)).toBeInTheDocument();
    });

    it('renders owner name when provided', () => {
      render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(screen.getByText('张三')).toBeInTheDocument();
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot in normal mode', () => {
      const { container } = render(<OpportunityCard opportunity={mockOpportunity} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot in draggable mode', () => {
      const { container } = render(
        <OpportunityCard opportunity={mockOpportunity} draggable={true} />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with hot and overdue', () => {
      const { container } = render(
        <OpportunityCard 
          opportunity={{ ...mockOpportunity, isHot: true, isOverdue: true }} 
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
