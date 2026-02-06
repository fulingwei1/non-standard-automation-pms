# 62个API端点测试覆盖率推进计划

**生成时间**: 2026-01-20  
**目标**: 为62个未测试的API端点生成并实现测试用例  
**当前状态**: ✅ 测试文件已生成，待实现测试逻辑

---

## 📊 概览

### 端点分布

| 模块 | 端点数 | 测试文件 | 状态 |
|------|--------|----------|------|
| projects | 45 | `test_projects_api.py` | ✅ 已生成 |
| members | 6 | `test_members_api.py` | ✅ 已生成 |
| stages | 6 | `test_stages_api.py` | ✅ 已生成 |
| machines | 3 | `test_machines_api.py` | ✅ 已生成 |
| org | 3 | `test_org_api.py` | ✅ 已生成 |
| milestones | 1 | `test_milestones_api.py` | ✅ 已生成 |
| **总计** | **64** | **6个文件** | ✅ **已生成** |

---

## 🎯 推进策略

### 阶段1: 基础测试实现（优先级：高）

**目标**: 实现基础的成功路径测试，覆盖所有端点的基本功能

#### 1.1 Projects模块（45个端点）- 预计3-4天

**重点端点**:
- 项目模板管理（10个端点）
  - `GET /api/v1/projects/templates` - 列表
  - `POST /api/v1/projects/templates` - 创建
  - `GET /api/v1/projects/templates/{template_id}` - 详情
  - `PUT /api/v1/projects/templates/{template_id}` - 更新
  - `GET /api/v1/projects/templates/{template_id}/versions` - 版本列表
  - `POST /api/v1/projects/templates/{template_id}/versions` - 创建版本
  - `PUT /api/v1/projects/templates/{template_id}/versions/{version_id}/publish` - 发布版本
  - `GET /api/v1/projects/templates/{template_id}/versions/compare` - 版本对比
  - `POST /api/v1/projects/templates/{template_id}/versions/{version_id}/rollback` - 回滚
  - `GET /api/v1/projects/templates/{template_id}/usage-statistics` - 使用统计

- 项目归档管理（4个端点）
  - `PUT /api/v1/projects/{project_id}/archive` - 归档
  - `PUT /api/v1/projects/{project_id}/unarchive` - 取消归档
  - `GET /api/v1/projects/archived` - 归档列表
  - `POST /api/v1/projects/batch/archive` - 批量归档

- 项目同步功能（4个端点）
  - `POST /api/v1/projects/{project_id}/sync-from-contract` - 从合同同步
  - `POST /api/v1/projects/{project_id}/sync-to-contract` - 同步到合同
  - `GET /api/v1/projects/{project_id}/sync-status` - 同步状态
  - `POST /api/v1/projects/{project_id}/sync-to-erp` - 同步到ERP

- 项目健康度（4个端点）
  - `PUT /api/v1/projects/{project_id}/health` - 更新健康度
  - `POST /api/v1/projects/{project_id}/health/calculate` - 计算健康度
  - `GET /api/v1/projects/{project_id}/health/details` - 健康度详情
  - `POST /api/v1/projects/health/batch-calculate` - 批量计算

- 项目阶段管理（3个端点）
  - `POST /api/v1/projects/{project_id}/stages/init` - 初始化阶段
  - `POST /api/v1/projects/{project_id}/stage-advance` - 推进阶段
  - `GET /api/v1/projects/{project_id}/status-history` - 状态历史

- 项目批量操作（3个端点）
  - `POST /api/v1/projects/batch/update-status` - 批量更新状态
  - `POST /api/v1/projects/batch/update-stage` - 批量更新阶段
  - `POST /api/v1/projects/batch/assign-pm` - 批量分配PM

- 项目支付计划（4个端点）
  - `GET /api/v1/projects/{project_id}/payment-plans` - 支付计划列表
  - `POST /api/v1/projects/{project_id}/payment-plans` - 创建支付计划
  - `PUT /api/v1/projects/payment-plans/{plan_id}` - 更新支付计划
  - `DELETE /api/v1/projects/payment-plans/{plan_id}` - 删除支付计划

- 其他项目功能（13个端点）
  - `GET /api/v1/projects/overview` - 概览
  - `GET /api/v1/projects/dashboard` - 仪表板
  - `GET /api/v1/projects/in-production-summary` - 生产中摘要
  - `GET /api/v1/projects/{project_id}/timeline` - 时间线
  - `GET /api/v1/projects/board` - 看板
  - `DELETE /api/v1/projects/{project_id}` - 删除项目
  - `POST /api/v1/projects/{project_id}/clone` - 克隆项目
  - `PUT /api/v1/projects/{project_id}/stage` - 更新阶段
  - `GET /api/v1/projects/{project_id}/status` - 获取状态
  - `PUT /api/v1/projects/{project_id}/status` - 更新状态
  - `GET /api/v1/projects/{project_id}/erp-status` - ERP状态
  - `PUT /api/v1/projects/{project_id}/erp-status` - 更新ERP状态
  - `GET /api/v1/projects/statistics` - 统计

**测试策略**:
1. 使用 `tests/factories.py` 创建测试数据
2. 每个端点至少实现：
   - 成功路径测试（Happy Path）
   - 权限测试（如果需要）
   - 数据验证测试（边界条件）
3. 使用 `pytest.mark.parametrize` 进行参数化测试

#### 1.2 Members模块（6个端点）- 预计1天

