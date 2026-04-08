/**
 * 批量修复测试 mock 配置问题
 */

const fs = require('fs');
const path = require('path');

// 1. 修复 Login.test.jsx 中的 authApi mock
function fixLoginTest() {
  const filePath = path.join(__dirname, 'src/pages/__tests__/Login.test.jsx');
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 检查是否已经修复
  if (content.includes('authApi.login.mockResolvedValue')) {
    console.log('Login.test.jsx already fixed');
    return false;
  }
  
  // 添加 mock 返回值到 beforeEach
  const oldBeforeEach = `  beforeEach(() => {
    vi.clearAllMocks();

    storage = {};`;
  
  const newBeforeEach = `  beforeEach(() => {
    vi.clearAllMocks();

    // Mock authApi login/me responses
    authApi.login.mockResolvedValue({
      status: 200,
      data: {
        success: true,
        data: {
          token: 'mock-token',
          user: {
            id: 1,
            username: 'testuser',
            role: 'admin',
          },
        },
      },
    });

    authApi.me.mockResolvedValue({
      status: 200,
      data: {
        success: true,
        data: {
          id: 1,
          username: 'testuser',
          role: 'admin',
          permissions: ['all'],
        },
      },
    });

    authApi.getPermissions.mockResolvedValue({
      status: 200,
      data: {
        success: true,
        data: [{ id: 1, name: 'all', code: 'all' }],
      },
    });

    storage = {};`;
  
  if (content.includes(oldBeforeEach)) {
    content = content.replace(oldBeforeEach, newBeforeEach);
    fs.writeFileSync(filePath, content);
    console.log('Fixed: Login.test.jsx');
    return true;
  }
  return false;
}

// 2. 修复 FilterPanel.test.tsx 中的按钮文本问题
function fixFilterPanelTest() {
  const filePath = path.join(__dirname, 'src/core/components/FilterPanel/__tests__/FilterPanel.test.tsx');
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 检查是否已经修复
  if (content.includes('应该显示清除按钮')) {
    console.log('FilterPanel.test.tsx already fixed');
    return false;
  }
  
  // 检查测试内容
  if (!content.includes('should render date range filter')) {
    console.log('FilterPanel.test.tsx - test format different');
    return false;
  }
  
  // 添加一个测试 case - 修复 "should render date range filter"
  // 这个测试需要正确的 mock dateRange
  const dateRangeFix = `    // Mock dateRange value
    const mockOnChange = vi.fn();
    
    render(
      <FilterPanel
        filters={[
          {
            field: 'dateRange',
            label: '日期范围',
            type: 'dateRange',
            value: ['2024-01-01', '2024-12-31'],
            onChange: mockOnChange,
          },
        ]}
      />
    );
    
    expect(screen.getByText('日期范围')).toBeInTheDocument();`;
  
  // 修复 clear button 测试
  const clearButtonFix = `  it('should show clear button when showClear is true', () => {
    const mockOnChange = vi.fn();
    
    render(
      <FilterPanel
        filters={[
          {
            field: 'status',
            label: '状态',
            type: 'select',
            value: 'active',
            options: [
              { label: '活跃', value: 'active' },
              { label: '禁用', value: 'inactive' },
            ],
            showClear: true,
            onChange: mockOnChange,
          },
        ]}
      />
    );
    
    // Look for clear button - Ant Design uses "清除" text
    const clearButton = screen.getByRole('button', { name: /清除/i });
    expect(clearButton).toBeInTheDocument();
  });`;
  
  // 检查是否有问题的测试
  if (content.includes("screen.getByRole('button', { name: /清除|重置/i })")) {
    // 直接修改按钮选择器
    content = content.replace(
      "screen.getByRole('button', { name: /清除|重置/i })",
      "screen.getByRole('button', { name: /清除/i })"
    );
    fs.writeFileSync(filePath, content);
    console.log('Fixed: FilterPanel.test.tsx button selector');
    return true;
  }
  
  return false;
}

