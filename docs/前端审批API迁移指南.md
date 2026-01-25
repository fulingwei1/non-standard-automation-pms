# 前端审批 API 迁移指南

## 概述

统一审批系统已部署，前端需要从旧的审批 API 迁移到新的统一 API。

## 迁移时间线

- **Phase 1** (立即): 使用新的统一审批服务
- **Phase 2** (1-2周): 更新审批组件以支持委托功能
- **Phase 3** (未来): 完全移除旧审批 API 调用

## 统一审批服务

### 新文件位置

```
frontend/src/services/api/approval.js
```

### 导入方式

```javascript
import unifiedApprovalApi from "../services/api/approval";
// 或
import { submitApproval, approveApproval, rejectApproval, delegateApproval } from "../services/api/approval";
```

### API 方法

#### 1. 提交审批

**ECN 审批**:
```javascript
import { submitEcnApproval } from "../services/api/approval";

const result = await submitEcnApproval(
  ecn_id,  // ECN ID
  "设计变更审批",  // 标题（可选）
  "需要添加安全传感器...",  // 摘要（可选）
  "NORMAL",  // 紧急程度：NORMAL/URGENT/CRITICAL
  [10, 15, 20]  // 抄送人ID列表（可选）
);

// 返回: { instance_id, instance_no, status, entity_type, entity_id, submitted_at }
```

**报价审批**:
```javascript
import { submitQuoteApproval } from "../services/api/approval";

const result = await submitQuoteApproval(
  quote_id,  // 报价ID
  "报价审批",  // 标题
  "项目金额 35 万元",  // 摘要
  "NORMAL",
  []
);
```

**合同审批**:
```javascript
import { submitContractApproval } from "../services/api/approval";

const result = await submitContractApproval(
  contract_id,  // 合同ID
  "合同审批",
  "项目总金额 120 万元",
  "URGENT",
  []
);
```

**发票审批**:
```javascript
import { submitInvoiceApproval } from "../services/api/approval";

const result = await submitInvoiceApproval(
  invoice_id,  // 发票ID
  "发票审批",
  "根据合同开票，金额 40 万元",
  "NORMAL",
  []
);
```

#### 2. 审批操作

**通过审批**:
```javascript
import { approveApproval } from "../services/api/approval";

const result = await approveApproval(
  instance_id,  // 审批实例ID（注意：不是 approvalId）
  "同意该变更"  // 审批意见
);

// 返回: { instance_id, instance_no, status, current_level, progress }
```

**驳回审批**:
```javascript
import { rejectApproval } from "../services/api/approval";

const result = await rejectApproval(
  instance_id,
  "设计不符合要求，请重新评估"
);
```

**委托审批（新功能）**:
```javascript
import { delegateApproval } from "../services/api/approval";

const result = await delegateApproval(
  instance_id,
  delegate_to_id,  // 被委托人ID
  "因外出，委托给王经理处理"
);
```

**撤回审批**:
```javascript
import { withdrawApproval } from "../services/api/approval";

const result = await withdrawApproval(
  instance_id,
  "需要补充资料"
);
```

#### 3. 查询接口

**我的待审批任务**:
```javascript
import { getMyApprovalTasks } from "../services/api/approval";

const result = await getMyApprovalTasks();

// 返回: { total, pending, tasks, total_levels, current_level, progress }
```

**审批历史**:
```javascript
import { getApprovalHistory } from "../services/api/approval";

const history = await getApprovalHistory(instance_id);
```

**审批详情**:
```javascript
import { getApprovalDetail } from "../services/api/approval";

const detail = await getApprovalDetail(instance_id);
```

## 状态映射

统一审批系统使用新的状态枚举：

| 旧状态 | 新状态 | 说明 |
|---------|--------|------|
| SUBMITTED | PENDING | 已提交，等待审批 |
| EVALUATING | IN_PROGRESS | 评审中 |
| EVALUATED | IN_PROGRESS | 已评审，等待审批 |
| PENDING_APPROVAL | PENDING | 等待当前节点审批 |
| APPROVED | APPROVED | 审批通过 |
| REJECTED | REJECTED | 审批驳回 |
| WITHDRAWN | WITHDRAWN | 已撤回 |
| DELEGATED | DELEGATED | 已委托（新增） |

