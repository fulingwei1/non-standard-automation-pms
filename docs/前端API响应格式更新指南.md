# 前端API响应格式更新指南

> 更新前端代码以适应后端统一响应格式

---

## 📋 响应格式变化

### 1. 单个对象响应

**原格式**:
```json
{
  "id": 1,
  "name": "供应商名称",
  ...
}
```

**新格式**:
```json
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "供应商名称",
    ...
  }
}
```

### 2. 列表响应（分页）

**原格式**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

**新格式**: 保持不变（PaginatedResponse）

### 3. 列表响应（无分页）

**原格式**:
```json
[
  {"id": 1, "name": "..."},
  {"id": 2, "name": "..."}
]
```

**新格式**:
```json
{
  "items": [
    {"id": 1, "name": "..."},
    {"id": 2, "name": "..."}
  ],
  "total": 2
}
```

---

## 🔧 工具函数

### 位置
- `frontend/src/utils/responseFormatter.js` - 响应格式处理工具
- `frontend/src/utils/apiResponse.js` - API响应辅助函数

### 可用函数

#### 1. `extractData(responseData)`
从统一响应格式中提取数据（单个对象）

```javascript
import { extractData } from '@/utils/responseFormatter';

const response = await supplierApi.get(id);
const data = extractData(response.data);
// 自动处理新旧格式
```

#### 2. `extractItems(responseData)`
从列表响应中提取items数组

```javascript
import { extractItems } from '@/utils/responseFormatter';

const response = await supplierApi.list();
const items = extractItems(response.data);
// 自动处理新旧格式
```

#### 3. `extractPaginatedData(responseData)`
从分页响应中提取完整分页信息

```javascript
import { extractPaginatedData } from '@/utils/responseFormatter';

const response = await supplierApi.list({ page: 1 });
const { items, total, page, page_size } = extractPaginatedData(response.data);
```

#### 4. `extractListData(responseData)`
从列表响应中提取列表数据（无分页）

```javascript
import { extractListData } from '@/utils/responseFormatter';

const response = await memberApi.list();
const { items, total } = extractListData(response.data);
```

#### 5. `getResponseData(response)` / `getItems(response)` / `getPaginatedResponse(response)`
便捷的API响应处理方法

```javascript
import { getResponseData, getItems, getPaginatedResponse } from '@/utils/apiResponse';

// 单个对象
const data = getResponseData(response);

// 列表
const items = getItems(response);

// 分页列表
const paginated = getPaginatedResponse(response);
```

---

## 📝 更新模式

### 模式1：使用API拦截器（推荐）

API客户端已自动处理响应格式，响应对象会包含 `formatted` 字段：

```javascript
// 原代码
const response = await supplierApi.list();
const data = response.data;
setSuppliers(data.items || []);

// 新代码（使用formatted字段）
const response = await supplierApi.list();
const paginatedData = response.formatted || response.data;
setSuppliers(paginatedData.items || []);
```

### 模式2：使用工具函数

```javascript
import { extractData, extractItems } from '@/utils/responseFormatter';

// 单个对象
const response = await supplierApi.get(id);
const data = extractData(response.data);
setSupplier(data);

// 列表
const response = await supplierApi.list();
const items = extractItems(response.data);
setSuppliers(items);
```

### 模式3：兼容旧代码（向后兼容）

如果代码已经有兼容性处理，可以保持不变：

```javascript
// 已有兼容性处理，无需修改
const response = await supplierApi.list();
const items = response.data?.items || response.data || [];
setSuppliers(items);
```

---

## 🔄 具体更新示例

### 示例1：供应商列表

**原代码**:
```javascript
const response = await supplierApi.list(params);
const data = response.data;
setSuppliers(data.items || []);
setTotal(data.total || 0);
```

**新代码**:
```javascript
const response = await supplierApi.list(params);
// 使用formatted字段（由拦截器自动处理）
const paginatedData = response.formatted || response.data;
setSuppliers(paginatedData.items || []);
setTotal(paginatedData.total || 0);
```

### 示例2：供应商详情

