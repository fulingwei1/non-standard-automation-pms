# 已弃用 API 使用情况报告

生成时间: 2026-01-24

## 执行摘要

本报告识别了代码库中所有已弃用的 API 使用情况，包括：
- 已标记为 deprecated 的 FastAPI 端点
- 已弃用的数据模型
- 已弃用的 Pydantic v2 方法
- 已弃用的前端组件
- 前端代码中对已弃用 API 的调用

---

## 1. 已弃用的 FastAPI 端点

### 1.1 里程碑端点 (Milestones)

**位置**: `app/api/v1/endpoints/milestones/`

所有以下端点已标记为 `deprecated=True`，应迁移到项目中心 API：

#### `crud.py` 中的端点：

1. **GET `/milestones/`** (行 20)
   - 替代方案: `GET /projects/{project_id}/milestones/`
   - 状态: ⚠️ 已弃用

2. **GET `/milestones/projects/{project_id}/milestones`** (行 83)
   - 替代方案: `GET /projects/{project_id}/milestones/`
   - 状态: ⚠️ 已弃用

3. **POST `/milestones/`** (行 108)
   - 替代方案: `POST /projects/{project_id}/milestones/`
   - 状态: ⚠️ 已弃用

4. **GET `/milestones/{milestone_id}`** (行 131)
   - 替代方案: `GET /projects/{project_id}/milestones/{milestone_id}`
   - 状态: ⚠️ 已弃用

5. **PUT `/milestones/{milestone_id}`** (行 151)
   - 替代方案: `PUT /projects/{project_id}/milestones/{milestone_id}`
   - 状态: ⚠️ 已弃用

#### `workflow.py` 中的端点：

6. **PUT `/milestones/{milestone_id}/complete`** (行 25)
   - 替代方案: `PUT /projects/{project_id}/milestones/{milestone_id}/complete`
   - 状态: ⚠️ 已弃用

7. **DELETE `/milestones/{milestone_id}`** (行 154)
   - 替代方案: `DELETE /projects/{project_id}/milestones/{milestone_id}`
   - 状态: ⚠️ 已弃用

---

## 2. 已弃用的数据模型

### 2.1 Supplier 模型

**位置**: `app/models/material.py:101`

```python
class Supplier(Base, TimestampMixin):
    # ...
    def __repr__(self):
        return f'<Supplier {self.supplier_code} (deprecated, use Vendor instead)>'
```

**状态**: ⚠️ 已弃用，应使用 `Vendor` 模型

**使用位置**:
- `app/api/v1/endpoints/suppliers.py:11`
- `app/api/v1/endpoints/materials/suppliers.py:16`
- `app/services/urgent_purchase_from_shortage_service.py:17`
- `app/services/inventory_analysis_service.py:14`
- `app/api/v1/endpoints/business_support_orders/customer_registrations.py:14`

### 2.2 OutsourcingVendor 模型

**位置**: `app/models/outsourcing.py:24`

```python
class OutsourcingVendor(Base, TimestampMixin):
    # ...
    def __repr__(self):
        return f'<OutsourcingVendor {self.vendor_code} (deprecated, use Vendor instead)>'
```

**状态**: ⚠️ 已弃用，应使用 `Vendor` 模型

**使用位置**:
- `app/api/v1/endpoints/outsourcing/payments/print.py:35`
- `app/api/v1/endpoints/outsourcing/payments/crud.py:16`
- `app/api/v1/endpoints/report_center/templates.py:26`
- `app/api/v1/endpoints/report_center/rd_expense.py:26`
- `app/api/v1/endpoints/report_center/configs.py:26`
- `app/api/v1/endpoints/report_center/bi.py:26`
- `app/api/v1/endpoints/outsourcing/suppliers.py:229`

---

## 3. 已弃用的 Pydantic v2 方法

### 3.1 `.dict()` 方法

在 Pydantic v2 中，`.dict()` 方法已被弃用，应使用 `.model_dump()` 替代。

#### 问题文件 1: `app/api/v1/endpoints/culture_wall_config.py`

**行 136**:
```python
config = CultureWallConfig(
    **config_data.dict(),  # ❌ 应使用 config_data.model_dump()
    created_by=current_user.id
)
```

#### 问题文件 2: `app/api/v1/endpoints/management_rhythm/report_configs.py`

