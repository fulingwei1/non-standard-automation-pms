import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import MaterialRow from '../MaterialRow';

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                'initial',
                'animate',
                'exit',
                'variants',
                'transition',
                'whileHover',
                'whileTap',
                'whileInView',
                'layout',
                'layoutId',
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
}));

describe('MaterialRow', () => {
  it('zero quantities render progress as 0% instead of NaN', () => {
    const { container } = render(
      <MaterialRow
        onView={vi.fn()}
        material={{
          id: 'm-1',
          name: '测试物料',
          code: 'MAT-TEST',
          category: '电气件',
          supplier: '',
          status: 'not-arrived',
          totalQuantity: 0,
          arrivedQuantity: 0,
          usedQuantity: 0,
          remainingQuantity: 0,
          expectedDate: '',
          actualArrivalDate: '',
          location: '',
          daysUntilExpiry: 365,
          qualityStatus: 'qualified',
          nextAction: '等待到货',
        }}
      />,
    );

    expect(container.textContent).toContain('到货进度');
    expect(container.textContent).toContain('0%');
    expect(container.textContent).not.toMatch(/NaN|Infinity/);
  });
});
