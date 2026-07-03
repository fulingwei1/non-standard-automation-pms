import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import BoardView from '../BoardView';

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        return ({ children, ...props }) => {
          const filtered = Object.fromEntries(
            Object.entries(props).filter(
              ([key]) =>
                ![
                  'variants',
                  'initial',
                  'animate',
                  'exit',
                  'transition',
                  'whileHover',
                  'whileTap',
                  'whileInView',
                  'layout',
                  'layoutId',
                ].includes(key),
            ),
          );
          return <Tag {...filtered}>{children}</Tag>;
        };
      },
    },
  ),
}));

describe('BoardView', () => {
  it('renders opportunity stages without React key warnings', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <BoardView
        groupedOpportunities={{
          lead: [
            {
              id: 1,
              name: '自动化测试线改造',
              customerName: '金凯博客户 A',
              expectedAmount: 1200000,
            },
          ],
        }}
        hideLost={false}
        onOpportunityClick={() => {}}
        onStageChange={() => {}}
      />,
    );

    expect(consoleError.mock.calls.flat().join('\n')).not.toContain(
      'Each child in a list should have a unique "key" prop',
    );

    consoleError.mockRestore();
  });
});
