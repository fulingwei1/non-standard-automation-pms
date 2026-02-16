# API路由修复方案

## 背景

系统有740条registered routes，通过初步分析发现以下问题：

1. **路径斜杠问题**：某些API路径带尾部斜杠会返回404
   - 例如：`GET /api/v1/production/workshops/` 返回404
   - 正确路径：`GET /api/v1/production/workshops`

2. **路径错误**：某些文档或使用中的路径与实际路由不符
   - 例如：`GET /api/v1/users/me` 应该是 `GET /api/v1/auth/me`

## 已知问题

### 1. Production Workshops路由

**问题**：
```bash
GET /api/v1/production/workshops/  # 404 Not Found
```

**正确路径**：
```bash
GET /api/v1/production/workshops   # 200 OK
```

**修复方案**：
- 确保所有文档和前端调用使用正确的路径（不带尾部斜杠）
- 或者在FastAPI中配置自动重定向尾部斜杠

### 2. User Me路由

**问题**：
```bash
GET /api/v1/users/me  # 可能不存在或返回错误
```

**正确路径**：
```bash
GET /api/v1/auth/me   # 获取当前用户信息
```

**位置**：`app/api/v1/endpoints/auth.py:390`

**修复方案**：
- 更新所有文档和前端调用
- 考虑在users路由下添加一个/me的别名路由（可选）

## 路由规范

### 1. 路径规范

1. **不使用尾部斜杠**
   - ✅ 正确：`/api/v1/projects`
   - ❌ 错误：`/api/v1/projects/`

2. **路径参数使用大括号**
   - ✅ 正确：`/api/v1/projects/{project_id}`
   - ❌ 错误：`/api/v1/projects/:project_id`

3. **使用连字符而非下划线**
   - ✅ 正确：`/api/v1/sales-teams`
   - ⚠️ 可接受：`/api/v1/sales_teams`（但不推荐）

### 2. 方法规范

- GET: 查询资源
- POST: 创建资源
- PUT: 完整更新资源
- PATCH: 部分更新资源
- DELETE: 删除资源

### 3. 响应码规范

- 200: 成功
- 201: 创建成功
- 204: 删除成功（无内容）
- 400: 请求参数错误
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 422: 验证错误
- 500: 服务器错误

## 修复优先级

### P0（立即修复）

1. ✅ 路径文档错误
   - 更新API文档中的错误路径
   - 更新前端代码中的API调用

2. ✅ 尾部斜杠处理
   - 在FastAPI中配置`redirect_slashes=True`（默认启用）
   - 或统一要求不使用尾部斜杠

### P1（重要但不紧急）

1. 添加路由别名
   - 为常用路由添加别名（如`/users/me` -> `/auth/me`）
   - 保持向后兼容性

2. 路由命名规范化
   - 统一使用连字符或下划线
   - 更新现有不规范的路由

### P2（优化项）

1. 路由版本管理
   - 为重大变更准备v2版本
   - 保持v1版本的兼容性

2. 性能优化
   - 添加路由级别的缓存
   - 优化数据库查询

## 验证清单

- [ ] 所有核心endpoints返回正确状态码
- [ ] 文档中的路径与实际路由一致
- [ ] 前端调用使用正确的路径
- [ ] 路径参数验证正常工作
- [ ] 认证和权限检查正常
- [ ] 错误响应格式统一
- [ ] API响应时间在可接受范围内

## 测试覆盖

### 核心模块测试

1. **用户管理** (`/api/v1/users/*`)
   - [ ] GET /users (列表)
   - [ ] GET /users/{id} (详情)
   - [ ] POST /users (创建)
   - [ ] PUT /users/{id} (更新)
   - [ ] DELETE /users/{id} (删除)

2. **认证** (`/api/v1/auth/*`)
   - [ ] POST /auth/login
   - [ ] POST /auth/logout
   - [ ] POST /auth/refresh
   - [ ] GET /auth/me

3. **项目管理** (`/api/v1/projects/*`)
   - [ ] GET /projects
   - [ ] GET /projects/{id}
   - [ ] POST /projects
   - [ ] PUT /projects/{id}

4. **生产管理** (`/api/v1/production/*`)
   - [ ] GET /production/workshops
   - [ ] GET /production/plans
   - [ ] GET /production/work-orders

5. **销售管理** (`/api/v1/sales/*`)
   - [ ] GET /sales/leads
   - [ ] GET /sales/opportunities
   - [ ] GET /sales/quotations

## 实施计划

### 第一阶段：扫描和分析（已完成）
- [x] 提取所有registered routes (740条)
- [x] 自动测试所有GET endpoints
- [ ] 识别所有404/422/500错误

### 第二阶段：修复核心问题（进行中）
- [ ] 修复路径文档错误
- [ ] 统一路径格式（尾部斜杠）
- [ ] 修复路由配置问题

### 第三阶段：验证和测试（待进行）
- [ ] 重新运行全面测试
- [ ] 更新前端代码
- [ ] 更新API文档
- [ ] 验收测试

## 交付物

1. ✅ 路由扫描脚本：`scripts/extract_routes.py`
2. ✅ 路由测试脚本：`scripts/test_all_routes.py`
3. 🔄 路由检查报告：`data/route_test_report.txt` (生成中)
4. 🔄 路由测试结果JSON：`data/route_test_results.json` (生成中)
5. ✅ 修复方案文档：`data/route_fix_plan.md` (本文档)
6. ⏳ 验证测试脚本：待创建

## 备注

- 所有脚本位于 `scripts/` 目录
- 所有报告和数据位于 `data/` 目录
- 测试使用admin账户（username: admin, password: admin123）
- 注意rate limiting（5次/分钟），测试时需要适当延迟
