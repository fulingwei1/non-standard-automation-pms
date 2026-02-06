# 多租户数据隔离设计指南

## 概述

**不是所有表都需要 `tenant_id`！** 多租户隔离需要根据数据性质分类处理。

## 分类标准

### 1. 需要 `tenant_id` 的表（租户隔离数据）

**判断标准：**
- ✅ 由租户用户创建的业务数据
- ✅ 不同租户之间需要完全隔离的数据
- ✅ 每条记录明确属于某个租户

**示例：**
```python
class Project(Base, TimestampMixin):
    """项目表 - 需要租户隔离"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)  # ✅ 必需
    project_name = Column(String(200))
    # ...
```

**应该添加 `tenant_id` 的表：**
- ✅ `projects` - 项目
- ✅ `leads` - 销售线索
- ✅ `opportunities` - 销售商机
- ✅ `contracts` - 合同
- ✅ `purchase_orders` - 采购订单
- ✅ `work_orders` - 生产工单
- ✅ `materials` - 物料（如果每个租户独立管理）
- ✅ `tasks` - 任务
- ✅ `timesheets` - 工时记录
- ✅ `ecn` - 工程变更通知
- ✅ `issues` - 问题工单
- ✅ `notifications` - 通知消息

### 2. 不需要 `tenant_id` 的表（全局共享数据）

**判断标准：**
- ❌ 系统级元数据表
- ❌ 全局字典/配置表
- ❌ 跨租户共享的参考数据
- ❌ 审计日志（需要跨租户查看）

**示例：**
```python
class Province(Base):
    """省份表 - 全局共享，不需要租户隔离"""
    __tablename__ = "provinces"

    id = Column(Integer, primary_key=True)
    province_name = Column(String(50))
    # ❌ 不需要 tenant_id
```

**不应该添加 `tenant_id` 的表：**
- ❌ `tenants` - 租户表本身
- ❌ `provinces` / `cities` - 地区数据（全国通用）
- ❌ `industry_categories` - 行业分类（全局字典）
- ❌ `holidays` - 法定节假日（全国统一）
- ❌ `system_configs` - 系统配置
- ❌ `audit_logs` - 全局审计日志（超级管理员需要跨租户查看）

### 3. 通过关联继承租户的表（间接隔离）

**判断标准：**
- 🔗 明确属于某个主表的子记录
- 🔗 通过外键关联主表，主表已有 `tenant_id`
- 🔗 不会独立查询，总是和主表一起查询

**示例：**
```python
class ProjectMilestone(Base, TimestampMixin):
    """项目里程碑 - 通过project_id间接隔离"""
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))  # 主表有tenant_id
    # 🔗 可选：为了查询性能，可以冗余 tenant_id
    # tenant_id = Column(Integer, ForeignKey("tenants.id"))
    milestone_name = Column(String(200))
```

**可以通过关联隔离的表：**
- 🔗 `project_milestones` - 项目里程碑（通过 `project_id`）
- 🔗 `contract_deliverables` - 合同交付物（通过 `contract_id`）
- 🔗 `purchase_order_items` - 采购订单明细（通过 `purchase_order_id`）
- 🔗 `work_order_tasks` - 工单任务（通过 `work_order_id`）

**优化建议：** 如果子表需要独立查询（不通过主表），建议冗余添加 `tenant_id` 以提升查询性能。

### 4. 特殊表（需要单独设计）

**用户和角色：**
```python
class User(Base, TimestampMixin):
    """用户表 - 特殊处理"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))  # ✅ 必需
    username = Column(String(50))
    # 注意：租户管理员可能需要访问多个租户
```

**权限和角色：**
```python
class Role(Base, TimestampMixin):
    """角色表 - 租户级别"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))  # ✅ 租户独立角色
    role_name = Column(String(100))
```

## 当前系统状态

### 已实现租户隔离的表
- ✅ `users` - 用户表
- ✅ `roles` - 角色表
- ✅ `permissions` - 权限表（部分）

### 需要添加 `tenant_id` 的核心业务表

