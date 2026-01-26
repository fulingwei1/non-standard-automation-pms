# 代码重构实施计划

**生成日期**: 2026-01-25
**目标**: 解决96类重复问题，消除至少50%的重复代码
**预计工作量**: 80-120小时（2-3周）

---

## 一、问题统计

| 类别 | 问题数 | 严重 | 高 | 中 | 总计 |
|------|--------|------|-----|------|------|
| 模型层 | 5 | 2 | 2 | 1 | 5 |
| API端点 | 23 | 15 | 7 | 1 | 23 |
| 服务层 | 22 | 4 | 14 | 4 | 22 |
| 权限检查 | 2 | 1 | 1 | 0 | 2 |
| 通用模式 | 11 | 2 | 2 | 7 | 11 |
| 前端代码 | 30 | 6 | 14 | 10 | 30 |
| 数据库 | 3 | 0 | 0 | 3 | 3 |
| **总计** | **96** | **28** | **41** | **27** | **96** |

### 关键数据

- **分页逻辑重复**: 109处（105个文件）
- **权限检查重复**: 56次（25个文件）
- **workflow.py文件**: 10个独立实现
- **dashboard.py文件**: 12个独立实现
- **statistics服务**: 20+个分散实现
- **notification服务**: 15+个文件混用
- **迁移文件**: 228个SQL文件
- **Projects表ALTER**: 55次

---

## 二、重构策略

### 核心原则

1. **渐进式重构** - 分阶段实施，每个阶段可验证、可回滚
2. **高风险隔离** - 关键路径（如审批系统）单独验证
3. **向后兼容** - 不破坏现有功能，支持平滑迁移
4. **测试驱动** - 每个重构都要有测试覆盖
5. **文档同步** - 及时更新设计文档和API文档

### 执行顺序

**优先级排序**：
1. **高影响力、低风险** - 如分页工具、权限统一
2. **已启动项目** - 如审批框架迁移
3. **架构级问题** - 如CRUD基类、状态机框架
4. **模块级合并** - 如API重复合并
5. **清理工作** - 删除旧代码、合并迁移文件

---

## 三、详细计划

### 阶段0: 准备工作 (2小时)

**目标**: 建立基础框架目录和文档

**任务**:
1. ✅ 创建 `app/common/` 目录（存放通用工具）
   - `app/common/pagination.py` - 分页工具
   - `app/common/query.py` - 查询辅助
   - `app/common/crud.py` - CRUD基类
2. ✅ 创建 `REFACTORING_PLAN.md` 本文档
3. ✅ 创建 `REFACTORING_PROGRESS.md` 进度跟踪文档

**验收标准**:
- 目录结构完整
- 文档清晰描述目标和进度

---

### 阶段1: P0 - 基础框架重构 (12-18小时)

#### 1.1 分页工具类 (3-4小时)

**目标**: 消除109处分页逻辑重复

**文件**: `app/common/pagination.py`

**实现**:
```python
class PaginationHelper:
    @staticmethod
    def paginate(query, page: int = 1, page_size: int = 20):
        """通用分页工具"""
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
```

**迁移计划**:
- 分批迁移：每次迁移10-20个文件
- 从高频使用的端点开始
- 保持API响应格式不变

**验收标准**:
- 所有迁移后的端点测试通过
- 分页逻辑统一使用工具类
- 减少至少100处重复代码

---

#### 1.2 权限检查统一 (2-3小时)

**目标**: 统一56次权限检查到 `core/permissions/`

**现状**:
- `check_timesheet_approval_permission` 重复定义
- `check_sales_*_permission` 分散在多个文件
- `_check_performance_view_permission` 重复定义

**行动计划**:
1. 审核现有 `core/permissions/` 下的权限函数
2. 迁移 `timesheet.py` 中的权限函数
3. 迁移 `sales_permissions.py` 中的权限函数
4. 清理 `core/security.py` 中的重复导出
5. 更新所有引用到统一位置

**验收标准**:
- 所有权限检查函数集中在 `core/permissions/`
- 删除重复定义
- API端点统一使用 `core.permissions` 的导入

---

#### 1.3 通知系统统一 (3-4小时)

**目标**: 整合15+个通知服务到统一服务

