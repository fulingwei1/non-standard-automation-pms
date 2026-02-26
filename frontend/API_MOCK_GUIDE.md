# Frontend API Mock Guide

## 常见问题

**症状**: 测试失败，组件调用 `xxxApi.method()` 返回 undefined

**原因**: 测试mock了底层 `api`，但组件使用高层 API 模块

## API模块列表

从 `src/services/api/` 导出的API模块：

```javascript
// Service相关
serviceApi          // 服务记录、工单、满意度、知识库
installationDispatchApi  // 安装派单
itrApi             // ITR流程分析

// 项目相关
projectApi         // 项目管理
stageApi           // 阶段管理
milestoneApi       // 里程碑
costApi            // 成本管理
resourcePlanApi    // 资源计划

// 业务相关
presaleApi         // 售前
salesApi           // 销售
procurementApi     // 采购
productionApi      // 生产
materialApi        // 物料
qualificationApi   // 资质管理

// 人力资源
hrApi              // 人力资源
performanceApi     // 绩效
staffingApi        // 人员配置
workloadApi        // 工作量

// 其他
customerApi        // 客户管理
supplierApi        // 供应商
approvalApi        // 审批
adminApi           // 行政管理
organizationApi    // 组织架构
roleApi            // 角色权限
```

## Mock模式

### ❌ 错误模式 (Mock底层API)

```javascript
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  }
}));
```

### ✅ 正确模式 (Mock特定API模块)

```javascript
vi.mock('../../services/api', () => ({
  serviceApi: {
    records: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    }
  }
}));
```

### ✅ 多个API模块

```javascript
vi.mock('../../services/api', () => ({
  materialApi: {
    list: vi.fn(),
    get: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
    get: vi.fn(),
  },
  supplierApi: {
    list: vi.fn(),
  }
}));
```

## 常见API结构

### 列表型API
```javascript
xxxApi: {
  list: vi.fn(),      // GET /xxx?params
  get: vi.fn(),       // GET /xxx/:id
  create: vi.fn(),    // POST /xxx
  update: vi.fn(),    // PUT /xxx/:id
  delete: vi.fn(),    // DELETE /xxx/:id
}
```

### 嵌套型API (如serviceApi)
```javascript
serviceApi: {
  tickets: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    // ...
  },
  records: {
    list: vi.fn(),
    get: vi.fn(),
    // ...
  }
}
```

## 修复步骤

1. **找到组件使用的API**
   ```bash
   grep "import.*Api.*from.*services/api" src/pages/ServiceRecord.jsx
   # 结果: import { serviceApi } from "../services/api";
   ```

2. **找到组件调用的方法**
   ```bash
   grep "serviceApi\." src/pages/ServiceRecord.jsx
   # 结果: serviceApi.records.list(params)
   ```

3. **修改测试mock**
   ```javascript
   vi.mock('../../services/api', () => ({
     serviceApi: {
       records: {
         list: vi.fn().mockResolvedValue({ data: mockData }),
       }
     }
   }));
   ```

4. **设置mock返回值**
   ```javascript
   beforeEach(() => {
     serviceApi.records.list.mockResolvedValue({
       data: { items: [...], total: 100 }
     });
   });
   ```

## 验证修复

```bash
# 单个测试
npx vitest run src/pages/__tests__/ServiceRecord.test.jsx

# 全量测试
npm test
```

## 常见失败模式

| 错误信息 | 原因 | 修复 |
|---------|------|------|
| `Cannot read property 'list' of undefined` | serviceApi未mock | 添加serviceApi mock |
| `TypeError: xxx is not a function` | mock方法缺失 | 添加对应方法到mock |
| `await waitFor` 超时 | mock返回值格式错误 | 检查返回值结构 |
| `'加载失败' / '未知错误'` | API调用失败 | 确保mock正确返回Promise |

## 受影响的主要测试

- [ ] ServiceRecord.test.jsx (serviceApi)
- [ ] MaterialTracking.test.jsx (materialApi, projectApi, supplierApi)
- [ ] QualificationManagement.test.jsx (qualificationApi)
- [ ] WorkOrderManagement.test.jsx (productionApi)
- [ ] WorkshopManagement.test.jsx (productionApi)
- [ ] BudgetManagement.test.jsx (projectApi, costApi)
- [ ] SupplierManagement.test.jsx (supplierApi)
- [ ] CustomerCommunication.test.jsx (communicationApi, customerApi)
