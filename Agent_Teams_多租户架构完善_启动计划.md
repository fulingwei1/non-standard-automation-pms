# 多租户架构完善 - 6 Agent Teams 启动计划

**启动时间**: 2026-02-16 04:31  
**目标**: 完善多租户架构，实现完整数据隔离  
**预计耗时**: 1-2天 (并行执行)  
**并行Teams**: 6个

---

## Team 1: 数据模型补全

### 任务目标
为所有核心业务表添加 `tenant_id` 字段，实现数据库级别的租户隔离。

### 交付清单

1. **模型扫描和分析**
   - 扫描 `app/models/` 所有模型
   - 识别缺少 `tenant_id` 的核心业务表
   - 生成完整的表清单

2. **数据模型修改** (预估50+表)
   重点表包括但不限于：
   - `Project` (项目)
   - `RdProject` (研发项目)
   - `SalesContract` (销售合同)
   - `WorkOrder` (生产工单)
   - `ProductionPlan` (生产计划)
   - `MaterialRequisition` (领料单)
   - `QualityInspection` (质检记录)
   - `PurchaseOrder` (采购单)
   - `Timesheet` (工时记录)
   - `Equipment` (设备)
   - `BOM` (物料清单)
   - `Task` (任务)
   - 所有其他核心业务表

3. **数据库迁移文件**
   ```sql
   -- migrations/add_tenant_id_to_all_tables.sql
   
   -- 添加 tenant_id 字段（初期允许 NULL，迁移后改为 NOT NULL）
   ALTER TABLE projects ADD COLUMN tenant_id INT NULL 
       COMMENT '租户ID（多租户隔离）';
   ALTER TABLE rd_projects ADD COLUMN tenant_id INT NULL 
       COMMENT '租户ID（多租户隔离）';
   -- ... 其他50+表
   
   -- 添加外键约束
   ALTER TABLE projects ADD CONSTRAINT fk_projects_tenant 
       FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;
   ALTER TABLE rd_projects ADD CONSTRAINT fk_rd_projects_tenant 
       FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT;
   -- ... 其他表
   
   -- 添加索引（性能优化）
   CREATE INDEX idx_projects_tenant ON projects(tenant_id);
   CREATE INDEX idx_rd_projects_tenant ON rd_projects(tenant_id);
   -- ... 其他表
   
   -- 创建复合索引（常用查询优化）
   CREATE INDEX idx_projects_tenant_status ON projects(tenant_id, status);
   CREATE INDEX idx_work_orders_tenant_status ON work_orders(tenant_id, status);
   -- ... 其他常用查询
   ```

4. **模型代码更新**
   ```python
   # 为所有模型添加 tenant_id 字段
   class Project(Base, TimestampMixin):
       __tablename__ = "projects"
       __table_args__ = (
           Index("idx_projects_tenant", "tenant_id"),
           Index("idx_projects_tenant_status", "tenant_id", "status"),
           {"extend_existing": True}
       )
       
       id = Column(Integer, primary_key=True)
       tenant_id = Column(
           Integer,
           ForeignKey("tenants.id", ondelete="RESTRICT"),
           nullable=True,  # 初期允许NULL，迁移后改为False
           comment="租户ID（多租户隔离）"
       )
       # ... 其他字段
       
       # 关系
       tenant = relationship("Tenant", back_populates="projects")
   ```

5. **文档**
   - 数据模型变更清单（表名、字段、索引）
   - 数据库迁移指南
   - 回滚方案

### 技术要求
- 所有表必须包含 `extend_existing=True`
- 外键使用 `ON DELETE RESTRICT`（防止误删租户）
- 索引设计合理（单列索引 + 复合索引）
- 迁移文件支持MySQL/PostgreSQL

### 验收标准
- ✅ 50+核心业务表全部添加 tenant_id
- ✅ 外键约束完整
- ✅ 索引合理
- ✅ 迁移脚本可执行
- ✅ 文档完整

### 输出文件
- `migrations/add_tenant_id_to_all_tables.sql`
- `docs/多租户数据模型变更清单.md`
- `Agent_Team_1_数据模型补全_交付报告.md`

---

## Team 2: 数据迁移脚本