**现状**:
- `notification_service.py` - 旧服务
- `notification_dispatcher.py` - 分发器
- `unified_notification_service.py` - 新尝试
- `approval_engine/notify/` - 审批通知
- `ecn_notification/` - ECN通知

**行动计划**:
1. 对比分析各通知服务的功能
2. 确定统一的服务接口
3. 将所有通知调用迁移到统一服务
4. 删除旧的服务文件

**验收标准**:
- 只保留一个主要的通知服务
- 所有模块使用统一接口
- 通知功能不减少

---

#### 1.4 完成审批框架迁移 (4-7小时)

**目标**: 完成Project Approval到统一审批引擎的迁移

**现状**:
- ✅ `ApprovalEngineService` 已实现
- ✅ `ProjectApprovalAdapter` 已创建
- ✅ `PROJECT_TEMPLATE` 已定义
- ✅ Submit 端点已迁移
- ⏳ Action, Cancel, Status, History 端点待迁移

**行动计划**:

##### 1.4.1 创建 action_new.py (1-2小时)
- 使用 `ApprovalEngineService.approve_step()` / `reject_step()`
- 权限检查：当前用户是否为当前步骤审批人
- 参考 `submit_new.py` 的实现风格

##### 1.4.2 创建 cancel_new.py (0.5-1小时)
- 使用 `ApprovalEngineService.withdraw_approval()`
- 验证：仅发起人可以撤回

##### 1.4.3 创建 status_new.py (0.5-1小时)
- 使用 `ApprovalEngineService.get_approval_record()`
- 使用 `ApprovalEngineService.get_current_step()`
- 返回：当前步骤、审批人、进度、可操作权限

##### 1.4.4 创建 history_new.py (0.5-1小时)
- 使用 `ApprovalEngineService.get_approval_history()`
- 返回完整的历史记录列表

##### 1.4.5 测试和清理 (1-2小时)
- 测试所有端点
- 删除旧文件（action.py, cancel.py, status.py, history.py, utils.py）
- 更新 `__init__.py`

**验收标准**:
- 所有4个端点使用统一审批引擎
- API响应格式与旧端点一致
- 测试覆盖所有审批流程
- 删除所有旧代码

---

#### 1.5 CRUD基类 (3-4小时)

**目标**: 消除35处CRUD重复

**文件**: `app/common/crud.py`

**实现**:
```python
class CRUDBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> T:
        obj = self.model(**obj_in)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, *, db_obj: T, obj_in: Dict[str, Any]) -> T:
        for field in obj_in:
            setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> T:
        obj = self.get(db, id=id)
        db.delete(obj)
        db.commit()
        return obj
```

**验收标准**:
- CRUD基类实现完整
- 迁移至少10个模块到基类
- 减少至少500行重复代码

---

### 阶段2: P1 - 架构扩展 (20-30小时)

#### 2.1 搜索过滤工具类 (4-5小时)

**目标**: 消除80+处搜索过滤重复

**文件**: `app/common/query.py`

**实现**:
- `QueryHelper.filter_by_keyword()` - 关键词搜索
- `QueryHelper.filter_by_date_range()` - 日期范围过滤
- `QueryHelper.filter_by_status()` - 状态过滤
- `QueryHelper.build_query()` - 复杂查询构建器

**验收标准**:
- 消除至少50处 `like('%keyword%')` 重复
- 支持多种过滤条件的组合

---

#### 2.2 扩展统一状态机框架 (5-6小时)

**目标**: 10个独立状态机迁移到统一框架

**现状**:
- ✅ `app/core/state_machine/` 基础框架已实现
- ⚠️ 各模块仍使用独立实现

**迁移模块**:
1. ECN - ✅ 已有适配器
2. Project - ⚠️ 需要迁移
3. Sales Quote - 需要迁移
4. Sales Contract - 需要迁移
5. Sales Invoice - 需要迁移
6. Approval - ✅ 已有适配器
7. Task - 需要迁移
8. Issue - 需要迁移
9. Outsourcing - 需要迁移
10. Acceptance - 需要迁移

**验收标准**:
- 至少5个模块迁移到统一状态机
- 删除独立的 workflow.py 文件

---

#### 2.3 统一报表框架 (5-6小时)

**目标**: 整合50+处报表统计逻辑

