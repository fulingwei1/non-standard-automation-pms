/**
 * SolutionList 渲染测试
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SolutionList from '../SolutionList';

// Mock dependencies
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    presaleApi: {
      solutions: {
        list: vi.fn().mockResolvedValue({ data: { items: [] } })
      }
    }
  };
});

describe('SolutionList Render Test', () => {
  it('should render without crashing', () => {
    expect(() => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );
    }).not.toThrow();
    
    expect(screen.getByText('方案中心')).toBeInTheDocument();
  });
});