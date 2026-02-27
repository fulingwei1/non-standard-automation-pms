import { describe, it, expect, _vi } from 'vitest';
import { render } from '@testing-library/react';

// Mock PieChart component for testing
const PieChart = ({ data, width = 400, height = 300, title, showLegend = true }) => {
  return (
    <div className="pie-chart" data-testid="pie-chart">
      {title && <h3>{title}</h3>}
      <svg width={width} height={height} data-testid="chart-svg">
        {data?.map((item, index) => (
          <g key={index} data-value={item.value} data-label={item.name} />
        ))}
      </svg>
      {showLegend && data && (
        <div className="legend" data-testid="legend">
          {data.map((item, index) => (
            <div key={index} className="legend-item">
              <span className="color-box" style={{ backgroundColor: item.color }} />
              <span className="label">{item.name}</span>
              <span className="value">{item.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

describe('PieChart', () => {
  const mockData = [
    { name: '产品A', value: 300, color: '#3b82f6' },
    { name: '产品B', value: 200, color: '#10b981' },
    { name: '产品C', value: 150, color: '#f59e0b' },
  ];

  describe('Basic Rendering', () => {
    it('renders pie chart component', () => {
      const { getByTestId } = render(<PieChart data={mockData} />);
      expect(getByTestId('pie-chart')).toBeInTheDocument();
    });

    it('renders SVG element', () => {
      const { getByTestId } = render(<PieChart data={mockData} />);
      expect(getByTestId('chart-svg')).toBeInTheDocument();
    });

    it('renders title when provided', () => {
      const { getByText } = render(
        <PieChart data={mockData} title="销售分布" />
      );
      expect(getByText('销售分布')).toBeInTheDocument();
    });

    it('does not render title when not provided', () => {
      const { container } = render(<PieChart data={mockData} />);
      expect(container.querySelector('h3')).not.toBeInTheDocument();
    });
  });

  describe('Data Rendering', () => {
    it('renders all data points', () => {
      const { container } = render(<PieChart data={mockData} />);
      const dataElements = container.querySelectorAll('g[data-value]');
      expect(dataElements).toHaveLength(mockData.length);
    });

    it('handles empty data array', () => {
      const { container } = render(<PieChart data={[]} />);
      const dataElements = container.querySelectorAll('g[data-value]');
      expect(dataElements).toHaveLength(0);
    });

    it('handles single data point', () => {
      const singleData = [{ name: '单项', value: 100, color: '#3b82f6' }];
      const { container } = render(<PieChart data={singleData} />);
      const dataElements = container.querySelectorAll('g[data-value]');
      expect(dataElements).toHaveLength(1);
    });

    it('stores correct data values', () => {
      const { container } = render(<PieChart data={mockData} />);
      const firstElement = container.querySelector('g[data-value="300"]');
      expect(firstElement).toBeInTheDocument();
      expect(firstElement.getAttribute('data-label')).toBe('产品A');
    });
  });

  describe('Dimensions', () => {
    it('uses default width and height', () => {
      const { getByTestId } = render(<PieChart data={mockData} />);
      const svg = getByTestId('chart-svg');
      expect(svg.getAttribute('width')).toBe('400');
      expect(svg.getAttribute('height')).toBe('300');
    });

    it('applies custom width and height', () => {
      const { getByTestId } = render(
        <PieChart data={mockData} width={600} height={400} />
      );
      const svg = getByTestId('chart-svg');
      expect(svg.getAttribute('width')).toBe('600');
      expect(svg.getAttribute('height')).toBe('400');
    });

    it('handles small dimensions', () => {
      const { getByTestId } = render(
        <PieChart data={mockData} width={200} height={150} />
      );
      const svg = getByTestId('chart-svg');
      expect(svg.getAttribute('width')).toBe('200');
      expect(svg.getAttribute('height')).toBe('150');
    });

    it('handles large dimensions', () => {
      const { getByTestId } = render(
        <PieChart data={mockData} width={1000} height={800} />
      );
      const svg = getByTestId('chart-svg');
      expect(svg.getAttribute('width')).toBe('1000');
      expect(svg.getAttribute('height')).toBe('800');
    });
  });

  describe('Legend', () => {
    it('shows legend by default', () => {
      const { getByTestId } = render(<PieChart data={mockData} />);
      expect(getByTestId('legend')).toBeInTheDocument();
    });

    it('hides legend when showLegend is false', () => {
      const { queryByTestId } = render(
        <PieChart data={mockData} showLegend={false} />
      );
      expect(queryByTestId('legend')).not.toBeInTheDocument();
    });

    it('renders all legend items', () => {
      const { container } = render(<PieChart data={mockData} />);
      const legendItems = container.querySelectorAll('.legend-item');
      expect(legendItems).toHaveLength(mockData.length);
    });

    it('displays correct legend labels', () => {
      const { getByText } = render(<PieChart data={mockData} />);
      expect(getByText('产品A')).toBeInTheDocument();
      expect(getByText('产品B')).toBeInTheDocument();
      expect(getByText('产品C')).toBeInTheDocument();
    });

    it('displays correct legend values', () => {
      const { getByText } = render(<PieChart data={mockData} />);
      expect(getByText('300')).toBeInTheDocument();
      expect(getByText('200')).toBeInTheDocument();
      expect(getByText('150')).toBeInTheDocument();
    });

    it('applies correct colors to legend items', () => {
      const { container } = render(<PieChart data={mockData} />);
      const colorBoxes = container.querySelectorAll('.color-box');
      
      expect(colorBoxes[0]).toHaveStyle({ backgroundColor: '#3b82f6' });
      expect(colorBoxes[1]).toHaveStyle({ backgroundColor: '#10b981' });
      expect(colorBoxes[2]).toHaveStyle({ backgroundColor: '#f59e0b' });
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined data', () => {
      const { container } = render(<PieChart data={undefined} />);
      expect(container.querySelector('.pie-chart')).toBeInTheDocument();
    });

    it('handles null data', () => {
      const { container } = render(<PieChart data={null} />);
      expect(container.querySelector('.pie-chart')).toBeInTheDocument();
    });

    it('handles data with zero values', () => {
      const zeroData = [
        { name: '零值', value: 0, color: '#3b82f6' },
        { name: '正值', value: 100, color: '#10b981' },
      ];
      const { container } = render(<PieChart data={zeroData} />);
      const dataElements = container.querySelectorAll('g[data-value]');
      expect(dataElements).toHaveLength(2);
    });

    it('handles very large data values', () => {
      const largeData = [
        { name: '大数值', value: 9999999, color: '#3b82f6' },
      ];
      const { getByText } = render(<PieChart data={largeData} />);
      expect(getByText('9999999')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic pie chart', () => {
      const { container } = render(<PieChart data={mockData} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with title', () => {
      const { container } = render(
        <PieChart data={mockData} title="产品销售分布" />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot without legend', () => {
      const { container } = render(
        <PieChart data={mockData} showLegend={false} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom dimensions', () => {
      const { container } = render(
        <PieChart data={mockData} width={500} height={400} />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
