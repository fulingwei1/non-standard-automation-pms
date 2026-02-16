# SQLAlchemy Relationship 修复报告

生成时间: 2026-02-16 15:27:44.013339

## 修复统计

- 总计: 13
- 成功: 2
- 失败: 0
- 需手动处理: 3
- 已存在: 8

## 修复详情

### 修复 1: class_name_conflict - manual_required

**类名**: PresaleSolutionTemplate

**涉及文件**:
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_ai_solution.py`
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

**操作**: 需要手动重命名其中一个类

### 修复 2: class_name_conflict - manual_required

**类名**: ReportTemplate

**涉及文件**:
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

**操作**: 需要手动重命名其中一个类

### 修复 3: class_name_conflict - manual_required

**类名**: Employee

**涉及文件**:
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/organization.py`
- `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/employee_encrypted_example.py`

**操作**: 需要手动重命名其中一个类

### 修复 4: back_populates_asymmetry - success

**模型**: PresaleAISolution.requirement_analysis

**目标**: PresaleAIRequirementAnalysis.solutions

**文件**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_ai_requirement_analysis.py`

**添加代码**:
```python
    solutions = relationship('PresaleAISolution', back_populates='requirement_analysis')
```

### 修复 5: back_populates_asymmetry - already_exists

**模型**: Investor.equity_structures

**目标**: EquityStructure.investor

### 修复 6: back_populates_asymmetry - already_exists

**模型**: EmployeeHrProfile.employee

**目标**: Employee.hr_profile

### 修复 7: back_populates_asymmetry - success

**模型**: CostPrediction.project

**目标**: Project.cost_predictions

**文件**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/core.py`

**添加代码**:
```python
    cost_predictions = relationship('CostPrediction', back_populates='project')
```

### 修复 8: back_populates_asymmetry - already_exists

**模型**: RdProject.documents

**目标**: ProjectDocument.rd_project

### 修复 9: back_populates_asymmetry - already_exists

**模型**: Quote.approvals

**目标**: QuoteApproval.quote

### 修复 10: back_populates_asymmetry - already_exists

**模型**: QuoteVersion.cost_approvals

**目标**: QuoteCostApproval.quote_version

### 修复 11: back_populates_asymmetry - already_exists

**模型**: QuoteVersion.cost_histories

**目标**: QuoteCostHistory.quote_version

### 修复 12: back_populates_asymmetry - already_exists

**模型**: ProjectMember.team_members

**目标**: ProjectMember.lead

### 修复 13: back_populates_asymmetry - already_exists

**模型**: Customer.opportunities

**目标**: Opportunity.customer