| 表名 | 优先级 | 原因 |
|------|-------|------|
| `projects` | 🔴 高 | 核心业务数据，必须隔离 |
| `leads` | 🔴 高 | 销售线索属于租户私有 |
| `opportunities` | 🔴 高 | 商机属于租户私有 |
| `contracts` | 🔴 高 | 合同属于租户私有 |
| `purchase_orders` | 🟡 中 | 采购数据属于租户 |
| `work_orders` | 🟡 中 | 生产数据属于租户 |
| `materials` | 🟡 中 | 物料可能需要隔离 |
| `tasks` | 🟡 中 | 任务属于租户 |
| `timesheets` | 🟡 中 | 工时记录属于租户 |
| `ecn` | 🟢 低 | 工程变更属于项目 |
| `issues` | 🟢 低 | 问题工单属于租户 |

## 实施建议

### 阶段1：最小可行方案（当前）
使用 `DataScopeService` 通过用户权限范围间接实现租户隔离：
- 通过 `created_by` / `owner_id` 关联到 User
- User 有 `tenant_id`
- 查询时过滤用户可见范围

**优点：** 不需要修改数据库
**缺点：** 查询性能差，需要复杂的JOIN

### 阶段2：添加核心业务表的 `tenant_id`（推荐）
1. 为 🔴 高优先级表添加 `tenant_id` 字段
2. 创建数据迁移脚本填充历史数据
3. 添加数据库约束确保数据完整性
4. 修改API查询自动添加 `tenant_id` 过滤

**优点：** 查询性能好，隔离清晰
**缺点：** 需要数据迁移

### 阶段3：完善所有业务表（长期）
1. 逐步为所有业务表添加 `tenant_id`
2. 建立统一的租户过滤基类
3. 添加自动化测试确保隔离有效

## 数据库设计模式

### 模式1：必需字段（推荐）
```python
tenant_id = Column(
    Integer,
    ForeignKey("tenants.id", ondelete="CASCADE"),  # 租户删除时级联删除数据
    nullable=False,  # 不允许为空
    index=True,  # 添加索引提升查询性能
    comment="租户ID"
)
```

### 模式2：可选字段（用于过渡期）
```python
tenant_id = Column(
    Integer,
    ForeignKey("tenants.id", ondelete="SET NULL"),
    nullable=True,  # 允许为空（兼容历史数据）
    index=True,
    comment="租户ID（过渡期可为空）"
)
```

### 模式3：冗余字段（性能优化）
```python
# 子表既有主表外键，又冗余tenant_id
project_id = Column(Integer, ForeignKey("projects.id"))
tenant_id = Column(Integer, ForeignKey("tenants.id"))  # 冗余，提升查询性能
```

## 查询最佳实践

### 自动添加租户过滤
```python
class TenantMixin:
    """租户隔离Mixin"""

    @classmethod
    def filter_by_tenant(cls, query, tenant_id: int):
        """自动添加租户过滤"""
        return query.filter(cls.tenant_id == tenant_id)

class Project(Base, TenantMixin):
    # ...

# 使用
projects = Project.filter_by_tenant(db.query(Project), current_user.tenant_id).all()
```

### 创建通用过滤器
```python
def apply_tenant_filter(query, model, user: User):
    """应用租户过滤（如果模型有tenant_id字段）"""
    if hasattr(model, 'tenant_id') and user.tenant_id:
        return query.filter(model.tenant_id == user.tenant_id)
    return query
```

## 数据迁移示例

```sql
-- 1. 添加tenant_id字段（允许为空）
ALTER TABLE projects ADD COLUMN tenant_id INT NULL;

-- 2. 填充历史数据（通过creator关联）
UPDATE projects p
JOIN users u ON p.created_by = u.id
SET p.tenant_id = u.tenant_id;

-- 3. 添加NOT NULL约束
ALTER TABLE projects MODIFY tenant_id INT NOT NULL;

-- 4. 添加外键约束
ALTER TABLE projects
ADD CONSTRAINT fk_projects_tenant
FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- 5. 添加索引
CREATE INDEX idx_projects_tenant ON projects(tenant_id);

-- 6. 添加复合索引（常见查询模式）
CREATE INDEX idx_projects_tenant_status ON projects(tenant_id, status);
```

## 总结

**简单规则：**
1. **业务数据表** → 加 `tenant_id` ✅
2. **全局字典表** → 不加 ✅
3. **子表/明细表** → 看情况（可通过主表隔离，或冗余tenant_id提升性能）🔗
4. **用户/角色/权限** → 必须加 ✅

**当前系统：**
- 已有 tenant_id: 2个表（users, permissions）
- 需要添加: 约20-30个核心业务表
- 不需要添加: 约100+个字典/系统表

**建议：** 优先为核心业务表（项目、销售、采购）添加 `tenant_id`，其他表可以逐步迁移。
