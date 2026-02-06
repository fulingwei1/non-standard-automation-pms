# 权限补强行动计划

## 背景
- 权限测试已在 2026-01-26 通过，但报告指出仍缺少普通角色账号、数据范围用例，以及审计/前端适配等后续事项。参见 `PERMISSION_TEST_REPORT.md:253-288`。
- 权限模型已统一迁移（2026-01-27），仍需按迁移报告 checklist 逐一复核数据库与文档同步项。参见 `PERMISSION_MIGRATION_REPORT.md:29-185`。

## 1. 角色与测试账号矩阵
| 角色编码 | 数据范围 | 适用场景 | 建议权限示例 | 创建方式 |
|----------|----------|----------|--------------|----------|
| `GLOBAL_ADMIN` | ALL | 保留现有 admin，验证正向完全访问 | 现有 98 个权限全量 | 无需新增 |
| `DEPT_MANAGER_UAT` | DEPT | 只能访问所属部门及其项目，覆盖 `DataScopeEnum.DEPT` | 用户管理读/写、项目读、部门读写 | 通过 Alembic seeding 或脚本（参照 `reset_admin_password.py` 模式，批量插入 User + Role + RoleApiPermission） |
| `PROJECT_MANAGER_UAT` | PROJECT | 仅访问被分配项目，验证项目级过滤 | 项目 CRUD、工单处理、仅本项目数据 | 同上，并在 `project_members` 中绑定样例项目 |
| `AUDITOR_READONLY` | SUBORDINATE | 复核直属下属与下钻数据，验证 `SUBORDINATE` 策略 | 只读接口 + 审计 API | 将角色 `inherit_permissions=True`，仅赋予 GET 类权限 |
| `LIMITED_OPERATOR` | OWN | 验证个人级别数据隔离 | 仅本人任务/单据的创建+查看 | 脚本创建普通职员，并确保没有项目成员身份 |
| `TENANT_ADMIN_SANDBOX` | ALL (tenant scoped) | 多租户管理员，排查租户隔离 | 管理本租户用户/角色、仅本租户项目 | 将 `tenant_id` 指向测试租户并验证 `tenant_id` 过滤 |

**落地步骤**
1. 在 `scripts/` 下新增 `seed_permission_test_users.py`：
   - 复用 `app.models.user.Role`, `User`, `RoleApiPermission`，以及 `UserRole`，封装 `create_role`, `create_user`, `attach_permissions` 三个 helper。
   - 支持幂等（role_code/user不存在才创建，存在则更新 data_scope/描述）。
2. 选定 3 个示例项目 & 2 个示例部门，写入 fixtures（可复用 `migrations/skip/20260121_role_management_sqlite.sql` 里扩展的结构）。
3. 在 `.env.test` 或 pytest fixture 中通过环境变量控制是否自动创建这些账号，避免污染生产数据。

## 2. 负例与数据范围测试用例
| 用例 | 用户 | 入口 | 期望 | 备注 |
|------|------|------|------|------|
| `dept_manager_cannot_access_other_department_users` | `DEPT_MANAGER_UAT` | `GET /api/v1/users?department=Other` | 403 + `INSUFFICIENT_SCOPE` | 验证部门过滤 |
| `project_manager_cannot_delete_unassigned_project` | `PROJECT_MANAGER_UAT` | `DELETE /api/v1/projects/{id}` | 403 | 配合 `ProjectMember` 关系 |
| `auditor_readonly_cannot_post` | `AUDITOR_READONLY` | `POST /api/v1/issues` | 403 | 验证只读角色 |
| `limited_operator_cannot_view_peer_tasks` | `LIMITED_OPERATOR` | `GET /api/v1/tasks/{peer}` | 404/403 | 视数据权限实现决定 |
| `tenant_admin_cannot_cross_tenant` | `TENANT_ADMIN_SANDBOX` | `GET /api/v1/projects?tenant_id=other` | 403 or 空集 | 验证租户隔离 |

**脚本改造**
- 将 `test_permissions_optimized.py` 参数化，允许 `ROLE_MATRIX = { 'admin': {...}, 'dept_manager': {...}}`；循环登录各账号，运行基础/拒绝/数据权限用例，按用户输出。参考 `test_permissions_optimized.py:96-199` 的结构，将 `test_cases` 列表扩展为 `scoped_test_suites`，并允许 `expected_status` 传 403。
- 新增 `tests/test_data_scope_matrix.py`（pytest）来对 ORM 层 `DataScopeService` / `UserScopeService` 做单元测试，直接构造 SQLAlchemy session + fixtures 验证 `OWN/PROJECT/DEPT/SUBORDINATE` 返回。
- 在 CI 中标记该套件为 `permissions-scope`，仅在含有数据改动的 pipeline 运行，以降低执行时间。

## 3. 权限审计与日志
1. **API 访问日志**：在 `app/core/middleware/auth_middleware.py:37-139` 中添加结构化日志（user_id, role_codes, data_scope, endpoint, verdict）。落到 `logs/permission_audit.log`。
2. **权限检查钩子**：在 `app/core/security.py` 的 `require_permission` 装饰器内记录拒绝事件（权限编码、主体、资源 ID）。
3. **审计报表**：新增 `scripts/export_permission_audit.py`，聚合最近 N 天拒绝事件，供安全团队审阅。
4. **监控指标**：将拒绝次数/角色分布推送到现有监控（参考 `monitoring/` 目录中的 exporter 模式）。

## 4. 前端权限适配
1. **权限拉取**：前端登录后调用 `/api/v1/permissions/matrix`（已迁移到新模型，见 `PERMISSION_MIGRATION_REPORT.md:39-52`），缓存用户权限列表。
2. **Route Guard**：在 `frontend/src` 中创建 `withPermission` HOC/Hook，依据权限码隐藏菜单、按钮。
3. **数据范围提示**：当后端返回 403/`INSUFFICIENT_SCOPE` 时，展示“超出数据范围”的定制组件。
4. **Token 自动刷新**：扩展前端请求层对 401 `AUTH_FAILED` 的处理，调用 `/api/v1/auth/refresh` 并重放请求。

## 5. 迁移 Checklist 复核
| 项 | 动作 | 负责人 |
|----|------|--------|
| 模块导入 | 运行迁移报告中的 `python3 -c` 校验脚本，纳入 CI preflight。 | 平台工程 |
| 数据库 | 在所有环境执行数据校验：`SELECT COUNT(*) FROM permissions;` 应为 0；`api_permissions`、`role_api_permissions` 与生产对齐。 | DBA |
| 文档 | 更新 `README.md`、`PERMISSION_MODULE_COMPLETION_SUMMARY.md`、API 文档中关于权限模型的段落。 | 技术文档 |
| 测试 | CI 中新增 job：运行 `test_permissions_optimized.py` + 新的 scope 测试，在成功后上传报告至 `reports/`. | QA |
| 监控 | 新日志/指标纳入 `monitoring/` dashboards。 | SRE |

> 执行完上述事项后，再次生成 `PERMISSION_TEST_REPORT.md` v3.0，并在文末记录新的测试账号矩阵与审计/前端状态。
