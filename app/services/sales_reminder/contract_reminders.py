# -*- coding: utf-8 -*-
"""
销售提醒服务 - 合同提醒
"""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import ContractStatusEnum
from app.models.notification import Notification
from app.models.sales import Contract
from app.services.sales_reminder.base import create_notification


def notify_contract_signed(db: Session, contract_id: int) -> Optional[Notification]:
    """
    合同签订提醒
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or not contract.owner_id:
        return None

    return create_notification(
        db=db,
        user_id=contract.owner_id,
        notification_type="CONTRACT_SIGNED",
        title=f"合同已签订：{contract.contract_code}",
        content=f"合同 {contract.contract_code} 已签订，金额：{contract.contract_amount}，请及时跟进后续流程。",
        source_type="contract",
        source_id=contract.id,
        link_url=f"/sales/contracts/{contract.id}",
        priority="HIGH",
        extra_data={
            "contract_code": contract.contract_code,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "signed_date": contract.signed_date.isoformat() if contract.signed_date else None
        }
    )


def notify_contract_expiring(db: Session) -> int:
    """
    Issue 3.4: 合同到期提醒
    检查合同到期时间，在到期前30天、15天、7天发送提醒
    """
    today = date.today()
    count = 0

    # 查询所有有效的合同（使用正确的枚举值）
    contracts = db.query(Contract).filter(
        Contract.status.in_([ContractStatusEnum.SIGNED, ContractStatusEnum.ACTIVE])
    ).all()

    for contract in contracts:
        if not contract.delivery_deadline:
            continue

        deadline = contract.delivery_deadline
        days_left = (deadline - today).days

        # 即将到期（30天、15天、7天前）
        if days_left in settings.SALES_CONTRACT_EXPIRE_REMINDER_DAYS and days_left > 0:
            # 获取需要通知的用户：合同负责人、项目经理、财务
            user_ids = set()
            if contract.owner_id:
                user_ids.add(contract.owner_id)
            if contract.project_id:
                project = contract.project
                if project and project.pm_id:
                    user_ids.add(project.pm_id)

            for user_id in user_ids:
                existing = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.source_type == "contract",
                        Notification.source_id == contract.id,
                        Notification.notification_type == "CONTRACT_EXPIRING",
                        Notification.created_at >= datetime.combine(today, datetime.min.time())
                    )
                ).first()

                # 检查是否已发送过相同天数的提醒
                if existing and existing.extra_data:
                    existing_days_left = existing.extra_data.get('days_left')
                    if existing_days_left == days_left:
                        continue

                if not existing:
                    priority = "URGENT" if days_left == 7 else ("HIGH" if days_left == 15 else "NORMAL")
                    create_notification(
                        db=db,
                        user_id=user_id,
                        notification_type="CONTRACT_EXPIRING",
                        title=f"合同即将到期：{contract.contract_code}（{days_left}天后）",
                        content=f"合同 {contract.contract_code} 的交期将在 {days_left} 天后（{deadline}）到期，请及时跟进。",
                        source_type="contract",
                        source_id=contract.id,
                        link_url=f"/sales/contracts/{contract.id}",
                        priority=priority,
                        extra_data={
                            "contract_code": contract.contract_code,
                            "delivery_deadline": deadline.isoformat(),
                            "days_left": days_left
                        }
                    )
                    count += 1

    return count
