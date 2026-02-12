# -*- coding: utf-8 -*-
"""
gate_s4_s5 阶段门检查

包含gate_s4_s5相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project



def check_gate_s4_to_s5(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G4: S4→S5 阶段门校验 - 方案评审通过、BOM发布

    Issue 1.3: 细化校验条件
    """
    missing = []

    # 检查方案评审已通过（有评审记录）
    from app.models.technical_review import TechnicalReview
    scheme_review = db.query(TechnicalReview).filter(
        TechnicalReview.project_id == project.id,
        TechnicalReview.review_type.in_(["DDR", "SCHEME", "DESIGN"]),
        TechnicalReview.status == "COMPLETED"
    ).first()

    if not scheme_review:
        from app.models.project import ProjectDocument
        design_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["DESIGN", "SCHEME"]),
            ProjectDocument.status == "APPROVED"
        ).count()

        if design_docs == 0:
            missing.append("方案评审未通过（请完成方案评审或上传已评审通过的设计文档）")

    # 检查BOM已发布
    from app.models.material import BomHeader
    released_boms = db.query(BomHeader).filter(
        BomHeader.project_id == project.id,
        BomHeader.status == "RELEASED"
    ).all()

    if not released_boms:
        missing.append("BOM未发布（请发布至少一个BOM）")
    else:
        # 检查每个机台是否有BOM
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                machine_bom = db.query(BomHeader).filter(
                    BomHeader.machine_id == machine.id,
                    BomHeader.status == "RELEASED"
                ).first()
                if not machine_bom:
                    missing.append(f"机台 {machine.machine_code} 的BOM未发布")

    # 检查关键设计文档已上传
    from app.models.project import ProjectDocument
    key_doc_types = ["DESIGN", "SCHEME", "DRAWING", "ELECTRICAL", "SOFTWARE"]
    key_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(key_doc_types),
        ProjectDocument.status == "APPROVED"
    ).count()

    if key_docs == 0:
        missing.append("关键设计文档未上传（请上传机械/电气/软件设计文档）")

    return (len(missing) == 0, missing)


