import { describe, expect, it } from 'vitest';

import { compactQueryParams } from '../queryParams';

describe('QualificationManagement query params', () => {
  it('removes blank and all-valued filters before API requests', () => {
    expect(
      compactQueryParams({
        page: 1,
        page_size: 10,
        position_type: '',
        level_id: '',
        status: 'all',
        keyword: '机械',
      })
    ).toEqual({
      page: 1,
      page_size: 10,
      keyword: '机械',
    });
  });
});