## 工具函数

### 1. 获取状态配置

```javascript
import { getStatusConfig } from "../services/api/approval";

const config = getStatusConfig("PENDING");
// { label: "待审批", color: "orange", icon: "⏳" }
```

### 2. 计算审批进度

```javascript
import { calculateProgress } from "../services/api/approval";

const progress = calculateProgress(current_level, total_levels);
// 返回 0-100 的百分比
```

## 迁移步骤

### Phase 1: 最小迁移（立即）

1. **ECN 组件更新**:
   ```diff
   - import { ecnApi } from "../services/api/ecn";
   + import { submitEcnApproval, approveApproval, rejectApproval } from "../services/api/approval";

   - await ecnApi.createApproval(id, data);
   + const { instance_id } = await submitEcnApproval(id, title, summary);
   ```

2. **报价组件更新**:
   ```diff
   - import salesApi from "../services/api/sales";
   + import { submitQuoteApproval } from "../services/api/approval";

   - await salesApi.approve(id, data);
   + await approveApproval(instance_id, comment);
   ```

3. **合同/发票组件更新**:
   ```diff
   - await salesApi.approve(id, params);
   + await approveApproval(instance_id, comment);
   ```

### Phase 2: 增强功能（1-2周）

1. **添加委托审批按钮**:
   ```javascript
   // 在审批操作区域添加委托按钮
   <Button onClick={() => handleDelegate()}>
     委托
   </Button>

   const handleDelegate = async () => {
     const { delegate_to_id, comment } = await showDelegateDialog();
     await delegateApproval(instance_id, delegate_to_id, comment);
     refreshApprovalDetail();
   };
   ```

2. **更新进度显示**:
   ```javascript
   // 使用新的进度计算
   const progress = calculateProgress(current_level, total_levels);
   <Progress percent={progress} />
   ```

### Phase 3: 清理（未来）

1. **移除旧 API 调用**:
   - 删除 `ecnApi.getApprovals()`
   - 删除 `salesApi.approve()`
   - 删除旧的审批相关服务方法

2. **统一组件**:
   - 创建通用的审批组件
   - 统一审批操作按钮
   - 统一审批历史显示

## 常见问题

### Q1: 如何获取 instance_id？

A1: 提交审批时，响应中会返回 `instance_id`，需要保存到组件状态中。

```javascript
const [instanceId, setInstanceId] = useState(null);

const handleSubmit = async () => {
  const result = await submitEcnApproval(ecnId);
  setInstanceId(result.instance_id);
};
```

### Q2: 委托审批如何实现？

A2: 新的统一 API 已经支持委托，只需：
1. 显示被委托人选择器
2. 调用 `delegateApproval(instance_id, delegate_to_id, comment)`
3. 刷新审批详情

### Q3: 旧的 approval_id 还能用吗？

A3: 不推荐。旧的审批 API 已经被废弃，应该使用新的统一 API。

### Q4: 如何测试迁移？

A4:
1. 启动前端：`pnpm dev`
2. 打开浏览器控制台，检查 API 请求
3. 验证请求路径为 `/api/v1/approvals/`
4. 验证响应数据格式正确

### Q5: 迁移后旧的 API 会失效吗？

A5: 短期内不会。旧的 API 端点仍然存在，但建议尽快迁移以避免未来的兼容性问题。

## 测试清单

- [ ] ECN 提交审批成功
- [ ] 报价提交审批成功
- [ ] 合同提交审批成功
- [ ] 发票提交审批成功
- [ ] 通过审批功能正常
- [ ] 驳回审批功能正常
- [ ] 委托审批功能正常
- [ ] 撤回审批功能正常
- [ ] 查询待审批任务正常
- [ ] 审批历史查询正常
- [ ] 审批详情查询正常
- [ ] 状态显示正确（使用新的状态枚举）
- [ ] 进度计算正确

## 需要帮助？

如有问题，请查看：
- 统一审批系统文档：`docs/统一审批系统迁移指南.md`
- API 文档：`http://127.0.0.1:8000/docs`
- 迁移指南本文件

---

**迁移完成时间**: 2026-01-25
**版本**: v1.0
