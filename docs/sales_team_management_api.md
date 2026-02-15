# 销售团队管理 API 文档

## 概述

销售团队管理模块提供了完整的销售团队组织架构、销售目标管理和销售区域管理功能。

## 基础路径

- 销售团队：`/api/v1/sales-teams`
- 销售目标：`/api/v1/sales-targets`
- 销售区域：`/api/v1/sales-regions`

---

## 一、销售团队管理

### 1.1 创建团队

**请求**
```http
POST /api/v1/sales-teams
Content-Type: application/json

{
  "team_code": "T001",
  "team_name": "华东团队",
  "team_type": "REGION",
  "description": "负责华东区域销售",
  "department_id": 1,
  "leader_id": 10,
  "parent_team_id": null,
  "is_active": true,
  "sort_order": 0
}
```

**响应**
```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 1,
    "team_code": "T001",
    "team_name": "华东团队",
    "team_type": "REGION",
    "description": "负责华东区域销售",
    "created_at": "2026-02-15T10:00:00"
  }
}
```

### 1.2 获取团队列表

**请求**
```http
GET /api/v1/sales-teams?skip=0&limit=100&team_type=REGION&is_active=true
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "team_code": "T001",
      "team_name": "华东团队",
      "team_type": "REGION",
      "leader_name": "张三",
      "member_count": 5
    }
  ]
}
```

### 1.3 获取团队组织树

**请求**
```http
GET /api/v1/sales-teams/tree
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "team_code": "T001",
      "team_name": "销售总部",
      "sub_teams": [
        {
          "id": 2,
          "team_code": "T002",
          "team_name": "华东分部",
          "sub_teams": []
        }
      ]
    }
  ]
}
```

### 1.4 获取团队详情

**请求**
```http
GET /api/v1/sales-teams/1
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": 1,
    "team_code": "T001",
    "team_name": "华东团队",
    "team_type": "REGION",
    "leader_id": 10,
    "leader_name": "张三",
    "member_count": 5
  }
}
```

### 1.5 更新团队

**请求**
```http
PUT /api/v1/sales-teams/1
Content-Type: application/json

{
  "team_name": "华东大区",
  "description": "更新后的描述"
}
```

### 1.6 删除团队

**请求**
```http
DELETE /api/v1/sales-teams/1
```

**响应**
```json
{
  "code": 200,
  "message": "删除成功"
}
```

### 1.7 添加团队成员

**请求**
```http
POST /api/v1/sales-teams/1/members
Content-Type: application/json

{
  "team_id": 1,
  "user_id": 20,
  "role": "MEMBER",
  "is_primary": true,
  "remark": "销售骨干"
}
```

### 1.8 获取团队成员列表

**请求**
```http
GET /api/v1/sales-teams/1/members?is_active=true
```

### 1.9 移除团队成员

**请求**
```http
DELETE /api/v1/sales-teams/1/members/20
```

### 1.10 更新成员角色

**请求**
```http
PUT /api/v1/sales-teams/1/members/20/role
Content-Type: application/json

{
  "role": "LEADER"
}
```

---

## 二、销售目标管理

### 2.1 创建目标

**请求 - 公司目标**
```http
POST /api/v1/sales-targets
Content-Type: application/json

{
  "target_period": "year",
  "target_year": 2026,
  "target_type": "company",
  "sales_target": "10000000.00",
  "payment_target": "8000000.00",
  "new_customer_target": 50,
  "lead_target": 500,
  "opportunity_target": 200,
  "deal_target": 100,
  "description": "2026年度公司销售目标"
}
```

**请求 - 团队目标**
```http
POST /api/v1/sales-targets
Content-Type: application/json

{
  "target_period": "month",
  "target_year": 2026,
  "target_month": 3,
  "target_type": "team",
  "team_id": 1,
  "sales_target": "500000.00",
  "payment_target": "400000.00"
}
```

**请求 - 个人目标**
```http
POST /api/v1/sales-targets
Content-Type: application/json

{
  "target_period": "quarter",
  "target_year": 2026,
  "target_quarter": 1,
  "target_type": "personal",
  "user_id": 10,
  "sales_target": "100000.00",
  "deal_target": 10
}
```

### 2.2 获取目标列表

**请求**
```http
GET /api/v1/sales-targets?target_type=team&target_year=2026&target_month=3&skip=0&limit=100
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": [
    {
      "id": 1,
      "target_period": "month",
      "target_year": 2026,
      "target_month": 3,
      "target_type": "team",
      "team_id": 1,
      "team_name": "华东团队",
      "sales_target": "500000.00",
      "actual_sales": "300000.00",
      "completion_rate": "60.00"
    }
  ]
}
```

### 2.3 获取目标详情

**请求**
```http
GET /api/v1/sales-targets/1
```

### 2.4 更新目标

**请求**
```http
PUT /api/v1/sales-targets/1
Content-Type: application/json

{
  "actual_sales": "350000.00",
  "actual_payment": "280000.00",
  "actual_deals": 12
}
```

### 2.5 删除目标

**请求**
```http
DELETE /api/v1/sales-targets/1
```

### 2.6 手动分解目标

