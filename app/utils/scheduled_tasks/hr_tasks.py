# -*- coding: utf-8 -*-
"""
定时任务 - HR相关任务
包含：合同到期提醒、员工转正提醒
"""
import logging
from datetime import date, datetime, timedelta

from app.models.base import get_db_session

logger = logging.getLogger(__name__)


def check_contract_expiry_reminder():
    """
    合同到期提醒定时任务
    - 提前60天（两个月）、30天（一个月）、14天（两周）生成提醒
    - 已到期的合同也生成提醒
    """
    logger.info(f"[{datetime.now()}] 开始执行合同到期提醒检查...")

    try:
        from app.models.organization import ContractReminder, Employee, EmployeeContract

        with get_db_session() as db:
            today = date.today()
            reminders_created = 0

            # 定义提醒规则：(天数, 提醒类型)
            reminder_rules = [
                (60, "two_months"),
                (30, "one_month"),
                (14, "two_weeks"),
                (0, "expired"),  # 已到期
            ]

            # 查询所有生效中的合同
            active_contracts = db.query(EmployeeContract).filter(
                EmployeeContract.status == "active",
                EmployeeContract.end_date.isnot(None)
            ).all()

            for contract in active_contracts:
                if not contract.end_date:
                    continue

                days_until_expiry = (contract.end_date - today).days

                for days, reminder_type in reminder_rules:
                    # 检查是否需要生成该类型提醒
                    should_create = False

                    if reminder_type == "expired":
                        should_create = days_until_expiry <= 0
                    elif reminder_type == "two_months":
                        should_create = 30 < days_until_expiry <= 60
                    elif reminder_type == "one_month":
                        should_create = 14 < days_until_expiry <= 30
                    elif reminder_type == "two_weeks":
                        should_create = 0 < days_until_expiry <= 14

                    if not should_create:
                        continue

                    # 检查是否已存在相同类型的提醒
                    existing = db.query(ContractReminder).filter(
                        ContractReminder.contract_id == contract.id,
                        ContractReminder.reminder_type == reminder_type
                    ).first()

                    if existing:
                        continue

                    # 创建提醒记录
                    reminder = ContractReminder(
                        contract_id=contract.id,
                        employee_id=contract.employee_id,
                        reminder_type=reminder_type,
                        reminder_date=today,
                        contract_end_date=contract.end_date,
                        days_until_expiry=days_until_expiry if days_until_expiry > 0 else 0,
                        status="pending"
                    )
                    db.add(reminder)
                    reminders_created += 1

                    # 更新合同的提醒状态
                    contract.reminder_sent = True
                    contract.reminder_sent_at = datetime.now()

            db.commit()

            logger.info(
                f"合同到期提醒检查完成: 检查合同数={len(active_contracts)}, "
                f"生成提醒数={reminders_created}"
            )

            return {
                'contracts_checked': len(active_contracts),
                'reminders_created': reminders_created,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 合同到期提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_employee_confirmation_reminder():
    """
    员工转正提醒定时任务
    - 检查试用期即将结束的员工（提前7天提醒）
    - 自动生成转正事务记录
    """
    logger.info(f"[{datetime.now()}] 开始执行员工转正提醒检查...")

    try:
        from app.models.notification import Notification
        from app.models.organization import Employee, EmployeeHrProfile, HrTransaction

        with get_db_session() as db:
            today = date.today()
            reminder_date = today + timedelta(days=7)  # 提前7天
            reminders_created = 0

            # 查询试用期员工
            probation_employees = db.query(Employee).join(
                EmployeeHrProfile,
                Employee.id == EmployeeHrProfile.employee_id
            ).filter(
                Employee.status == "active",
                EmployeeHrProfile.employment_status == "probation",
                EmployeeHrProfile.probation_end_date.isnot(None),
                EmployeeHrProfile.probation_end_date <= reminder_date,
                EmployeeHrProfile.probation_end_date >= today
            ).all()

            for employee in probation_employees:
                profile = db.query(EmployeeHrProfile).filter(
                    EmployeeHrProfile.employee_id == employee.id
                ).first()

                if not profile or not profile.probation_end_date:
                    continue

                days_until_confirmation = (profile.probation_end_date - today).days

                # 检查是否已有转正事务记录
                existing = db.query(HrTransaction).filter(
                    HrTransaction.employee_id == employee.id,
                    HrTransaction.transaction_type == "confirmation",
                    HrTransaction.status == "pending"
                ).first()

                if existing:
                    continue

                # 创建转正事务记录
                transaction = HrTransaction(
                    employee_id=employee.id,
                    transaction_type="confirmation",
                    transaction_date=profile.probation_end_date,
                    status="pending",
                    confirmation_date=profile.probation_end_date,
                    remark=f"系统自动生成：{employee.name}试用期将于"
                           f"{profile.probation_end_date}结束，请安排转正评估"
                )
                db.add(transaction)
                reminders_created += 1

                # 创建系统通知
                notification = Notification(
                    user_id=None,  # 发给HR管理员
                    title="员工转正提醒",
                    content=f"员工 {employee.name}（{employee.employee_code}）的试用期将于"
                            f"{profile.probation_end_date}结束（还有{days_until_confirmation}天），"
                            f"请安排转正评估。",
                    notification_type="hr_reminder",
                    priority="high" if days_until_confirmation <= 3 else "normal",
                    is_read=False,
                    source_type="hr_transaction",
                    source_id=None
                )
                db.add(notification)

            db.commit()

            logger.info(
                f"员工转正提醒检查完成: 检查员工数={len(probation_employees)}, "
                f"生成提醒数={reminders_created}"
            )

            return {
                'employees_checked': len(probation_employees),
                'reminders_created': reminders_created,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 员工转正提醒检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
