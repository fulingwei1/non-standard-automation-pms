# 服务工单API测试指南

## 快速开始

### 1. 启动服务器

```bash
cd 非标自动化项目管理系统
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 运行测试脚本

```bash
python3 test_service_apis.py
```

## 测试内容

### 服务工单API

1. **GET /api/v1/service/service-tickets** - 获取服务工单列表
   - 支持分页、筛选、搜索
   - 参数：`page`, `page_size`, `status`, `urgency`, `project_id`, `customer_id`, `keyword`

2. **POST /api/v1/service/service-tickets** - 创建服务工单
   - 自动生成工单号：SRV-yymmdd-xxx
   - 自动创建时间线记录

3. **GET /api/v1/service/service-tickets/{ticket_id}** - 获取工单详情

4. **PUT /api/v1/service/service-tickets/{ticket_id}/assign** - 分配工单
   - 更新状态为 IN_PROGRESS
   - 记录分配时间线

5. **PUT /api/v1/service/service-tickets/{ticket_id}/close** - 关闭工单
   - 更新状态为 CLOSED
   - 记录解决方案、根本原因、预防措施
   - 记录客户满意度

6. **GET /api/v1/service/service-tickets/statistics** - 获取工单统计
   - 返回：总数、待分配、处理中、待验证、已关闭、紧急工单数

### 现场服务记录API

1. **GET /api/v1/service/service-records** - 获取服务记录列表
   - 支持分页、筛选、搜索
   - 参数：`page`, `page_size`, `service_type`, `status`, `project_id`, `customer_id`, `date_from`, `date_to`, `keyword`

2. **POST /api/v1/service/service-records** - 创建服务记录
   - 自动生成记录号：REC-yymmdd-xxx

3. **GET /api/v1/service/service-records/{record_id}** - 获取记录详情

4. **GET /api/v1/service/service-records/statistics** - 获取记录统计
   - 返回：总数、进行中、已完成、已取消、本月服务数、总服务时长

## 手动测试（curl）

### 1. 登录获取Token

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

### 2. 获取服务工单列表

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/service/service-tickets?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 3. 获取服务工单统计

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/service/service-tickets/statistics" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 4. 创建服务工单

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/service/service-tickets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "customer_id": 1,
    "problem_type": "SOFTWARE",
    "problem_desc": "设备控制软件频繁崩溃",
    "urgency": "URGENT",
    "reported_by": "测试用户",
    "reported_time": "2026-01-06T10:00:00"
  }' | python3 -m json.tool
```

### 5. 获取服务记录列表

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/service/service-records?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 6. 创建服务记录

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/service/service-records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "INSTALLATION",
    "project_id": 1,
    "customer_id": 1,
    "service_date": "2026-01-06",
    "service_engineer_id": 1,
    "service_content": "完成设备安装"
  }' | python3 -m json.tool
```

## API文档

启动服务器后，访问以下地址查看完整的API文档：

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

在Swagger UI中，可以找到 `/service` 标签下的所有API端点。

## 注意事项

1. **数据库初始化**：确保数据库已初始化，运行 `python3 init_db.py`
2. **项目/客户数据**：创建工单或记录时，需要确保数据库中存在对应的项目（project_id）和客户（customer_id）
3. **用户数据**：分配工单时，需要确保数据库中存在对应的用户（assignee_id）
4. **Token有效期**：默认24小时，过期后需要重新登录

## 常见问题

### 问题1: 404 Not Found
**原因**：路由未正确注册或URL错误
**解决**：检查 `app/api/v1/api.py` 中是否已注册服务路由

### 问题2: 422 Validation Error
**原因**：请求数据格式不正确或缺少必填字段
**解决**：检查请求体是否符合Schema定义，参考Swagger文档

### 问题3: 500 Internal Server Error
**原因**：数据库表不存在或模型定义有问题
**解决**：
1. 检查数据库表是否已创建
2. 运行数据库迁移或初始化脚本
3. 检查模型定义是否正确

### 问题4: 外键约束错误
**原因**：引用的项目、客户或用户不存在
**解决**：确保数据库中存在对应的项目、客户和用户数据

## 测试数据准备

如果测试时遇到外键约束错误，可以先创建测试数据：

```python
# 创建测试项目
# 创建测试客户
# 创建测试用户
```

或者使用现有的项目、客户和用户ID。



