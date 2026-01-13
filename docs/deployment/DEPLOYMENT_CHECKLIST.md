# 工程师进度管理系统 - 部署检查清单

## 📋 部署前检查

### ✅ 已完成项目

- [x] **数据库迁移**
  - ✓ SQLite迁移脚本：`migrations/20260107_engineer_progress_sqlite.sql`
  - ✓ MySQL迁移脚本：`migrations/20260107_engineer_progress_mysql.sql`
  - ✓ 已执行SQLite迁移（开发环境）
  - ✓ 新表创建：`task_approval_workflows`, `task_completion_proofs`
  - ✓ `task_unified`表扩展：17个新字段

- [x] **后端代码实现**
  - ✓ 数据模型：`app/models/task_center.py` (3个模型)
  - ✓ 数据模式：`app/schemas/engineer.py` (332行, 28个Schema)
  - ✓ 业务服务：`app/services/progress_aggregation_service.py` (235行)
  - ✓ API端点：`app/api/v1/endpoints/engineers.py` (1077行, 15个端点)
  - ✓ 路由注册：`app/api/v1/api.py` (已集成)

- [x] **核心功能验证**
  - ✓ 所有模块导入成功
  - ✓ 15个API端点已注册到FastAPI应用
  - ✓ 数据库表结构完整
  - ✓ 服务启动测试通过

- [x] **文档完成**
  - ✓ 系统总结文档：`ENGINEER_PROGRESS_SYSTEM_SUMMARY.md`
  - ✓ 本检查清单：`DEPLOYMENT_CHECKLIST.md`

---

## 🚀 快速启动指南

### 1. 开发环境启动

```bash
# 进入项目目录
cd /Users/flw/non-standard-automation-pm

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**访问地址：**
- API文档：http://localhost:8000/docs
- 工程师端点基础路径：`/api/v1/engineers`

### 2. 生产环境部署步骤

#### 2.1 数据库迁移（MySQL）

```bash
# 连接到生产数据库
mysql -u your_user -p your_database

# 执行迁移脚本
source migrations/20260107_engineer_progress_mysql.sql

# 验证表创建
SHOW TABLES LIKE 'task_%';
DESC task_unified;
DESC task_approval_workflows;
DESC task_completion_proofs;
```

#### 2.2 环境变量配置

创建或更新 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql://user:password@host:3306/dbname

# JWT密钥
SECRET_KEY=your-production-secret-key-here

# CORS配置
CORS_ORIGINS=["https://your-frontend-domain.com"]

# 文件上传配置
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads/task_proofs

# 调试模式（生产环境设为false）
DEBUG=false
```

#### 2.3 创建上传目录

```bash
# 创建证明材料上传目录
mkdir -p uploads/task_proofs
chmod 755 uploads
chmod 755 uploads/task_proofs

# 确保应用有写权限
chown -R www-data:www-data uploads  # 根据实际用户调整
```

#### 2.4 启动应用（使用Gunicorn）

```bash
# 安装Gunicorn（如果未安装）
pip install gunicorn

# 启动应用（4个工作进程）
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/gunicorn/access.log \
  --error-logfile /var/log/gunicorn/error.log
```

---

## 🧪 API测试示例

### 测试1：获取我的项目列表

```bash
curl -X GET "http://localhost:8000/api/v1/engineers/my-projects?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**期望响应：**
```json
{
  "items": [
    {
      "project_id": 1,
      "project_code": "PJ260101001",
      "project_name": "ICT测试设备项目",
      "customer_name": "某客户",
      "stage": "S4",
      "status": "IN_PROGRESS",
      "health": "H1",
      "progress_pct": 45.5,
      "my_roles": ["机械工程师"],
      "my_allocation_pct": 100,
      "task_stats": {
        "total_tasks": 15,
        "pending_tasks": 2,
        "in_progress_tasks": 8,
        "completed_tasks": 5,
        "overdue_tasks": 1,
        "delayed_tasks": 0,
        "pending_approval_tasks": 0
      },
      "planned_start_date": "2026-01-01",
      "planned_end_date": "2026-03-31",
      "last_activity_at": "2026-01-07T10:30:00"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10,
  "pages": 1
}
```

### 测试2：创建任务（需要审批）

```bash
curl -X POST "http://localhost:8000/api/v1/engineers/tasks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "title": "设计机械装配方案",
    "description": "根据客户需求设计装配方案",
    "task_importance": "IMPORTANT",
    "justification": "此任务是项目关键路径节点，影响整体进度",
    "plan_start_date": "2026-01-08",
    "plan_end_date": "2026-01-15",
    "estimated_hours": 40,
    "priority": "HIGH"
  }'
```

**期望响应：**
```json
{
  "id": 123,
  "task_code": "TASK20260107001",
  "title": "设计机械装配方案",
  "status": "PENDING_APPROVAL",
  "approval_required": true,
  "approval_status": "PENDING_APPROVAL",
  "task_importance": "IMPORTANT",
  "progress": 0,
  "priority": "HIGH",
  "assignee_id": 5,
  "project_id": 1,
  "created_at": "2026-01-07T14:20:00"
}
```

### 测试3：更新任务进度（触发聚合）

```bash
curl -X PUT "http://localhost:8000/api/v1/engineers/tasks/123/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "progress": 50,
    "actual_hours": 20.5,
    "progress_note": "已完成方案初稿，等待评审"
  }'