### 任务目标
编写数据迁移脚本，将现有数据关联到默认租户，确保数据完整性。

### 交付清单

1. **创建默认租户**
   ```python
   # scripts/create_default_tenant.py
   from app.models.tenant import Tenant, TenantStatus, TenantPlan
   
   def create_default_tenant(db: Session):
       """创建默认租户：金凯博"""
       tenant = Tenant(
           tenant_code="jinkaibo",
           tenant_name="金凯博自动化测试",
           status=TenantStatus.ACTIVE.value,
           plan_type=TenantPlan.ENTERPRISE.value,
           max_users=-1,  # 无限用户
           max_roles=-1,  # 无限角色
           max_storage_gb=1000,  # 1TB
           contact_name="管理员",
           contact_email="admin@jinkaibo.com",
           expired_at=None  # 永不过期
       )
       db.add(tenant)
       db.commit()
       return tenant
   ```

2. **数据迁移脚本**
   ```python
   # scripts/migrate_to_default_tenant.py
   
   def migrate_all_data_to_default_tenant(db: Session, tenant_id: int):
       """将所有现有数据迁移到默认租户"""
       
       # 表清单（从Team 1获取）
       tables = [
           'projects', 'rd_projects', 'sales_contracts', 
           'work_orders', 'production_plans', ...
       ]
       
       for table in tables:
           try:
               # 更新 tenant_id
               result = db.execute(
                   text(f"UPDATE {table} SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
                   {"tenant_id": tenant_id}
               )
               db.commit()
               
               logger.info(f"✅ {table}: {result.rowcount} rows migrated")
           except Exception as e:
               logger.error(f"❌ {table} migration failed: {e}")
               db.rollback()
               raise
       
       return True
   ```

3. **数据验证脚本**
   ```python
   # scripts/verify_tenant_migration.py
   
   def verify_tenant_migration(db: Session, tenant_id: int):
       """验证数据迁移完整性"""
       
       issues = []
       
       # 检查每个表
       for table in tables:
           # 检查是否有 NULL tenant_id
           null_count = db.execute(
               text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")
           ).scalar()
           
           if null_count > 0:
               issues.append(f"{table}: {null_count} rows with NULL tenant_id")
           
           # 检查外键完整性
           invalid_fk = db.execute(
               text(f"""
                   SELECT COUNT(*) FROM {table} t
                   LEFT JOIN tenants tn ON t.tenant_id = tn.id
                   WHERE t.tenant_id IS NOT NULL AND tn.id IS NULL
               """)
           ).scalar()
           
           if invalid_fk > 0:
               issues.append(f"{table}: {invalid_fk} rows with invalid tenant_id")
       
       return issues
   ```

4. **回滚脚本**
   ```python
   # scripts/rollback_tenant_migration.py
   
   def rollback_tenant_migration(db: Session, tenant_id: int):
       """回滚数据迁移（将 tenant_id 设置回 NULL）"""
       
       for table in tables:
           db.execute(
               text(f"UPDATE {table} SET tenant_id = NULL WHERE tenant_id = :tenant_id"),
               {"tenant_id": tenant_id}
           )
           db.commit()
   ```

5. **迁移主脚本**
   ```python
   # scripts/run_tenant_migration.py
   
   def run_full_migration():
       """执行完整的租户迁移流程"""
       
       db = SessionLocal()
       try:
           # 1. 创建默认租户
           tenant = create_default_tenant(db)
           logger.info(f"✅ Default tenant created: {tenant.tenant_code} (ID: {tenant.id})")
           
           # 2. 迁移数据
           migrate_all_data_to_default_tenant(db, tenant.id)
           logger.info(f"✅ All data migrated to tenant {tenant.id}")
           
           # 3. 验证数据
           issues = verify_tenant_migration(db, tenant.id)
           if issues:
               logger.error(f"❌ Migration verification failed:\n" + "\n".join(issues))
               raise Exception("Migration verification failed")
           
           logger.info("✅ Migration verification passed")
           
           # 4. 更新字段为 NOT NULL（可选，谨慎执行）
           # update_tenant_id_not_null(db)
           
           logger.info("🎉 Tenant migration completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Migration failed: {e}")
           # 提示是否回滚
           raise
       finally:
           db.close()
   ```