- `POST /api/v1/members/projects/{project_id}/members` - 添加成员
- `PUT /api/v1/members/project-members/{member_id}` - 更新成员
- `GET /api/v1/members/projects/{project_id}/members/conflicts` - 冲突检查
- `POST /api/v1/members/projects/{project_id}/members/batch` - 批量添加
- `POST /api/v1/members/projects/{project_id}/members/{member_id}/notify-dept-manager` - 通知部门经理
- `GET /api/v1/members/projects/{project_id}/members/from-dept/{dept_id}` - 从部门获取成员

#### 1.3 Stages模块（6个端点）- 预计1天

- `POST /api/v1/stages` - 创建阶段
- `PUT /api/v1/stages/{stage_id}` - 更新阶段
- `PUT /api/v1/stages/project-stages/{stage_id}` - 更新项目阶段
- `GET /api/v1/stages/project-stages/{stage_id}/statuses` - 获取状态列表
- `PUT /api/v1/stages/project-statuses/{status_id}/complete` - 完成状态
- `POST /api/v1/stages/statuses` - 创建状态

#### 1.4 Machines模块（3个端点）- 预计0.5天

- `GET /api/v1/projects/{project_id}/machines` - 项目机台列表
- `POST /api/v1/projects/{project_id}/machines` - 创建机台
- `PUT /api/v1/projects/{project_id}/machines/{machine_id}/progress` - 更新进度

#### 1.5 Org模块（3个端点）- 预计0.5天

- `POST /api/v1/org/employees` - 创建员工
- `GET /api/v1/org/employees/{emp_id}` - 获取员工
- `PUT /api/v1/org/employees/{emp_id}` - 更新员工

#### 1.6 Milestones模块（1个端点）- 预计0.5天

- `DELETE /api/v1/milestones/{milestone_id}` - 删除里程碑

---

### 阶段2: 完善测试（优先级：中）

**目标**: 添加边界条件、异常处理、权限测试

1. **边界条件测试**
   - 空数据测试
   - 最大/最小值测试
   - 特殊字符测试

2. **异常处理测试**
   - 404 Not Found
   - 403 Forbidden
   - 400 Bad Request
   - 500 Internal Server Error

3. **权限测试**
   - 不同角色的权限验证
   - 数据范围权限验证

---

### 阶段3: 集成测试（优先级：中）

**目标**: 实现端到端业务流程测试

1. **项目完整生命周期测试**
   - 创建项目 → 初始化阶段 → 推进阶段 → 归档

2. **项目模板完整流程测试**
   - 创建模板 → 创建版本 → 发布版本 → 使用统计

3. **成员管理完整流程测试**
   - 添加成员 → 检查冲突 → 批量添加 → 通知部门经理

---

## 📋 实施检查清单

### 每个测试文件需要包含：

- [ ] 导入必要的依赖（pytest, TestClient, factories等）
- [ ] 实现 `api_client` fixture（带认证）
- [ ] 为每个端点实现至少1个成功路径测试
- [ ] 添加数据验证测试
- [ ] 添加权限测试（如需要）
- [ ] 添加异常处理测试
- [ ] 使用 `pytest.mark.parametrize` 进行参数化（如适用）
- [ ] 添加测试文档字符串

### 测试质量标准：

- ✅ 测试通过率: 100%
- ✅ 代码覆盖率: 每个端点至少60%
- ✅ 测试执行时间: 单个测试文件 < 30秒
- ✅ 测试独立性: 每个测试可以独立运行

---

## 🚀 执行步骤

### 步骤1: 实现Projects模块测试（优先级最高）

```bash
# 1. 查看生成的测试文件
cat tests/api/test_projects_api.py

# 2. 实现测试逻辑（参考现有测试）
# 参考: tests/api/test_projects.py

# 3. 运行测试
pytest tests/api/test_projects_api.py -v

# 4. 检查覆盖率
pytest --cov=app/api/v1/endpoints/projects --cov-report=term-missing tests/api/test_projects_api.py
```

### 步骤2: 依次实现其他模块测试

按照优先级顺序：
1. Members模块
2. Stages模块
3. Machines模块
4. Org模块
5. Milestones模块

### 步骤3: 运行所有测试并生成报告

```bash
# 运行所有新生成的测试
pytest tests/api/test_*_api.py -v --cov=app/api/v1/endpoints --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

---

## 📈 预期成果

### 覆盖率提升

- **当前状态**: 62个端点未测试
- **目标状态**: 62个端点全部有测试覆盖
- **预期覆盖率提升**: +5-10%（取决于端点复杂度）

### 测试文件统计

- **新增测试文件**: 6个
- **新增测试用例**: 预计100-150个
- **代码行数**: 预计3000-4000行

---

## ⚠️ 注意事项

1. **测试数据管理**
   - 使用 `tests/factories.py` 创建测试数据
   - 确保测试数据隔离，避免测试间相互影响
   - 测试后清理数据

2. **权限测试**
   - 确保测试覆盖不同角色的权限验证
   - 使用 `tests/conftest.py` 中的权限相关fixture

3. **API契约**
   - 确保测试与实际API实现匹配
   - 参考 `app/api/v1/endpoints/` 中的实际实现

4. **性能考虑**
   - 避免在测试中创建过多数据
   - 使用mock替代外部服务调用（如ERP同步）

---

## 📝 更新日志

- **2026-01-20**: 创建推进计划，生成6个测试文件框架
- **待更新**: 各模块测试实现进度

---

**下一步行动**: 开始实现 `test_projects_api.py` 中的测试逻辑