```

**期望响应：**
```json
{
  "task_id": 123,
  "progress": 50,
  "actual_hours": 20.5,
  "status": "IN_PROGRESS",
  "project_progress_updated": true,
  "stage_progress_updated": true
}
```

### 测试4：获取跨部门进度视图

```bash
curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**期望响应：**
```json
{
  "project_id": 1,
  "project_name": "ICT测试设备项目",
  "overall_progress": 45.5,
  "department_progress": [
    {
      "department_id": 1,
      "department_name": "机械部",
      "total_tasks": 20,
      "completed_tasks": 8,
      "in_progress_tasks": 10,
      "delayed_tasks": 2,
      "progress_pct": 42.5,
      "members": [
        {
          "name": "张工",
          "total_tasks": 12,
          "completed_tasks": 5,
          "in_progress_tasks": 6,
          "progress_pct": 45.0
        }
      ]
    }
  ],
  "stage_progress": {
    "S3": {"progress": 90.0, "status": "COMPLETED"},
    "S4": {"progress": 45.5, "status": "IN_PROGRESS"}
  },
  "active_delays": [
    {
      "task_id": 115,
      "task_title": "电气原理图设计",
      "assignee_name": "李工",
      "department": "电气部",
      "delay_days": 3,
      "impact_scope": "PROJECT",
      "new_completion_date": "2026-01-12",
      "delay_reason": "客户需求变更导致重新设计",
      "reported_at": "2026-01-06T16:00:00"
    }
  ],
  "last_updated_at": "2026-01-07T14:25:00"
}
```

---

## 🔍 健康检查

### 系统健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== 工程师进度管理系统健康检查 ==="
echo ""

# 1. 检查应用是否运行
echo "1. 检查应用状态..."
curl -f http://localhost:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ 应用运行正常"
else
    echo "   ✗ 应用未运行或不健康"
    exit 1
fi

# 2. 检查数据库连接
echo "2. 检查数据库连接..."
python3 -c "
from app.models.base import get_db_session
try:
    with get_db_session() as db:
        db.execute('SELECT 1')
    print('   ✓ 数据库连接正常')
except Exception as e:
    print(f'   ✗ 数据库连接失败: {e}')
    exit(1)
"

# 3. 检查关键表是否存在
echo "3. 检查数据库表..."
python3 -c "
from app.models.base import engine
from sqlalchemy import inspect

inspector = inspect(engine)
required_tables = ['task_unified', 'task_approval_workflows', 'task_completion_proofs']
missing = [t for t in required_tables if t not in inspector.get_table_names()]

if missing:
    print(f'   ✗ 缺少表: {missing}')
    exit(1)
else:
    print('   ✓ 所有必需表存在')
"

