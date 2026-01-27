# 统一状态机框架增强设计

**设计日期**: 2026-01-26
**设计人**: Claude Code
**状态**: 已批准

---

## 执行摘要

本设计文档描述了对现有统一状态机框架的增强方案，旨在解决8个模块中状态机重复实现的技术债务问题。

### 核心目标

1. **增强现有框架**：在已有的 `app/core/state_machine/` 基础上添加企业级特性
2. **统一审计日志**：创建通用的状态转换日志表，替代各模块分散的日志实现
3. **集成通知系统**：内置声明式通知支持，消除重复的通知代码
4. **权限控制**：支持简单权限声明和复杂验证器的混合方案
5. **批量迁移**：将8个模块迁移到统一框架

### 设计决策

| 决策点 | 选择方案 | 理由 |
|--------|---------|------|
| 审计日志 | 统一审计日志表 (StateTransitionLog) | 便于统一查询、审计、统计 |
| 通知系统 | 内置通知支持（声明式配置） | 80%场景的通用需求，声明式更简洁 |
| 权限控制 | 混合方案（简单声明 + 复杂validator） | 兼顾简单和灵活 |
| 操作人追踪 | transition_to参数传递 | 显式、清晰、类型安全 |

---

## 现状分析

### 已有基础设施

系统已实现基础状态机框架（`app/core/state_machine/`）：

```
app/core/state_machine/
├── __init__.py
├── base.py              # StateMachine基类 (243行)
├── decorators.py        # @transition装饰器
├── exceptions.py        # 异常定义
├── ecn.py              # ECN状态机（已迁移）
├── ecn_status.py
└── examples.py         # ProjectStage示例
```

**核心能力**：
- ✅ 声明式状态转换定义
- ✅ 转换验证器
- ✅ 前后钩子机制
- ✅ 内存转换历史
- ✅ SQLAlchemy集成
- ✅ 枚举类型支持

### 待解决问题

**模块状态**：
- ✅ ECN：已使用统一框架
- ❌ Issues：独立实现（workflow.py, 287行）
- ❌ Sales/Invoice：部分使用ApprovalWorkflow
- ❌ Projects/Milestones：独立实现
- ❌ Acceptance：状态管理分散
- ❌ Purchase：状态更新分散
- ❌ Outsourcing：状态更新分散
- ❌ InstallationDispatch：独立workflow

**缺失功能**：
- ❌ 数据库持久化的审计日志
- ❌ 通知系统集成
- ❌ 权限控制
- ❌ 操作人追踪
- ❌ 批量状态转换

---

## 架构设计

### 1. 数据模型层

#### StateTransitionLog - 统一审计日志表

```python
# app/models/state_machine.py
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Index
from app.models.base import Base, TimestampMixin

class StateTransitionLog(Base, TimestampMixin):
    """统一状态转换审计日志表"""
    __tablename__ = "state_transition_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    entity_type = Column(String(50), nullable=False, comment="实体类型：ISSUE/ECN/PROJECT等")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    from_state = Column(String(50), nullable=False, comment="源状态")
    to_state = Column(String(50), nullable=False, comment="目标状态")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    operator_name = Column(String(100), comment="操作人姓名")
    action_type = Column(String(50), comment="操作类型：SUBMIT/APPROVE/REJECT/ASSIGN等")
    comment = Column(Text, comment="备注/原因")
    extra_data = Column(JSON, comment="额外数据（如通知接收人、附件等）")

    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_state_log_entity", "entity_type", "entity_id"),
        Index("idx_state_log_operator", "operator_id"),
        Index("idx_state_log_created", "created_at"),
    )
```

**字段说明**：
- `entity_type` + `entity_id`：通用实体引用（类似审批引擎设计）
- `action_type`：业务动作分类（提交、审批、分配、解决等）
- `extra_data`：JSON扩展字段，存储特定场景的额外信息
- `operator_name`：冗余字段，便于查询和显示

**索引策略**：
- 按实体查询历史：`(entity_type, entity_id)`
- 按操作人查询：`operator_id`
- 按时间查询：`created_at`

---

### 2. 核心组件增强

#### 2.1 增强的 @transition 装饰器

