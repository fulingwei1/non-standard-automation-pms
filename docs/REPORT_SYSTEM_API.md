# 工时报表自动生成系统 - API 文档

**版本**: 1.0.0  
**创建时间**: 2026-02-15

---

## 📚 目录

- [概述](#概述)
- [认证](#认证)
- [报表模板管理](#报表模板管理)
- [报表生成](#报表生成)
- [报表归档管理](#报表归档管理)
- [收件人管理](#收件人管理)
- [错误码](#错误码)

---

## 概述

工时报表自动生成系统提供了一套完整的 RESTful API，用于管理报表模板、生成报表、查询归档和管理收件人。

**Base URL**: `/api/v1/reports`

---

## 认证

所有 API 请求都需要 JWT Token 认证。

```bash
Authorization: Bearer <your_jwt_token>
```

---

## 报表模板管理

### 1. 创建报表模板

**接口**: `POST /templates`  
**权限**: HR/Admin

**请求体**:
```json
{
  "name": "人员月度工时报表",
  "report_type": "USER_MONTHLY",
  "description": "每月统计所有人员的工时情况",
  "config": {
    "fields": ["user_name", "total_hours", "work_days"],
    "filters": {
      "department_ids": [1, 2, 3]
    }
  },
  "output_format": "EXCEL",
  "frequency": "MONTHLY",
  "enabled": true
}
```

**响应**:
```json
{
  "code": 0,
  "message": "报表模板创建成功",
  "data": {
    "id": 1,
    "name": "人员月度工时报表",
    "report_type": "USER_MONTHLY",
    "enabled": true
  }
}
```

---

### 2. 获取模板列表

**接口**: `GET /templates`  
**权限**: HR/Manager

**查询参数**:
- `report_type` (可选): 报表类型筛选
- `enabled` (可选): 启用状态筛选
- `page` (默认 1): 页码
- `page_size` (默认 20): 每页数量

**响应**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "name": "人员月度工时报表",
        "report_type": "USER_MONTHLY",
        "output_format": "EXCEL",
        "frequency": "MONTHLY",
        "enabled": true,
        "created_at": "2026-02-01T10:00:00"
      }
    ]
  }
}
```

---

### 3. 获取模板详情

**接口**: `GET /templates/{template_id}`

**响应**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "id": 1,
    "name": "人员月度工时报表",
    "report_type": "USER_MONTHLY",
    "description": "...",
    "config": {...},
    "output_format": "EXCEL",
    "frequency": "MONTHLY",
    "enabled": true,
    "recipients": [
      {
        "id": 1,
        "recipient_type": "USER",
        "recipient_id": 10,
        "delivery_method": "EMAIL",
        "enabled": true
      }
    ]
  }
}
```

---

### 4. 更新模板

**接口**: `PUT /templates/{template_id}`  
**权限**: HR/Admin

**请求体**: (所有字段可选)
```json
{
  "name": "更新后的名称",
  "description": "更新后的描述",
  "enabled": false
}
```

---

### 5. 删除模板

**接口**: `DELETE /templates/{template_id}`  
**权限**: Admin only

---

### 6. 启用/禁用模板

**接口**: `POST /templates/{template_id}/toggle`

**响应**:
```json
{
  "code": 0,
  "message": "报表模板已启用",
  "data": {
    "enabled": true
  }
}
```

---

## 报表生成

### 7. 手动生成报表

**接口**: `POST /generate`

**请求体**:
```json
{
  "template_id": 1,
  "period": "2026-01"
}
```

**响应**:
```json
{
  "code": 0,
  "message": "报表生成成功",
  "data": {
    "archive_id": 101,
    "file_path": "/reports/2026/01/人员月度工时报表_2026-01.xlsx",
    "file_size": 1024567,
    "row_count": 150
  }
}
```

---

### 8. 预览报表数据

**接口**: `GET /preview`

**查询参数**:
- `template_id`: 模板ID
- `period`: 报表周期 (格式: YYYY-MM)
- `limit` (默认 50): 返回的数据行数

**响应**:
```json
{
  "code": 0,
  "message": "预览成功",
  "data": {
    "summary": [
      {
        "user_name": "张三",
        "total_hours": 160.0,
        "work_days": 20
      }
    ],
    "detail": [...],
    "total_summary_rows": 150,
    "total_detail_rows": 3000,
    "period": "2026-01"
  }
}
```

---

### 9. 导出报表

**接口**: `GET /export`

**查询参数**:
- `template_id`: 模板ID
- `period`: 报表周期
- `format` (默认 excel): 导出格式

**响应**: 同 `/generate`

---

## 报表归档管理

### 10. 获取归档列表

**接口**: `GET /archives`

**查询参数**:
- `template_id` (可选): 模板ID
- `report_type` (可选): 报表类型
- `period` (可选): 报表周期
- `status` (可选): 状态 (SUCCESS/FAILED)
- `page` (默认 1): 页码
- `page_size` (默认 20): 每页数量

**响应**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 101,
        "template_id": 1,
        "report_type": "USER_MONTHLY",
        "period": "2026-01",
        "file_path": "/reports/2026/01/report.xlsx",
        "file_size": 1024567,
        "row_count": 150,
        "generated_at": "2026-02-01T09:00:00",
        "generated_by": "SYSTEM",
        "status": "SUCCESS",
        "download_count": 5
      }
    ]
  }
}
```

---

### 11. 获取归档详情

**接口**: `GET /archives/{archive_id}`

**响应**:
```json
{
  "code": 0,
  "message": "查询成功",
  "data": {
    "id": 101,
    "template_id": 1,
    "template_name": "人员月度工时报表",
    "report_type": "USER_MONTHLY",
    "period": "2026-01",
    "file_path": "/reports/2026/01/report.xlsx",
    "file_size": 1024567,
    "row_count": 150,
    "generated_at": "2026-02-01T09:00:00",
    "generated_by": "SYSTEM",
    "status": "SUCCESS",
    "download_count": 5
  }
}
```

---

### 12. 下载报表

**接口**: `GET /archives/{archive_id}/download`

**响应**: 直接返回文件流 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

---

### 13. 批量下载报表

**接口**: `POST /archives/batch-download`

**请求体**:
```json
{
  "archive_ids": [101, 102, 103]
}
```

**响应**:
```json
{
  "code": 0,
  "message": "批量下载准备完成",
  "data": {
    "files": [
      {
        "id": 101,
        "file_path": "/reports/2026/01/report_101.xlsx",
        "period": "2026-01"
      }
    ]
  }
}
```

---

## 收件人管理

### 14. 添加收件人

**接口**: `POST /templates/{template_id}/recipients`

**请求体**:
```json
{
  "recipient_type": "USER",
  "recipient_id": 10,
  "delivery_method": "EMAIL",
  "enabled": true
}
```

**收件人类型**:
- `USER`: 用户
- `ROLE`: 角色
- `DEPT`: 部门
- `EMAIL`: 外部邮箱

**分发方式**:
- `EMAIL`: 邮件
- `WECHAT`: 企业微信
- `DOWNLOAD`: 下载链接

---

### 15. 删除收件人

**接口**: `DELETE /recipients/{recipient_id}`

---

## 错误码

| 错误码 | 说明 |
|-------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 枚举值

### 报表类型 (ReportType)
- `USER_MONTHLY`: 人员月度工时报表
- `DEPT_MONTHLY`: 部门月度工时报表
- `PROJECT_MONTHLY`: 项目月度工时报表
- `COMPANY_MONTHLY`: 公司整体工时报表
- `OVERTIME_MONTHLY`: 加班统计报表

### 输出格式 (OutputFormat)
- `EXCEL`: Excel格式
- `PDF`: PDF格式
- `CSV`: CSV格式

### 生成频率 (Frequency)
- `MONTHLY`: 月度
- `QUARTERLY`: 季度
- `YEARLY`: 年度

---

## 示例代码

### Python

```python
import requests

# 获取模板列表
response = requests.get(
    'http://localhost:8000/api/v1/reports/templates',
    headers={'Authorization': f'Bearer {token}'}
)
templates = response.json()['data']['items']

# 生成报表
response = requests.post(
    'http://localhost:8000/api/v1/reports/generate',
    json={'template_id': 1, 'period': '2026-01'},
    headers={'Authorization': f'Bearer {token}'}
)
result = response.json()

# 下载报表
archive_id = result['data']['archive_id']
response = requests.get(
    f'http://localhost:8000/api/v1/reports/archives/{archive_id}/download',
    headers={'Authorization': f'Bearer {token}'}
)
with open('report.xlsx', 'wb') as f:
    f.write(response.content)
```

### cURL

```bash
# 获取模板列表
curl -X GET "http://localhost:8000/api/v1/reports/templates" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 生成报表
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template_id": 1, "period": "2026-01"}'

# 下载报表
curl -X GET "http://localhost:8000/api/v1/reports/archives/101/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o report.xlsx
```

---

**文档更新**: 2026-02-15