6. **文档**
   - 数据迁移指南（步骤、注意事项、回滚方法）
   - 数据验证报告模板
   - FAQ文档

### 技术要求
- 支持MySQL/PostgreSQL
- 事务保护（失败自动回滚）
- 详细日志记录
- 数据验证完整
- 支持回滚

### 验收标准
- ✅ 默认租户创建成功
- ✅ 所有数据迁移到默认租户
- ✅ 数据验证通过（无NULL tenant_id）
- ✅ 外键完整性验证通过
- ✅ 回滚脚本可用
- ✅ 文档完整

### 输出文件
- `scripts/create_default_tenant.py`
- `scripts/migrate_to_default_tenant.py`
- `scripts/verify_tenant_migration.py`
- `scripts/rollback_tenant_migration.py`
- `scripts/run_tenant_migration.py`
- `docs/数据迁移指南.md`
- `Agent_Team_2_数据迁移_交付报告.md`

---

## Team 3: 强制租户过滤

### 任务目标
实现框架级的强制租户过滤，确保所有查询自动添加 tenant_id 条件。

### 交付清单

1. **自定义Query类**
   ```python
   # app/core/database/tenant_query.py
   
   from sqlalchemy.orm import Query
   from app.core.middleware.tenant_middleware import get_current_tenant_id
   
   class TenantQuery(Query):
       """自动添加租户过滤的Query类"""
       
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self._tenant_filter_applied = False
       
       def __iter__(self):
           """执行查询前自动添加租户过滤"""
           if not self._tenant_filter_applied:
               self._apply_tenant_filter()
           return super().__iter__()
       
       def _apply_tenant_filter(self):
           """应用租户过滤逻辑"""
           # 获取当前租户ID
           tenant_id = get_current_tenant_id()
           
           # 获取查询的主模型
           if not self.column_descriptions:
               self._tenant_filter_applied = True
               return
           
           model = self.column_descriptions[0]['type']
           
           # 检查模型是否有 tenant_id 字段
           if not hasattr(model, 'tenant_id'):
               self._tenant_filter_applied = True
               return
           
           # 超级管理员（tenant_id=None）可以访问所有数据
           if tenant_id is None:
               # 检查用户是否真的是超级管理员
               from app.core.context import get_current_user_from_context
               user = get_current_user_from_context()
               if user and not user.is_superuser:
                   # 非超级管理员但 tenant_id=None，应该报错
                   raise ValueError("Invalid user: tenant_id=None but is_superuser=False")
               # 超级管理员不添加过滤
               self._tenant_filter_applied = True
               return
           
           # 添加租户过滤条件
           self.filter(model.tenant_id == tenant_id)
           self._tenant_filter_applied = True
       
       def all(self):
           """重写 all() 方法"""
           if not self._tenant_filter_applied:
               self._apply_tenant_filter()
           return super().all()
       
       def first(self):
           """重写 first() 方法"""
           if not self._tenant_filter_applied:
               self._apply_tenant_filter()
           return super().first()
       
       def one(self):
           """重写 one() 方法"""
           if not self._tenant_filter_applied:
               self._apply_tenant_filter()
           return super().one()
       
       def get(self, ident):
           """重写 get() 方法"""
           if not self._tenant_filter_applied:
               self._apply_tenant_filter()
           return super().get(ident)
   ```

2. **配置Session使用TenantQuery**
   ```python
   # app/core/database/__init__.py
   
   from sqlalchemy.orm import sessionmaker
   from .tenant_query import TenantQuery
   
   # 配置Session使用TenantQuery
   SessionLocal = sessionmaker(
       bind=engine,
       query_cls=TenantQuery,  # 使用自定义Query类
       autocommit=False,
       autoflush=False,
   )
   ```

3. **API装饰器（双重保障）**
   ```python
   # app/core/decorators/tenant_isolation.py
   
   from functools import wraps
   from fastapi import HTTPException
   
   def require_tenant_isolation(func):
       """装饰器：强制API端点执行租户隔离检查"""
       
       @wraps(func)
       async def wrapper(*args, **kwargs):
           # 从依赖注入获取 current_user
           current_user = kwargs.get('current_user')
           db = kwargs.get('db')
           
           if not current_user or not db:
               raise ValueError("require_tenant_isolation requires current_user and db dependencies")
           
           # 为当前Session设置租户上下文
           db.info['tenant_id'] = current_user.tenant_id
           db.info['is_superuser'] = current_user.is_superuser
           
           # 执行函数
           result = await func(*args, **kwargs)
           
           return result
       
       return wrapper
   ```

