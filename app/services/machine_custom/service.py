# -*- coding: utf-8 -*-
"""
机台定制服务层

提供机台进度、BOM、文档、服务历史等业务逻辑
"""

import uuid
from decimal import Decimal
from pathlib import Path as FilePath
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import BomHeader
from app.models.project import Machine, ProjectDocument
from app.models.service import ServiceRecord
from app.models.user import User
from app.utils.db_helpers import save_obj
from app.common.query_filters import apply_pagination

# 文档类型到权限代码的映射
DOC_TYPE_PERMISSION_MAP = {
    "CIRCUIT_DIAGRAM": "machine:doc_circuit",
    "PLC_PROGRAM": "machine:doc_plc",
    "LABELWORK_PROGRAM": "machine:doc_vision",
    "VISION_PROGRAM": "machine:doc_vision",
    "MOTION_PROGRAM": "machine:doc_motion",
    "ROBOT_PROGRAM": "machine:doc_robot",
    "OPERATION_MANUAL": "machine:doc_manual",
    "DRAWING": "machine:doc_drawing",
    "BOM_DOCUMENT": "machine:doc_bom",
    "FAT_DOCUMENT": "machine:doc_other",
    "SAT_DOCUMENT": "machine:doc_other",
    "OTHER": "machine:doc_other",
}

