# 工时报表自动生成系统 - 管理员配置指南

**版本**: 1.0.0  
**适用角色**: 系统管理员、HR 主管

---

## 📖 目录

1. [系统架构](#系统架构)
2. [数据库表结构](#数据库表结构)
3. [报表模板配置](#报表模板配置)
4. [定时任务管理](#定时任务管理)
5. [收件人配置](#收件人配置)
6. [故障排查](#故障排查)
7. [性能优化](#性能优化)

---

## 系统架构

### 组件说明

```
┌─────────────────────────────────────────────┐
│           工时报表自动生成系统              │
├─────────────────────────────────────────────┤
│  前端界面 (React)                           │
│  - 报表模板管理页面                         │
│  - 报表生成页面                             │
│  - 报表归档查询页面                         │
├─────────────────────────────────────────────┤
│  API 层 (FastAPI)                          │
│  - 15个 RESTful API 端点                   │
│  - JWT 认证 + 权限控制                     │
├─────────────────────────────────────────────┤
│  服务层                                     │
│  - ReportService (报表生成)                │
│  - ReportExcelService (Excel 导出)         │
├─────────────────────────────────────────────┤
│  定时任务 (APScheduler)                    │
│  - 每月1号 09:00 自动生成报表              │
├─────────────────────────────────────────────┤
│  数据层 (SQLAlchemy + MySQL)               │
│  - report_template (模板表)                │
│  - report_archive (归档表)                 │
│  - report_recipient (收件人表)             │
└─────────────────────────────────────────────┘
```

---

## 数据库表结构

### 1. report_template (报表模板表)

```sql
CREATE TABLE `report_template` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '模板名称',
  `report_type` VARCHAR(50) NOT NULL COMMENT '报表类型',
  `description` TEXT COMMENT '描述',
  `config` JSON COMMENT '模板配置',
  `output_format` VARCHAR(20) DEFAULT 'EXCEL',
  `frequency` VARCHAR(20) DEFAULT 'MONTHLY',
  `enabled` BOOLEAN DEFAULT TRUE,
  `created_by` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_report_type (report_type),
  INDEX idx_enabled (enabled)
);
```

### 2. report_archive (报表归档表)

```sql
CREATE TABLE `report_archive` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `template_id` INT NOT NULL,
  `report_type` VARCHAR(50) NOT NULL,
  `period` VARCHAR(20) NOT NULL COMMENT '报表周期',
  `file_path` VARCHAR(500) NOT NULL,
  `file_size` INT COMMENT '文件大小（字节）',
  `row_count` INT COMMENT '数据行数',
  `generated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `generated_by` VARCHAR(50) NOT NULL,
  `status` VARCHAR(20) DEFAULT 'SUCCESS',
  `error_message` TEXT,
  `download_count` INT DEFAULT 0,
  INDEX idx_template_period (template_id, period),
  INDEX idx_period (period)
);
```

### 3. report_recipient (报表收件人表)

```sql
CREATE TABLE `report_recipient` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `template_id` INT NOT NULL,
  `recipient_type` VARCHAR(20) NOT NULL COMMENT 'USER/ROLE/DEPT/EMAIL',
  `recipient_id` INT COMMENT '用户/角色/部门ID',
  `recipient_email` VARCHAR(200) COMMENT '外部邮箱',
  `delivery_method` VARCHAR(20) DEFAULT 'EMAIL' COMMENT 'EMAIL/WECHAT/DOWNLOAD',
  `enabled` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_template_id (template_id)
);
```

---

## 报表模板配置

### 创建模板的完整配置示例

```json
{
  "name": "研发部门人员月度工时报表",
  "report_type": "USER_MONTHLY",
  "description": "每月统计研发部门所有人员的工时情况",
  "config": {
    "fields": [
      "user_name",
      "department",
      "total_hours",
      "normal_hours",
      "overtime_hours",
      "work_days",
      "avg_hours_per_day"
    ],
    "filters": {
      "department_ids": [1, 2, 3],
      "role_ids": null
    },
    "chart_types": ["bar", "pie"],
    "conditional_format": true
  },
  "output_format": "EXCEL",
  "frequency": "MONTHLY",
  "enabled": true
}
```

### config 字段详解

#### fields (包含字段)
可选字段列表：
- `user_id`: 用户ID
- `user_name`: 姓名
- `department`: 部门
- `total_hours`: 总工时
- `normal_hours`: 正常工时
- `overtime_hours`: 加班工时
- `work_days`: 工作天数
- `avg_hours_per_day`: 日均工时
- `project_name`: 项目名称
- `task_name`: 任务名称

#### filters (筛选条件)
- `department_ids`: 部门ID列表（数组）
- `role_ids`: 角色ID列表（数组）
- `user_ids`: 用户ID列表（数组）
- `project_ids`: 项目ID列表（数组）

### 报表类型说明

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| USER_MONTHLY | 人员月度工时报表 | HR、部门经理查看每个人的工时 |
| DEPT_MONTHLY | 部门月度工时报表 | 高管查看各部门工时统计 |
| PROJECT_MONTHLY | 项目月度工时报表 | 项目经理、PMO查看项目工时投入 |
| COMPANY_MONTHLY | 公司整体工时报表 | 管理层了解公司整体工时情况 |
| OVERTIME_MONTHLY | 加班统计报表 | HR统计加班情况，用于加班费核算 |

---

## 定时任务管理

### 配置文件位置

```
app/utils/scheduler_config/timesheet.py
```

### 任务配置

```python
{
    "id": "monthly_report_generation",
    "name": "每月自动生成工时报表",
    "module": "app.utils.scheduled_tasks.report_tasks",
    "callable": "monthly_report_generation_task",
    "cron": {"day": 1, "hour": 9, "minute": 0},  # 每月1号 09:00
    "enabled": True,
    "dependencies_tables": [
        "timesheet", 
        "report_template", 
        "report_archive"
    ],
    "risk_level": "HIGH",
    "sla": {
        "max_execution_time_seconds": 1800,  # 最长30分钟
        "retry_on_failure": True
    }
}
```

### 修改执行时间

如果需要修改定时任务的执行时间，编辑上述配置文件中的 `cron` 字段：

```python
# 示例1: 每月2号凌晨2点执行
"cron": {"day": 2, "hour": 2, "minute": 0}

# 示例2: 每月1号和15号执行
"cron": {"day": "1,15", "hour": 9, "minute": 0}
```

### 手动触发定时任务

```python
# Python Shell
from app.utils.scheduled_tasks.report_tasks import monthly_report_generation_task
from app.models.base import get_db_session

with get_db_session() as db:
    result = monthly_report_generation_task()
    print(result)
```

### 查看任务执行日志

```bash
# 查看系统日志
tail -f server.log | grep "报表生成"

# 查看定时任务日志
tail -f server.log | grep "monthly_report_generation"
```

---

## 收件人配置

### 配置方式1: 通过 API

```bash
curl -X POST "http://localhost:8000/api/v1/reports/templates/1/recipients" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_type": "USER",
    "recipient_id": 10,
    "delivery_method": "EMAIL",
    "enabled": true
  }'
```

### 配置方式2: 直接插入数据库

```sql
INSERT INTO report_recipient (template_id, recipient_type, recipient_id, delivery_method, enabled)
VALUES
  (1, 'USER', 10, 'EMAIL', TRUE),      -- 用户ID=10，邮件发送
  (1, 'ROLE', 5, 'WECHAT', TRUE),      -- 角色ID=5（如：HR角色），企业微信发送
  (1, 'DEPT', 2, 'EMAIL', TRUE),       -- 部门ID=2，邮件发送
  (1, 'EMAIL', NULL, 'EMAIL', TRUE);   -- 外部邮箱: boss@company.com
```

### 收件人类型详解

1. **USER (用户)**
   - `recipient_id`: 用户ID
   - 发送给指定用户

2. **ROLE (角色)**
   - `recipient_id`: 角色ID
   - 发送给拥有该角色的所有用户

3. **DEPT (部门)**
   - `recipient_id`: 部门ID
   - 发送给该部门的所有成员

4. **EMAIL (外部邮箱)**
   - `recipient_email`: 邮箱地址
   - 发送给外部邮箱（如：外部审计、顾问）

### 分发方式

- **EMAIL**: 邮件附件形式发送 Excel 文件
- **WECHAT**: 企业微信消息 + 下载链接
- **DOWNLOAD**: 仅发送下载链接

---

## 故障排查

### 问题1: 报表未自动生成

**排查步骤**:

1. 检查定时任务是否启用
```bash
# 查看定时任务配置
cat app/utils/scheduler_config/timesheet.py | grep monthly_report_generation
```

2. 检查模板是否启用
```sql
SELECT id, name, enabled FROM report_template WHERE frequency = 'MONTHLY';
```

3. 查看错误日志
```bash
tail -f server.log | grep "报表生成失败"
```

4. 手动触发测试
```python
from app.utils.scheduled_tasks.report_tasks import test_report_generation
result = test_report_generation()
```

### 问题2: 报表生成失败

**常见原因**:

1. **数据库查询超时**
   - 解决: 增加查询超时时间，优化索引
   
2. **磁盘空间不足**
   - 解决: 清理旧报表文件，扩容磁盘

3. **openpyxl 库未安装**
   - 解决: `pip install openpyxl`

4. **工时数据为空**
   - 解决: 检查是否有已审批的工时数据

### 问题3: Excel 文件无法打开

**排查**:

1. 检查文件大小
```bash
ls -lh reports/2026/01/*.xlsx
```

2. 验证文件完整性
```python
from openpyxl import load_workbook
wb = load_workbook('report.xlsx')
print(wb.sheetnames)
```

3. 检查文件权限
```bash
chmod 644 reports/2026/01/*.xlsx
```

---

## 性能优化

### 1. 数据库优化

#### 添加索引
```sql
-- 工时表索引
CREATE INDEX idx_timesheet_work_date ON timesheet(work_date);
CREATE INDEX idx_timesheet_status ON timesheet(status);
CREATE INDEX idx_timesheet_user_id ON timesheet(user_id);
CREATE INDEX idx_timesheet_department_id ON timesheet(department_id);
CREATE INDEX idx_timesheet_project_id ON timesheet(project_id);

-- 组合索引
CREATE INDEX idx_timesheet_date_status ON timesheet(work_date, status);
```

#### 数据分区（大数据量场景）
```sql
-- 按月份分区
ALTER TABLE timesheet PARTITION BY RANGE (YEAR(work_date) * 100 + MONTH(work_date)) (
    PARTITION p202601 VALUES LESS THAN (202602),
    PARTITION p202602 VALUES LESS THAN (202603),
    ...
);
```

### 2. 报表生成优化

#### 批量查询
```python
# 优化前: N+1 查询
for user in users:
    timesheets = query_timesheets(user.id)

# 优化后: 一次查询
timesheets = query_all_timesheets()
grouped = group_by_user(timesheets)
```

#### 缓存策略
```python
# 缓存上月报表数据（避免重复生成）
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_report_data(template_id, period):
    return generate_report_data(template_id, period)
```

### 3. 文件存储优化

#### 文件压缩
```python
# 对大文件启用压缩
import zipfile

with zipfile.ZipFile('report.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write('report.xlsx')
```

#### 对象存储
```python
# 上传到 OSS/S3（可选）
import boto3

s3 = boto3.client('s3')
s3.upload_file('report.xlsx', 'my-bucket', 'reports/2026/01/report.xlsx')
```

---

## 监控与告警

### 设置监控指标

```python
# 报表生成成功率
success_rate = successful_reports / total_reports * 100

# 报表生成耗时
generation_time = end_time - start_time

# 文件大小监控
file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
```

### 告警规则

1. **生成失败**: 立即告警
2. **生成耗时 > 30分钟**: 告警
3. **文件大小 > 50MB**: 告警
4. **连续3次失败**: 严重告警

---

## 数据迁移

### 导出迁移脚本

```bash
# 运行迁移
python -m alembic upgrade head

# 或使用项目内的迁移
cd migrations
python versions/20260215_add_report_system_tables.py
```

### 初始化默认模板

```python
# scripts/init_report_templates.py

templates = [
    {
        "name": "人员月度工时报表",
        "report_type": "USER_MONTHLY",
        "output_format": "EXCEL",
        "frequency": "MONTHLY",
        "enabled": True
    },
    {
        "name": "部门月度工时报表",
        "report_type": "DEPT_MONTHLY",
        "output_format": "EXCEL",
        "frequency": "MONTHLY",
        "enabled": True
    }
]

for tmpl in templates:
    ReportTemplate(**tmpl).save()
```

---

## 安全建议

1. **文件权限**: 报表文件应设置适当权限，防止未授权访问
2. **下载限流**: 避免恶意批量下载
3. **数据脱敏**: 敏感字段可配置脱敏显示
4. **审计日志**: 记录所有报表生成和下载操作

---

## 联系开发团队

- **技术负责人**: xxx@company.com
- **开发团队**: dev@company.com
- **紧急联系**: 13800138000

---

**文档更新**: 2026-02-15
