# 前端常量文件统一迁移指南

## 迁移状态

### ✅ 已完成
- ✅ 创建 `lib/constants/` 目录结构
- ✅ 迁移通用常量到 `lib/constants/common.js`
- ✅ 迁移战略模块常量到 `lib/constants/strategy.js`
- ✅ 迁移财务模块常量到 `lib/constants/finance.js`
- ✅ 更新 Strategy 模块所有文件的引用路径
- ✅ 更新 Invoice 模块所有文件的引用路径

### 🔄 进行中
- 迁移其他模块的常量文件（约160个文件待处理）

### 📋 待处理模块

#### Pages 目录下的常量文件（约100+个）
需要根据业务模块分类迁移到对应的 `lib/constants/` 文件：

- **项目相关**: `ProjectStaffingNeed`, `ProjectTaskList`, `ProjectRoleTypeManagement`, `ProjectRoles`, `ProjectPhaseManagement`, `ProjectStageView`, `ProjectSettlement`, `ProjectClosureManagement` → `lib/constants/project.js`
- **销售相关**: `OpportunityManagement`, `OpportunityBoard`, `LeadAssessment`, `SalesTarget`, `QuotationList`, `QuoteCreateEdit`, `QuoteCostAnalysis`, `BiddingCenter`, `BiddingDetail`, `SalesProjectTrack` → `lib/constants/sales.js`
- **采购相关**: `PurchaseOrders`, `PurchaseOrderDetail`, `PurchaseRequestNew`, `PurchaseRequestDetail`, `PurchaseMaterialCostManagement`, `ProcurementEngineerWorkstation` → `lib/constants/procurement.js`
- **财务相关**: `PaymentManagement`, `PaymentApproval`, `ReceivableManagement`, `CostAccounting`, `CostTemplateManagement`, `FinancialReports` → `lib/constants/finance.js`
- **HR相关**: `HRManagement`, `UserManagement`, `EmployeeProfileList`, `DepartmentManagement`, `OrganizationManagement`, `PositionManagement`, `QualificationManagement`, `LeaveManagement`, `AIStaffMatching` → `lib/constants/hr.js`
- **服务相关**: `CustomerServiceDashboard`, `ServiceRecord`, `ServiceKnowledgeBase`, `ServiceAnalytics`, `CustomerCommunication` → `lib/constants/service.js`
- **客户相关**: `CustomerManagement`, `CustomerList`, `Customer360` → `lib/constants/customer.js`
- **物料相关**: `BOMManagement`, `MaterialTracking`, `MaterialReadiness`, `ShortageManagement`, `ShortageAlert`, `ShortageReportDetail`, `InventoryAnalysis`, `BomAssemblyAttrs`, `AssemblyKitBoard` → `lib/constants/material.js`
- **ECN相关**: `ECNOverdueAlerts` → `lib/constants/ecn.js`
- **审批相关**: `ApprovalCenter`, `ApprovalDesigner`, `ContractApproval`, `PaymentApproval`, `AdministrativeApprovals` → `lib/constants/approval.js`
- **告警相关**: `AlertCenter`, `AlertSubscriptionSettings`, `ExceptionManagement`, `IssueStatisticsSnapshot` → `lib/constants/alert.js`
- **知识库相关**: `KnowledgeBase`, `EngineerKnowledge`, `LessonsLearnedLibrary` → `lib/constants/knowledge.js`
- **其他**: `Timesheet`, `TimesheetBatchOperations`, `WorkLog`, `WorkOrderManagement`, `WorkerManagement`, `WorkshopManagement`, `MachineManagement`, `KitCheck`, `Acceptance`, `AcceptanceExecution`, `AcceptanceTemplateManagement`, `GoodsReceiptNew`, `ArrivalDetail`, `DependencyCheck`, `Settings`, `SchedulerConfigManagement`, `SchedulerMonitoringDashboard`, `PresalesTasks`, `PresalesManagerWorkstation`, `EngineerWorkstation`, `InitiationManagement`, `TechnicalReviewList`, `TechnicalReviewDetail`, `TechnicalAssessment`, `RequirementSurvey`, `SolutionList`, `SolutionDetail`, `RdProjectList`, `RdProjectDetail`, `ProductionPlanList`, `ProductionExceptionList`, `ContractList`, `CpqConfigurator`, `SubstitutionDetail`

#### Components 目录下的常量文件（约60+个）
需要根据组件所属业务模块迁移：

