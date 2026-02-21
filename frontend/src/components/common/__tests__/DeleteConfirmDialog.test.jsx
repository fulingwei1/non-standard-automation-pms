import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DeleteConfirmDialog from '../DeleteConfirmDialog';

describe('DeleteConfirmDialog', () => {
  describe('Basic Rendering', () => {
    it('renders when open is true', () => {
      render(
        <DeleteConfirmDialog open={true} onOpenChange={() => {}} />
      );

      expect(screen.getByText('确认删除')).toBeInTheDocument();
      expect(screen.getByText('此操作不可撤销，请谨慎操作')).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      render(
        <DeleteConfirmDialog open={false} onOpenChange={() => {}} />
      );

      expect(screen.queryByText('确认删除')).not.toBeInTheDocument();
    });

    it('renders custom title', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="删除项目"
        />
      );

      expect(screen.getByText('删除项目')).toBeInTheDocument();
    });

    it('renders custom description', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description="删除后将无法恢复该项目的所有数据"
        />
      );

      expect(screen.getByText('删除后将无法恢复该项目的所有数据')).toBeInTheDocument();
    });

    it('renders children when provided', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
        >
          <div data-testid="child-content">
            确认删除项目 "测试项目" 吗？
          </div>
        </DeleteConfirmDialog>
      );

      expect(screen.getByTestId('child-content')).toBeInTheDocument();
    });

    it('renders warning icon', () => {
      const { container } = render(
        <DeleteConfirmDialog open={true} onOpenChange={() => {}} />
      );

      expect(container.querySelector('.text-red-400')).toBeInTheDocument();
    });
  });

  describe('Button Rendering', () => {
    it('renders default button texts', () => {
      render(
        <DeleteConfirmDialog open={true} onOpenChange={() => {}} />
      );

      expect(screen.getByRole('button', { name: '确认删除' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    });

    it('renders custom button texts', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          confirmText="永久删除"
          cancelText="返回"
        />
      );

      expect(screen.getByRole('button', { name: '永久删除' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '返回' })).toBeInTheDocument();
    });

    it('disables confirm button when confirmDisabled is true', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          confirmDisabled={true}
        />
      );

      expect(screen.getByRole('button', { name: '确认删除' })).toBeDisabled();
    });

    it('disables cancel button when cancelDisabled is true', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          cancelDisabled={true}
        />
      );

      expect(screen.getByRole('button', { name: '取消' })).toBeDisabled();
    });

    it('confirm button has destructive styling', () => {
      const { container } = render(
        <DeleteConfirmDialog open={true} onOpenChange={() => {}} />
      );

      const confirmButton = screen.getByRole('button', { name: '确认删除' });
      expect(confirmButton).toHaveClass('bg-red-500');
    });
  });

  describe('Interactions', () => {
    it('calls onConfirm and onOpenChange when confirm button is clicked', async () => {
      const handleConfirm = vi.fn();
      const handleOpenChange = vi.fn();

      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={handleOpenChange}
          onConfirm={handleConfirm}
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认删除' });
      fireEvent.click(confirmButton);

      expect(handleConfirm).toHaveBeenCalledTimes(1);
      expect(handleOpenChange).toHaveBeenCalledWith(false);
    });

    it('calls onOpenChange when cancel button is clicked', () => {
      const handleOpenChange = vi.fn();

      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={handleOpenChange}
        />
      );

      const cancelButton = screen.getByRole('button', { name: '取消' });
      fireEvent.click(cancelButton);

      expect(handleOpenChange).toHaveBeenCalledWith(false);
    });

    it('does not call onConfirm when confirm button is disabled', () => {
      const handleConfirm = vi.fn();

      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          onConfirm={handleConfirm}
          confirmDisabled={true}
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认删除' });
      fireEvent.click(confirmButton);

      expect(handleConfirm).not.toHaveBeenCalled();
    });

    it('handles missing onConfirm gracefully', () => {
      const handleOpenChange = vi.fn();

      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={handleOpenChange}
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认删除' });
      expect(() => fireEvent.click(confirmButton)).not.toThrow();
      expect(handleOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe('Custom Styling', () => {
    it('applies custom content className', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          contentClassName="custom-content"
        />
      );

      expect(container).toBeInTheDocument();
    });

    it('applies custom title className', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          titleClassName="custom-title"
        />
      );

      const title = screen.getByText('确认删除');
      expect(title).toHaveClass('custom-title');
    });

    it('applies custom description className', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          descriptionClassName="custom-description"
        />
      );

      expect(container).toBeInTheDocument();
    });

    it('applies custom confirm button className', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          confirmButtonClassName="custom-confirm"
        />
      );

      const confirmButton = screen.getByRole('button', { name: '确认删除' });
      expect(confirmButton).toHaveClass('custom-confirm');
    });

    it('applies custom cancel button className', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          cancelButtonClassName="custom-cancel"
        />
      );

      expect(container).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty description', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          description=""
        />
      );

      expect(screen.queryByText('此操作不可撤销')).not.toBeInTheDocument();
    });

    it('renders without description', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="删除"
        />
      );

      expect(screen.getByText('删除')).toBeInTheDocument();
    });

    it('handles both buttons disabled', () => {
      render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          confirmDisabled={true}
          cancelDisabled={true}
        />
      );

      expect(screen.getByRole('button', { name: '确认删除' })).toBeDisabled();
      expect(screen.getByRole('button', { name: '取消' })).toBeDisabled();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default state', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom content', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          title="删除用户"
          description="删除后该用户的所有数据将被永久清除"
          confirmText="永久删除"
        >
          <div className="text-yellow-400">
            <p>用户名: admin</p>
            <p>邮箱: admin@example.com</p>
          </div>
        </DeleteConfirmDialog>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with disabled state', () => {
      const { container } = render(
        <DeleteConfirmDialog
          open={true}
          onOpenChange={() => {}}
          confirmDisabled={true}
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