4. **资源访问权限检查**
   ```python
   # app/core/permissions/tenant_access.py
   
   from fastapi import HTTPException
   from app.models.user import User
   
   def check_tenant_access(user: User, resource_tenant_id: int) -> bool:
       """检查用户是否有权访问指定租户的资源"""
       
       # 超级管理员可以访问所有租户
       if user.is_superuser and user.tenant_id is None:
           return True
       
       # 系统级资源（tenant_id=NULL）所有租户可访问
       if resource_tenant_id is None:
           return True
       
       # 检查是否同一租户
       if user.tenant_id == resource_tenant_id:
           return True
       
       return False
   
   def require_tenant_access(user: User, resource_tenant_id: int):
       """要求租户访问权限，不满足则抛出403异常"""
       if not check_tenant_access(user, resource_tenant_id):
           raise HTTPException(
               status_code=403,
               detail="无权访问其他租户的资源"
           )
   ```

5. **使用示例和最佳实践**
   ```python
   # 示例1: 使用自定义Query（自动过滤）
   @router.get("/projects")
   async def list_projects(
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_active_user)
   ):
       # TenantQuery会自动添加 tenant_id 过滤
       projects = db.query(Project).all()  # 自动过滤
       return projects
   
   # 示例2: 使用装饰器（双重保障）
   @router.get("/projects")
   @require_tenant_isolation
   async def list_projects(
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_active_user)
   ):
       projects = db.query(Project).all()
       return projects
   
   # 示例3: 单个资源访问（显式检查）
   @router.get("/projects/{project_id}")
   async def get_project(
       project_id: int,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_active_user)
   ):
       project = db.query(Project).filter(Project.id == project_id).first()
       if not project:
           raise HTTPException(404, "项目不存在")
       
       # 显式检查租户访问权限
       require_tenant_access(current_user, project.tenant_id)
       
       return project
   ```

6. **文档**
   - 租户过滤实现原理
   - API开发最佳实践
   - 使用示例和反模式

### 技术要求
- TenantQuery自动应用租户过滤
- 支持超级管理员访问所有数据
- 防御性编程（检查 tenant_id=None 但 is_superuser=False）
- 性能优化（避免重复过滤）

### 验收标准
- ✅ TenantQuery正确过滤租户数据
- ✅ 超级管理员可访问所有数据
- ✅ 普通用户只能访问本租户数据
- ✅ 装饰器正常工作
- ✅ 文档完整

### 输出文件
- `app/core/database/tenant_query.py`
- `app/core/decorators/tenant_isolation.py`
- `app/core/permissions/tenant_access.py`
- `docs/租户过滤实现原理.md`
- `docs/API开发最佳实践.md`
- `Agent_Team_3_强制租户过滤_交付报告.md`

---

## Team 4: 超级管理员统一

### 任务目标
统一超级管理员判断标准，消除 `is_superuser` 和 `tenant_id is None` 的混乱。

### 交付清单

1. **数据库约束**
   ```sql
   -- migrations/fix_superuser_constraints.sql
   
   -- 添加检查约束：超级管理员 tenant_id 必须为 NULL
   ALTER TABLE users ADD CONSTRAINT chk_superuser_tenant 
       CHECK (
           (is_superuser = FALSE) OR 
           (is_superuser = TRUE AND tenant_id IS NULL)
       );
   
   -- 修复现有数据（如果有）
   -- 将 is_superuser=TRUE 但 tenant_id!=NULL 的用户设置为普通用户
   UPDATE users 
   SET is_superuser = FALSE 
   WHERE is_superuser = TRUE AND tenant_id IS NOT NULL;
   
   -- 将 is_superuser=FALSE 但 tenant_id=NULL 的用户删除或修正
   -- （根据实际情况决定）
   ```

