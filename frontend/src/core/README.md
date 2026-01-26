# 前端核心基础设施使用指南

## 一、通用Hooks

### 1. useDataLoader - 数据加载

**用途**：统一处理数据加载、错误处理、加载状态

```tsx
import { useDataLoader } from '@/core/hooks';

const { data, isLoading, error, refetch } = useDataLoader(
  ['projects', projectId],
  () => projectApi.getProject(projectId)
);
```

### 2. usePaginatedData - 分页数据

**用途**：统一处理分页、筛选、搜索

```tsx
import { usePaginatedData } from '@/core/hooks';

const {
  data,
  total,
  pagination,
  filters,
  keyword,
  isLoading,
  handlePageChange,
  handleFilterChange,
  setKeyword,
  refetch
} = usePaginatedData(
  ['projects'],
  (params) => projectApi.listProjects(params)
);
```

### 3. useForm - 表单处理

**用途**：统一处理表单状态、验证、提交

```tsx
import { useForm } from '@/core/hooks';

const {
  values,
  errors,
  isSubmitting,
  handleChange,
  handleSubmit,
  reset
} = useForm({
  initialValues: { name: '', code: '' },
  onSubmit: async (values) => {
    return await projectApi.createProject(values);
  },
  onSuccess: () => {
    message.success('创建成功');
    navigate('/projects');
  }
});
```

### 4. useTable - 表格处理

**用途**：统一处理表格选择、排序

```tsx
import { useTable } from '@/core/hooks';

const {
  selectedRowKeys,
  selectedRows,
  rowSelection,
  handleSelect,
  clearSelection
} = useTable({
  data: projects,
  rowKey: 'id'
});
```

---

## 二、通用组件

### 1. DataTable - 数据表格

**用途**：统一的数据表格组件，自动处理筛选、搜索、分页

```tsx
import { DataTable } from '@/core/components';

<DataTable
  queryKey={['projects']}
  queryFn={(params) => projectApi.listProjects(params)}
  columns={columns}
  filters={[
    { key: 'status', label: '状态', type: 'select', options: statusOptions }
  ]}
  keywordFields={['code', 'name']}
/>
```

### 2. FilterPanel - 筛选面板

**用途**：统一的筛选面板组件

```tsx
import { FilterPanel } from '@/core/components';

<FilterPanel
  filters={[
    { key: 'status', label: '状态', type: 'select', options: statusOptions },
    { key: 'date', label: '日期', type: 'dateRange' }
  ]}
  values={filters}
  onChange={handleFilterChange}
/>
```

### 3. CommonForm - 通用表单

**用途**：统一的表单组件

```tsx
import { CommonForm } from '@/core/components';

<CommonForm
  initialValues={{ name: '', code: '' }}
  onSubmit={async (values) => {
    return await projectApi.createProject(values);
  }}
  onSuccess={() => navigate('/projects')}
>
  <Form.Item name="name" label="名称" rules={[{ required: true }]}>
    <Input />
  </Form.Item>
</CommonForm>
```

### 4. Dashboard - Dashboard组件

**用途**：统一的Dashboard组件

```tsx
import { Dashboard } from '@/core/components';

<Dashboard
  title="项目Dashboard"
  queryKey={['dashboard', 'projects']}
  queryFn={() => dashboardApi.getProjectDashboard()}
  statsCols={4}
/>
```

---

## 三、使用示例对比

### 之前（100+行）

```tsx
function ProjectList() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20 });
  const [filters, setFilters] = useState({});
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    loadData();
  }, [pagination, filters, keyword]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await projectApi.list({
        ...pagination,
        ...filters,
        keyword
      });
      setData(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // ... 大量重复代码
}
```

### 现在（20行）

```tsx
function ProjectList() {
  const {
    data,
    total,
    pagination,
    filters,
    keyword,
    isLoading,
    handlePageChange,
    handleFilterChange,
    setKeyword
  } = usePaginatedData(
    ['projects'],
    (params) => projectApi.listProjects(params)
  );

  return (
    <DataTable
      queryKey={['projects']}
      queryFn={(params) => projectApi.listProjects(params)}
      columns={columns}
    />
  );
}
```

---

## 四、预期收益

- **代码量减少**：从100行 → 20行（减少80%）
- **开发速度**：从2天 → 0.5天（提升4倍）
- **维护成本**：减少60%维护工作量
- **代码质量**：统一的错误处理、加载状态

---

## 五、更多示例

查看各组件和Hook的源码注释获取更多使用示例。