```python
# app/core/state_machine/decorators.py
from typing import Callable, Optional, List

def transition(
    from_state: str,
    to_state: str,
    validator: Optional[Callable] = None,
    # === 新增参数 ===
    required_permission: Optional[str] = None,      # 所需权限
    required_role: Optional[str] = None,            # 所需角色
    action_type: Optional[str] = None,              # 操作类型（用于日志）
    notify_users: Optional[List[str]] = None,       # 通知用户类型
    notification_template: Optional[str] = None,    # 通知模板
    # === 原有参数 ===
    on_success: Optional[Callable] = None,
    on_failure: Optional[Callable] = None,
):
    """
    增强的状态转换装饰器

    新增功能：
    1. 权限声明：required_permission / required_role
    2. 审计分类：action_type
    3. 通知配置：notify_users + notification_template

    参数说明：
    - required_permission: 权限字符串，如 "ecn:approve"
    - required_role: 角色字符串，如 "PROJECT_MANAGER"
    - action_type: 操作类型，用于审计日志分类和查询
    - notify_users: 通知接收人类型列表，如 ["assignee", "reporter"]
    - notification_template: 通知模板名称

    示例：
        @transition(
            from_state="DRAFT",
            to_state="PENDING_REVIEW",
            required_permission="ecn:submit",
            action_type="SUBMIT",
            notify_users=["approvers"],
            notification_template="ecn_submitted"
        )
        def submit_for_review(self, from_state, to_state, **kwargs):
            pass
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args and hasattr(args[0], "_transitions"):
                args = args[1:]
            return method(*args, **kwargs)

        wrapper._is_transition = True
        wrapper._from_state = from_state
        wrapper._to_state = to_state
        wrapper._validator = validator
        wrapper._on_success = on_success
        wrapper._on_failure = on_failure
        # 新增属性
        wrapper._required_permission = required_permission
        wrapper._required_role = required_role
        wrapper._action_type = action_type
        wrapper._notify_users = notify_users
        wrapper._notification_template = notification_template

        return wrapper

    return decorator
```

#### 2.2 增强的 StateMachine 基类