// 3. 修复 ChartContainer.test.jsx 中的 height 测试
function fixChartContainerTest() {
  const filePath = path.join(__dirname, 'src/components/charts/__tests__/ChartContainer.test.jsx');
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 检查是否已经修复
  if (content.includes('getByText with height')) {
    console.log('ChartContainer.test.jsx already fixed');
    return false;
  }
  
  // 修复 height 测试 - 使用 getByText 而不是 getByTestId
  if (content.includes("uses default height'")) {
    const oldTest = `    it('uses default height', () => {
      render(<ChartContainer>Content</ChartContainer>);
      const container = screen.getByTestId('chart-container');
      expect(container.style.height).toBe('400px');
    });`;
    
    const newTest = `    it('uses default height', () => {
      render(<ChartContainer>Content</ChartContainer>);
      const container = screen.getByText('Content').parentElement;
      expect(container.style.height).toBe('400px');
    });`;
    
    if (content.includes(oldTest)) {
      content = content.replace(oldTest, newTest);
      fs.writeFileSync(filePath, content);
      console.log('Fixed: ChartContainer.test.jsx default height');
      return true;
    }
  }
  
  if (content.includes("uses custom height'")) {
    const oldTest = `    it('uses custom height', () => {
      render(<ChartContainer height={500}>Content</ChartContainer>);
      const container = screen.getByTestId('chart-container');
      expect(container.style.height).toBe('500px');
    });`;
    
    const newTest = `    it('uses custom height', () => {
      render(<ChartContainer height={500}>Content</ChartContainer>);
      const container = screen.getByText('Content').parentElement;
      expect(container.style.height).toBe('500px');
    });`;
    
    if (content.includes(oldTest)) {
      content = content.replace(oldTest, newTest);
      fs.writeFileSync(filePath, content);
      console.log('Fixed: ChartContainer.test.jsx custom height');
      return true;
    }
  }
  
  return false;
}

// 4. 修复 BOMManagement.test.jsx 的 API mock
function fixBOMManagementTest() {
  const filePath = path.join(__dirname, 'src/pages/__tests__/BOMManagement.test.jsx');
  
  if (!fs.existsSync(filePath)) {
    console.log('BOMManagement.test.jsx not found');
    return false;
  }
  
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 检查是否已经修复
  if (content.includes('api.get.mockResolvedValue')) {
    console.log('BOMManagement.test.jsx already fixed');
    return false;
  }
  
  // 添加 API mock
  const apiMock = `
  // Mock API calls
  const mockApi = {
    get: vi.fn().mockResolvedValue({ 
      status: 200, 
      data: { success: true, data: [] } 
    }),
    post: vi.fn().mockResolvedValue({ 
      status: 200, 
      data: { success: true, data: { id: 1 } } 
    }),
    put: vi.fn().mockResolvedValue({ 
      status: 200, 
      data: { success: true, data: { id: 1 } } 
    }),
    delete: vi.fn().mockResolvedValue({ 
      status: 200, 
      data: { success: true } 
    }),
  };

  vi.mocked(api.get).mockResolvedValue({
    status: 200,
    data: {
      success: true,
      data: [],
    },
  });

  vi.mocked(api.post).mockResolvedValue({
    status: 200,
    data: {
      success: true,
      data: { id: 1 },
    },
  });`;
  
  // 在 beforeEach 后添加 mock
  const beforeEachMatch = content.match(/beforeEach\(\(\) => \{[\s\S]*?\}\);/);
  if (beforeEachMatch) {
    const insertPos = beforeEachMatch.index + beforeEachMatch[0].length;
    content = content.slice(0, insertPos) + '\n' + apiMock + content.slice(insertPos);
    fs.writeFileSync(filePath, content);
    console.log('Fixed: BOMManagement.test.jsx');
    return true;
  }
  
  return false;
}

// 主函数
function main() {
  console.log('=== Batch Fix Test Mocks ===\n');
  
  const fixes = [
    fixLoginTest,
    fixFilterPanelTest,
    fixChartContainerTest,
    fixBOMManagementTest,
  ];
  
  let fixed = 0;
  for (const fix of fixes) {
    try {
      if (fix()) {
        fixed++;
      }
    } catch (e) {
      console.error(`Error in ${fix.name}:`, e.message);
    }
  }
  
  console.log(`\n=== Fixed ${fixed} files ===`);
}

main();