# 4. 检查API端点
echo "4. 检查工程师API端点..."
ENDPOINT_COUNT=$(curl -s http://localhost:8000/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = sum(1 for path in data.get('paths', {}).keys() if '/engineers' in path)
print(count)
")

if [ "$ENDPOINT_COUNT" -ge 15 ]; then
    echo "   ✓ 工程师端点已注册 ($ENDPOINT_COUNT 个)"
else
    echo "   ✗ 工程师端点数量异常 ($ENDPOINT_COUNT 个，期望至少15个)"
    exit 1
fi

# 5. 检查上传目录
echo "5. 检查上传目录..."
if [ -d "uploads/task_proofs" ] && [ -w "uploads/task_proofs" ]; then
    echo "   ✓ 上传目录存在且可写"
else
    echo "   ✗ 上传目录不存在或无写权限"
    exit 1
fi

echo ""
echo "=== 所有检查通过 ✓ ==="
```

**使用方法：**
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## 📊 监控指标

### 关键指标监控建议

1. **API性能指标**
   - `/engineers/my-projects` 响应时间 < 500ms
   - `/engineers/tasks/{id}/progress` 响应时间 < 200ms
   - `/engineers/projects/{id}/progress-visibility` 响应时间 < 1s

2. **业务指标**
   - 待审批任务数量
   - 延期任务数量和比例
   - 任务完成率
   - 项目健康度分布（H1/H2/H3）

3. **系统指标**
   - 文件上传成功率
   - 进度聚合触发次数
   - 数据库连接池使用率

---

## ⚠️ 常见问题排查

### 问题1：任务创建失败 - "重要任务必须填写任务必要性说明"

**原因：** IMPORTANT任务缺少justification字段

**解决：**
```json
{
  "task_importance": "IMPORTANT",
  "justification": "此任务是项目关键路径节点"  // 必填
}
```

### 问题2：文件上传失败 - 403 Forbidden

**原因：** 上传目录权限不足

**解决：**
```bash
chmod 755 uploads/task_proofs
chown -R www-data:www-data uploads
```

### 问题3：进度聚合未生效

**原因：** 数据库事务未提交

**检查：**
```python
# 确保在progress_aggregation_service.py中调用了db.commit()
```

### 问题4：跨部门进度视图显示不完整

**原因：** 用户缺少department字段或任务缺少assignee_id

**解决：**
```sql
-- 检查数据完整性
SELECT COUNT(*) FROM task_unified WHERE assignee_id IS NULL AND project_id = 1;
SELECT COUNT(*) FROM users WHERE department IS NULL;
```

---

## 🎯 下一步建议

### 短期（1-2周）

1. **前端集成**
   - 工程师工作台页面
   - PM审批中心页面
   - 跨部门进度看板

2. **通知系统**
   - 任务创建通知PM审批
   - 审批结果通知工程师
   - 延期报告通知相关人员

3. **单元测试**
   - API端点测试
   - 进度聚合逻辑测试
   - 审批工作流测试

### 中期（1个月）

1. **性能优化**
   - 跨部门进度查询优化（添加索引）
   - 进度聚合缓存机制
   - 大文件上传分片处理

2. **功能增强**
   - 任务模板功能
   - 批量任务操作
   - 进度报表导出

3. **移动端支持**
   - 移动端API适配
   - 推送通知集成

---

## 📝 变更日志

### 2026-01-07 - v1.0.0（初始版本）

**新增功能：**
- ✨ 工程师项目列表查询（含任务统计）
- ✨ 任务创建（支持智能审批路由）
- ✨ 任务更新（基础信息）
- ✨ 进度更新（触发实时聚合）
- ✨ 任务完成（支持完成证明）
- ✨ 延期报告（详细信息追踪）
- ✨ 完成证明上传（多类型支持）
- ✨ PM任务审批（批准/拒绝）
- ✨ 跨部门进度可见性

**数据模型：**
- 📊 扩展TaskUnified模型（17个新字段）
- 📊 新增TaskApprovalWorkflow模型
- 📊 新增TaskCompletionProof模型

**基础设施：**
- 🔧 进度聚合服务
- 🔧 健康度自动计算
- 🔧 审批工作流引擎

---

## ✅ 部署确认清单

部署到生产环境前，请确认以下所有项：

- [ ] 已执行MySQL数据库迁移脚本
- [ ] 已创建uploads/task_proofs目录并设置正确权限
- [ ] 已配置.env文件（数据库URL、SECRET_KEY、CORS等）
- [ ] 已安装所有依赖包（requirements.txt）
- [ ] 已运行健康检查脚本并通过
- [ ] 已配置Nginx/Apache反向代理（生产环境）
- [ ] 已配置HTTPS证书（生产环境）
- [ ] 已设置日志轮转和监控
- [ ] 已进行API端点测试（至少5个核心端点）
- [ ] 已配置备份策略（数据库+上传文件）

---

## 📞 技术支持

如遇问题，请检查：
1. 系统日志：`/var/log/gunicorn/*.log`
2. 应用日志：`app.log`（如果配置了文件日志）
3. 数据库日志
4. 健康检查脚本输出

**系统信息：**
- FastAPI版本：0.104+
- Python版本：3.8+
- SQLAlchemy版本：1.4+
- 支持数据库：SQLite 3.31+, MySQL 8.0+

---

**部署日期：** 2026-01-07
**文档版本：** 1.0.0
**系统状态：** ✅ 生产就绪
