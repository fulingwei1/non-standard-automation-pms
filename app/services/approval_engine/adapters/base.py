# -*- coding: utf-8 -*-
"""
审批适配器基类

定义业务实体接入审批系统的标准接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
)


class ApprovalAdapter(ABC):
    """
    审批适配器基类

    每个业务模块需要实现自己的适配器，用于：
    1. 提供业务实体数据供审批条件判断
    2. 在审批状态变更时更新业务实体状态
    3. 动态解析审批人
    4. 生成审批摘要信息
    """

    # 适配器标识
    entity_type: str = ""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def get_entity(self, entity_id: int) -> Any:
        """
        获取业务实体

        Args:
            entity_id: 业务实体ID

        Returns:
            业务实体对象
        """
        pass

    @abstractmethod
    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取业务实体数据（用于条件路由）

        Args:
            entity_id: 业务实体ID

        Returns:
            实体数据字典，用于审批条件判断
        """
        pass

    @abstractmethod
    def on_submit(self, entity_id: int, instance: ApprovalInstance):
        """
        审批提交时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    @abstractmethod
    def on_approved(self, entity_id: int, instance: ApprovalInstance):
        """
        审批通过时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    @abstractmethod
    def on_rejected(self, entity_id: int, instance: ApprovalInstance):
        """
        审批驳回时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance):
        """
        审批撤回时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def on_terminated(self, entity_id: int, instance: ApprovalInstance):
        """
        审批终止时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def resolve_approvers(
        self,
        node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ) -> List[int]:
        """
        动态解析审批人（可选实现）

        当节点的 approver_type 为 DYNAMIC 时调用

        Args:
            node: 节点定义
            context: 上下文数据

        Returns:
            审批人ID列表
        """
        return []

    def generate_title(self, entity_id: int) -> str:
        """
        生成审批标题

        Args:
            entity_id: 业务实体ID

        Returns:
            审批标题
        """
        return f"{self.entity_type}审批 - {entity_id}"

    def generate_summary(self, entity_id: int) -> str:
        """
        生成审批摘要

        Args:
            entity_id: 业务实体ID

        Returns:
            审批摘要
        """
        return ""

    def get_form_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取表单数据

        可以将业务实体数据转换为表单数据

        Args:
            entity_id: 业务实体ID

        Returns:
            表单数据
        """
        return self.get_entity_data(entity_id)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        """
        验证是否可以提交审批

        Args:
            entity_id: 业务实体ID

        Returns:
            (是否可以提交, 错误信息)
        """
        return True, None

    def get_cc_user_ids(self, entity_id: int) -> List[int]:
        """
        获取默认抄送人列表

        Args:
            entity_id: 业务实体ID

        Returns:
            抄送人ID列表
        """
        return []

    # ==================== 部门负责人查询辅助方法 ====================

    def get_department_manager_user_id(self, dept_name: str) -> Optional[int]:
        """
        根据部门名称获取部门负责人的用户ID

        查询链路:
        1. Department(dept_name) → manager_id → Employee
        2. Employee(name/employee_code) → User(real_name/username)
        3. 返回 User.id

        Args:
            dept_name: 部门名称

        Returns:
            部门负责人的用户ID，如果找不到返回None
        """
        from sqlalchemy import or_
        from app.models.organization import Department, Employee
        from app.models.user import User

        # 查找部门
        dept = self.db.query(Department).filter(
            Department.dept_name == dept_name,
            Department.is_active == True
        ).first()

        if not dept or not dept.manager_id:
            return None

        # 查找部门经理（Employee）
        manager = self.db.query(Employee).filter(
            Employee.id == dept.manager_id
        ).first()

        if not manager:
            return None

        # 通过员工信息查找用户
        user = self.db.query(User).filter(
            or_(
                User.real_name == manager.name,
                User.username == manager.employee_code
            ),
            User.is_active == True
        ).first()

        return user.id if user else None

    def get_department_manager_user_ids_by_codes(self, dept_codes: List[str]) -> List[int]:
        """
        根据部门编码列表获取部门负责人的用户ID列表

        Args:
            dept_codes: 部门编码列表 (如 ['PROD', 'QA', 'PURCHASE'])

        Returns:
            部门负责人用户ID列表（去重）
        """
        from sqlalchemy import or_
        from app.models.organization import Department, Employee
        from app.models.user import User

        user_ids = []

        # 批量查询部门
        depts = self.db.query(Department).filter(
            Department.dept_code.in_(dept_codes),
            Department.is_active == True
        ).all()

        manager_ids = [d.manager_id for d in depts if d.manager_id]
        if not manager_ids:
            return []

        # 批量查询员工
        managers = self.db.query(Employee).filter(
            Employee.id.in_(manager_ids)
        ).all()

        if not managers:
            return []

        # 构建查询条件
        name_conditions = []
        for manager in managers:
            name_conditions.append(User.real_name == manager.name)
            name_conditions.append(User.username == manager.employee_code)

        # 批量查询用户
        users = self.db.query(User).filter(
            or_(*name_conditions),
            User.is_active == True
        ).all()

        user_ids = [u.id for u in users]
        return list(set(user_ids))

    def get_project_sales_user_id(self, project_id: int) -> Optional[int]:
        """
        获取项目关联的销售负责人用户ID

        通过项目关联的销售合同/报价单查找销售负责人

        Args:
            project_id: 项目ID

        Returns:
            销售负责人用户ID，如果找不到返回None
        """
        from app.models.project import Project

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 优先从项目的 sales_id 字段获取
        if hasattr(project, 'sales_id') and project.sales_id:
            return project.sales_id

        # 其次尝试从关联的销售合同获取
        if hasattr(project, 'contract_id') and project.contract_id:
            from app.models.sales import SalesContract
            contract = self.db.query(SalesContract).filter(
                SalesContract.id == project.contract_id
            ).first()
            if contract and hasattr(contract, 'sales_id') and contract.sales_id:
                return contract.sales_id

        return None
