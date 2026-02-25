import React, { useState } from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../tabs';

describe('Tabs Component', () => {
  const TabsExample = ({ onValueChange: externalOnChange, defaultValue = 'tab1' }) => {
    const [value, setValue] = useState(defaultValue);
    const handleChange = (v) => {
      setValue(v);
      externalOnChange?.(v);
    };
    return (
      <Tabs value={value} onValueChange={handleChange}>
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
  };

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
      expect(screen.queryByText('内容2')).not.toBeInTheDocument();
    });
  });

  describe('Tab Switching', () => {
    it('switches content when clicking different tab', () => {
      render(<TabsExample />);
      fireEvent.click(screen.getByText('标签2'));
      expect(screen.getByText('内容2')).toBeVisible();
    });

    it('calls onValueChange when tab is switched', () => {
      const handleChange = vi.fn();
      render(<TabsExample onValueChange={handleChange} />);
      fireEvent.click(screen.getByText('标签2'));
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
        <Tabs value="test" onValueChange={() => {}}>
          <TabsList>
            <TabsTrigger value="test">测试</TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(container.firstChild).toBeInTheDocument();
    });

    it('applies custom className to tabs list', () => {
      const { container } = render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsList className="custom-list">
            <TabsTrigger value="test">测试</TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(container.querySelector('.custom-list')).toBeInTheDocument();
    });
  });

  describe('TabsTrigger', () => {
    it('renders trigger button', () => {
      render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsList>
            <TabsTrigger value="test">触发器</TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(screen.getByText('触发器')).toBeInTheDocument();
    });

    it('applies custom className to trigger', () => {
      const { container } = render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsList>
            <TabsTrigger value="test" className="custom-trigger">
              触发器
            </TabsTrigger>
          </TabsList>
        </Tabs>
      );
      expect(container.querySelector('.custom-trigger')).toBeInTheDocument();
    });

    it('highlights active tab', () => {
      render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsList>
            <TabsTrigger value="test">Active</TabsTrigger>
            <TabsTrigger value="other">Other</TabsTrigger>
          </TabsList>
        </Tabs>
      );
      const activeBtn = screen.getByText('Active');
      expect(activeBtn.className).toContain('text-white');
    });
  });

  describe('TabsContent', () => {
    it('renders content when tab is active', () => {
      render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsContent value="test">活动内容</TabsContent>
        </Tabs>
      );
      expect(screen.getByText('活动内容')).toBeInTheDocument();
    });

    it('does not render content when tab is inactive', () => {
      render(
        <Tabs value="other" onValueChange={() => {}}>
          <TabsContent value="test">隐藏内容</TabsContent>
        </Tabs>
      );
      expect(screen.queryByText('隐藏内容')).not.toBeInTheDocument();
    });

    it('applies custom className to content', () => {
      const { container } = render(
        <Tabs value="test" onValueChange={() => {}}>
          <TabsContent value="test" className="custom-content">
            内容
          </TabsContent>
        </Tabs>
      );
      expect(container.querySelector('.custom-content')).toBeInTheDocument();
    });
  });

  describe('Controlled Mode', () => {
    it('works in controlled mode', () => {
      const ControlledTabs = () => {
        const [value, setValue] = useState('tab1');
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
});