```python
# app/core/state_machine/base.py (部分方法)
class StateMachine:
    """增强的状态机基类"""

    def transition_to(
        self,
        target_state: str,
        current_user: Optional[Any] = None,         # 新增：当前操作人
        comment: str = "",                           # 新增：备注
        action_type: Optional[str] = None,           # 新增：覆盖装饰器的action_type
        skip_notification: bool = False,             # 新增：跳过通知
        skip_audit_log: bool = False,                # 新增：跳过审计日志
        **kwargs: Any
    ) -> bool:
        """
        执行状态转换（增强版）

        执行流程：
        1. 检查转换是否允许
        2. 权限验证（新增）
        3. 执行before hooks
        4. 执行validator
        5. 执行转换函数
        6. 更新状态
        7. 创建审计日志（新增）
        8. 发送通知（新增）
        9. 执行after hooks

        参数：
        - current_user: 当前操作人（User对象）
        - comment: 操作备注/原因
        - action_type: 操作类型（覆盖装饰器配置）
        - skip_notification: 跳过通知发送
        - skip_audit_log: 跳过审计日志记录

        Raises:
        - InvalidStateTransitionError: 转换未定义
        - PermissionDeniedError: 权限不足（新增）
        - StateMachineValidationError: 验证失败
        """
        from_state = self.current_state
        to_state = str(target_state)

        # 1. 检查转换是否允许
        can_transition, reason = self.can_transition_to(target_state)
        if not can_transition:
            raise InvalidStateTransitionError(from_state, to_state, reason)

        # 2. 权限验证（新增）
        transition_key = (from_state, to_state)
        transition_func = self._transitions[transition_key]

        if hasattr(transition_func, '_required_permission') or hasattr(transition_func, '_required_role'):
            from .permissions import StateMachinePermissionChecker
            has_permission, perm_reason = StateMachinePermissionChecker.check_permission(
                current_user,
                getattr(transition_func, '_required_permission', None),
                getattr(transition_func, '_required_role', None)
            )
            if not has_permission:
                raise PermissionDeniedError(perm_reason)

        try:
            # 3-6. 执行转换（原有逻辑）
            for hook in self._before_hooks:
                hook(self, from_state, to_state, **kwargs)

            if hasattr(transition_func, "_validator") and transition_func._validator:
                validator = transition_func._validator
                is_valid, reason = validator(self, from_state, to_state)
                if not is_valid:
                    raise StateMachineValidationError(reason)

            transition_func(self, from_state, to_state, **kwargs)
            setattr(self.model, self.state_field, target_state)

            # 7. 创建审计日志（新增）
            if not skip_audit_log:
                self._create_audit_log(
                    from_state=from_state,
                    to_state=to_state,
                    current_user=current_user,
                    comment=comment,
                    action_type=action_type or getattr(transition_func, '_action_type', None),
                    **kwargs
                )

            # 8. 发送通知（新增）
            if not skip_notification:
                self._send_notifications(
                    from_state=from_state,
                    to_state=to_state,
                    transition_func=transition_func,
                    current_user=current_user,
                    **kwargs
                )

            # 9. 执行after hooks
            for hook in self._after_hooks:
                hook(self, from_state, target_state, **kwargs)

            return True

        except Exception as e:
            logger.error(f"状态转换失败: {e}", exc_info=True)
            raise

    def _create_audit_log(
        self,
        from_state: str,
        to_state: str,
        current_user: Optional[Any],
        comment: str,
        action_type: Optional[str],
        **kwargs
    ):
        """创建审计日志记录"""
        from app.models.state_machine import StateTransitionLog

        entity_type = self._get_entity_type()
        entity_id = self._get_entity_id()

        log = StateTransitionLog(
            entity_type=entity_type,
            entity_id=entity_id,
            from_state=from_state,
            to_state=to_state,
            operator_id=current_user.id if current_user else None,
            operator_name=getattr(current_user, 'real_name', None) or getattr(current_user, 'username', None) if current_user else None,
            action_type=action_type,
            comment=comment,
            extra_data=self._extract_extra_data(**kwargs)
        )

        self.db.add(log)
        self.db.flush()

    def _send_notifications(
        self,
        from_state: str,
        to_state: str,
        transition_func: Callable,
        current_user: Optional[Any],
        **kwargs
    ):
        """发送状态转换通知"""
        notify_users = getattr(transition_func, '_notify_users', None)
        notification_template = getattr(transition_func, '_notification_template', None)

        if not notify_users or not notification_template:
            return

        from .notifications import StateMachineNotifier
        notifier = StateMachineNotifier(self.db)

        # 解析通知接收人
        recipients = notifier.resolve_notification_recipients(
            state_machine=self,
            notify_users=notify_users,
            current_user=current_user
        )

        if recipients:
            entity_type = self._get_entity_type()
            entity_id = self._get_entity_id()

            notifier.send_transition_notification(
                entity_type=entity_type,
                entity_id=entity_id,
                from_state=from_state,
                to_state=to_state,
                recipients=recipients,
                template=notification_template,
                context={
                    'model': self.model,
                    'current_user': current_user,
                    **kwargs
                }
            )

    def _get_entity_type(self) -> str:
        """获取实体类型（子类可覆盖）"""
        # 默认使用模型类名
        return self.model.__class__.__name__.upper()

    def _get_entity_id(self) -> int:
        """获取实体ID"""
        return self.model.id

    def _extract_extra_data(self, **kwargs) -> dict:
        """提取额外数据（子类可覆盖以添加特定字段）"""
        # 移除内部参数
        excluded_keys = {'current_user', 'comment', 'action_type', 'skip_notification', 'skip_audit_log'}
        return {k: v for k, v in kwargs.items() if k not in excluded_keys}
```

---

### 3. 支持组件

#### 3.1 通知服务

