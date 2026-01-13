# 跨部门进度查看指南（项目经理实用手册）

**文档版本**: 1.0
**创建日期**: 2026-01-07
**适用角色**: 项目经理、部门主管、管理层

---

## 📋 目录

1. [快速入门](#快速入门)
2. [项目经理如何查看跨部门进度](#项目经理如何查看跨部门进度)
3. [实际API调用示例](#实际api调用示例)
4. [Swagger UI可视化操作](#swagger-ui可视化操作)
5. [返回数据详解](#返回数据详解)
6. [权限说明](#权限说明)
7. [常见场景示例](#常见场景示例)

---

## 快速入门

### 核心端点

```
GET /api/v1/engineers/projects/{project_id}/progress-visibility
```

**功能**: 查看指定项目的跨部门进度全貌

**特点**:
- ✅ **无部门过滤** - 一次查询看到所有部门的进度
- ✅ **实时聚合** - 数据实时计算，不依赖定时任务
- ✅ **多维度统计** - 按部门、按人员、按阶段三个维度
- ✅ **延期预警** - 自动标识延期任务

---

## 项目经理如何查看跨部门进度

### 方式一：Swagger UI（推荐新手）

**步骤**:

1. **启动系统**
   ```bash
   cd /Users/flw/non-standard-automation-pm
   python3 -m uvicorn app.main:app --reload
   ```

2. **打开Swagger UI**
   ```
   浏览器访问: http://localhost:8000/docs
   ```

3. **登录认证**
   - 点击右上角 🔓 **Authorize** 按钮
   - 输入项目经理账号密码（如 `pm_user` / `password123`）
   - 点击 **Authorize** → **Close**

4. **查找端点**
   - 在页面中搜索 `progress-visibility`
   - 或者展开 `engineers` 分组

5. **执行查询**
   - 点击 `GET /api/v1/engineers/projects/{project_id}/progress-visibility`
   - 点击 **Try it out** 按钮
   - 在 `project_id` 输入框中输入项目ID（例如 `1`）
   - 点击 **Execute** 按钮

6. **查看结果**
   - 滚动到 **Response body** 区域
   - 查看JSON格式的跨部门进度数据

### 方式二：命令行（推荐技术人员）

**步骤**:

1. **获取访问令牌**
   ```bash
   TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
       -H "Content-Type: application/json" \
       -d '{
           "username": "pm_user",
           "password": "password123"
       }' | jq -r '.access_token')
   ```

2. **查询跨部门进度**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
       -H "Authorization: Bearer $TOKEN" \
       -H "Content-Type: application/json" | jq
   ```

3. **美化输出**（使用jq工具）
   ```bash
   curl -s -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
       -H "Authorization: Bearer $TOKEN" | jq '.department_progress'
   ```

### 方式三：Postman/Insomnia（推荐测试人员）

**步骤**:

1. **创建登录请求**
   - Method: `POST`
   - URL: `http://localhost:8000/api/v1/auth/login`
   - Body (JSON):
     ```json
     {
       "username": "pm_user",
       "password": "password123"
     }
     ```
   - 发送请求，复制返回的 `access_token`

2. **创建查询请求**
   - Method: `GET`
   - URL: `http://localhost:8000/api/v1/engineers/projects/1/progress-visibility`
   - Headers:
     ```
     Authorization: Bearer <粘贴你的token>
     Content-Type: application/json
     ```
   - 发送请求

---

## 实际API调用示例

### 示例1：查看项目1的跨部门进度

**请求**:
```bash
GET /api/v1/engineers/projects/1/progress-visibility
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应**（完整示例）:
```json
{
  "project_id": 1,
  "project_name": "ICT测试设备-华为",
  "overall_progress": 45.67,
  "project_health": "H2",
  "total_tasks": 24,
  "completed_tasks": 8,
  "in_progress_tasks": 12,
  "pending_tasks": 4,
  "cancelled_tasks": 0,

  "department_progress": [
    {
      "department": "机械部",
      "total_tasks": 10,
      "completed_tasks": 4,
      "in_progress_tasks": 5,
      "pending_tasks": 1,
      "average_progress": 52.3,
      "completion_rate": 40.0,
      "members": {
        "张工": {
          "real_name": "张工",
          "total_tasks": 5,
          "completed_tasks": 2,
          "average_progress": 60.0
        },
        "李工": {
          "real_name": "李工",
          "total_tasks": 5,
          "completed_tasks": 2,
          "average_progress": 44.6
        }
      }
    },
    {
      "department": "电气部",
      "total_tasks": 8,
      "completed_tasks": 3,
      "in_progress_tasks": 4,
      "pending_tasks": 1,
      "average_progress": 41.25,
      "completion_rate": 37.5,
      "members": {
        "王工": {
          "real_name": "王工",
          "total_tasks": 4,
          "completed_tasks": 2,
          "average_progress": 50.0
        },
        "赵工": {
          "real_name": "赵工",
          "total_tasks": 4,
          "completed_tasks": 1,
          "average_progress": 32.5
        }
      }
    },
    {
      "department": "软件部",
      "total_tasks": 6,
      "completed_tasks": 1,
      "in_progress_tasks": 3,
      "pending_tasks": 2,
      "average_progress": 38.33,
      "completion_rate": 16.67,
      "members": {
        "孙工": {
          "real_name": "孙工",
          "total_tasks": 3,
          "completed_tasks": 1,
          "average_progress": 46.67
        },
        "周工": {
          "real_name": "周工",
          "total_tasks": 3,
          "completed_tasks": 0,
          "average_progress": 30.0
        }
      }
    }
  ],

  "assignee_progress": [
    {
      "assignee_id": 101,
      "real_name": "张工",
      "department": "机械部",
      "total_tasks": 5,
      "completed_tasks": 2,
      "in_progress_tasks": 2,
      "pending_tasks": 1,
      "average_progress": 60.0,
      "completion_rate": 40.0
    },
    {
      "assignee_id": 102,
      "real_name": "李工",
      "department": "机械部",
      "total_tasks": 5,
      "completed_tasks": 2,
      "in_progress_tasks": 3,
      "pending_tasks": 0,
      "average_progress": 44.6,
      "completion_rate": 40.0
    },
    {
      "assignee_id": 201,
      "real_name": "王工",
      "department": "电气部",
      "total_tasks": 4,
      "completed_tasks": 2,
      "in_progress_tasks": 2,
      "pending_tasks": 0,
      "average_progress": 50.0,
      "completion_rate": 50.0
    }
  ],

  "stage_progress": {
    "S2-方案设计": {
      "total_tasks": 6,
      "completed_tasks": 3,
      "average_progress": 58.33
    },
    "S3-采购备料": {
      "total_tasks": 8,
      "completed_tasks": 2,
      "average_progress": 35.0
    },
    "S4-加工制造": {
      "total_tasks": 10,
      "completed_tasks": 3,
      "average_progress": 48.5
    }
  },

  "active_delays": [
    {
      "task_id": 1024,
      "task_name": "PLC程序开发",
      "assignee": "赵工",
      "department": "电气部",
      "planned_end_date": "2026-01-05",
      "actual_end_date": null,
      "delay_days": 2,
      "progress": 65
    },
    {
      "task_id": 1056,
      "task_name": "视觉算法优化",
      "assignee": "周工",
      "department": "软件部",
      "planned_end_date": "2026-01-03",
      "actual_end_date": null,
      "delay_days": 4,
      "progress": 40
    }
  ],

  "timestamp": "2026-01-07T10:30:45"
}
```

---

## Swagger UI可视化操作

### 界面截图说明

**步骤1: 找到端点**

在Swagger UI页面中，端点显示为：

```
GET /api/v1/engineers/projects/{project_id}/progress-visibility
跨部门进度可见性视图（核心功能）
```

**步骤2: 展开端点**

点击端点后会显示：

```
Parameters
  project_id * integer (path)
    项目ID

  Example Value | Schema

Security
  HTTPBearer (http, Bearer)
```

**步骤3: 填写参数**

```
project_id: [1]  ← 在这里输入项目ID
```

**步骤4: 查看响应**

```
Response body

{
  "project_id": 1,
  "project_name": "ICT测试设备-华为",
  "overall_progress": 45.67,
  ...
}

Response headers

content-type: application/json; charset=utf-8
```

---

## 返回数据详解

### 一、项目整体信息

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `project_id` | int | 项目ID | `1` |
| `project_name` | str | 项目名称 | `"ICT测试设备-华为"` |
| `overall_progress` | float | 项目整体进度（%） | `45.67` |
| `project_health` | str | 项目健康度 | `"H2"` (H1/H2/H3) |
| `total_tasks` | int | 总任务数 | `24` |
| `completed_tasks` | int | 已完成任务数 | `8` |
| `in_progress_tasks` | int | 进行中任务数 | `12` |
| `pending_tasks` | int | 待开始任务数 | `4` |

**健康度说明**:
- `H1`: ✅ 正常（绿色）- 延期任务 ≤ 10%
- `H2`: ⚠️ 有风险（黄色）- 延期任务 10%-25%
- `H3`: 🔴 阻塞（红色）- 延期任务 > 25%

### 二、部门维度统计（department_progress）

**核心价值**: 项目经理可以一眼看到哪个部门进度快，哪个部门慢

```json
{
  "department": "机械部",           // 部门名称
  "total_tasks": 10,                // 该部门总任务数
  "completed_tasks": 4,             // 已完成数
  "in_progress_tasks": 5,           // 进行中数
  "pending_tasks": 1,               // 待开始数
  "average_progress": 52.3,         // 该部门平均进度（%）
  "completion_rate": 40.0,          // 完成率（%）= 已完成/总任务

  "members": {                      // 该部门成员明细
    "张工": {
      "real_name": "张工",
      "total_tasks": 5,
      "completed_tasks": 2,
      "average_progress": 60.0
    }
  }
}
```

**项目经理如何使用**:
1. 快速对比各部门 `average_progress`，找出进度慢的部门
2. 查看 `completion_rate`，判断哪个部门完成效率低
3. 展开 `members`，定位到具体责任人

### 三、人员维度统计（assignee_progress）

**核心价值**: 跨部门查看所有工程师的进度，不受部门限制

```json
{
  "assignee_id": 101,
  "real_name": "张工",
  "department": "机械部",            // 可以看到该工程师所属部门
  "total_tasks": 5,
  "completed_tasks": 2,
  "in_progress_tasks": 2,
  "pending_tasks": 1,
  "average_progress": 60.0,
  "completion_rate": 40.0
}
```

**项目经理如何使用**:
1. 按 `average_progress` 排序，找出进度最慢的工程师
2. 跨部门对比工程师效率
3. 识别高负荷工程师（`total_tasks` 过多）

### 四、阶段维度统计（stage_progress）

**核心价值**: 从项目阶段角度查看进度

```json
{
  "S2-方案设计": {
    "total_tasks": 6,
    "completed_tasks": 3,
    "average_progress": 58.33
  },
  "S3-采购备料": {
    "total_tasks": 8,
    "completed_tasks": 2,
    "average_progress": 35.0         // ⚠️ 采购阶段进度慢
  }
}
```

**项目经理如何使用**:
1. 识别哪个阶段成为瓶颈
2. 判断是否需要调配资源到慢阶段
3. 预测项目整体完成时间

### 五、延期任务列表（active_delays）

**核心价值**: 自动列出所有延期任务，无需手工统计

```json
{
  "task_id": 1024,
  "task_name": "PLC程序开发",
  "assignee": "赵工",
  "department": "电气部",
  "planned_end_date": "2026-01-05",
  "actual_end_date": null,
  "delay_days": 2,                   // 延期2天
  "progress": 65                     // 当前进度65%
}
```

**项目经理如何使用**:
1. 每日检查 `delay_days`，找出严重延期任务
2. 联系 `assignee` 询问原因
3. 根据 `progress` 判断是否需要介入

---

## 权限说明

### 谁可以查看跨部门进度？

| 角色 | 是否可查看 | 查看范围 | 代码位置 |
|------|-----------|---------|----------|
| **项目经理** | ✅ 可以 | 所有部门进度 | `engineers.py:933` |
| **部门主管** | ✅ 可以 | 所有部门进度 | 无部门过滤逻辑 |
| **工程师** | ✅ 可以 | 所有部门进度 | 只要有Token即可 |
| **未登录用户** | ❌ 不可以 | - | 需要JWT认证 |

### 关键代码验证

**无部门过滤逻辑** ([engineers.py:952-954](app/api/v1/endpoints/engineers.py#L952-L954)):

```python
# ✅ 查询所有任务，无部门过滤
all_tasks = db.query(TaskUnified).filter(
    TaskUnified.project_id == project_id  # 只按项目过滤
).all()

# ❌ 传统做法（有部门过滤，本系统未使用）
# all_tasks = db.query(TaskUnified).filter(
#     TaskUnified.project_id == project_id,
#     User.department == current_user.department  # 部门过滤
# ).all()
```

### 与传统系统的对比

| 场景 | 传统系统 | 工程师进度管理系统 |
|------|---------|-------------------|
| 机械部工程师查看电气部进度 | ❌ 无权限，看不到 | ✅ 可以看到 |
| 项目经理查看所有部门进度 | ⚠️ 需要切换部门或查询多次 | ✅ 一次查询获取所有 |
| 数据实时性 | ⚠️ 依赖定时任务更新 | ✅ 实时计算 |

---

## 常见场景示例

### 场景1: 项目经理周会前准备

**需求**: 准备周会，需要了解项目整体进度和各部门情况

**操作**:
```bash
# 1. 获取项目1的跨部门进度
curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
    -H "Authorization: Bearer $PM_TOKEN" | jq > project_1_progress.json

# 2. 查看整体进度
jq '.overall_progress' project_1_progress.json
# 输出: 45.67

# 3. 查看各部门进度
jq '.department_progress[] | {dept: .department, progress: .average_progress}' project_1_progress.json
# 输出:
# {
#   "dept": "机械部",
#   "progress": 52.3
# }
# {
#   "dept": "电气部",
#   "progress": 41.25
# }
# {
#   "dept": "软件部",
#   "progress": 38.33
# }

# 4. 查看延期任务
jq '.active_delays[] | {task: .task_name, assignee: .assignee, delay: .delay_days}' project_1_progress.json
```

**结论**:
- 项目整体进度45.67%
- 软件部进度最慢（38.33%），需要关注
- 有2个任务延期，需要跟进

### 场景2: 紧急调配资源

**需求**: 电气部人手不足，需要查看哪个部门工程师负载较轻

**操作**:
```bash
# 查看各部门人员负载
curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
    -H "Authorization: Bearer $PM_TOKEN" | \
    jq '.assignee_progress | sort_by(.total_tasks) | reverse | .[] |
        {name: .real_name, dept: .department, tasks: .total_tasks, progress: .average_progress}'
```

**输出**:
```json
{
  "name": "张工",
  "dept": "机械部",
  "tasks": 5,
  "progress": 60.0
}
{
  "name": "李工",
  "dept": "机械部",
  "tasks": 5,
  "progress": 44.6
}
{
  "name": "王工",
  "dept": "电气部",
  "tasks": 4,
  "progress": 50.0
}
```

**决策**: 李工任务数适中但进度较快，可以考虑协助电气部

### 场景3: 识别延期风险

**需求**: 每天早上检查是否有新的延期任务

**操作**:
```bash
# 查看延期任务，按延期天数排序
curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
    -H "Authorization: Bearer $PM_TOKEN" | \
    jq '.active_delays | sort_by(.delay_days) | reverse | .[] |
        {task: .task_name, assignee: .assignee, delay: .delay_days, progress: .progress}'
```

**输出**:
```json
{
  "task": "视觉算法优化",
  "assignee": "周工",
  "delay": 4,
  "progress": 40
}
{
  "task": "PLC程序开发",
  "assignee": "赵工",
  "delay": 2,
  "progress": 65
}
```

**行动**:
1. 优先联系周工，4天延期且进度只有40%，风险高
2. 赵工虽然延期2天，但进度已65%，风险较低

### 场景4: 跨部门协调

**需求**: 软件部依赖电气部的接口文档，需要查看电气部任务进度

**操作**:
```bash
# 查看电气部的任务明细
curl -X GET "http://localhost:8000/api/v1/engineers/projects/1/progress-visibility" \
    -H "Authorization: Bearer $PM_TOKEN" | \
    jq '.department_progress[] | select(.department == "电气部") | .members'
```

**输出**:
```json
{
  "王工": {
    "real_name": "王工",
    "total_tasks": 4,
    "completed_tasks": 2,
    "average_progress": 50.0
  },
  "赵工": {
    "real_name": "赵工",
    "total_tasks": 4,
    "completed_tasks": 1,
    "average_progress": 32.5
  }
}
```

**决策**: 赵工进度慢（32.5%），如果接口文档是赵工负责，需要催促

---

## 总结：项目经理的核心优势

### 传统系统 vs 工程师进度管理系统

| 项目经理需求 | 传统系统 | 工程师进度管理系统 |
|------------|---------|-------------------|
| 查看所有部门进度 | ❌ 需要多次查询或权限申请 | ✅ 一次API调用获取所有 |
| 识别延期任务 | ❌ 手工统计或依赖报表 | ✅ 自动列出延期任务 |
| 跨部门资源调配 | ❌ 数据分散，难以对比 | ✅ 统一视图，易于对比 |
| 数据实时性 | ⚠️ 依赖定时任务（延迟） | ✅ 实时计算（0延迟） |
| 健康度判断 | ❌ 需要手工分析 | ✅ 自动计算H1/H2/H3 |

### 核心价值总结

1. **全局视野** - 一次查询看到所有部门，打破信息孤岛
2. **实时数据** - 工程师更新进度，项目经理立即可见
3. **自动预警** - 延期任务自动标识，无需手工统计
4. **多维分析** - 按部门、按人员、按阶段三个维度统计
5. **决策支持** - 基于数据调配资源，而非凭感觉

---

**文档维护**: 如有疑问或需要补充，请联系开发团队
**相关文档**:
- [WORK_RESULTS_SHOWCASE.md](WORK_RESULTS_SHOWCASE.md) - 系统整体介绍
- [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md) - 代码质量报告
- [UNIT_TEST_RESULTS.md](UNIT_TEST_RESULTS.md) - 单元测试报告
