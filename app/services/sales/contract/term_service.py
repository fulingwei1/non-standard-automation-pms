# -*- coding: utf-8 -*-
"""
合同条款管理服务

处理合同条款的增删改查
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.sales.contracts import ContractTerm
from app.schemas.sales.contract_enhanced import ContractTermCreate
from app.utils.db_helpers import delete_obj, save_obj


class ContractTermService:
    """合同条款管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def add_term(self, contract_id: int, term_data: ContractTermCreate) -> ContractTerm:
        """添加条款"""
        term = ContractTerm(contract_id=contract_id, **term_data.model_dump())
        save_obj(self.db, term)
        return term

    def get_terms(self, contract_id: int) -> List[ContractTerm]:
        """获取条款列表"""
        return (
            self.db.query(ContractTerm)
            .filter(ContractTerm.contract_id == contract_id)
            .all()
        )

    def update_term(self, term_id: int, term_content: str) -> Optional[ContractTerm]:
        """更新条款"""
        term = self.db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        if term:
            term.term_content = term_content
            self.db.commit()
            self.db.refresh(term)
        return term

    def delete_term(self, term_id: int) -> bool:
        """删除条款"""
        term = self.db.query(ContractTerm).filter(ContractTerm.id == term_id).first()
        if term:
            delete_obj(self.db, term)
            return True
        return False
