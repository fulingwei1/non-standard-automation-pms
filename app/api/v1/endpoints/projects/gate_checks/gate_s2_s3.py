# -*- coding: utf-8 -*-
"""
gate_s2_s3 阶段门检查

包含gate_s2_s3相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Project



def check_gate_s2_to_s3(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G2: S2→S3 阶段门校验 - 需求规格书已确认、客户签字"""
    missing = []

    # 检查需求规格书文档
    from app.models.project import ProjectDocument
    spec_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
        ProjectDocument.status == "APPROVED"
    ).count()

    if spec_docs == 0:
        missing.append("需求规格书未确认（请上传并确认需求规格书）")

    # 检查验收标准
    if not project.requirements or "验收标准" not in project.requirements:
        missing.append("验收标准未明确（请在需求中明确验收标准）")

    return (len(missing) == 0, missing)
