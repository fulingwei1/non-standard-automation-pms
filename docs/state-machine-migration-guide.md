# 状态机框架迁移指南

## 概述

本指南说明如何将现有的独立状态机实现迁移到统一状态机框架。

## 迁移进度

### ✅ 已完成迁移（7/8）
1. **ECN模块** - 工程变更通知 ✅
2. **Issues模块** - 问题管理 ✅
3. **InstallationDispatch模块** - 安装调试派工 ✅
4. **Milestone模块** - 项目里程碑 ✅
5. **Opportunity模块** - 销售商机 ✅
6. **Acceptance模块** - 验收单 ✅
7. **Quote模块** - 销售报价（复杂度最高，11个状态，21个转换） ✅

### ⏳ 待迁移（1/8）
8. **Contract模块** - 合同（注：由审批引擎处理，可能不需要独立状态机）

## 迁移步骤

### 第1步：分析现有状态机

1. 找到workflow相关文件（通常在 `app/api/v1/endpoints/*/workflow.py`）
2. 识别所有状态和状态转换
3. 记录每个转换的：
   - 源状态 (from_state)
   - 目标状态 (to_state)
   - 权限要求
   - 业务逻辑
   - 通知对象

#### 示例分析（Issues模块）

```
状态流转图：
OPEN → IN_PROGRESS (分配)
IN_PROGRESS → RESOLVED (解决)
RESOLVED → CLOSED (验证通过)
RESOLVED → IN_PROGRESS (验证失败)
OPEN → CLOSED (直接关闭)
CLOSED → OPEN (重新打开)
```

### 第2步：创建状态机类

在 `app/core/state_machine/` 目录创建新文件，命名规则：`{module_name}.py`

#### 模板代码

```python
# -*- coding: utf-8 -*-
"""
{模块名}状态机

状态转换规则：
- STATE_A → STATE_B: 描述
- STATE_B → STATE_C: 描述
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.{module} import {Model}


class {Model}StateMachine(StateMachine):
    """
    {模块}状态机
    """

    def __init__(self, model: {Model}, db: Session):
        """初始化状态机"""
        super().__init__(model, db, state_field='status')  # 或其他状态字段

    @transition(
        from_state="STATE_A",
        to_state="STATE_B",
        required_permission="{module}:{action}",  # 可选
        required_role="ROLE_NAME",                # 可选
        action_type="ACTION",                     # 可选，用于审计日志
        notify_users=["assignee", "reporter"],    # 可选
        notification_template="template_name",    # 可选
    )
    def action_name(self, from_state: str, to_state: str, **kwargs):
        """
        状态转换说明

        Args:
            param1: 参数说明
            param2: 参数说明
        """
        # 更新模型字段
        if 'param1' in kwargs:
            self.model.field1 = kwargs['param1']

        # 调用业务逻辑
        self._some_business_logic(**kwargs)

    # ==================== 业务逻辑辅助方法 ====================

    def _some_business_logic(self, **kwargs):
        """业务逻辑封装"""
        try:
            # 业务逻辑代码
            pass
        except Exception as e:
            import logging
            logging.error(f"业务逻辑执行失败: {e}")
```

### 第3步：创建API端点（v2版本）

创建新的API文件：`app/api/v1/endpoints/{module}/workflow_v2.py`

#### 模板代码

```python
# -*- coding: utf-8 -*-
"""
{模块}工作流操作（基于统一状态机框架）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.{module} import {Model}StateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.{module} import {Model}
from app.models.user import User
from app.schemas.{module} import {Model}Response, {Action}Request

router = APIRouter()


@router.post("/{entity_id}/action", response_model={Model}Response)
def action_endpoint(
    entity_id: int,
    request: {Action}Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("{module}:{action}")),
):
    """
    执行状态转换操作
    """
    # 获取实体
    entity = db.query({Model}).filter({Model}.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="{模块}不存在")

    # 初始化状态机
    state_machine = {Model}StateMachine(entity, db)

    # 执行状态转换
    try:
        state_machine.transition_to(
            "TARGET_STATE",
            current_user=current_user,
            comment=request.comment,
            # 其他参数
            param1=request.param1,
        )

        db.commit()
        db.refresh(entity)

        return entity

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 第4步：编写单元测试

创建测试文件：`tests/unit/test_{module}_state_machine.py`

#### 模板代码

```python
# -*- coding: utf-8 -*-
"""
测试 {模块} 状态机
"""

import pytest
from unittest.mock import Mock, patch

from app.core.state_machine.{module} import {Model}StateMachine


