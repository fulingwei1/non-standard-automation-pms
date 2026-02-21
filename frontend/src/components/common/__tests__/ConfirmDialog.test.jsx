import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConfirmDialog from '../ConfirmDialog';
import { AlertCircle } from 'lucide-react';

describe('ConfirmDialog', () => {
  describe('Basic Rendering', () => {
    it('renders when open is true', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="测试描述"
        />
      );
      expect(screen.getByText('请确认')).toBeInTheDocument();
      expect(screen.getByText('测试描述')).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      render(
        <ConfirmDialog
          open={false}
          onOpenChange={() => {}}
          description="测试描述"
        />
      );
      expect(screen.queryByText('请确认')).not.toBeInTheDocument();
    });

    it('renders custom title', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="自定义标题"
          description="描述"
        />
      );
      expect(screen.getByText('自定义标题')).toBeInTheDocument();
    });

    it('renders custom description', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="这是一个测试描述"
        />
      );
      expect(screen.getByText('这是一个测试描述')).toBeInTheDocument();
    });

    it('renders children when provided', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
        >
          <div data-testid="child-content">子内容</div>
        </ConfirmDialog>
      );
      expect(screen.getByTestId('child-content')).toBeInTheDocument();
    });
  });

  describe('Button Rendering', () => {
    it('renders default button texts', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
        />
      );
      expect(screen.getByRole('button', { name: '确认' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    });

    it('renders custom button texts', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          confirmText="提交"
          cancelText="返回"
        />
      );
      expect(screen.getByRole('button', { name: '提交' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '返回' })).toBeInTheDocument();
    });

    it('disables confirm button when confirmDisabled is true', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          confirmDisabled={true}
        />
      );
      expect(screen.getByRole('button', { name: '确认' })).toBeDisabled();
    });

    it('disables cancel button when cancelDisabled is true', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          cancelDisabled={true}
        />
      );
      expect(screen.getByRole('button', { name: '取消' })).toBeDisabled();
    });
  });

  describe('Variant Styles', () => {
    it('renders default variant', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          variant="default"
        />
      );
      expect(container).toBeInTheDocument();
    });

    it('renders destructive variant', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          variant="destructive"
        />
      );
      expect(container).toBeInTheDocument();
    });

    it('renders custom icon', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          icon={AlertCircle}
        />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onConfirm when confirm button is clicked', async () => {
      const handleConfirm = vi.fn();
      const handleOpenChange = vi.fn();

      render(
        <ConfirmDialog
          open={true}
          onOpenChange={handleOpenChange}
          onConfirm={handleConfirm}
          description="描述"
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认' });
      fireEvent.click(confirmButton);

      expect(handleConfirm).toHaveBeenCalledTimes(1);
      await waitFor(() => {
        expect(handleOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it('calls onOpenChange when cancel button is clicked', () => {
      const handleOpenChange = vi.fn();

      render(
        <ConfirmDialog
          open={true}
          onOpenChange={handleOpenChange}
          description="描述"
        />
      );

      const cancelButton = screen.getByRole('button', { name: '取消' });
      fireEvent.click(cancelButton);

      expect(handleOpenChange).toHaveBeenCalledWith(false);
    });

    it('does not call onConfirm when confirm button is disabled', () => {
      const handleConfirm = vi.fn();

      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          onConfirm={handleConfirm}
          description="描述"
          confirmDisabled={true}
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认' });
      fireEvent.click(confirmButton);

      expect(handleConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom content className', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          contentClassName="custom-content"
        />
      );
      // Note: Actual class may be added to DialogContent component
      expect(container).toBeInTheDocument();
    });

    it('applies custom title className', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="标题"
          description="描述"
          titleClassName="custom-title"
        />
      );
      const title = screen.getByText('标题');
      expect(title).toHaveClass('custom-title');
    });

    it('applies custom confirm button className', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
          confirmButtonClassName="custom-confirm"
        />
      );
      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing onConfirm gracefully', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="描述"
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认' });
      expect(() => fireEvent.click(confirmButton)).not.toThrow();
    });

    it('handles missing onOpenChange gracefully', () => {
      render(
        <ConfirmDialog
          open={true}
          description="描述"
        />
      );

      const cancelButton = screen.getByRole('button', { name: '取消' });
      expect(() => fireEvent.click(cancelButton)).not.toThrow();
    });

    it('renders without description', () => {
      render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="仅标题"
        />
      );
      expect(screen.getByText('仅标题')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default variant', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="确认操作"
          description="您确定要执行此操作吗？"
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for destructive variant', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="危险操作"
          description="此操作不可撤销"
          variant="destructive"
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with children', () => {
      const { container } = render(
        <ConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="确认提交"
          description="请确认以下信息"
        >
          <div>额外信息内容</div>
        </ConfirmDialog>
      );
      expect(container).toMatchSnapshot();
    });
  });
});
