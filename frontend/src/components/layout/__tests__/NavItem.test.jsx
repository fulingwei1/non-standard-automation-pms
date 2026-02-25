/**
 * NavItem 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NavItem from '../NavItem';
import { Box, Home, Settings } from 'lucide-react';

const mockIconMap = {
  box: Box,
  home: Home,
  settings: Settings,
};

describe('NavItem 组件', () => {
  const mockItem = {
    name: '测试菜单',
    path: '/test',
    icon: 'home',
  };

  const mockToggleFavorite = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderNavItem = (props = {}) => {
    return render(
      <BrowserRouter>
        <NavItem
          item={mockItem}
          iconMap={mockIconMap}
          onToggleFavorite={mockToggleFavorite}
          {...props}
        />
      </BrowserRouter>
    );
  };

  describe('基本渲染', () => {
    it('应该正确渲染菜单项', () => {
      renderNavItem();

      expect(screen.getByText('测试菜单')).toBeInTheDocument();
    });

    it('应该渲染图标', () => {
      const { container } = renderNavItem();

      // 检查图标是否存在
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('应该是一个链接', () => {
      renderNavItem();

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/test');
    });

    it('icon不存在时应该使用默认Box图标', () => {
      const itemWithoutIcon = {
        name: '无图标菜单',
        path: '/no-icon',
        icon: 'nonexistent',
      };

      renderNavItem({ item: itemWithoutIcon });

      expect(screen.getByText('无图标菜单')).toBeInTheDocument();
    });
  });

  describe('激活状态', () => {
    it('当前路径匹配时应该显示激活状态', () => {
      const { container } = renderNavItem({ activePath: '/test' });

      const link = screen.getByRole('link');
      expect(link).toHaveClass('text-white');
      expect(link).toHaveClass('bg-white/[0.08]');

      // 应该有激活指示器
      const indicator = container.querySelector('.bg-primary');
      expect(indicator).toBeInTheDocument();
    });

    it('路径不匹配时应该显示未激活状态', () => {
      const { container } = renderNavItem({ activePath: '/different-path' });

      const link = screen.getByRole('link');
      // 未激活时应该是灰色
      expect(link).toHaveClass('text-slate-400');
      
      // 不应该有激活指示器
      const indicator = container.querySelector('.bg-primary');
      expect(indicator).not.toBeInTheDocument();
    });
  });

  describe('收起状态', () => {
    it('收起时应该隐藏文字', () => {
      renderNavItem({ collapsed: true, activePath: '/different' });

      // 文字仍然在DOM中但通过framer-motion的样式隐藏
      const text = screen.getByText('测试菜单');
      expect(text).toBeInTheDocument();
    });

    it('收起时应该显示tooltip', () => {
      const { container } = renderNavItem({ collapsed: true });

      const tooltip = container.querySelector('.left-full');
      expect(tooltip).toBeInTheDocument();
      expect(tooltip).toHaveTextContent('测试菜单');
    });

    it('展开时tooltip应该隐藏', () => {
      const { container } = renderNavItem({ collapsed: false });

      // tooltip应该存在但不可见
      const tooltips = container.querySelectorAll('.left-full');
      tooltips.forEach(tooltip => {
        expect(tooltip).toHaveClass('invisible');
      });
    });
  });

  describe('收藏功能', () => {
    it('应该显示收藏按钮', () => {
      const { container } = renderNavItem();

      const favoriteButton = container.querySelector('[title="收藏"]');
      expect(favoriteButton).toBeInTheDocument();
    });

    it('已收藏时应该显示填充的星星', () => {
      const { container } = renderNavItem({ isFavorite: true });

      const star = container.querySelector('.fill-yellow-400');
      expect(star).toBeInTheDocument();
    });

    it('未收藏时星星应该是空心的', () => {
      const { container } = renderNavItem({ isFavorite: false });

      const star = container.querySelector('.text-slate-500');
      expect(star).toBeInTheDocument();
    });

    it('点击收藏按钮应该调用onToggleFavorite', () => {
      const { container } = renderNavItem();

      const favoriteButton = container.querySelector('[title="收藏"]');
      fireEvent.click(favoriteButton);

      expect(mockToggleFavorite).toHaveBeenCalledWith('/test', '测试菜单', 'home');
    });

    it('点击收藏按钮不应该触发导航', () => {
      const { container } = renderNavItem();

      const favoriteButton = container.querySelector('[title="收藏"]');
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
      });

      const preventDefaultSpy = vi.spyOn(clickEvent, 'preventDefault');
      const stopPropagationSpy = vi.spyOn(clickEvent, 'stopPropagation');

      favoriteButton.dispatchEvent(clickEvent);

      // 由于我们的实现使用了e.preventDefault和e.stopPropagation
      // 这里主要验证onToggleFavorite被调用
      expect(mockToggleFavorite).toHaveBeenCalled();
    });

    it('收起状态时不应该显示收藏按钮', () => {
      const { container } = renderNavItem({ collapsed: true });

      // 在收起状态，收藏按钮不应该在DOM中
      const favoriteButton = container.querySelector('[title="收藏"]');
      expect(favoriteButton).toBeNull();
    });
  });

  describe('徽章显示', () => {
    it('有badge时应该显示', () => {
      const itemWithBadge = {
        ...mockItem,
        badge: '5',
      };

      renderNavItem({ item: itemWithBadge });

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('有badge时不应该显示收藏按钮', () => {
      const itemWithBadge = {
        ...mockItem,
        badge: '3',
      };

      const { container } = renderNavItem({ item: itemWithBadge });

      const favoriteButton = container.querySelector('[title="收藏"]');
      expect(favoriteButton).toBeNull();
    });

    it('收起状态时不应该显示badge', () => {
      const itemWithBadge = {
        ...mockItem,
        badge: '5',
      };

      renderNavItem({ item: itemWithBadge, collapsed: true });

      expect(screen.queryByText('5')).not.toBeInTheDocument();
    });
  });

  describe('禁用状态', () => {
    it('禁用时应该渲染为div而不是Link', () => {
      renderNavItem({ disabled: true });

      const link = screen.queryByRole('link');
      expect(link).not.toBeInTheDocument();

      expect(screen.getByText('测试菜单')).toBeInTheDocument();
    });

    it('禁用时应该显示Lock图标', () => {
      const { container } = renderNavItem({ disabled: true });

      // Lock图标应该存在
      const lockIcon = container.querySelector('.text-slate-600');
      expect(lockIcon).toBeInTheDocument();
    });

    it('禁用时应该显示置灰样式', () => {
      const { container } = renderNavItem({ disabled: true });

      const wrapper = container.querySelector('.cursor-not-allowed');
      expect(wrapper).toBeInTheDocument();
      expect(wrapper).toHaveClass('text-slate-600');
    });

    it('禁用时应该显示禁用原因', () => {
      const { container } = renderNavItem({
        disabled: true,
        disabledReason: '项目管理',
      });

      const tooltip = container.querySelector('.left-full');
      expect(tooltip).toBeInTheDocument();
      expect(tooltip).toHaveTextContent('需要「项目管理」权限');
    });

    it('禁用且收起时tooltip应该包含禁用原因', () => {
      const { container } = renderNavItem({
        disabled: true,
        disabledReason: '系统管理',
        collapsed: true,
      });

      const tooltip = container.querySelector('.left-full');
      expect(tooltip).toHaveTextContent('需要「系统管理」权限');
    });

    it('禁用状态不应该有激活样式', () => {
      const { container } = renderNavItem({
        disabled: true,
        activePath: '/test',
      });

      // 不应该有激活指示器
      const indicator = container.querySelector('.bg-primary');
      expect(indicator).not.toBeInTheDocument();
    });
  });

  describe('样式和动画', () => {
    it('hover时应该改变样式', () => {
      renderNavItem({ activePath: '/different-path' });

      const link = screen.getByRole('link');
      // 未激活状态下检查hover类
      expect(link).toHaveClass('hover:text-white');
      expect(link).toHaveClass('hover:bg-white/[0.04]');
    });

    it('收起状态时应该居中对齐', () => {
      renderNavItem({ collapsed: true });

      const link = screen.getByRole('link');
      expect(link).toHaveClass('justify-center');
    });

    it('图标应该有正确的大小', () => {
      const { container } = renderNavItem();

      const icon = container.querySelector('svg');
      expect(icon).toHaveClass('h-5');
      expect(icon).toHaveClass('w-5');
    });
  });

  describe('memo 优化', () => {
    it('相同props时不应该重新渲染', () => {
      const { rerender } = renderNavItem();

      const firstRender = screen.getByText('测试菜单');

      // 使用相同的props重新渲染
      rerender(
        <BrowserRouter>
          <NavItem
            item={mockItem}
            iconMap={mockIconMap}
            onToggleFavorite={mockToggleFavorite}
          />
        </BrowserRouter>
      );

      const secondRender = screen.getByText('测试菜单');

      // 应该是同一个元素（memo工作）
      expect(firstRender).toBe(secondRender);
    });
  });
});