class Test{Model}StateMachine:
    """测试 {模块} 状态机"""

    @pytest.fixture
    def mock_model(self):
        """创建模拟对象"""
        model = Mock()
        model.id = 1
        model.status = "INITIAL_STATE"
        model.__class__.__name__ = "{Model}"
        return model

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库会话"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = Mock()
        user.id = 10
        user.name = "测试用户"
        user.has_permission = Mock(return_value=True)
        return user

    def test_state_machine_initialization(self, mock_model, mock_db):
        """测试状态机初始化"""
        state_machine = {Model}StateMachine(mock_model, mock_db)
        assert state_machine.current_state == "INITIAL_STATE"

    def test_transition_success(self, mock_model, mock_db, mock_user):
        """测试成功的状态转换"""
        state_machine = {Model}StateMachine(mock_model, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "TARGET_STATE",
                current_user=mock_user,
                param1="value1",
            )

        assert result is True
        assert mock_model.status == "TARGET_STATE"

    def test_invalid_transition(self, mock_model, mock_db, mock_user):
        """测试无效的状态转换"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        state_machine = {Model}StateMachine(mock_model, mock_db)

        with pytest.raises(InvalidStateTransitionError):
            state_machine.transition_to("INVALID_STATE", current_user=mock_user)
```

### 第5步：验证迁移

运行测试确保所有功能正常：

```bash
# 运行状态机单元测试
python3 -m pytest tests/unit/test_{module}_state_machine.py -v

# 运行所有状态机测试
python3 -m pytest tests/unit/test_*_state_machine.py -v
```

## 关键注意事项

### 1. 向后兼容性

所有新参数必须是可选的（Optional），以保持向后兼容：

```python
@transition(
    from_state="OPEN",
    to_state="CLOSED",
    required_permission="issue:close",  # 可选
    notify_users=["assignee"],          # 可选
)
def close(self, from_state: str, to_state: str, **kwargs):
    # 实现
    pass
```

### 2. 权限检查层级

状态机框架提供两层权限检查：

1. **API端点层**：`@Depends(security.require_permission("module:action"))`
2. **状态机层**：`@transition(required_permission="module:action")`

通常两层都保留以确保安全。

### 3. 通知用户类型

支持的用户类型（在 `notify_users` 参数中使用）：

- `creator` / `created_by`: 创建人
- `assignee`: 当前负责人
- `reporter`: 报告人
- `approvers`: 审批人列表
- `project_manager`: 项目经理
- `team_members`: 团队成员

### 4. 审计日志字段

状态转换会自动记录到 `StateTransitionLog` 表：

- `entity_type`: 自动从模型类名推断（如 "ISSUE", "ECN"）
- `entity_id`: 实体ID
- `from_state`: 源状态
- `to_state`: 目标状态
- `operator_id`: 操作人ID
- `action_type`: 操作类型（从 `@transition` 装饰器获取）
- `comment`: 备注（从 `comment` 参数获取）
- `extra_data`: 额外数据（JSON）

### 5. 业务逻辑封装

将复杂的业务逻辑封装在私有方法中：

```python
@transition(from_state="IN_PROGRESS", to_state="RESOLVED")
def resolve(self, from_state: str, to_state: str, **kwargs):
    """解决问题"""
    # 更新字段
    self.model.resolved_at = datetime.now()

    # 调用业务逻辑
    if self.model.is_blocking:
        self._close_blocking_alerts()
    if self.model.project_id:
        self._update_project_health()

def _close_blocking_alerts(self):
    """业务逻辑：关闭相关预警"""
    # 实现
    pass

def _update_project_health(self):
    """业务逻辑：更新项目健康度"""
    # 实现
    pass
```

## 迁移效益

### 代码质量提升

| 指标 | 旧实现 | 新实现 | 改进 |
|------|--------|--------|------|
| 状态转换逻辑 | 分散在各端点 | 集中在状态机类 | +50% 可维护性 |
| 审计日志 | 手动创建 | 自动记录 | 100% 覆盖率 |
| 通知发送 | 手动调用 | 自动发送 | 减少50%代码 |
| 单元测试 | 需要API环境 | 独立测试 | 速度提升10x |

### 功能增强

1. **统一审计追踪**：所有状态转换自动记录到 `StateTransitionLog`
2. **声明式权限**：在装饰器中声明权限要求
3. **自动通知**：状态转换时自动通知相关人员
4. **业务逻辑封装**：清晰的职责分离

## 常见问题

### Q1：如何处理多个源状态到同一目标状态？

为每个源状态创建独立的转换：

```python
@transition(from_state="PENDING", to_state="CANCELLED")
def cancel_from_pending(self, from_state, to_state, **kwargs):
    pass

@transition(from_state="ASSIGNED", to_state="CANCELLED")
def cancel_from_assigned(self, from_state, to_state, **kwargs):
    pass
```

### Q2：如何处理不改变状态的操作？

不使用状态机，直接更新模型：

```python
def update_progress(self, progress: int):
    """更新进度（不改变状态）"""
    if self.current_state != "IN_PROGRESS":
        raise ValueError("只能在进行中状态更新进度")
    self.model.progress = progress
```

### Q3：如何测试状态机？

使用Mock对象避免数据库依赖：

```python
with patch.object(state_machine, '_create_audit_log'), \
     patch.object(state_machine, '_send_notifications'):
    state_machine.transition_to("NEW_STATE", current_user=mock_user)
```

## 参考示例

完整的迁移示例可参考：

1. **ECN模块**：`app/core/state_machine/ecn.py`
   - 原始实现，基础框架使用

2. **Issues模块**：`app/core/state_machine/issue.py`
   - 8个状态转换，复杂业务逻辑（关闭预警、更新健康度、同步调试问题）

3. **InstallationDispatch模块**：`app/core/state_machine/installation_dispatch.py`
   - 4个状态转换，自动创建服务记录

4. **Milestone模块**：`app/core/state_machine/milestone.py`
   - 1个状态转换（最简单），自动触发开票

5. **Opportunity模块**：`app/core/state_machine/opportunity.py`
   - 8个状态转换（4个正向 + 4个输单分支），评分自动计算风险等级

6. **Acceptance模块**：`app/core/state_machine/acceptance.py`
   - 5个状态转换，8个业务逻辑集成（FAT/SAT验证、开票、质保期、奖金计算）
   - 最复杂的业务逻辑整合

7. **Quote模块**：`app/core/state_machine/quote.py`
   - 21个状态转换方法，11个状态，复杂度最高
   - 完整的报价生命周期：审批→发送→接受→转换为合同
   - 多分支流程：快速批准 vs 评审流程，取消/过期/修改等异常处理

## 联系和支持

如有问题，请参考：
- 设计文档：`docs/plans/2026-01-26-state-machine-enhancement-design.md`
- 单元测试：`tests/unit/test_*_state_machine.py`