**行 155-157**:
```python
enabled_metrics=[item.dict() for item in config_data.enabled_metrics] if config_data.enabled_metrics else [],  # ❌
comparison_config=config_data.comparison_config.dict() if config_data.comparison_config else None,  # ❌
display_config=config_data.display_config.dict() if config_data.display_config else None,  # ❌
```

**行 240-244**:
```python
update_data["enabled_metrics"] = [item.dict() for item in config_data.enabled_metrics]  # ❌
update_data["comparison_config"] = config_data.comparison_config.dict()  # ❌
update_data["display_config"] = config_data.display_config.dict()  # ❌
```

**总计**: 7 处使用 `.dict()` 需要替换为 `.model_dump()`

---

## 4. 已弃用的前端组件

### 4.1 Ant Design TabPane 组件

**状态**: Ant Design 4.x+ 中 `TabPane` 已弃用，应使用 `items` prop

**使用位置** (共 15 个文件):

1. `frontend/src/pages/EngineerPerformanceDetail.jsx` (行 8, 287, 293, 294, 345)
2. `frontend/src/pages/EngineerKnowledge.jsx` (行 8)
3. `frontend/src/pages/EngineerPerformanceDashboard.jsx` (行 8)
4. `frontend/src/pages/CustomerServiceDashboard.jsx` (行 100, 520, 551, 553, 569, 571, 585, 587, 600, 602, 615)
5. `frontend/src/pages/AlertStatistics.jsx` (行 72, 457, 459)
6. `frontend/src/pages/MeetingManagement.jsx` (行 48, 156, 158)
7. `frontend/src/pages/LeadAssessment.jsx` (行 105, 572, 596, 598, 615, 617, 644, 646, 663, 665, 680)
8. `frontend/src/pages/EngineerCollaboration.jsx` (行 8, 334, 342, 343, 351)
9. `frontend/src/pages/CustomerSatisfaction.jsx` (行 89, 352, 366, 368, 384, 386, 400, 402, 416, 418, 431)
10. `frontend/src/pages/ContractManagement.jsx` (行 99, 433, 451, 453, 470, 472, 493, 495, 509, 511, 524)
11. `frontend/src/pages/KnowledgeBase.jsx` (行 105) - ⚠️ 已有注释说明已弃用
12. `frontend/src/pages/Customer360.jsx` (行 81, 430, 432)
13. `frontend/src/pages/EngineerPerformanceRanking.jsx` (行 8, 252, 253, 254, 255)
14. `frontend/src/pages/DeliveryManagement.jsx` (行 66, 211, 213)

**迁移指南**:
```jsx
// ❌ 旧方式
<Tabs>
  <TabPane tab="Tab 1" key="1">Content 1</TabPane>
  <TabPane tab="Tab 2" key="2">Content 2</TabPane>
</Tabs>

// ✅ 新方式
<Tabs
  items={[
    { key: '1', label: 'Tab 1', children: 'Content 1' },
    { key: '2', label: 'Tab 2', children: 'Content 2' },
  ]}
/>
```

---

## 5. 前端对已弃用 API 的调用

### 5.1 里程碑 API 调用

**位置**: `frontend/src/services/api/projects.js:126-138`

```javascript
export const milestoneApi = {
  list: (params) => {
    const projectId = params?.project_id;
    if (projectId) {
      return api.get(`/milestones/projects/${projectId}/milestones`);  // ❌ 已弃用
    }
    return api.get("/milestones/", { params });  // ❌ 已弃用
  },
  get: (id) => api.get(`/milestones/${id}`),  // ❌ 已弃用
  create: (data) => api.post("/milestones/", data),  // ❌ 已弃用
  update: (id, data) => api.put(`/milestones/${id}`, data),  // ❌ 已弃用
  complete: (id, data) => api.put(`/milestones/${id}/complete`, data || {}),  // ❌ 已弃用
};
```

**使用这些 API 的页面**:
- `frontend/src/pages/MilestoneManagement.jsx` (行 107, 131, 142)
- `frontend/src/pages/ScheduleBoard.jsx` (行 63)
- `frontend/src/pages/ProjectDetail.jsx`