```python
# app/core/state_machine/notifications.py
from typing import List, Dict, Any
from sqlalchemy.orm import Session

class StateMachineNotifier:
    """状态机通知服务"""

    def __init__(self, db: Session):
        self.db = db
        # 复用审批引擎的通知服务
        from app.services.approval_engine.notify import ApprovalNotifyService
        self.notify_service = ApprovalNotifyService(db)

    def resolve_notification_recipients(
        self,
        state_machine,
        notify_users: List[str],
        current_user: Any,
    ) -> List[int]:
        """
        解析通知接收人

        支持的用户类型：
        - "creator" / "created_by": 实体创建人
        - "assignee": 当前负责人/处理人
        - "reporter": 报告人/提出人
        - "approvers": 审批人列表
        - "followers": 关注者
        - "project_manager": 项目经理（针对项目相关实体）
        - "team_members": 团队成员
        - 直接传user_id: 如 "user:123"

        Args:
            state_machine: 状态机实例
            notify_users: 用户类型列表
            current_user: 当前操作人

        Returns:
            用户ID列表（去重，排除当前操作人）
        """
        recipients = []
        model = state_machine.model

        for user_type in notify_users:
            # 直接指定用户ID
            if user_type.startswith("user:"):
                user_id = int(user_type.split(":")[1])
                recipients.append(user_id)
                continue

            # 创建人
            if user_type in ["creator", "created_by"]:
                if hasattr(model, 'created_by') and model.created_by:
                    recipients.append(model.created_by)

            # 负责人/处理人
            elif user_type == "assignee":
                if hasattr(model, 'assignee_id') and model.assignee_id:
                    recipients.append(model.assignee_id)

            # 报告人/提出人
            elif user_type == "reporter":
                if hasattr(model, 'reporter_id') and model.reporter_id:
                    recipients.append(model.reporter_id)

            # 审批人列表
            elif user_type == "approvers":
                if hasattr(model, 'approver_ids'):
                    recipients.extend(model.approver_ids or [])

            # 项目经理
            elif user_type == "project_manager":
                project = self._get_related_project(model)
                if project and hasattr(project, 'manager_id') and project.manager_id:
                    recipients.append(project.manager_id)

            # 团队成员
            elif user_type == "team_members":
                project = self._get_related_project(model)
                if project:
                    from app.models.project import ProjectMember
                    members = self.db.query(ProjectMember).filter(
                        ProjectMember.project_id == project.id
                    ).all()
                    recipients.extend([m.user_id for m in members])

        # 去重并排除当前操作人
        recipients = list(set(recipients))
        if current_user and hasattr(current_user, 'id'):
            recipients = [r for r in recipients if r != current_user.id]

        return recipients

    def send_transition_notification(
        self,
        entity_type: str,
        entity_id: int,
        from_state: str,
        to_state: str,
        recipients: List[int],
        template: str,
        context: Dict[str, Any],
    ):
        """
        发送状态转换通知

        复用审批引擎的通知基础设施
        """
        # 构建通知标题和内容
        title, content = self._build_notification_content(
            template, entity_type, from_state, to_state, context
        )

        # 批量发送通知
        for user_id in recipients:
            try:
                from app.services.sales_reminder import create_notification
                create_notification(
                    db=self.db,
                    user_id=user_id,
                    notification_type=f'STATE_TRANSITION_{entity_type}',
                    title=title,
                    content=content,
                    source_type=entity_type,
                    source_id=entity_id,
                    link_url=self._build_link_url(entity_type, entity_id),
                    priority=self._determine_priority(from_state, to_state),
                    extra_data={
                        'from_state': from_state,
                        'to_state': to_state,
                        'template': template
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"发送通知失败 user_id={user_id}: {e}")

    def _get_related_project(self, model):
        """获取实体关联的项目"""
        if hasattr(model, 'project_id') and model.project_id:
            from app.models.project import Project
            return self.db.query(Project).filter(Project.id == model.project_id).first()
        return None

    def _build_notification_content(
        self, template: str, entity_type: str, from_state: str, to_state: str, context: Dict
    ) -> tuple:
        """构建通知标题和内容"""
        # 简化实现：可以后续扩展为模板引擎
        model = context.get('model')

        title_map = {
            'issue_assigned': f'问题已分配给您',
            'issue_resolved': f'问题已解决',
            'ecn_submitted': f'ECN已提交审核',
            'ecn_approved': f'ECN已批准',
            # ... 更多模板
        }

        title = title_map.get(template, f'{entity_type}状态变更')
        content = f'状态从 {from_state} 变更为 {to_state}'

        return title, content

    def _build_link_url(self, entity_type: str, entity_id: int) -> str:
        """构建跳转链接"""
        url_map = {
            'ISSUE': f'/issues/{entity_id}',
            'ECN': f'/ecn/{entity_id}',
            'PROJECT': f'/projects/{entity_id}',
            # ... 更多映射
        }
        return url_map.get(entity_type, f'/{entity_type.lower()}/{entity_id}')

    def _determine_priority(self, from_state: str, to_state: str) -> str:
        """确定通知优先级"""
        # 简化逻辑：可以根据状态转换类型调整
        urgent_states = ['REJECTED', 'BLOCKED', 'URGENT']
        if to_state in urgent_states:
            return 'HIGH'
        return 'NORMAL'
```