- **销售组件**: `components/sales/`, `components/quote/`, `components/opportunity-board/`, `components/lead-assessment/`, `components/lead-management/`, `components/sales-director/`, `components/sales/team/` → `lib/constants/sales.js`
- **项目组件**: `components/project-detail/`, `components/project-review/` → `lib/constants/project.js`
- **采购组件**: `components/purchase-orders/`, `components/purchase/orders/`, `components/procurement-analysis/`, `components/procurement-manager-dashboard/` → `lib/constants/procurement.js`
- **财务组件**: `components/finance-dashboard/`, `components/payment-management/`, `components/invoice-management/` → `lib/constants/finance.js`
- **客户组件**: `components/customer-360/`, `components/customer-communication/`, `components/customer-satisfaction/`, `components/customer-service/`, `components/customer-service-dashboard/` → `lib/constants/customer.js` 或 `lib/constants/service.js`
- **物料组件**: `components/material-analysis/`, `components/material-readiness/` → `lib/constants/material.js`
- **ECN组件**: `components/ecn/` → `lib/constants/ecn.js`
- **审批组件**: `components/approval-center/` → `lib/constants/approval.js`
- **告警组件**: `components/alert-center/`, `components/alert-statistics/` → `lib/constants/alert.js`
- **知识库组件**: `components/knowledge-base/` → `lib/constants/knowledge.js`
- **其他组件**: `components/hr/`, `components/user-management/`, `components/issue/`, `components/issue-template-management/`, `components/contract-management/`, `components/delivery-management/`, `components/installation-dispatch/`, `components/service-record/`, `components/service/`, `components/serviceTicket/`, `components/worker-workstation/`, `components/schedule-board/`, `components/meeting-management/`

## 迁移步骤

### 1. 分析常量文件
```bash
# 查找所有常量文件
find frontend/src -type f \( -name "constants.js" -o -name "constants.jsx" -o -name "*Constants.js" -o -name "*Constants.jsx" \)
```

### 2. 确定目标模块
根据文件路径和内容，确定应该迁移到哪个 `lib/constants/` 文件。

### 3. 合并常量内容
将相同模块的多个常量文件内容合并到对应的 `lib/constants/模块名.js` 文件中。

### 4. 更新引用路径
查找所有使用该常量的文件，更新导入路径：
```javascript
// 旧路径
import { CONSTANT_NAME } from './constants';
import { CONSTANT_NAME } from '../constants';
import { CONSTANT_NAME } from '../../components/module/constants';

// 新路径
import { CONSTANT_NAME } from '../../lib/constants/module';
// 或
import { CONSTANT_NAME } from '@/lib/constants/module'; // 如果配置了路径别名
```

### 5. 删除旧文件
确认所有引用都已更新后，删除旧的常量文件。

## 迁移脚本示例

可以创建一个脚本来自动化部分迁移工作：

```python
#!/usr/bin/env python3
"""
常量文件迁移脚本
自动将常量文件迁移到 lib/constants/ 目录
"""

import os
import re
from pathlib import Path

# 模块映射规则
MODULE_MAPPING = {
    'sales': ['sales', 'quote', 'opportunity', 'lead', 'bidding'],
    'project': ['project', 'milestone', 'stage'],
    'procurement': ['purchase', 'procurement'],
    'finance': ['invoice', 'payment', 'receivable', 'cost', 'financial'],
    'hr': ['hr', 'user', 'employee', 'department', 'organization', 'position'],
    'service': ['service', 'customer-service'],
    'customer': ['customer'],
    'material': ['material', 'bom', 'shortage', 'inventory'],
    'ecn': ['ecn'],
    'approval': ['approval'],
    'alert': ['alert', 'exception'],
    'knowledge': ['knowledge', 'engineer-knowledge'],
}

def find_constants_files(root_dir):
    """查找所有常量文件"""
    constants_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file in ['constants.js', 'constants.jsx'] or 'Constants' in file:
                constants_files.append(os.path.join(root, file))
    return constants_files

def determine_module(file_path):
    """根据文件路径确定应该迁移到哪个模块"""
    file_path_lower = file_path.lower()
    for module, keywords in MODULE_MAPPING.items():
        if any(keyword in file_path_lower for keyword in keywords):
            return module
    return 'common'  # 默认放到 common

# 使用示例
if __name__ == '__main__':
    root = 'frontend/src'
    constants_files = find_constants_files(root)
    for file_path in constants_files:
        module = determine_module(file_path)
        print(f"{file_path} -> lib/constants/{module}.js")
```

## 注意事项

1. **避免命名冲突**: 合并多个文件时，注意检查是否有同名的常量导出，如有冲突需要重命名。

2. **保持向后兼容**: 旧的 `lib/constants.js` 文件暂时保留，重新导出新目录的内容，确保现有代码不会立即报错。

3. **测试验证**: 每迁移一个模块，都应该运行测试确保功能正常。

4. **逐步迁移**: 建议按模块逐步迁移，不要一次性迁移所有文件，降低风险。

5. **更新文档**: 迁移完成后，更新相关文档说明新的常量使用方式。

## 完成标准

- [ ] 所有常量文件已迁移到 `lib/constants/` 目录
- [ ] 所有引用路径已更新
- [ ] 旧的常量文件已删除
- [ ] 代码测试通过
- [ ] 文档已更新