**建议修复**:
```javascript
export const milestoneApi = {
  list: (projectId, params) => {
    if (!projectId) {
      throw new Error("project_id is required");
    }
    return api.get(`/projects/${projectId}/milestones/`, { params });
  },
  get: (projectId, milestoneId) => 
    api.get(`/projects/${projectId}/milestones/${milestoneId}`),
  create: (projectId, data) => 
    api.post(`/projects/${projectId}/milestones/`, data),
  update: (projectId, milestoneId, data) => 
    api.put(`/projects/${projectId}/milestones/${milestoneId}`, data),
  complete: (projectId, milestoneId, data) => 
    api.put(`/projects/${projectId}/milestones/${milestoneId}/complete`, data || {}),
};
```

---

## 6. 其他已弃用配置

### 6.1 Passlib CryptContext

**位置**: `app/core/auth.py:26`

```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
```

**状态**: ⚠️ `deprecated="auto"` 表示自动处理已弃用的方案，但 `pbkdf2_sha256` 本身不是问题

**建议**: 考虑迁移到 `bcrypt` 方案（如 `docs/technical/SECURITY_REVIEW_CHECKLIST.md:205` 中建议）

---

## 7. 修复优先级

### 🔴 高优先级

1. **前端里程碑 API 调用** - 影响用户体验，应立即修复
   - 文件: `frontend/src/services/api/projects.js`
   - 影响页面: MilestoneManagement, ScheduleBoard, ProjectDetail

2. **Pydantic `.dict()` 方法** - 在 Pydantic v2 中已移除，会导致运行时错误
   - 文件: `app/api/v1/endpoints/culture_wall_config.py`
   - 文件: `app/api/v1/endpoints/management_rhythm/report_configs.py`

### 🟡 中优先级

3. **数据模型迁移** - Supplier 和 OutsourcingVendor 应迁移到 Vendor
   - 影响多个 API 端点和服务
   - 需要数据迁移脚本

4. **Ant Design TabPane** - 组件已弃用，但功能正常
   - 15 个文件需要更新
   - 建议分批迁移

### 🟢 低优先级

5. **已弃用的 FastAPI 端点** - 已标记为 deprecated，但仍在工作
   - 建议在下一个主要版本中移除
   - 需要确保所有前端调用已迁移

---

## 8. 修复建议

### 8.1 立即修复项

1. **修复 Pydantic `.dict()` 调用**:
   ```python
   # 替换所有 .dict() 为 .model_dump()
   config_data.model_dump()
   ```

2. **更新前端里程碑 API**:
   - 修改 `milestoneApi` 使用新的项目中心端点
   - 更新所有调用方传递 `projectId` 参数

### 8.2 计划迁移项

3. **迁移 TabPane 到 items prop**:
   - 创建迁移脚本或逐个文件更新
   - 测试每个页面的功能

4. **迁移 Supplier/OutsourcingVendor 到 Vendor**:
   - 创建数据迁移脚本
   - 更新所有导入和使用
   - 更新 API 端点

### 8.3 长期清理

5. **移除已弃用的 FastAPI 端点**:
   - 确保所有前端调用已迁移
   - 在下一个主要版本中移除
   - 更新 API 文档

---

## 9. 统计摘要

| 类别 | 数量 | 状态 |
|------|------|------|
| 已弃用的 FastAPI 端点 | 7 | ⚠️ 已标记 |
| 已弃用的数据模型 | 2 | ⚠️ 需要迁移 |
| Pydantic `.dict()` 使用 | 7 | 🔴 需要立即修复 |
| TabPane 组件使用 | 15 个文件 | 🟡 建议迁移 |
| 前端调用已弃用 API | 1 个服务 | 🔴 需要立即修复 |

---

## 10. 下一步行动

1. ✅ 创建本报告
2. 🔄 修复 Pydantic `.dict()` 调用（高优先级）
3. 🔄 更新前端里程碑 API（高优先级）
4. 📋 计划 TabPane 迁移（中优先级）
5. 📋 计划数据模型迁移（中优先级）
6. 📋 计划移除已弃用端点（低优先级）

---

## 附录：相关文档

- [项目模块整合设计文档](./plans/2026-01-21-project-module-consolidation-design.md)
- [项目模块整合实施文档](./plans/2026-01-21-project-module-consolidation-implementation.md)
- [API 重构指南](./reports/API_REFACTORING_GUIDE.md)