#### 3.2 权限验证器

```python
# app/core/state_machine/permissions.py
from typing import Optional, Tuple, Any

class PermissionDeniedError(Exception):
    """权限拒绝异常"""
    pass

class StateMachinePermissionChecker:
    """状态机权限检查器"""

    @staticmethod
    def check_permission(
        current_user: Any,
        required_permission: Optional[str] = None,
        required_role: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        检查权限

        验证逻辑：
        1. 如果没有权限要求，直接通过
        2. 如果需要权限但未提供用户，拒绝
        3. 检查用户是否有所需权限
        4. 检查用户是否有所需角色

        Args:
            current_user: 当前用户对象
            required_permission: 所需权限字符串
            required_role: 所需角色字符串

        Returns:
            (是否有权限, 失败原因)
        """
        # 无权限要求，直接通过
        if not required_permission and not required_role:
            return True, ""

        # 需要权限但未提供用户
        if not current_user:
            return False, "未提供操作人信息"

        # 检查权限
        if required_permission:
            if not hasattr(current_user, 'has_permission'):
                return False, "用户对象不支持权限检查"

            # 支持权限函数或权限列表
            if callable(getattr(current_user, 'has_permission')):
                if not current_user.has_permission(required_permission):
                    return False, f"缺少权限: {required_permission}"
            elif hasattr(current_user, 'permissions'):
                if required_permission not in current_user.permissions:
                    return False, f"缺少权限: {required_permission}"

        # 检查角色
        if required_role:
            if not hasattr(current_user, 'has_role'):
                return False, "用户对象不支持角色检查"

            # 支持角色函数或角色列表
            if callable(getattr(current_user, 'has_role')):
                if not current_user.has_role(required_role):
                    return False, f"缺少角色: {required_role}"
            elif hasattr(current_user, 'roles'):
                if required_role not in [r.name for r in current_user.roles]:
                    return False, f"缺少角色: {required_role}"

        return True, ""
```

#### 3.3 异常增强

```python
# app/core/state_machine/exceptions.py (新增)
class PermissionDeniedError(StateMachineException):
    """权限拒绝异常"""

    def __init__(self, reason: str = ""):
        self.reason = reason
        message = "Permission denied"
        if reason:
            message += f": {reason}"
        super().__init__(message)
```

---

## 使用示例

### 示例1: Issue状态机

```python
# app/core/state_machine/issue.py
from datetime import datetime
from app.core.state_machine import StateMachine, transition

class IssueStateMachine(StateMachine):
    """
    问题状态机

    状态转换：
    OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → VERIFIED → CLOSED
           ↓                         ↓
         CANCELLED                REOPENED
    """

    def __init__(self, model, db):
        super().__init__(model, db, state_field="status")

    @transition(
        from_state="OPEN",
        to_state="ASSIGNED",
        action_type="ASSIGNMENT",
        required_permission="issue:assign",
        notify_users=["assignee"],
        notification_template="issue_assigned"
    )
    def assign(self, from_state, to_state, **kwargs):
        """分配问题"""
        assignee_id = kwargs.get('assignee_id')
        if not assignee_id:
            raise ValueError("必须指定处理人")

        # 更新模型字段
        self.model.assignee_id = assignee_id

        # 获取处理人信息
        from app.models.user import User
        assignee = self.db.query(User).filter(User.id == assignee_id).first()
        if assignee:
            self.model.assignee_name = assignee.real_name or assignee.username

        # 设置截止日期
        if 'due_date' in kwargs:
            self.model.due_date = kwargs['due_date']

    @transition(
        from_state="ASSIGNED",
        to_state="IN_PROGRESS",
        action_type="START_WORK",
        required_permission="issue:update",
        notify_users=["reporter"],
        notification_template="issue_work_started"
    )
    def start_work(self, from_state, to_state, **kwargs):
        """开始处理"""
        self.model.started_at = datetime.now()

    @transition(
        from_state="IN_PROGRESS",
        to_state="RESOLVED",
        action_type="RESOLUTION",
        required_permission="issue:resolve",
        notify_users=["reporter", "project_manager"],
        notification_template="issue_resolved"
    )
    def resolve(self, from_state, to_state, **kwargs):
        """解决问题"""
        solution = kwargs.get('solution')
        if not solution:
            raise ValueError("必须填写解决方案")

        self.model.solution = solution
        self.model.resolved_at = datetime.now()

        current_user = kwargs.get('current_user')
        if current_user:
            self.model.resolved_by = current_user.id
            self.model.resolved_by_name = current_user.real_name or current_user.username

    @transition(
        from_state="RESOLVED",
        to_state="VERIFIED",
        action_type="VERIFICATION",
        required_permission="issue:verify",
        notify_users=["assignee"],
        notification_template="issue_verified"
    )
    def verify(self, from_state, to_state, **kwargs):
        """验证解决方案"""
        verified_result = kwargs.get('verified_result')
        if not verified_result:
            raise ValueError("必须填写验证结果")

        self.model.verified_result = verified_result
        self.model.verified_at = datetime.now()

        current_user = kwargs.get('current_user')
        if current_user:
            self.model.verified_by = current_user.id
            self.model.verified_by_name = current_user.real_name or current_user.username

    @transition(
        from_state="VERIFIED",
        to_state="CLOSED",
        action_type="CLOSURE",
        required_permission="issue:close"
    )
    def close(self, from_state, to_state, **kwargs):
        """关闭问题"""
        self.model.closed_at = datetime.now()

    def _get_entity_type(self) -> str:
        return "ISSUE"
```

