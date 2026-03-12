# -*- coding: utf-8 -*-
"""
合同附件管理服务

处理合同附件的上传、查询和删除
"""

from typing import List

from sqlalchemy.orm import Session

from app.models.sales.contracts import ContractAttachment
from app.schemas.sales.contract_enhanced import ContractAttachmentCreate
from app.utils.db_helpers import delete_obj, save_obj


class ContractAttachmentService:
    """合同附件管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def add_attachment(
        self, contract_id: int, attachment_data: ContractAttachmentCreate, user_id: int
    ) -> ContractAttachment:
        """上传附件"""
        attachment = ContractAttachment(
            contract_id=contract_id,
            uploaded_by=user_id,
            **attachment_data.model_dump(),
        )
        save_obj(self.db, attachment)
        return attachment

    def get_attachments(self, contract_id: int) -> List[ContractAttachment]:
        """获取附件列表"""
        return (
            self.db.query(ContractAttachment)
            .filter(ContractAttachment.contract_id == contract_id)
            .all()
        )

    def delete_attachment(self, attachment_id: int) -> bool:
        """删除附件"""
        attachment = (
            self.db.query(ContractAttachment)
            .filter(ContractAttachment.id == attachment_id)
            .first()
        )
        if attachment:
            delete_obj(self.db, attachment)
            return True
        return False