**文件**: `app/services/report_engine/`

**核心组件**:
- `ReportTemplate` - 报表模板
- `ReportGenerator` - 报表生成器
- `ReportExporter` - 报表导出器

**整合的报表类型**:
- 项目报表
- 销售报表
- 财务报表
- 人力资源报表
- 绩效报表

**验收标准**:
- 创建报表基类
- 迁移至少10个报表服务
- 统一报表数据格式

---

#### 2.4 统一导入导出框架 (3-4小时)

**目标**: 整合23+处导入导出逻辑

**文件**: `app/services/import_export/`

**核心组件**:
- `ExcelImportService` - Excel导入
- `ExcelExportService` - Excel导出
- `PDFExportService` - PDF导出

**验收标准**:
- 创建统一导入导出服务
- 迁移至少10个模块
- 统一文件格式和错误处理

---

#### 2.5 Dashboard基类 (3-4小时)

**目标**: 消除10个Dashboard重复

**文件**: `app/common/dashboard.py`

**实现**:
```python
class DashboardBase:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def get_summary(self) -> Dict[str, Any]:
        """获取仪表盘摘要"""
        raise NotImplementedError

    def get_kpi_metrics(self) -> List[Dict[str, Any]]:
        """获取KPI指标"""
        raise NotImplementedError

    def get_charts_data(self) -> Dict[str, Any]:
        """获取图表数据"""
        raise NotImplementedError
```

**验收标准**:
- 创建Dashboard基类
- 迁移至少5个Dashboard
- 统一数据格式

---

### 阶段3: P2 - 模块合并 (20-25小时)

#### 3.1 合并9组模块级API重复 (8-10小时)

**目标**: 合并重复的API端点

**重复模块**:
| 模块 | 位置1 | 位置2 | 操作 |
|------|-------|-------|------|
| approvals | `/approvals/` | `/projects/approvals/` | 保留 `/approvals/` |
| costs | `/costs/` | `/projects/costs/` | 保留 `/projects/{id}/costs/` |
| machines | `/machines/` | `/projects/machines/` | 保留 `/projects/{id}/machines/` |
| members | `/members/` | `/projects/members/` | 保留 `/projects/{id}/members/` |
| milestones | `/milestones/` | `/projects/milestones/` | 保留 `/projects/{id}/milestones/` |
| progress | `/progress/` | `/projects/progress/` | 保留 `/projects/{id}/progress/` |
| roles | `/roles/` | `/projects/roles/` | 保留 `/projects/{id}/roles/` |
| timesheet | `/timesheet/` | `/projects/timesheet/` | 保留 `/projects/{id}/timesheet/` |
| workload | `/workload/` | `/projects/workload/` | 保留 `/projects/{id}/workload/` |

**验收标准**:
- 删除所有冗余的端点文件
- 更新前端调用到新端点
- API文档更新

---

#### 3.2 数据库迁移文件清理 (5-6小时)

**目标**: 合并55次ALTER TABLE语句，避免迁移冲突

**现状**:
- 228个SQL迁移文件
- Projects表被ALTER了55次
- 部分迁移可能相互依赖

**行动计划**:
1. 分析所有迁移文件的依赖关系
2. 创建合并的迁移文件
3. 备份现有数据
4. 执行合并迁移
5. 删除旧迁移文件

**验收标准**:
- 迁移文件数量减少50%以上
- Projects表的索引优化到18个以下
- 数据完整性验证通过

---

#### 3.3 合并组织架构模型到v2 (3-4小时)

**目标**: 删除旧的organization.py，统一使用organization_v2.py

**行动计划**:
1. 对比两个模型的差异
2. 迁移数据（如果需要）
3. 更新所有引用到v2版本
4. 删除旧的organization.py

**验收标准**:
- 只保留organization_v2.py
- 所有引用已更新
- 测试通过

---

#### 3.4 权限模型统一 (4-5小时)

**目标**: 合并user.py和permission_v2.py

**行动计划**:
1. 分析两个模型的关系
2. 合并到一个统一的模型
3. 迁移数据
4. 更新所有引用

**验收标准**:
- 权限模型统一
- 所有引用已更新
- 测试通过

---

### 阶段4: P3 - 清理和收尾 (8-12小时)

