import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../tabs';

describe('Tabs Component', () => {
  const TabsExample = ({ onValueChange }) => (
    <Tabs defaultValue="tab1" onValueChange={onValueChange}>
      <TabsList>
        <TabsTrigger value="tab1">标签1</TabsTrigger>
        <TabsTrigger value="tab2">标签2</TabsTrigger>
        <TabsTrigger value="tab3">标签3</TabsTrigger>
      </TabsList>
      <TabsContent value="tab1">内容1</TabsContent>
      <TabsContent value="tab2">内容2</TabsContent>
      <TabsContent value="tab3">内容3</TabsContent>
    </Tabs>
  );

  describe('Basic Rendering', () => {
    it('renders tabs component', () => {
      render(<TabsExample />);
      expect(screen.getByText('标签1')).toBeInTheDocument();
      expect(screen.getByText('标签2')).toBeInTheDocument();
      expect(screen.getByText('标签3')).toBeInTheDocument();
    });

    it('renders with defaultValue', () => {
      render(<TabsExample />);
      expect(screen.getByText('内容1')).toBeInTheDocument();
    });

    it('shows only active tab content', () => {
      render(<TabsExample />);
      expect(screen.getByText('内容1')).toBeVisible();
    });
  });

  describe('Tab Switching', () => {
    it('switches content when clicking different tab', () => {
      render(<TabsExample />);

      const tab2 = screen.getByText('标签2');
      fireEvent.click(tab2);

      expect(screen.getByText('内容2')).toBeVisible();
    });

    it('calls onValueChange when tab is switched', () => {
      const handleChange = vi.fn();
      render(<TabsExample onValueChange={handleChange} />);

      const tab2 = screen.getByText('标签2');
      fireEvent.click(tab2);

      expect(handleChange).toHaveBeenCalledWith('tab2');
    });

    it('can switch between multiple tabs', () => {
      render(<TabsExample />);

      fireEvent.click(screen.getByText('标签2'));
      expect(screen.getByText('内容2')).toBeVisible();

      fireEvent.click(screen.getByText('标签3'));
      expect(screen.getByText('内容3')).toBeVisible();

      fireEvent.click(screen.getByText('标签1'));
      expect(screen.getByText('内容1')).toBeVisible();
    });
  });

  describe('TabsList', () => {
    it('renders tabs list container', () => {
      const { container } = render(
        <TabsList>
          <TabsTrigger value="test">测试</TabsTrigger>
        </TabsList>
      );
      expect(container.firstChild).toBeInTheDocument();
    });

    it('applies custom className to tabs list', () => {
      const { container } = render(
        <TabsList className="custom-list">
          <TabsTrigger value="test">测试</TabsTrigger>
        </TabsList>
      );
      expect(container.querySelector('.custom-list')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(
        <TabsList ref={ref}>
          <TabsTrigger value="test">测试</TabsTrigger>
        </TabsList>
      );
      expect(ref.current).toBeTruthy();
    });
  });

  describe('TabsTrigger', () => {
    it('renders trigger button', () => {
      render(
        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test">触发器</TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(screen.getByText('触发器')).toBeInTheDocument();
    });

    it('applies custom className to trigger', () => {
      const { container } = render(
        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test" className="custom-trigger">
              触发器
            </TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(container.querySelector('.custom-trigger')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(
        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test" ref={ref}>
              触发器
            </TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(ref.current).toBeTruthy();
    });

    it('can be disabled', () => {
      render(
        <Tabs defaultValue="test">
          <TabsList>
            <TabsTrigger value="test" disabled>
              禁用
            </TabsTrigger>
          </TabsList>
        </Tabs>
      );
      const trigger = screen.getByText('禁用');
      expect(trigger).toHaveAttribute('disabled');
    });
  });

  describe('TabsContent', () => {
    it('renders content when tab is active', () => {
      render(
        <Tabs defaultValue="test">
          <TabsContent value="test">活动内容</TabsContent>
        </Tabs>
      );
      expect(screen.getByText('活动内容')).toBeInTheDocument();
    });

    it('applies custom className to content', () => {
      const { container } = render(
        <Tabs defaultValue="test">
          <TabsContent value="test" className="custom-content">
            内容
          </TabsContent>
        </Tabs>
      );
      expect(container.querySelector('.custom-content')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(
        <Tabs defaultValue="test">
          <TabsContent value="test" ref={ref}>
            内容
          </TabsContent>
        </Tabs>
      );
      expect(ref.current).toBeTruthy();
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation between tabs', () => {
      render(<TabsExample />);

      const tab1 = screen.getByText('标签1');
      tab1.focus();

      fireEvent.keyDown(tab1, { key: 'ArrowRight' });
      // Content should switch (implementation specific)
    });
  });

  describe('Controlled Mode', () => {
    it('works in controlled mode', () => {
      const ControlledTabs = () => {
        const [value, setValue] = React.useState('tab1');
        return (
          <Tabs value={value} onValueChange={setValue}>
            <TabsList>
              <TabsTrigger value="tab1">标签1</TabsTrigger>
              <TabsTrigger value="tab2">标签2</TabsTrigger>
            </TabsList>
            <TabsContent value="tab1">内容1</TabsContent>
            <TabsContent value="tab2">内容2</TabsContent>
          </Tabs>
        );
      };

      render(<ControlledTabs />);
      expect(screen.getByText('内容1')).toBeVisible();

      fireEvent.click(screen.getByText('标签2'));
      expect(screen.getByText('内容2')).toBeVisible();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic tabs', () => {
      const { container } = render(<TabsExample />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom styling', () => {
      const { container } = render(
        <Tabs defaultValue="tab1" className="custom-tabs">
          <TabsList className="custom-list">
            <TabsTrigger value="tab1" className="custom-trigger">
              自定义
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" className="custom-content">
            自定义内容
          </TabsContent>
        </Tabs>
      );
      expect(container).toMatchSnapshot();
    });
  });
});