# 文档上传目录
DOCUMENT_UPLOAD_DIR = FilePath(settings.UPLOAD_DIR) / "documents" / "machines"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class MachineCustomService:
    """机台定制服务"""

    def __init__(self, db: Session):
        self.db = db

    def update_machine_progress(
        self,
        machine: Machine,
        progress_pct: Decimal
    ) -> Machine:
        """
        更新机台进度并触发项目聚合计算

        Args:
            machine: 机台对象
            progress_pct: 进度百分比（0-100）

        Returns:
            更新后的机台对象
        """
        from app.services.machine_service import ProjectAggregationService

        machine.progress_pct = progress_pct
        save_obj(self.db, machine)

        # 更新项目聚合数据
        aggregation_service = ProjectAggregationService(self.db)
        aggregation_service.update_project_aggregation(machine.project_id)

        return machine

    def get_machine_bom_list(self, machine_id: int) -> List[Dict[str, Any]]:
        """
        获取机台的BOM列表

        Args:
            machine_id: 机台ID

        Returns:
            BOM列表
        """
        bom_headers = (
            self.db.query(BomHeader)
            .filter(BomHeader.machine_id == machine_id)
            .order_by(desc(BomHeader.created_at))
            .all()
        )

        result = []
        for bom in bom_headers:
            result.append({
                "id": bom.id,
                "bom_no": bom.bom_no,
                "bom_name": bom.bom_name,
                "version": bom.version,
                "is_latest": bom.is_latest,
                "status": bom.status,
                "total_items": bom.total_items,
                "total_amount": float(bom.total_amount) if bom.total_amount else 0,
            })

        return result

    def check_document_permission(self, user: User, doc_type: str) -> bool:
        """
        检查用户是否有访问特定文档类型的权限

        Args:
            user: 用户对象
            doc_type: 文档类型

        Returns:
            是否有权限
        """
        from app.core.auth import check_permission

        perm_code = DOC_TYPE_PERMISSION_MAP.get(doc_type.upper(), "machine:doc_other")
        return check_permission(user, perm_code, self.db)

    async def upload_document(
        self,
        machine: Machine,
        file: UploadFile,
        doc_type: str,
        user: User,
        doc_category: Optional[str] = None,
        doc_name: Optional[str] = None,
        doc_no: Optional[str] = None,
        version: str = "1.0",
        description: Optional[str] = None,
        machine_stage: Optional[str] = None,
    ) -> ProjectDocument:
        """
        上传机台文档

        Args:
            machine: 机台对象
            file: 上传的文件
            doc_type: 文档类型
            user: 当前用户
            doc_category: 文档分类
            doc_name: 文档名称
            doc_no: 文档编号
            version: 版本号
            description: 描述
            machine_stage: 关联的设备生命周期阶段

        Returns:
            创建的文档对象
        """
        # 验证文档类型
        valid_doc_types = [
            "CIRCUIT_DIAGRAM", "PLC_PROGRAM", "LABELWORK_PROGRAM",
            "BOM_DOCUMENT", "FAT_DOCUMENT", "SAT_DOCUMENT", "OTHER"
        ]
        if doc_type.upper() not in valid_doc_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的文档类型。有效值：{', '.join(valid_doc_types)}"
            )

        # 检查权限
        if not self.check_document_permission(user, doc_type):
            raise HTTPException(status_code=403, detail="您没有权限上传此类型的文档")

        # 保存文件
        file_ext = FilePath(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = DOCUMENT_UPLOAD_DIR / str(machine.id) / unique_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

        # 创建文档记录
        doc_data = {
            "project_id": machine.project_id,
            "machine_id": machine.id,
            "doc_type": doc_type,
            "doc_category": doc_category or machine_stage,
            "doc_name": doc_name or file.filename,
            "doc_no": doc_no,
            "version": version,
            "file_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
            "file_name": file.filename,
            "file_size": len(content),
            "file_type": file.content_type or file_ext[1:] if file_ext else None,
            "description": description,
            "uploaded_by": user.id,
            "status": "DRAFT",
        }

        document = ProjectDocument(**doc_data)
        save_obj(self.db, document)

        return document

    def get_machine_documents(
        self,
        machine: Machine,
        user: User,
        doc_type: Optional[str] = None,
        group_by_type: bool = True
    ) -> Dict[str, Any]:
        """
        获取机台文档列表

        Args:
            machine: 机台对象
            user: 当前用户
            doc_type: 文档类型筛选
            group_by_type: 是否按类型分组

        Returns:
            文档列表数据
        """
        query = self.db.query(ProjectDocument).filter(
            ProjectDocument.machine_id == machine.id
        )
        if doc_type:
            query = query.filter(ProjectDocument.doc_type == doc_type)

        all_documents = query.order_by(desc(ProjectDocument.created_at)).all()

        # 权限过滤
        accessible_documents = [
            doc for doc in all_documents
            if self.check_document_permission(user, doc.doc_type)
        ]

        if group_by_type:
            from app.schemas.project import ProjectDocumentResponse

            grouped = {}
            for doc in accessible_documents:
                dtype = doc.doc_type
                if dtype not in grouped:
                    grouped[dtype] = []
                grouped[dtype].append(ProjectDocumentResponse.model_validate(doc))

            return {
                "machine_id": machine.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                "documents_by_type": grouped,
                "total_count": len(accessible_documents),
            }
        else:
            from app.schemas.project import ProjectDocumentResponse

            return {
                "machine_id": machine.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                "documents": [
                    ProjectDocumentResponse.model_validate(doc)
                    for doc in accessible_documents
                ],
                "total_count": len(accessible_documents),
            }

    def get_document_download_path(
        self,
        document: ProjectDocument,
        user: User
    ) -> Tuple[FilePath, str]:
        """
        获取文档下载路径

        Args:
            document: 文档对象
            user: 当前用户

        Returns:
            (文件路径, 文件名)
        """
        # 检查权限
        if not self.check_document_permission(user, document.doc_type):
            raise HTTPException(status_code=403, detail="您没有权限下载此类型的文档")

        file_path = FilePath(document.file_path)
        upload_dir = FilePath(settings.UPLOAD_DIR)

        if not file_path.is_absolute():
            file_path = upload_dir / file_path

        # 安全检查：确保文件在上传目录内
        resolved_path = file_path.resolve()
        try:
            resolved_path.relative_to(upload_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="访问被拒绝")

        if not resolved_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return resolved_path, document.file_name

    def get_document_versions(
        self,
        document: ProjectDocument,
        user: User
    ) -> List[ProjectDocument]:
        """
        获取文档的所有版本

        Args:
            document: 文档对象
            user: 当前用户

        Returns:
            文档版本列表
        """
        # 检查权限
        if not self.check_document_permission(user, document.doc_type):
            raise HTTPException(status_code=403, detail="您没有权限查看此类型的文档版本")

        query = self.db.query(ProjectDocument).filter(
            ProjectDocument.machine_id == document.machine_id
        )

        # 根据 doc_no 或 doc_name 查询同一文档的不同版本
        if document.doc_no:
            query = query.filter(ProjectDocument.doc_no == document.doc_no)
        else:
            query = query.filter(ProjectDocument.doc_name == document.doc_name)

        all_versions = query.order_by(desc(ProjectDocument.created_at)).all()

        # 权限过滤
        return [
            doc for doc in all_versions
            if self.check_document_permission(user, doc.doc_type)
        ]

    def get_service_history(
        self,
        machine: Machine,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取机台服务历史记录

        Args:
            machine: 机台对象
            page: 页码
            page_size: 每页数量

        Returns:
            服务历史数据
        """
        query = self.db.query(ServiceRecord).filter(
            ServiceRecord.machine_no == machine.machine_no
        )

        total = query.count()
        offset = (page - 1) * page_size
        records = apply_pagination(
            query.order_by(desc(ServiceRecord.service_date)),
            offset,
            page_size
        ).all()

        history_items = []
        for record in records:
            history_items.append({
                "id": record.id,
                "record_no": record.record_no,
                "service_type": record.service_type,
                "service_date": record.service_date.isoformat() if record.service_date else None,
                "service_content": record.service_content,
                "service_result": record.service_result,
                "issues_found": record.issues_found,
                "solution_provided": record.solution_provided,
                "duration_hours": float(record.duration_hours) if record.duration_hours else None,
                "service_engineer_name": record.service_engineer_name,
                "customer_satisfaction": record.customer_satisfaction,
                "customer_feedback": record.customer_feedback,
                "location": record.location,
                "created_at": record.created_at.isoformat() if record.created_at else None
            })

        # 统计信息
        total_hours = sum([float(r.duration_hours or 0) for r in records])
        satisfaction_scores = [
            r.customer_satisfaction for r in records
            if r.customer_satisfaction
        ]
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores else None
        )

        return {
            "machine_id": machine.id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "summary": {
                "total_records": total,
                "total_service_hours": round(total_hours, 2),
                "avg_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None
            },
            "items": history_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