2. **统一判断函数**
   ```python
   # app/core/auth.py
   
   def is_superuser(user: User) -> bool:
       """判断用户是否为超级管理员
       
       超级管理员必须同时满足：
       1. is_superuser = True
       2. tenant_id IS NULL
       
       Args:
           user: 用户对象
       
       Returns:
           是否为超级管理员
       """
       return user.is_superuser and user.tenant_id is None
   
   def validate_user_tenant_consistency(user: User):
       """验证用户租户数据一致性
       
       检查规则：
       - is_superuser=True 必须 tenant_id=NULL
       - tenant_id=NULL 必须 is_superuser=True
       
       Raises:
           ValueError: 数据不一致
       """
       if user.is_superuser and user.tenant_id is not None:
           raise ValueError(
               f"Invalid user {user.id}: is_superuser=True but tenant_id={user.tenant_id}"
           )
       
       if user.tenant_id is None and not user.is_superuser:
           raise ValueError(
               f"Invalid user {user.id}: tenant_id=NULL but is_superuser=False"
           )
   ```

3. **修改所有超级管理员判断点**
   ```python
   # 查找并替换所有判断点
   
   # ❌ 错误做法（删除）
   if user.tenant_id is None:
       ...
   
   # ✅ 正确做法（统一）
   if is_superuser(user):
       ...
   
   # 需要修改的文件：
   # - app/core/middleware/tenant_middleware.py
   # - app/core/auth.py
   # - app/core/permissions/*.py
   # - 所有API端点
   ```

4. **用户创建/更新验证**
   ```python
   # app/api/v1/endpoints/users/crud.py
   
   @router.post("/users")
   async def create_user(
       user_data: UserCreate,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_active_superuser)
   ):
       # 验证超级管理员规则
       if user_data.is_superuser:
           if user_data.tenant_id is not None:
               raise HTTPException(
                   400,
                   "超级管理员的 tenant_id 必须为 NULL"
               )
       else:
           if user_data.tenant_id is None:
               raise HTTPException(
                   400,
                   "普通用户必须属于某个租户"
               )
       
       # 创建用户
       ...
   ```

5. **数据修复脚本**
   ```python
   # scripts/fix_superuser_data.py
   
   def fix_superuser_data(db: Session):
       """修复不一致的超级管理员数据"""
       
       # 情况1: is_superuser=True 但 tenant_id!=NULL
       case1 = db.query(User).filter(
           User.is_superuser == True,
           User.tenant_id.isnot(None)
       ).all()
       
       if case1:
           logger.warning(f"Found {len(case1)} users with is_superuser=True but tenant_id!=NULL")
           for user in case1:
               logger.info(f"  - User {user.id} ({user.username}): setting is_superuser=False")
               user.is_superuser = False
           db.commit()
       
       # 情况2: is_superuser=False 但 tenant_id=NULL
       case2 = db.query(User).filter(
           User.is_superuser == False,
           User.tenant_id.is_(None)
       ).all()
       
       if case2:
           logger.error(f"Found {len(case2)} users with is_superuser=False but tenant_id=NULL")
           for user in case2:
               logger.error(f"  - User {user.id} ({user.username}): MANUAL FIX REQUIRED")
           raise Exception("Manual fix required for case2 users")
       
       logger.info("✅ Superuser data fixed")
   ```

6. **文档**
   - 超级管理员设计规范
   - 数据一致性检查清单
   - 常见问题修复指南

### 技术要求
- 数据库约束强制执行
- 所有代码统一使用 `is_superuser()` 函数
- 用户创建/更新时验证
- 现有数据修复

### 验收标准
- ✅ 数据库约束添加成功
- ✅ 所有代码使用统一判断函数
- ✅ 现有数据修复完成
- ✅ 用户创建/更新验证通过
- ✅ 文档完整

### 输出文件
- `migrations/fix_superuser_constraints.sql`
- `scripts/fix_superuser_data.py`
- `docs/超级管理员设计规范.md`
- `Agent_Team_4_超级管理员统一_交付报告.md`

---

## Team 5: 租户隔离测试

### 任务目标
编写完整的租户隔离测试套件，确保多租户数据安全。

### 交付清单