**请求**
```http
POST /api/v1/sales-targets/1/breakdown
Content-Type: application/json

{
  "breakdown_items": [
    {
      "target_type": "team",
      "team_id": 2,
      "sales_target": "3000000.00",
      "payment_target": "2400000.00",
      "new_customer_target": 20
    },
    {
      "target_type": "team",
      "team_id": 3,
      "sales_target": "2000000.00",
      "payment_target": "1600000.00",
      "new_customer_target": 15
    }
  ]
}
```

**响应**
```json
{
  "code": 200,
  "message": "分解成功",
  "data": {
    "parent_target_id": 1,
    "breakdown_count": 2,
    "created_targets": [
      {
        "id": 10,
        "team_id": 2,
        "sales_target": "3000000.00"
      },
      {
        "id": 11,
        "team_id": 3,
        "sales_target": "2000000.00"
      }
    ]
  }
}
```

### 2.7 自动分解目标

**请求**
```http
POST /api/v1/sales-targets/1/auto-breakdown
Content-Type: application/json

{
  "breakdown_method": "EQUAL"
}
```

**响应**
```json
{
  "code": 200,
  "message": "自动分解成功",
  "data": {
    "parent_target_id": 1,
    "breakdown_count": 3,
    "created_targets": [...]
  }
}
```

### 2.8 获取分解树

**请求**
```http
GET /api/v1/sales-targets/1/breakdown-tree
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "id": 1,
    "target_type": "company",
    "sales_target": 10000000.00,
    "actual_sales": 6500000.00,
    "completion_rate": 65.00,
    "sub_targets": [
      {
        "id": 10,
        "target_type": "team",
        "team_id": 2,
        "sales_target": 3000000.00,
        "sub_targets": []
      }
    ]
  }
}
```

### 2.9 团队排名

**请求**
```http
GET /api/v1/sales-targets/stats/team-ranking?target_year=2026&target_month=3
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "period": "2026-3",
    "rankings": [
      {
        "rank": 1,
        "team_id": 1,
        "sales_target": "500000.00",
        "actual_sales": "520000.00",
        "completion_rate": "104.00"
      },
      {
        "rank": 2,
        "team_id": 2,
        "sales_target": "400000.00",
        "actual_sales": "380000.00",
        "completion_rate": "95.00"
      }
    ]
  }
}
```

### 2.10 个人排名

**请求**
```http
GET /api/v1/sales-targets/stats/personal-ranking?target_year=2026&target_month=3
```

### 2.11 完成趋势

**请求**
```http
GET /api/v1/sales-targets/stats/completion-trend?target_id=1
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "target_id": 1,
    "trend_data": [
      {
        "date": "2026-03-01",
        "completion_rate": "20.00",
        "actual_sales": "100000.00",
        "target_sales": "500000.00"
      },
      {
        "date": "2026-03-15",
        "completion_rate": "60.00",
        "actual_sales": "300000.00",
        "target_sales": "500000.00"
      }
    ]
  }
}
```

### 2.12 完成率分布

**请求**
```http
GET /api/v1/sales-targets/stats/distribution?target_year=2026&target_month=3
```

**响应**
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "period": "2026-3",
    "distribution": [
      {"range_label": "0-20%", "count": 2},
      {"range_label": "20-40%", "count": 5},
      {"range_label": "40-60%", "count": 8},
      {"range_label": "60-80%", "count": 6},
      {"range_label": "80-100%", "count": 4},
      {"range_label": "100%+", "count": 3}
    ]
  }
}
```

---

## 三、销售区域管理

### 3.1 创建区域

**请求**
```http
POST /api/v1/sales-regions
Content-Type: application/json

{
  "region_code": "R001",
  "region_name": "华东区",
  "provinces": ["江苏", "浙江", "上海"],
  "cities": ["南京", "杭州", "上海"],
  "description": "华东区域",
  "level": 1,
  "is_active": true
}
```

### 3.2 获取区域列表

**请求**
```http
GET /api/v1/sales-regions?skip=0&limit=100&is_active=true
```

### 3.3 获取区域详情

**请求**
```http
GET /api/v1/sales-regions/1
```

### 3.4 更新区域

**请求**
```http
PUT /api/v1/sales-regions/1
Content-Type: application/json

{
  "region_name": "华东大区",
  "cities": ["南京", "杭州", "上海", "苏州"]
}
```

### 3.5 分配团队

**请求**
```http
POST /api/v1/sales-regions/1/assign-team
Content-Type: application/json

{
  "team_id": 1,
  "leader_id": 10
}
```

**响应**
```json
{
  "code": 200,
  "message": "分配成功",
  "data": {
    "id": 1,
    "region_code": "R001",
    "region_name": "华东区",
    "team_id": 1,
    "leader_id": 10
  }
}
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 权限说明

| 权限代码 | 说明 |
|----------|------|
| `sales_team:view` | 查看销售团队 |
| `sales_team:create` | 创建销售团队 |
| `sales_team:update` | 更新销售团队 |
| `sales_team:delete` | 删除销售团队 |
| `sales_target:view` | 查看销售目标 |
| `sales_target:create` | 创建销售目标 |
| `sales_target:update` | 更新销售目标 |
| `sales_target:delete` | 删除销售目标 |
| `sales_region:view` | 查看销售区域 |
| `sales_region:create` | 创建销售区域 |
| `sales_region:update` | 更新销售区域 |
