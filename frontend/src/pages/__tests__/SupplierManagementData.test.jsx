import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagementData from '../SupplierManagementData';
import { supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  supplierApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateRating: vi.fn(),
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(
          ([key]) =>
            ![
              'initial',
              'animate',
              'exit',
              'transition',
              'variants',
            ].includes(key)
        )
      );
      return children ? children(filtered) : null;
    },
  }),
}));

vi.mock('@ant-design/icons', () => ({
  PlusOutlined: () => 'PlusOutlined',
  EditOutlined: () => 'EditOutlined',
  DeleteOutlined: () => 'DeleteOutlined',
  EyeOutlined: () => 'EyeOutlined',
  ExportOutlined: () => 'ExportOutlined',
}));

describe('SupplierManagementData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    vi.mocked(supplierApi.list).mockResolvedValue({
      data: {
        success: true,
        data: [],
        total: 0,
      },
    });
    
    render(
      <MemoryRouter>
        <SupplierManagementData />
      </MemoryRouter>
    );
  });
});