**原代码**:
```javascript
const response = await supplierApi.get(id);
const data = response.data;
setSupplier(data);
```

**新代码**:
```javascript
const response = await supplierApi.get(id);
// 使用formatted字段
const data = response.formatted || response.data;
setSupplier(data);
```

### 示例3：创建供应商

**原代码**:
```javascript
const response = await supplierApi.create(data);
const newSupplier = response.data;
```

**新代码**:
```javascript
const response = await supplierApi.create(data);
// 使用formatted字段
const newSupplier = response.formatted || response.data;
```

### 示例4：列表响应（无分页）

**原代码**:
```javascript
const response = await memberApi.list();
const members = response.data || [];
```

**新代码**:
```javascript
import { extractListData } from '@/utils/responseFormatter';

const response = await memberApi.list();
const { items } = extractListData(response.data);
const members = items;
```

---

## ✅ 已更新的文件

### 工具函数
- ✅ `frontend/src/utils/responseFormatter.js` - 响应格式处理工具
- ✅ `frontend/src/utils/apiResponse.js` - API响应辅助函数

### API客户端
- ✅ `frontend/src/services/api/client.js` - 添加响应拦截器，自动处理格式

### 页面组件
- ✅ `frontend/src/pages/SupplierManagementData.jsx` - 更新供应商列表
- ✅ `frontend/src/pages/MaterialList.jsx` - 更新物料列表
- ✅ `frontend/src/pages/ProcurementEngineerWorkstation/hooks/useProcurementWorkstation.js` - 更新采购工作台

---

## 🔍 查找需要更新的代码

### 搜索模式

```bash
# 查找直接使用response.data的代码
grep -r "response\.data" frontend/src/pages
grep -r "res\.data" frontend/src/pages

# 查找列表响应处理
grep -r "\.items\s*\|\|" frontend/src/pages
grep -r "data\.items" frontend/src/pages
```

### 需要更新的模式

1. **单个对象响应**:
   ```javascript
   // 查找
   response.data
   res.data
   
   // 替换为
   response.formatted || response.data
   res.formatted || res.data
   ```

2. **列表响应**:
   ```javascript
   // 查找
   response.data?.items || response.data || []
   res.data?.items || res.data || []
   
   // 替换为
   const paginatedData = response.formatted || response.data;
   paginatedData?.items || paginatedData || []
   ```

---

## ⚠️ 注意事项

### 1. 向后兼容

- API拦截器自动处理响应格式，添加 `formatted` 字段
- 工具函数支持新旧格式自动识别
- 现有代码可以逐步迁移，不会立即破坏

### 2. 错误处理

错误响应仍然使用HTTPException，格式不变：
```json
{
  "detail": "错误消息"
}
```

### 3. 分页响应

分页响应格式保持不变，可以直接使用：
```javascript
const { items, total, page, page_size } = response.data;
```

### 4. 列表响应（无分页）

无分页列表响应从数组变为对象：
```javascript
// 旧格式：直接是数组
const items = response.data;

// 新格式：包含items字段
const { items } = response.data;
```

---

## 📊 更新进度

### 已完成
- ✅ 创建响应格式处理工具函数
- ✅ 更新API客户端拦截器
- ✅ 更新suppliers相关页面
- ✅ 更新materials相关页面
- ✅ 更新采购工作台hook

### 待完成
- ⏭️ 更新customers相关页面
- ⏭️ 更新machines相关页面
- ⏭️ 更新milestones相关页面
- ⏭️ 更新members相关页面
- ⏭️ 更新stages相关页面
- ⏭️ 更新其他API调用
- ⏭️ 测试前端功能

---

## 🚀 快速更新脚本

可以使用以下模式批量更新：

```javascript
// 模式1：单个对象
// 查找: response.data
// 替换: response.formatted || response.data

// 模式2：列表响应
// 查找: response.data?.items || response.data || []
// 替换: (response.formatted || response.data)?.items || (response.formatted || response.data) || []
```

---

**创建日期**: 2026-01-23  
**状态**: ✅ 进行中  
**下一步**: 更新剩余页面并测试功能
