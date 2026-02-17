# -*- coding: utf-8 -*-
"""
D2组：状态机 & 流程转换验证（深度测试）

验证业务状态机的合法/非法转换：
1. 项目阶段状态机 (S1→S9)
2. 审批流状态机 (DRAFT→COMPLETED)
3. 采购单状态机 (DRAFT→CLOSED)
4. 合同状态机 (DRAFT→COMPLETED/TERMINATED)
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Optional

from fastapi import HTTPException


# =============================================================================
# ================  辅助函数：项目阶段状态机  =================================
# =============================================================================

VALID_STAGES = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']

STAGE_SEQUENCE = {stage: idx for idx, stage in enumerate(VALID_STAGES, 1)}


def transition_project_stage(project, target_stage: str, allow_backward: bool = False,
                               reason: Optional[str] = None):
    """
    项目阶段状态机核心逻辑：执行阶段转换

    规则：
    - 合法的目标阶段必须在 S1-S9 中
    - 不允许跳阶段（只能向前一格或允许回退一格）
    - S9（终态）不允许任何转换
    - 回退转换需要提供原因

    Args:
        project: 项目对象（有 current_stage 属性）
        target_stage: 目标阶段
        allow_backward: 是否允许回退（需要提供 reason）
        reason: 回退原因

    Returns:
        project: 更新后的项目对象

    Raises:
        ValueError: 无效转换时
    """
    current = getattr(project, 'current_stage', None)

    # 验证阶段合法性
    if target_stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: '{target_stage}'. Valid stages: {VALID_STAGES}")

    if current not in VALID_STAGES:
        raise ValueError(f"Invalid current stage: '{current}'")

    current_num = STAGE_SEQUENCE[current]
    target_num = STAGE_SEQUENCE[target_stage]

    # 终态保护：S9 不允许任何转换
    if current == 'S9':
        raise ValueError(f"Cannot transition from terminal stage S9 to '{target_stage}'")

    # 禁止同阶段转换
    if current == target_stage:
        raise ValueError(f"Already in stage '{current_stage}'")

    # 禁止跳阶段前进（只允许 +1）
    if target_num > current_num + 1:
        raise ValueError(
            f"Cannot skip stages: '{current}' → '{target_stage}'. "
            f"Must advance one stage at a time."
        )

    # 回退逻辑（允许 -1，需要原因）
    if target_num < current_num:
        if not allow_backward:
            raise ValueError(
                f"Backward transition not allowed: '{current}' → '{target_stage}'. "
                f"Set allow_backward=True and provide a reason."
            )
        if not reason:
            raise ValueError(
                f"Reason is required for backward transition: '{current}' → '{target_stage}'"
            )

    # 执行转换
    project.current_stage = target_stage
    if reason:
        project.last_transition_reason = reason
    return project


# =============================================================================
# ================  辅助函数：审批流状态机  ===================================
# =============================================================================

APPROVAL_TRANSITIONS = {
    'DRAFT': ['SUBMITTED'],
    'SUBMITTED': ['REVIEWING'],
    'REVIEWING': ['APPROVED', 'REJECTED'],
    'APPROVED': ['COMPLETED'],
    'REJECTED': ['DRAFT'],       # 允许修改后重新提交
    'COMPLETED': [],             # 终态
}

APPROVAL_TERMINAL_STATES = {'COMPLETED'}
APPROVAL_VALID_STATES = set(APPROVAL_TRANSITIONS.keys())


def transition_approval(approval, target_status: str):
    """
    审批流状态机

    规则：
    - APPROVED → COMPLETED ✅
    - REJECTED → DRAFT ✅（允许修改后重新提交）
    - COMPLETED → 任何状态 ❌（终态不可逆）
    - REVIEWING → DRAFT ❌（审批中不能直接撤回到草稿）

    Args:
        approval: 审批对象（有 status 属性）
        target_status: 目标状态

    Returns:
        approval: 更新后的审批对象

    Raises:
        ValueError: 无效转换时
    """
    current = approval.status

    # 验证状态合法性
    if current not in APPROVAL_VALID_STATES:
        raise ValueError(f"Unknown approval status: '{current}'")
    if target_status not in APPROVAL_VALID_STATES:
        raise ValueError(f"Unknown target approval status: '{target_status}'")

    # 终态保护
    if current in APPROVAL_TERMINAL_STATES:
        raise ValueError(
            f"Cannot transition from terminal state '{current}' to '{target_status}'"
        )

    # 检查转换是否被允许
    allowed = APPROVAL_TRANSITIONS.get(current, [])
    if target_status not in allowed:
        raise ValueError(
            f"Invalid approval transition: '{current}' → '{target_status}'. "
            f"Allowed: {allowed}"
        )

    approval.status = target_status
    return approval


# =============================================================================
# ================  辅助函数：采购单状态机  ===================================
# =============================================================================

PURCHASE_TRANSITIONS = {
    'DRAFT': ['SUBMITTED'],
    'SUBMITTED': ['APPROVED', 'DRAFT'],   # 可被退回草稿
    'APPROVED': ['ORDERED'],
    'ORDERED': ['PARTIAL_RECEIVED'],
    'PARTIAL_RECEIVED': ['PARTIAL_RECEIVED', 'RECEIVED'],  # 允许继续收货
    'RECEIVED': ['CLOSED'],
    'CLOSED': [],                           # 终态
}

PURCHASE_TERMINAL_STATES = {'CLOSED'}
PURCHASE_VALID_STATES = set(PURCHASE_TRANSITIONS.keys())


def transition_purchase_order(order, target_status: str, db=None):
    """
    采购单状态机

    规则：
    - DRAFT → SUBMITTED → APPROVED → ORDERED → PARTIAL_RECEIVED → RECEIVED → CLOSED
    - RECEIVED 后自动触发入库单创建
    - PARTIAL_RECEIVED 下允许继续收货

    Args:
        order: 采购单对象（有 status 属性）
        target_status: 目标状态
        db: 数据库会话（用于创建入库单）

    Returns:
        order: 更新后的采购单对象

    Raises:
        ValueError: 无效转换时
    """
    current = order.status

    if current not in PURCHASE_VALID_STATES:
        raise ValueError(f"Unknown purchase order status: '{current}'")
    if target_status not in PURCHASE_VALID_STATES:
        raise ValueError(f"Unknown target status: '{target_status}'")

    if current in PURCHASE_TERMINAL_STATES:
        raise ValueError(
            f"Cannot transition from terminal state '{current}' to '{target_status}'"
        )

    allowed = PURCHASE_TRANSITIONS.get(current, [])
    if target_status not in allowed:
        raise ValueError(
            f"Invalid purchase order transition: '{current}' → '{target_status}'. "
            f"Allowed: {allowed}"
        )

    order.status = target_status

    # RECEIVED 后自动触发入库单创建
    if target_status == 'RECEIVED':
        order.goods_receipt_created = True
        if db and hasattr(db, 'add'):
            # 模拟创建入库单
            receipt = MagicMock()
            receipt.order_id = getattr(order, 'id', None)
            receipt.status = 'COMPLETED'
            db.add(receipt)

    return order


# =============================================================================
# ================  辅助函数：合同状态机  =====================================
# =============================================================================

CONTRACT_TRANSITIONS = {
    'DRAFT': ['NEGOTIATING'],
    'NEGOTIATING': ['SIGNED', 'DRAFT'],     # 可回到草稿
    'SIGNED': ['EXECUTING'],
    'EXECUTING': ['COMPLETED', 'TERMINATED'],
    'COMPLETED': [],                         # 终态
    'TERMINATED': [],                        # 终态
}

CONTRACT_TERMINAL_STATES = {'COMPLETED', 'TERMINATED'}
CONTRACT_VALID_STATES = set(CONTRACT_TRANSITIONS.keys())


def transition_contract(contract, target_status: str, milestones_all_paid: bool = True):
    """
    合同状态机

    规则：
    - DRAFT → NEGOTIATING → SIGNED → EXECUTING → COMPLETED/TERMINATED
    - TERMINATED 后不允许任何操作
    - COMPLETED 需要所有里程碑付款已收

    Args:
        contract: 合同对象（有 status 属性）
        target_status: 目标状态
        milestones_all_paid: COMPLETED 转换时验证所有里程碑是否已付款

    Returns:
        contract: 更新后的合同对象

    Raises:
        ValueError: 无效转换时
    """
    current = contract.status

    if current not in CONTRACT_VALID_STATES:
        raise ValueError(f"Unknown contract status: '{current}'")
    if target_status not in CONTRACT_VALID_STATES:
        raise ValueError(f"Unknown target contract status: '{target_status}'")

    # 终态保护
    if current in CONTRACT_TERMINAL_STATES:
        raise ValueError(
            f"Cannot transition from terminal state '{current}' to '{target_status}'. "
            f"Contract is closed."
        )

    allowed = CONTRACT_TRANSITIONS.get(current, [])
    if target_status not in allowed:
        raise ValueError(
            f"Invalid contract transition: '{current}' → '{target_status}'. "
            f"Allowed: {allowed}"
        )

    # COMPLETED 需要所有里程碑付款已收
    if target_status == 'COMPLETED' and not milestones_all_paid:
        raise ValueError(
            "Cannot complete contract: not all milestone payments have been received"
        )

    contract.status = target_status
    return contract


# =============================================================================
# ==================  TEST CLASS 1: 项目阶段状态机  ===========================
# =============================================================================

class TestProjectStageMachine:
    """项目阶段状态机测试"""

    # ——— 合法转换 ———

    def test_s3_to_s4_legal_transition(self):
        """合法跳转：S3 → S4"""
        project = MagicMock(current_stage='S3')
        result = transition_project_stage(project, target_stage='S4')
        assert result.current_stage == 'S4'

    def test_s1_to_s2_legal_transition(self):
        """合法跳转：S1 → S2（第一阶段前进）"""
        project = MagicMock(current_stage='S1')
        result = transition_project_stage(project, target_stage='S2')
        assert result.current_stage == 'S2'

    def test_s8_to_s9_legal_transition(self):
        """合法跳转：S8 → S9（进入质保结项）"""
        project = MagicMock(current_stage='S8')
        result = transition_project_stage(project, target_stage='S9')
        assert result.current_stage == 'S9'

    # ——— 非法转换 ———

    def test_s3_to_s6_skip_not_allowed(self):
        """非法跳转：S3 → S6 ❌（不能跳阶段）"""
        project = MagicMock(current_stage='S3')
        with pytest.raises(ValueError, match="Cannot skip stages"):
            transition_project_stage(project, target_stage='S6')

    def test_s1_to_s9_skip_not_allowed(self):
        """非法跳转：S1 → S9 ❌（不能跨越多个阶段）"""
        project = MagicMock(current_stage='S1')
        with pytest.raises(ValueError, match="Cannot skip stages"):
            transition_project_stage(project, target_stage='S9')

    def test_s9_terminal_state_protection(self):
        """终态保护：S9 → 任何阶段 ❌"""
        project = MagicMock(current_stage='S9')
        with pytest.raises(ValueError, match="Cannot transition from terminal stage S9"):
            transition_project_stage(project, target_stage='S8')

    def test_s9_to_s1_terminal_state_protection(self):
        """终态保护：S9 → S1 ❌（终态不可逆）"""
        project = MagicMock(current_stage='S9')
        with pytest.raises(ValueError, match="Cannot transition from terminal stage S9"):
            transition_project_stage(project, target_stage='S1')

    # ——— 回退转换 ———

    def test_s6_to_s5_backward_with_reason(self):
        """回退跳转：S6 → S5 ✅（需要原因）"""
        project = MagicMock(current_stage='S6')
        project.last_transition_reason = None
        result = transition_project_stage(
            project,
            target_stage='S5',
            allow_backward=True,
            reason='装配发现缺件，需要回到采购制造阶段补料'
        )
        assert result.current_stage == 'S5'
        assert result.last_transition_reason == '装配发现缺件，需要回到采购制造阶段补料'

    def test_backward_without_reason_raises(self):
        """回退无原因 ❌"""
        project = MagicMock(current_stage='S6')
        with pytest.raises(ValueError, match="Reason is required for backward transition"):
            transition_project_stage(
                project,
                target_stage='S5',
                allow_backward=True,
                reason=None
            )

    def test_backward_without_flag_raises(self):
        """未设置 allow_backward=True 时回退 ❌"""
        project = MagicMock(current_stage='S6')
        with pytest.raises(ValueError, match="Backward transition not allowed"):
            transition_project_stage(project, target_stage='S5')

    def test_invalid_target_stage_raises(self):
        """无效的目标阶段 ❌"""
        project = MagicMock(current_stage='S3')
        with pytest.raises(ValueError, match="Invalid stage"):
            transition_project_stage(project, target_stage='S99')

    def test_validate_stage_advancement_from_service(self):
        """测试 stage_advance_service 中的 validate_stage_advancement"""
        from app.services.stage_advance_service import validate_stage_advancement

        # 合法：S3 → S4
        try:
            validate_stage_advancement('S3', 'S4')  # 不应抛出异常
        except HTTPException:
            pytest.fail("S3→S4 should not raise HTTPException")

    def test_validate_stage_backward_raises_http(self):
        """stage_advance_service 拒绝倒退"""
        from app.services.stage_advance_service import validate_stage_advancement

        with pytest.raises(HTTPException) as exc_info:
            validate_stage_advancement('S5', 'S3')
        assert exc_info.value.status_code == 400

    def test_validate_target_stage_invalid(self):
        """stage_advance_service 拒绝无效阶段名"""
        from app.services.stage_advance_service import validate_target_stage

        with pytest.raises(HTTPException) as exc_info:
            validate_target_stage('S99')
        assert exc_info.value.status_code == 400


# =============================================================================
# ==================  TEST CLASS 2: 审批流状态机  =============================
# =============================================================================

class TestApprovalFlowMachine:
    """审批流状态机测试"""

    # ——— 合法转换 ———

    def test_approved_to_completed(self):
        """合法：APPROVED → COMPLETED ✅"""
        approval = MagicMock(status='APPROVED')
        result = transition_approval(approval, 'COMPLETED')
        assert result.status == 'COMPLETED'

    def test_rejected_to_draft(self):
        """合法：REJECTED → DRAFT ✅（允许修改后重新提交）"""
        approval = MagicMock(status='REJECTED')
        result = transition_approval(approval, 'DRAFT')
        assert result.status == 'DRAFT'

    def test_draft_to_submitted(self):
        """合法：DRAFT → SUBMITTED ✅"""
        approval = MagicMock(status='DRAFT')
        result = transition_approval(approval, 'SUBMITTED')
        assert result.status == 'SUBMITTED'

    def test_submitted_to_reviewing(self):
        """合法：SUBMITTED → REVIEWING ✅"""
        approval = MagicMock(status='SUBMITTED')
        result = transition_approval(approval, 'REVIEWING')
        assert result.status == 'REVIEWING'

    def test_reviewing_to_approved(self):
        """合法：REVIEWING → APPROVED ✅"""
        approval = MagicMock(status='REVIEWING')
        result = transition_approval(approval, 'APPROVED')
        assert result.status == 'APPROVED'

    def test_reviewing_to_rejected(self):
        """合法：REVIEWING → REJECTED ✅"""
        approval = MagicMock(status='REVIEWING')
        result = transition_approval(approval, 'REJECTED')
        assert result.status == 'REJECTED'

    # ——— 非法转换 ———

    def test_completed_is_terminal_state(self):
        """非法：COMPLETED → 任何状态 ❌（终态不可逆）"""
        approval = MagicMock(status='COMPLETED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_approval(approval, 'DRAFT')

    def test_completed_to_approved_not_allowed(self):
        """非法：COMPLETED → APPROVED ❌"""
        approval = MagicMock(status='COMPLETED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_approval(approval, 'APPROVED')

    def test_reviewing_to_draft_not_allowed(self):
        """非法：REVIEWING → DRAFT ❌（审批中不能直接撤回到草稿）"""
        approval = MagicMock(status='REVIEWING')
        with pytest.raises(ValueError, match="Invalid approval transition"):
            transition_approval(approval, 'DRAFT')

    def test_draft_to_approved_not_allowed(self):
        """非法：DRAFT → APPROVED ❌（必须先提交再审批）"""
        approval = MagicMock(status='DRAFT')
        with pytest.raises(ValueError, match="Invalid approval transition"):
            transition_approval(approval, 'APPROVED')

    def test_submitted_to_completed_not_allowed(self):
        """非法：SUBMITTED → COMPLETED ❌（跳过审批步骤）"""
        approval = MagicMock(status='SUBMITTED')
        with pytest.raises(ValueError, match="Invalid approval transition"):
            transition_approval(approval, 'COMPLETED')

    def test_approved_to_draft_not_allowed(self):
        """非法：APPROVED → DRAFT ❌（已批准不能回草稿）"""
        approval = MagicMock(status='APPROVED')
        with pytest.raises(ValueError, match="Invalid approval transition"):
            transition_approval(approval, 'DRAFT')

    def test_full_approval_happy_path(self):
        """完整审批流：DRAFT → SUBMITTED → REVIEWING → APPROVED → COMPLETED"""
        approval = MagicMock(status='DRAFT')
        transition_approval(approval, 'SUBMITTED')
        assert approval.status == 'SUBMITTED'
        transition_approval(approval, 'REVIEWING')
        assert approval.status == 'REVIEWING'
        transition_approval(approval, 'APPROVED')
        assert approval.status == 'APPROVED'
        transition_approval(approval, 'COMPLETED')
        assert approval.status == 'COMPLETED'

    def test_full_rejection_and_resubmit_path(self):
        """驳回重提：REVIEWING → REJECTED → DRAFT → SUBMITTED"""
        approval = MagicMock(status='REVIEWING')
        transition_approval(approval, 'REJECTED')
        assert approval.status == 'REJECTED'
        transition_approval(approval, 'DRAFT')
        assert approval.status == 'DRAFT'
        transition_approval(approval, 'SUBMITTED')
        assert approval.status == 'SUBMITTED'


# =============================================================================
# ==================  TEST CLASS 3: 采购单状态机  =============================
# =============================================================================

class TestPurchaseOrderMachine:
    """采购单状态机测试"""

    # ——— 合法转换 ———

    def test_draft_to_submitted(self):
        """合法：DRAFT → SUBMITTED ✅"""
        order = MagicMock(status='DRAFT')
        result = transition_purchase_order(order, 'SUBMITTED')
        assert result.status == 'SUBMITTED'

    def test_submitted_to_approved(self):
        """合法：SUBMITTED → APPROVED ✅"""
        order = MagicMock(status='SUBMITTED')
        result = transition_purchase_order(order, 'APPROVED')
        assert result.status == 'APPROVED'

    def test_approved_to_ordered(self):
        """合法：APPROVED → ORDERED ✅"""
        order = MagicMock(status='APPROVED')
        result = transition_purchase_order(order, 'ORDERED')
        assert result.status == 'ORDERED'

    def test_ordered_to_partial_received(self):
        """合法：ORDERED → PARTIAL_RECEIVED ✅（部分到货）"""
        order = MagicMock(status='ORDERED')
        result = transition_purchase_order(order, 'PARTIAL_RECEIVED')
        assert result.status == 'PARTIAL_RECEIVED'

    def test_partial_received_continue_receiving(self):
        """合法：PARTIAL_RECEIVED → PARTIAL_RECEIVED ✅（继续收货）"""
        order = MagicMock(status='PARTIAL_RECEIVED')
        result = transition_purchase_order(order, 'PARTIAL_RECEIVED')
        assert result.status == 'PARTIAL_RECEIVED'

    def test_partial_received_to_received(self):
        """合法：PARTIAL_RECEIVED → RECEIVED ✅（全部收货完成）"""
        order = MagicMock(status='PARTIAL_RECEIVED')
        result = transition_purchase_order(order, 'RECEIVED')
        assert result.status == 'RECEIVED'

    def test_received_auto_triggers_goods_receipt(self):
        """合法：RECEIVED 后自动触发入库单创建"""
        order = MagicMock(status='PARTIAL_RECEIVED', id=42)
        order.goods_receipt_created = False
        mock_db = MagicMock()
        result = transition_purchase_order(order, 'RECEIVED', db=mock_db)
        assert result.status == 'RECEIVED'
        assert result.goods_receipt_created is True
        mock_db.add.assert_called_once()

    def test_received_to_closed(self):
        """合法：RECEIVED → CLOSED ✅"""
        order = MagicMock(status='RECEIVED')
        result = transition_purchase_order(order, 'CLOSED')
        assert result.status == 'CLOSED'

    # ——— 非法转换 ———

    def test_closed_is_terminal_state(self):
        """非法：CLOSED → 任何状态 ❌（终态不可逆）"""
        order = MagicMock(status='CLOSED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_purchase_order(order, 'DRAFT')

    def test_draft_to_approved_skip_not_allowed(self):
        """非法：DRAFT → APPROVED ❌（跳过提交步骤）"""
        order = MagicMock(status='DRAFT')
        with pytest.raises(ValueError, match="Invalid purchase order transition"):
            transition_purchase_order(order, 'APPROVED')

    def test_ordered_to_received_skip_not_allowed(self):
        """非法：ORDERED → RECEIVED ❌（跳过部分收货状态）"""
        order = MagicMock(status='ORDERED')
        with pytest.raises(ValueError, match="Invalid purchase order transition"):
            transition_purchase_order(order, 'RECEIVED')

    def test_purchase_service_submit_changes_status(self):
        """PurchaseService.submit_purchase_order 正确将状态改为 SUBMITTED"""
        from app.services.purchase.purchase_service import PurchaseService

        mock_db = MagicMock()
        service = PurchaseService(db=mock_db)

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = 'DRAFT'

        with patch.object(service, 'get_purchase_order_by_id', return_value=mock_order):
            result = service.submit_purchase_order(order_id=1)

        assert result is True
        assert mock_order.status == 'SUBMITTED'

    def test_purchase_service_approve_changes_status(self):
        """PurchaseService.approve_purchase_order 正确将状态改为 APPROVED"""
        from app.services.purchase.purchase_service import PurchaseService

        mock_db = MagicMock()
        service = PurchaseService(db=mock_db)

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = 'SUBMITTED'

        with patch.object(service, 'get_purchase_order_by_id', return_value=mock_order):
            result = service.approve_purchase_order(order_id=1, approver_id=99)

        assert result is True
        assert mock_order.status == 'APPROVED'
        assert mock_order.approver_id == 99


# =============================================================================
# ==================  TEST CLASS 4: 合同状态机  ===============================
# =============================================================================

class TestContractMachine:
    """合同状态机测试"""

    # ——— 合法转换 ———

    def test_draft_to_negotiating(self):
        """合法：DRAFT → NEGOTIATING ✅"""
        contract = MagicMock(status='DRAFT')
        result = transition_contract(contract, 'NEGOTIATING')
        assert result.status == 'NEGOTIATING'

    def test_negotiating_to_signed(self):
        """合法：NEGOTIATING → SIGNED ✅"""
        contract = MagicMock(status='NEGOTIATING')
        result = transition_contract(contract, 'SIGNED')
        assert result.status == 'SIGNED'

    def test_signed_to_executing(self):
        """合法：SIGNED → EXECUTING ✅"""
        contract = MagicMock(status='SIGNED')
        result = transition_contract(contract, 'EXECUTING')
        assert result.status == 'EXECUTING'

    def test_executing_to_completed_with_all_milestones_paid(self):
        """合法：EXECUTING → COMPLETED ✅（所有里程碑已付款）"""
        contract = MagicMock(status='EXECUTING')
        result = transition_contract(contract, 'COMPLETED', milestones_all_paid=True)
        assert result.status == 'COMPLETED'

    def test_executing_to_terminated(self):
        """合法：EXECUTING → TERMINATED ✅（合同终止）"""
        contract = MagicMock(status='EXECUTING')
        result = transition_contract(contract, 'TERMINATED')
        assert result.status == 'TERMINATED'

    def test_negotiating_back_to_draft(self):
        """合法：NEGOTIATING → DRAFT ✅（谈判失败，回草稿）"""
        contract = MagicMock(status='NEGOTIATING')
        result = transition_contract(contract, 'DRAFT')
        assert result.status == 'DRAFT'

    # ——— 非法转换 ———

    def test_terminated_is_terminal_state(self):
        """非法：TERMINATED → 任何状态 ❌（终态不允许任何操作）"""
        contract = MagicMock(status='TERMINATED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_contract(contract, 'DRAFT')

    def test_terminated_to_executing_not_allowed(self):
        """非法：TERMINATED → EXECUTING ❌"""
        contract = MagicMock(status='TERMINATED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_contract(contract, 'EXECUTING')

    def test_completed_is_terminal_state(self):
        """非法：COMPLETED → 任何状态 ❌"""
        contract = MagicMock(status='COMPLETED')
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_contract(contract, 'EXECUTING')

    def test_executing_to_completed_without_milestones_paid(self):
        """非法：COMPLETED 需要所有里程碑付款已收 ❌"""
        contract = MagicMock(status='EXECUTING')
        with pytest.raises(ValueError, match="not all milestone payments have been received"):
            transition_contract(contract, 'COMPLETED', milestones_all_paid=False)

    def test_draft_to_signed_skip_not_allowed(self):
        """非法：DRAFT → SIGNED ❌（跳过谈判阶段）"""
        contract = MagicMock(status='DRAFT')
        with pytest.raises(ValueError, match="Invalid contract transition"):
            transition_contract(contract, 'SIGNED')

    def test_draft_to_completed_skip_not_allowed(self):
        """非法：DRAFT → COMPLETED ❌（直接完成）"""
        contract = MagicMock(status='DRAFT')
        with pytest.raises(ValueError, match="Invalid contract transition"):
            transition_contract(contract, 'COMPLETED')

    def test_full_contract_happy_path(self):
        """完整合同流：DRAFT → NEGOTIATING → SIGNED → EXECUTING → COMPLETED"""
        contract = MagicMock(status='DRAFT')
        transition_contract(contract, 'NEGOTIATING')
        assert contract.status == 'NEGOTIATING'
        transition_contract(contract, 'SIGNED')
        assert contract.status == 'SIGNED'
        transition_contract(contract, 'EXECUTING')
        assert contract.status == 'EXECUTING'
        transition_contract(contract, 'COMPLETED', milestones_all_paid=True)
        assert contract.status == 'COMPLETED'

    def test_contract_termination_path(self):
        """合同终止流：EXECUTING → TERMINATED（终态锁定）"""
        contract = MagicMock(status='EXECUTING')
        transition_contract(contract, 'TERMINATED')
        assert contract.status == 'TERMINATED'

        # 终态后任何操作都应抛出异常
        with pytest.raises(ValueError, match="Cannot transition from terminal state"):
            transition_contract(contract, 'DRAFT')


# =============================================================================
# ==================  TEST CLASS 5: ECN状态机（基于框架）  ====================
# =============================================================================

class TestEcnStateMachineIntegration:
    """ECN 状态机集成测试（使用框架 StateMachine 基类）"""

    @pytest.fixture
    def mock_ecn(self):
        ecn = MagicMock()
        ecn.id = 100
        ecn.status = 'DRAFT'
        ecn.__class__.__name__ = 'Ecn'
        return ecn

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db

    def test_ecn_draft_to_pending_review(self, mock_ecn, mock_db):
        """ECN：DRAFT → PENDING_REVIEW ✅"""
        from app.core.state_machine.ecn import EcnStateMachine
        sm = EcnStateMachine(mock_ecn, mock_db)
        sm.transition_to('PENDING_REVIEW')
        assert mock_ecn.status == 'PENDING_REVIEW'

    def test_ecn_pending_to_approved(self, mock_ecn, mock_db):
        """ECN：PENDING_REVIEW → APPROVED ✅"""
        from app.core.state_machine.ecn import EcnStateMachine
        mock_ecn.status = 'PENDING_REVIEW'
        sm = EcnStateMachine(mock_ecn, mock_db)
        sm.transition_to('APPROVED')
        assert mock_ecn.status == 'APPROVED'

    def test_ecn_pending_to_rejected(self, mock_ecn, mock_db):
        """ECN：PENDING_REVIEW → REJECTED ✅"""
        from app.core.state_machine.ecn import EcnStateMachine
        mock_ecn.status = 'PENDING_REVIEW'
        sm = EcnStateMachine(mock_ecn, mock_db)
        sm.transition_to('REJECTED')
        assert mock_ecn.status == 'REJECTED'

    def test_ecn_rejected_to_draft(self, mock_ecn, mock_db):
        """ECN：REJECTED → DRAFT ✅（修改后重提）"""
        from app.core.state_machine.ecn import EcnStateMachine
        mock_ecn.status = 'REJECTED'
        sm = EcnStateMachine(mock_ecn, mock_db)
        sm.transition_to('DRAFT')
        assert mock_ecn.status == 'DRAFT'

    def test_ecn_invalid_transition_raises(self, mock_ecn, mock_db):
        """ECN：DRAFT → APPROVED ❌（跳过审核步骤）"""
        from app.core.state_machine.ecn import EcnStateMachine
        from app.core.state_machine.exceptions import InvalidStateTransitionError
        sm = EcnStateMachine(mock_ecn, mock_db)
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to('APPROVED')

    def test_ecn_can_transition_to_returns_false_for_invalid(self, mock_ecn, mock_db):
        """can_transition_to 对非法转换返回 False"""
        from app.core.state_machine.ecn import EcnStateMachine
        sm = EcnStateMachine(mock_ecn, mock_db)
        can, reason = sm.can_transition_to('APPROVED')
        assert can is False
        assert reason != ''

    def test_ecn_get_allowed_transitions(self, mock_ecn, mock_db):
        """get_allowed_transitions 返回正确的允许状态列表"""
        from app.core.state_machine.ecn import EcnStateMachine
        sm = EcnStateMachine(mock_ecn, mock_db)
        allowed = sm.get_allowed_transitions()
        assert 'PENDING_REVIEW' in allowed
        assert 'CANCELLED' in allowed
        assert 'APPROVED' not in allowed  # DRAFT 不能直接到 APPROVED
