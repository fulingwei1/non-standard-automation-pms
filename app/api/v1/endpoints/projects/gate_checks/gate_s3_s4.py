# -*- coding: utf-8 -*-
"""
gate_s3_s4 阶段门检查

包含gate_s3_s4相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Project



def check_gate_s3_to_s4(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G3: S3→S4 阶段门校验 - 立项评审通过、合同签订

    Issue 1.3: 细化校验条件
    """
    missing = []

    # 检查合同签订（如果配置了需要合同）
    from app.core.config import settings
    if getattr(settings, 'PROJECT_REQUIRE_CONTRACT', True):
        if not project.contract_id and not project.contract_no:
            missing.append("合同未签订（请关联合同或填写合同编号）")

        # 如果关联了合同，检查合同状态
        if project.contract_id:
            from app.models.sales import Contract
            contract = db.query(Contract).filter(Contract.id == project.contract_id).first()
            if contract and contract.status != "SIGNED":
                missing.append(f"合同状态为{contract.status}，需为已签订(SIGNED)")

    # 检查立项评审通过
    # 方式1：检查评审记录
    from app.models.technical_review import TechnicalReview
    approval_review = db.query(TechnicalReview).filter(
        TechnicalReview.project_id == project.id,
        TechnicalReview.review_type.in_(["PROPOSAL", "APPROVAL", "PROJECT_APPROVAL"]),
        TechnicalReview.status == "COMPLETED"
    ).first()

    if not approval_review:
        # 方式2：检查项目状态是否已过立项审批
        if project.status not in ["ST08", "ST09", "ST10", "ST11", "ST12", "ST13", "ST14", "ST15",
                                   "ST16", "ST17", "ST18", "ST19", "ST20", "ST21", "ST22", "ST23",
                                   "ST24", "ST25", "ST26", "ST27", "ST28", "ST29", "ST30"]:
            missing.append("立项评审未通过（请完成立项评审）")

    return (len(missing) == 0, missing)