1. **测试数据准备**
   ```python
   # tests/fixtures/tenant_fixtures.py
   
   import pytest
   from app.models.tenant import Tenant
   from app.models.user import User
   from app.models.project import Project
   
   @pytest.fixture
   def tenant_a(db):
       """租户A"""
       tenant = Tenant(
           tenant_code="tenant_a",
           tenant_name="租户A公司",
           status="ACTIVE"
       )
       db.add(tenant)
       db.commit()
       return tenant
   
   @pytest.fixture
   def tenant_b(db):
       """租户B"""
       tenant = Tenant(
           tenant_code="tenant_b",
           tenant_name="租户B公司",
           status="ACTIVE"
       )
       db.add(tenant)
       db.commit()
       return tenant
   
   @pytest.fixture
   def user_a(db, tenant_a):
       """租户A的普通用户"""
       user = User(
           username="user_a",
           email="user_a@tenant_a.com",
           tenant_id=tenant_a.id,
           is_superuser=False
       )
       db.add(user)
       db.commit()
       return user
   
   @pytest.fixture
   def user_b(db, tenant_b):
       """租户B的普通用户"""
       user = User(
           username="user_b",
           email="user_b@tenant_b.com",
           tenant_id=tenant_b.id,
           is_superuser=False
       )
       db.add(user)
       db.commit()
       return user
   
   @pytest.fixture
   def superuser(db):
       """超级管理员"""
       user = User(
           username="superuser",
           email="superuser@system.com",
           tenant_id=None,
           is_superuser=True
       )
       db.add(user)
       db.commit()
       return user
   
   @pytest.fixture
   def project_a(db, tenant_a):
       """租户A的项目"""
       project = Project(
           name="Project A1",
           tenant_id=tenant_a.id
       )
       db.add(project)
       db.commit()
       return project
   
   @pytest.fixture
   def project_b(db, tenant_b):
       """租户B的项目"""
       project = Project(
           name="Project B1",
           tenant_id=tenant_b.id
       )
       db.add(project)
       db.commit()
       return project
   ```

2. **基础隔离测试**
   ```python
   # tests/security/test_tenant_isolation.py
   
   class TestTenantIsolation:
       """多租户隔离测试"""
       
       def test_user_cannot_access_other_tenant_project(
           self, client, tenant_a, tenant_b, user_a, project_b
       ):
           """用户不能访问其他租户的项目"""
           # 租户A用户登录
           token = login(client, user_a)
           
           # 尝试访问租户B的项目
           response = client.get(
               f"/api/v1/projects/{project_b.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           # 应该返回 404 或 403
           assert response.status_code in [403, 404]
       
       def test_user_can_access_own_tenant_project(
           self, client, tenant_a, user_a, project_a
       ):
           """用户可以访问本租户的项目"""
           token = login(client, user_a)
           
           response = client.get(
               f"/api/v1/projects/{project_a.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           assert response.status_code == 200
           assert response.json()['id'] == project_a.id
       
       def test_list_projects_only_returns_same_tenant(
           self, client, db, tenant_a, tenant_b, user_a
       ):
           """列表接口只返回同租户数据"""
           # 创建项目
           create_project(db, tenant_a, "Project A1")
           create_project(db, tenant_a, "Project A2")
           create_project(db, tenant_b, "Project B1")  # 租户B
           create_project(db, tenant_b, "Project B2")  # 租户B
           
           # 租户A用户登录
           token = login(client, user_a)
           
           # 获取项目列表
           response = client.get(
               "/api/v1/projects",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           projects = response.json()
           
           # 只应返回租户A的项目
           assert len(projects) == 2
           assert all(p['name'].startswith('Project A') for p in projects)
       
       def test_superuser_can_access_all_tenants(
           self, client, tenant_a, tenant_b, superuser, project_a, project_b
       ):
           """超级管理员可以访问所有租户数据"""
           token = login(client, superuser)
           
           # 访问租户A项目
           response = client.get(
               f"/api/v1/projects/{project_a.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           assert response.status_code == 200
           
           # 访问租户B项目
           response = client.get(
               f"/api/v1/projects/{project_b.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           assert response.status_code == 200
       
       def test_superuser_list_returns_all_tenants(
           self, client, db, tenant_a, tenant_b, superuser
       ):
           """超级管理员列表接口返回所有租户数据"""
           create_project(db, tenant_a, "Project A1")
           create_project(db, tenant_b, "Project B1")
           
           token = login(client, superuser)
           
           response = client.get(
               "/api/v1/projects",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           projects = response.json()
           
           # 应返回所有租户的项目
           assert len(projects) == 2
   ```

