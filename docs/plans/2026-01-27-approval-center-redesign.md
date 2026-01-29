# 审批中心改造设计方案

## 概述

将审批中心从 mock 数据迁移到真实 API，并添加节点级进度可视化（垂直时间线），让申请人能够看到审批流程当前停在哪一级。

## 用户视角

- **审批人**：查看待我审批的任务，快速处理
- **申请人**：追踪我发起的审批进度，了解卡点
- **管理员**：查看已处理记录，抄送知会

## 架构设计

### 改造范围

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `ApprovalCenter.jsx` | 重构 | 替换 mock 数据，接入真实 API，调整标签页结构 |
| `ApprovalDetailPage.jsx` | 新建 | 独立详情页，左右两栏布局 |
| `ApprovalTimeline.jsx` | 新建 | 时间线组件，展示审批流程进度 |
| `useApprovalCenter.js` | 重构 | 改用真实 API 调用 |
| 路由配置 | 修改 | 添加 `/approvals/:id` 路由 |

### 数据流

```
前端                                    后端
────────────────────────────────────────────────
ApprovalCenter
  ├─ 待我审批 ──────────► /pending/mine
  ├─ 我发起的 ──────────► /pending/initiated
  ├─ 抄送我的 ──────────► /pending/cc
  ├─ 已处理 ────────────► /pending/processed
  └─ 统计数字 ──────────► /pending/counts

ApprovalDetailPage
  └─ 详情+时间线 ───────► /instances/{id}
```

## 审批中心页面

### 标签页结构

| 标签页 | 对应 API | 说明 |
|--------|----------|------|
| 待我审批 | `/pending/mine` | 审批人视角，需要我处理的任务 |
| 我发起的 | `/pending/initiated` | 申请人视角，我提交的审批进度 |
| 抄送我的 | `/pending/cc` | 知会项，可标记已读 |
| 已处理 | `/pending/processed` | 我审批过的历史记录 |

### 列表卡片字段

| 字段 | 来源 | 说明 |
|------|------|------|
| 标题 | `instance_title` | 审批标题 |
| 编号 | `instance_no` | AP2501250001 格式 |
| 类型 | `entity_type` | ECN/QUOTE/CONTRACT/INVOICE |
| 紧急程度 | `instance_urgency` | 普通/紧急/特急，用颜色区分 |
| 当前节点 | `node_name` | 如"技术评审"、"部门会签" |
| 发起人/时间 | `initiator_name` + `created_at` | 张三 · 2026-01-25 |
| 操作按钮 | - | [查看详情] [通过] [驳回]（仅待审批显示） |

### 筛选条件

- 紧急程度筛选（全部/普通/紧急/特急）
- 审批类型筛选（全部/ECN/报价/合同/发票）
- 关键词搜索（标题、编号）

## 详情页设计

### 路由

```
/approvals/:id → ApprovalDetailPage.jsx
```

### 布局（左右两栏）

#### 左侧 - 基本信息 + 操作

- 审批编号、标题、发起人、发起时间
- 紧急程度、当前状态、当前节点
- 关联业务（可跳转到业务详情）
- 审批摘要
- 审批操作区（仅当前审批人可见）：审批意见输入框 + [通过] [驳回] [委托]
- 申请人操作区（仅发起人可见）：[撤回申请] [催办]

#### 右侧 - 时间线

垂直时间线展示完整审批流程。

## 时间线组件设计

### 节点状态图标

| 图标 | 状态 | 颜色 |
|------|------|------|
| ● | 已提交 | 蓝色 |
| ✓ | 已通过 | 绿色 |
| ✗ | 已驳回 | 红色 |
| ◎ | 进行中（当前节点） | 黄色/橙色，带动画 |
| ○ | 待处理（未来节点） | 灰色 |
| ↩ | 已撤回 | 灰色 |

### 节点信息字段

每个节点显示：
- 节点名称
- 操作人（姓名 + 角色）
- 操作时间
- 耗时（该节点处理用时）
- 审批意见
- 附件（如果有）
- 委托信息（如果有委托，显示原审批人和被委托人）

### 数据结构

```typescript
interface TimelineNode {
  node_name: string;
  status: 'completed' | 'current' | 'pending' | 'rejected';
  operator_name?: string;
  operator_role?: string;
  action_time?: string;
  duration?: string;
  comment?: string;
  attachments?: Array<{name: string, url: string}>;
  delegate_info?: {
    from: string;
    to: string;
  };
}
```

## 实现计划

### 文件清单

| 序号 | 文件路径 | 操作 |
|------|----------|------|
| 1 | `frontend/src/components/approval/ApprovalTimeline.jsx` | 新建 |
| 2 | `frontend/src/pages/ApprovalDetailPage.jsx` | 新建 |
| 3 | `frontend/src/pages/ApprovalCenter/hooks/useApprovalCenter.js` | 重构 |
| 4 | `frontend/src/pages/ApprovalCenter.jsx` | 重构 |
| 5 | 路由配置 | 修改 |

### 实现顺序

1. ApprovalTimeline 组件（独立，可单独测试）
2. ApprovalDetailPage 页面（依赖时间线组件）
3. useApprovalCenter hook（API 调用逻辑）
4. ApprovalCenter 页面重构（整合所有改动）
5. 路由配置 + 测试验收

## API 依赖

需要调用的后端 API（均已存在）：

- `GET /api/v1/approvals/pending/mine` - 待我审批
- `GET /api/v1/approvals/pending/initiated` - 我发起的
- `GET /api/v1/approvals/pending/cc` - 抄送我的
- `GET /api/v1/approvals/pending/processed` - 已处理
- `GET /api/v1/approvals/pending/counts` - 统计数量
- `GET /api/v1/approvals/instances/{id}` - 详情（含 tasks + logs）
- `POST /api/v1/approvals/tasks/{task_id}/approve` - 通过
- `POST /api/v1/approvals/tasks/{task_id}/reject` - 驳回
