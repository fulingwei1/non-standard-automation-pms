import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../card';

describe('Card Components', () => {
  describe('Card', () => {
    it('renders card element', () => {
      const { container } = render(<Card>卡片内容</Card>);
      expect(screen.getByText('卡片内容')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<Card className="custom-card">内容</Card>);
      expect(container.querySelector('.custom-card')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<Card ref={ref}>内容</Card>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('renders children correctly', () => {
      render(
        <Card>
          <div data-testid="child1">子元素1</div>
          <div data-testid="child2">子元素2</div>
        </Card>
      );
      expect(screen.getByTestId('child1')).toBeInTheDocument();
      expect(screen.getByTestId('child2')).toBeInTheDocument();
    });

    it('spreads additional props', () => {
      const { container } = render(<Card data-testid="card">内容</Card>);
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });
  });

  describe('CardHeader', () => {
    it('renders header content', () => {
      render(<CardHeader>标题区域</CardHeader>);
      expect(screen.getByText('标题区域')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <CardHeader className="custom-header">标题</CardHeader>
      );
      expect(container.querySelector('.custom-header')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<CardHeader ref={ref}>标题</CardHeader>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('CardTitle', () => {
    it('renders title text', () => {
      render(<CardTitle>卡片标题</CardTitle>);
      expect(screen.getByText('卡片标题')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <CardTitle className="custom-title">标题</CardTitle>
      );
      expect(container.querySelector('.custom-title')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<CardTitle ref={ref}>标题</CardTitle>);
      expect(ref.current).toBeTruthy();
    });

    it('renders as h3 element by default', () => {
      render(<CardTitle>标题</CardTitle>);
      const title = screen.getByText('标题');
      expect(title.tagName).toBe('H3');
    });
  });

  describe('CardDescription', () => {
    it('renders description text', () => {
      render(<CardDescription>卡片描述</CardDescription>);
      expect(screen.getByText('卡片描述')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <CardDescription className="custom-desc">描述</CardDescription>
      );
      expect(container.querySelector('.custom-desc')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<CardDescription ref={ref}>描述</CardDescription>);
      expect(ref.current).toBeTruthy();
    });
  });

  describe('CardContent', () => {
    it('renders content area', () => {
      render(<CardContent>卡片内容区域</CardContent>);
      expect(screen.getByText('卡片内容区域')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <CardContent className="custom-content">内容</CardContent>
      );
      expect(container.querySelector('.custom-content')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<CardContent ref={ref}>内容</CardContent>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('renders complex children', () => {
      render(
        <CardContent>
          <p>段落1</p>
          <p>段落2</p>
          <ul>
            <li>项目</li>
          </ul>
        </CardContent>
      );
      expect(screen.getByText('段落1')).toBeInTheDocument();
      expect(screen.getByText('项目')).toBeInTheDocument();
    });
  });

  describe('CardFooter', () => {
    it('renders footer content', () => {
      render(<CardFooter>卡片底部</CardFooter>);
      expect(screen.getByText('卡片底部')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <CardFooter className="custom-footer">底部</CardFooter>
      );
      expect(container.querySelector('.custom-footer')).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<CardFooter ref={ref}>底部</CardFooter>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('Complete Card Structure', () => {
    it('renders full card with all sections', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>项目详情</CardTitle>
            <CardDescription>查看项目的详细信息</CardDescription>
          </CardHeader>
          <CardContent>
            <p>这是项目的内容部分</p>
          </CardContent>
          <CardFooter>
            <button>操作按钮</button>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText('项目详情')).toBeInTheDocument();
      expect(screen.getByText('查看项目的详细信息')).toBeInTheDocument();
      expect(screen.getByText('这是项目的内容部分')).toBeInTheDocument();
      expect(screen.getByText('操作按钮')).toBeInTheDocument();
    });

    it('renders card without optional sections', () => {
      render(
        <Card>
          <CardContent>仅内容</CardContent>
        </Card>
      );

      expect(screen.getByText('仅内容')).toBeInTheDocument();
    });

    it('renders card with only header and content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>标题</CardTitle>
          </CardHeader>
          <CardContent>内容</CardContent>
        </Card>
      );

      expect(screen.getByText('标题')).toBeInTheDocument();
      expect(screen.getByText('内容')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic card', () => {
      const { container } = render(<Card>基础卡片</Card>);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for complete card structure', () => {
      const { container } = render(
        <Card className="custom-card">
          <CardHeader>
            <CardTitle>完整卡片</CardTitle>
            <CardDescription>带描述的卡片</CardDescription>
          </CardHeader>
          <CardContent>卡片内容区域</CardContent>
          <CardFooter>卡片底部</CardFooter>
        </Card>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom styling', () => {
      const { container } = render(
        <Card className="bg-blue-500">
          <CardHeader className="border-b">
            <CardTitle className="text-lg">自定义样式</CardTitle>
          </CardHeader>
          <CardContent className="p-6">内容</CardContent>
        </Card>
      );
      expect(container).toMatchSnapshot();
    });
  });
});
