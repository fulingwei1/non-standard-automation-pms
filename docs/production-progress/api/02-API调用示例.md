# 生产进度模块 - API调用示例

## 1. Python示例

### 1.1 环境准备

```python
import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8000/api/v1"
ACCESS_TOKEN = "your_access_token_here"

# 通用请求头
HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
```

### 1.2 创建工单

```python
def create_work_order():
    """创建生产工单"""
    url = f"{BASE_URL}/production/work-orders"
    
    data = {
        "project_id": 10,
        "process_id": 5,
        "plan_qty": 200,
        "plan_start_date": "2026-02-17T08:00:00",
        "plan_end_date": "2026-02-18T17:00:00",
        "priority": 8,
        "estimated_hours": 16.5,
        "remark": "紧急订单，优先处理"
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    
    if response.status_code == 201:
        result = response.json()
        print(f"工单创建成功: {result['data']['work_order_no']}")
        return result['data']
    else:
        print(f"创建失败: {response.json()['message']}")
        return None
```

### 1.3 提交报工

```python
def submit_work_report(work_order_id, completed_qty):
    """提交工作报告"""
    url = f"{BASE_URL}/production/work-reports"
    
    data = {
        "work_order_id": work_order_id,
        "worker_id": 15,
        "report_type": "PROGRESS",
        "report_time": datetime.now().isoformat(),
        "work_hours": 2.5,
        "completed_qty": completed_qty,
        "qualified_qty": completed_qty - 1,
        "defect_qty": 1,
        "description": f"完成{completed_qty}件，1件不良"
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    return response.json()
```

### 1.4 AI智能排程

```python
def ai_optimize_schedule(workshop_id, order_ids):
    """AI优化排程"""
    url = f"{BASE_URL}/production/schedules/ai-optimize"
    
    data = {
        "workshop_id": workshop_id,
        "plan_date": "2026-02-17",
        "order_ids": order_ids,
        "constraints": {
            "max_overtime_hours": 2,
            "prefer_skill_match": True,
            "deadline_strict": True
        },
        "algorithm": "GENETIC",
        "population_size": 100,
        "max_generations": 200
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    result = response.json()
    
    if result['code'] == 200:
        metrics = result['data']['optimization_metrics']
        print(f"排程优化完成:")
        print(f"  总完工时间: {metrics['makespan']}小时")
        print(f"  资源利用率: {metrics['avg_utilization']*100:.1f}%")
        print(f"  适应度分数: {metrics['fitness_score']:.2f}")
    
    return result['data']
```

---

## 2. JavaScript/TypeScript示例

### 2.1 使用Axios

```typescript
import axios from 'axios';

const API_CLIENT = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
    }
});

// 获取工单列表
async function getWorkOrders(params: WorkOrderQueryParams) {
    try {
        const response = await API_CLIENT.get('/production/work-orders', { params });
        return response.data;
    } catch (error) {
        console.error('获取工单失败:', error);
        throw error;
    }
}

// 创建质检记录
async function createQualityInspection(data: QualityInspectionCreate) {
    try {
        const response = await API_CLIENT.post('/production/quality-inspections', data);
        return response.data;
    } catch (error) {
        console.error('创建质检记录失败:', error);
        throw error;
    }
}

// SPC分析
async function getSPCAnalysis(workOrderId: number) {
    try {
        const response = await API_CLIENT.get('/production/quality-inspections/spc-analysis', {
            params: { work_order_id: workOrderId }
        });
        return response.data;
    } catch (error) {
        console.error('SPC分析失败:', error);
        throw error;
    }
}
```

---

## 3. cURL示例

### 3.1 创建工单

```bash
curl -X POST http://localhost:8000/api/v1/production/work-orders \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 10,
    "process_id": 5,
    "plan_qty": 200,
    "plan_start_date": "2026-02-17T08:00:00",
    "plan_end_date": "2026-02-18T17:00:00",
    "priority": 8,
    "estimated_hours": 16.5
  }'
```

### 3.2 查询工单列表

```bash
curl -X GET "http://localhost:8000/api/v1/production/work-orders?status=IN_PROGRESS&page=1&page_size=20" \
  -H "Authorization: Bearer your_access_token"
```

### 3.3 提交报工

```bash
curl -X POST http://localhost:8000/api/v1/production/work-reports \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "work_order_id": 1001,
    "worker_id": 15,
    "report_type": "PROGRESS",
    "report_time": "2026-02-17T14:00:00",
    "work_hours": 2.5,
    "completed_qty": 20,
    "qualified_qty": 19,
    "defect_qty": 1
  }'
```

---

## 4. 完整业务流程示例

### 4.1 从排程到完工的完整流程

```python
def complete_production_workflow():
    """完整的生产流程示例"""
    
    # Step 1: 创建工单
    print("Step 1: 创建工单...")
    work_order = create_work_order()
    work_order_id = work_order['id']
    
    # Step 2: 派工
    print("Step 2: 派工...")
    assign_work_order(work_order_id, worker_id=15, workstation_id=8)
    
    # Step 3: 开工报工
    print("Step 3: 开工报工...")
    submit_work_report(work_order_id, report_type='START', completed_qty=0)
    
    # Step 4: 进度报工 (多次)
    print("Step 4: 进度报工...")
    for i in range(1, 5):
        submit_work_report(work_order_id, report_type='PROGRESS', completed_qty=50*i)
        time.sleep(2)  # 模拟时间间隔
    
    # Step 5: 质量检验
    print("Step 5: 质量检验...")
    create_quality_inspection(work_order_id, inspection_qty=50)
    
    # Step 6: 完工报工
    print("Step 6: 完工报工...")
    submit_work_report(work_order_id, report_type='COMPLETE', completed_qty=200)
    
    print("生产流程完成！")
```

---

## 5. 错误处理示例

```python
def safe_api_call(func, *args, **kwargs):
    """带错误处理的API调用"""
    try:
        response = func(*args, **kwargs)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_data = response.json()
            print(f"API错误: {error_data.get('message')}")
            print(f"详细信息: {error_data.get('detail')}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("连接错误: 无法连接到服务器")
        return None
    
    except requests.exceptions.Timeout:
        print("请求超时")
        return None
    
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return None
```

---

## 6. 版本历史

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| v1.0 | 2026-02-16 | Team 8 | 初始版本 |