3. **创建/更新/删除隔离测试**
   ```python
   class TestTenantIsolationCUD:
       """创建/更新/删除的租户隔离测试"""
       
       def test_user_cannot_update_other_tenant_project(
           self, client, user_a, project_b
       ):
           """用户不能更新其他租户的项目"""
           token = login(client, user_a)
           
           response = client.put(
               f"/api/v1/projects/{project_b.id}",
               json={"name": "Hacked Name"},
               headers={"Authorization": f"Bearer {token}"}
           )
           
           assert response.status_code in [403, 404]
       
       def test_user_cannot_delete_other_tenant_project(
           self, client, user_a, project_b
       ):
           """用户不能删除其他租户的项目"""
           token = login(client, user_a)
           
           response = client.delete(
               f"/api/v1/projects/{project_b.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           assert response.status_code in [403, 404]
       
       def test_created_resource_auto_assigned_to_user_tenant(
           self, client, db, user_a, tenant_a
       ):
           """创建的资源自动分配到用户的租户"""
           token = login(client, user_a)
           
           response = client.post(
               "/api/v1/projects",
               json={"name": "New Project"},
               headers={"Authorization": f"Bearer {token}"}
           )
           
           assert response.status_code == 201
           project_id = response.json()['id']
           
           # 验证 tenant_id
           project = db.query(Project).filter(Project.id == project_id).first()
           assert project.tenant_id == tenant_a.id
   ```

4. **多模型隔离测试**
   ```python
   class TestMultiModelIsolation:
       """多个模型的隔离测试"""
       
       @pytest.mark.parametrize("model,endpoint", [
           (Project, "/api/v1/projects"),
           (RdProject, "/api/v1/rd-projects"),
           (SalesContract, "/api/v1/sales/contracts"),
           (WorkOrder, "/api/v1/production/work-orders"),
           # ... 其他核心模型
       ])
       def test_model_isolation(
           self, client, db, tenant_a, tenant_b, user_a, model, endpoint
       ):
           """测试所有核心模型的租户隔离"""
           # 创建租户A的资源
           resource_a = create_resource(db, model, tenant_a)
           
           # 创建租户B的资源
           resource_b = create_resource(db, model, tenant_b)
           
           # 租户A用户登录
           token = login(client, user_a)
           
           # 列表查询
           response = client.get(endpoint, headers={"Authorization": f"Bearer {token}"})
           resources = response.json()
           
           # 只应返回租户A的资源
           assert len(resources) == 1
           assert resources[0]['id'] == resource_a.id
           
           # 尝试访问租户B资源
           response = client.get(
               f"{endpoint}/{resource_b.id}",
               headers={"Authorization": f"Bearer {token}"}
           )
           assert response.status_code in [403, 404]
   ```

5. **性能测试**
   ```python
   class TestTenantIsolationPerformance:
       """租户隔离性能测试"""
       
       def test_query_performance_with_tenant_filter(
           self, client, db, tenant_a, user_a
       ):
           """测试租户过滤的查询性能"""
           # 创建大量数据
           for i in range(1000):
               create_project(db, tenant_a, f"Project A{i}")
           
           token = login(client, user_a)
           
           # 测试查询时间
           import time
           start = time.time()
           
           response = client.get(
               "/api/v1/projects",
               headers={"Authorization": f"Bearer {token}"}
           )
           
           elapsed = time.time() - start
           
           assert response.status_code == 200
           assert len(response.json()) == 1000
           
           # 查询应在合理时间内完成（例如 < 1秒）
           assert elapsed < 1.0
   ```

6. **文档**
   - 租户隔离测试指南
   - 测试用例清单
   - 测试数据准备文档

### 技术要求
- 使用pytest框架
- 覆盖所有核心业务模型
- 包含CRUD操作测试
- 性能测试
- 超级管理员测试