#### 4.1 清理已废弃的旧代码 (3-4小时)

**目标**: 删除所有不再使用的旧代码

**待删除**:
- 旧的审批系统代码
- 旧的workflow.py文件（已迁移到统一框架）
- 重复的utils.py文件
- _refactored.py文件（重构完成后删除原文件）

**验收标准**:
- 删除所有标识为deprecated的代码
- 代码库减少至少5000行

---

#### 4.2 完整测试 (3-4小时)

**目标**: 确保所有重构不影响现有功能

**测试范围**:
- 单元测试：每个新的工具类
- 集成测试：每个迁移的API端点
- 回归测试：关键业务流程

**验收标准**:
- 测试覆盖率80%以上
- 所有测试通过
- 无新的bug引入

---

#### 4.3 文档更新 (2-3小时)

**目标**: 更新所有设计文档和API文档

**需要更新的文档**:
- `CLAUDE.md` - 开发指南
- 各模块的详细设计文档
- API文档（Swagger）
- 数据库架构文档

**验收标准**:
- 所有文档与代码一致
- 新框架的使用有完整示例
- API文档准确

---

## 四、风险管理

### 风险1: 重构破坏现有功能
- **可能性**: 高
- **影响**: 严重
- **缓解措施**:
  - 每个阶段都要有完整的测试
  - 分阶段提交，便于回滚
  - 保留旧代码直到新代码完全验证

### 风险2: 数据库迁移失败
- **可能性**: 中
- **影响**: 严重
- **缓解措施**:
  - 迁移前完整备份数据
  - 在测试环境先验证迁移
  - 准备回滚脚本

### 风险3: 前端调用失败
- **可能性**: 中
- **影响**: 中
- **缓解措施**:
  - 保持API响应格式不变
  - 提供过渡期的兼容端点
  - 提前与前端团队沟通

### 风险4: 工期超支
- **可能性**: 中
- **影响**: 中
- **缓解措施**:
  - 每个阶段有明确的时间估算
  - 优先完成高价值、低风险的任务
  - 遇到阻塞性问题及时调整计划

---

## 五、进度跟踪

### 完成标准

| 阶段 | 任务 | 状态 | 完成度 |
|------|------|------|--------|
| 阶段0 | 准备工作 | ⏳ | 0% |
| 阶段1.1 | 分页工具类 | ⏳ | 0% |
| 阶段1.2 | 权限检查统一 | ⏳ | 0% |
| 阶段1.3 | 通知系统统一 | ⏳ | 0% |
| 阶段1.4 | 审批框架迁移 | ⏳ | 40% |
| 阶段1.5 | CRUD基类 | ⏳ | 0% |
| 阶段2.1 | 搜索过滤工具类 | ⏳ | 0% |
| 阶段2.2 | 状态机框架 | ⏳ | 10% |
| 阶段2.3 | 报表框架 | ⏳ | 0% |
| 阶段2.4 | 导入导出框架 | ⏳ | 0% |
| 阶段2.5 | Dashboard基类 | ⏳ | 0% |
| 阶段3.1 | API合并 | ⏳ | 0% |
| 阶段3.2 | 数据库清理 | ⏳ | 0% |
| 阶段3.3 | 组织架构v2 | ⏳ | 0% |
| 阶段3.4 | 权限模型统一 | ⏳ | 0% |
| 阶段4.1 | 旧代码清理 | ⏳ | 0% |
| 阶段4.2 | 完整测试 | ⏳ | 0% |
| 阶段4.3 | 文档更新 | ⏳ | 0% |

### 代码减少目标

- **总重复代码**: 25,000+ 行
- **目标减少**: 15,000+ 行（60%）
- **当前减少**: 0 行
- **进度**: 0%

---

## 六、预期收益

### 代码质量
- ✅ 减少60%的重复代码
- ✅ 提高代码可维护性
- ✅ 统一代码风格

### 开发效率
- ✅ 新功能开发时间减少30%
- ✅ Bug修复时间减少40%
- ✅ 代码审查时间减少50%

### 系统稳定性
- ✅ 降低bug风险
- ✅ 提高测试覆盖率
- ✅ 简化部署流程

---

**文档版本**: v1.0
**最后更新**: 2026-01-25
**维护者**: Sisyphus AI Assistant