### 示例2: API��点使用

```python
# app/api/v1/endpoints/issues/workflow.py (重构后)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.state_machine.issue import IssueStateMachine
from app.schemas.issue import IssueAssignRequest, IssueResponse

router = APIRouter()

@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    assign_req: IssueAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(security.require_permission("issue:assign")),
):
    """分配问题（使用状态机）"""
    # 获取问题
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 创建状态机并执行转换
    sm = IssueStateMachine(issue, db)

    try:
        sm.transition_to(
            "ASSIGNED",
            current_user=current_user,
            comment=assign_req.comment or f"分配给 {assign_req.assignee_id}",
            assignee_id=assign_req.assignee_id,
            due_date=assign_req.due_date,
        )
        db.commit()
        db.refresh(issue)

        return issue

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    resolve_req: IssueResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(security.require_permission("issue:resolve")),
):
    """解决问题（使用状态机）"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    sm = IssueStateMachine(issue, db)

    try:
        sm.transition_to(
            "RESOLVED",
            current_user=current_user,
            comment=resolve_req.comment or "问题已解决",
            solution=resolve_req.solution,
        )
        db.commit()
        db.refresh(issue)

        return issue

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 实施计划

### 阶段1: 框架增强（1-2天）

**任务列表**：
1. ✅ 创建数据模型
   - `StateTransitionLog` 模型
   - 数据库迁移文件

2. ✅ 增强核心组件
   - 增强 `@transition` 装饰器
   - 增强 `StateMachine.transition_to` 方法
   - 添加 `_create_audit_log` 方法
   - 添加 `_send_notifications` 方法

3. ✅ 实现支持组件
   - `StateMachineNotifier` 通知服务
   - `StateMachinePermissionChecker` 权限验证
   - `PermissionDeniedError` 异常

4. ✅ 编写单元测试
   - 审计日志创建测试
   - 通知发送测试
   - 权限验证测试
   - 端到端转换测试

**交付物**：
- 增强的状态机框架代码
- 单元测试（覆盖率 > 80%）
- 数据库迁移脚本

---

### 阶段2: 试点迁移（1天）

**选择试点模块**: Issues

**迁移步骤**：
1. 创建 `IssueStateMachine` 类
2. 定义所有状态转换
3. 重构 API 端点使用状态机
4. 功能测试验证
5. 性能测试对比

**成功标准**：
- 所有Issue工作流功能正常
- 审计日志正确记录
- 通知正常发送
- 性能无明显下降

---

### 阶段3: 批量迁移（2-3天）

**迁移顺序**（按复杂度）：

| 模块 | 优先级 | 工作量 | 说明 |
|------|--------|--------|------|
| Projects/Milestones | P1 | 0.5天 | 简单状态转换 |
| Acceptance | P1 | 0.5天 | 3种类型，状态清晰 |
| Purchase | P2 | 0.5天 | 订单状态管理 |
| Outsourcing | P2 | 0.5天 | 类似Purchase |
| Sales/Invoice | P2 | 0.5天 | 已部分使用ApprovalWorkflow |
| InstallationDispatch | P3 | 0.5天 | 调度状态管理 |

**每个模块迁移步骤**：
1. 分析现有状态转换逻辑
2. 创建对应的StateMachine子类
3. 重构API端点
4. 删除旧的workflow代码
5. 功能测试

---

### 阶段4: 清理与优化（1天）

**清理任务**：
1. 删除废弃代码
   - 各模块的独立 workflow.py
   - 重复的通知代码
   - 分散的权限检查

2. 统一查询接口
   - 审计日志查询API
   - 状态转换历史API
   - 批量状态查询API

3. 文档更新
   - 更新开发文档
   - 更新API文档
   - 添加迁移指南

4. 性能优化
   - 审计日志批量插入
   - 通知批量发送
   - 索引优化

---

## 向后兼容性

### 兼容性保证

1. **可选参数**：所有新增参数都是可选的
   ```python
   # 旧代码仍可工作（无审计日志和通知）
   sm.transition_to("APPROVED")

   # 新代码使用完整功能
   sm.transition_to("APPROVED", current_user=user, comment="审批通过")
   ```

2. **渐进式迁移**：
   - ECN模块无需修改即可继续工作
   - 新模块逐个迁移，互不影响
   - 审计日志按需启用

3. **数据库迁移**：
   - 新表 `state_transition_logs` 不影响现有表
   - 无需修改现有表结构

### 废弃计划

**立即废弃**：
- 无

**6个月后废弃**：
- 各模块独立的 workflow.py 文件
- 重复的状态更新逻辑

**迁移指南**：
详见 `docs/migration/state-machine-migration.md`

---

## 风险与缓解

### 风险1: 性能影响

**风险描述**：
每次状态转换都创建审计日志和发送通知，可能影响性能。

**缓解措施**：
1. 异步通知发送（使用后台任务）
2. 审计日志批量提交（在事务提交时）
3. 可选禁用通知（`skip_notification=True`）
4. 数据库索引优化

**监控指标**：
- 状态转换平均耗时
- 审计日志写入QPS
- 通知发送延迟

---

### 风险2: 兼容性问题

**风险描述**：
现有代码可能依赖旧的workflow逻辑，迁移可能破坏功能。

**缓解措施**：
1. 渐进式迁移，每个模块单独测试
2. 保留旧代码直到验证完成
3. 全面的功能测试覆盖
4. 回滚计划（保留迁移前的代码分支）

---

### 风险3: 通知泛滥

**风险描述**：
过多的状态转换通知可能骚扰用户。

**缓解措施**：
1. 通知合并（同一实体的多次转换）
2. 用户通知偏好设置
3. 通知频率限制
4. 重要通知优先级

---

## 成功指标

### 技术指标

- [x] 代码重复率降低：从 8 个独立实现 → 1 个统一框架
- [ ] 审计日志覆盖率：100% 状态转换可追溯
- [ ] 单元测试覆盖率：> 80%
- [ ] 性能影响：状态转换耗时增加 < 20%

### 业务指标

- [ ] 开发效率：新增状态机从 2 天 → 0.5 天
- [ ] Bug 率降低：统一逻辑减少边界情况
- [ ] 审计能力：支持任意实体的状态历史查询

---

## 附录

### A. 相关文档

- 现有状态机框架：`app/core/state_machine/`
- 审批引擎设计：`APPROVAL_ENGINE_DESIGN.md`
- ECN状态机实现：`app/core/state_machine/ecn.py`

### B. 参考实现

- Django FSM: https://github.com/viewflow/django-fsm
- Python Transitions: https://github.com/pytransitions/transitions
- AWS Step Functions: State Machine概念

### C. 术语表

| 术语 | 说明 |
|------|------|
| State Machine | 状态机，管理对象状态转换的框架 |
| Transition | 状态转换，从一个状态到另一个状态的过程 |
| Validator | 验证器，检查转换是否允许的函数 |
| Hook | 钩子，在转换前后执行的回调函数 |
| Audit Log | 审计日志，记录状态转换历史的记录 |
| Entity Type | 实体类型，如 ISSUE, ECN, PROJECT |

---

**文档版本**: 1.0
**最后更新**: 2026-01-26
**状态**: 已批准，待实施