### 验收标准
- ✅ 50+测试用例
- ✅ 所有核心模型覆盖
- ✅ CRUD操作测试完整
- ✅ 超级管理员测试通过
- ✅ 性能测试达标
- ✅ 测试覆盖率 ≥ 80%

### 输出文件
- `tests/fixtures/tenant_fixtures.py`
- `tests/security/test_tenant_isolation.py`
- `tests/security/test_multi_model_isolation.py`
- `tests/security/test_tenant_performance.py`
- `docs/租户隔离测试指南.md`
- `Agent_Team_5_租户隔离测试_交付报告.md`

---

## Team 6: 文档和部署

### 任务目标
编写完整的文档和部署指南，确保系统可以顺利上线。

### 交付清单

1. **架构文档**
   - 多租户架构设计
   - 数据隔离实现原理
   - 租户上下文传递机制
   - 性能优化策略

2. **部署指南**
   - 环境准备
   - 数据库迁移步骤
   - 配置文件说明
   - 启动和验证

3. **开发指南**
   - API开发最佳实践
   - 租户隔离开发规范
   - 常见错误和解决方案
   - 代码审查清单

4. **运维指南**
   - 租户管理
   - 数据备份和恢复
   - 性能监控
   - 故障排查

5. **API文档更新**
   - 租户相关API
   - 权限说明
   - 请求示例

6. **README更新**
   - 系统简介
   - 快速开始
   - 多租户特性说明
   - 贡献指南

### 技术要求
- 文档使用Markdown格式
- 包含完整的代码示例
- 图文并茂
- 中英文双语（优先中文）

### 验收标准
- ✅ 架构文档完整
- ✅ 部署指南可执行
- ✅ 开发指南清晰
- ✅ 运维指南完整
- ✅ README更新

### 输出文件
- `docs/architecture/多租户架构设计.md`
- `docs/deployment/部署指南.md`
- `docs/development/开发指南.md`
- `docs/operations/运维指南.md`
- `README.md` (更新)
- `Agent_Team_6_文档部署_交付报告.md`

---

## 技术约束

### 通用要求

1. **数据库兼容性**
   - 支持MySQL 5.7+
   - 支持PostgreSQL 12+
   - 迁移脚本分别提供

2. **向后兼容**
   - 不破坏现有功能
   - 平滑升级
   - 支持回滚

3. **性能要求**
   - 租户过滤开销 < 10%
   - 索引合理
   - 查询优化

4. **代码质量**
   - 遵循PEP8
   - 类型注解完整
   - 注释清晰
   - 测试覆盖率 ≥ 80%

5. **安全要求**
   - 数据库约束强制执行
   - 代码防御性编程
   - 审计日志完整

---

## 验收标准

### 功能验收
- [ ] 所有核心业务表添加 tenant_id
- [ ] 数据迁移完成且验证通过
- [ ] TenantQuery自动过滤生效
- [ ] 超级管理员判断统一
- [ ] 租户隔离测试全部通过
- [ ] 文档完整

### 测试验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 隔离测试50+用例
- [ ] 性能测试达标
- [ ] 所有测试通过

### 文档验收
- [ ] 架构文档完整
- [ ] 部署指南可执行
- [ ] 开发指南清晰
- [ ] API文档更新

### 安全验收
- [ ] 数据库约束生效
- [ ] 租户隔离100%生效
- [ ] 超级管理员权限正确
- [ ] 审计日志记录完整

---

## 时间计划

**启动时间**: 2026-02-16 04:31  
**预计完成**: 2026-02-17 04:31 (24小时)

**并行执行**:
- Team 1-5: 并行开发核心功能 (12-18小时)
- Team 6: 在功能完成后编写文档 (6-8小时)

**检查点**:
- 6小时后: 检查Teams 1-5进度
- 12小时后: 检查数据迁移和测试
- 24小时后: 最终验收

---

## 备注

1. **优先级**: Team 1-2 (数据模型和迁移) 必须先完成，Team 3-5 可并行
2. **依赖关系**: Team 5 (测试) 依赖Team 1-4完成
3. **数据安全**: 所有操作在开发环境测试，确认后再部署到生产环境
4. **Git管理**: 每个Team独立分支，最后合并到main
5. **回滚准备**: 确保所有操作可回滚
