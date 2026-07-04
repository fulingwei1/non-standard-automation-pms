import uuid
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from app.models.bonus import TeamBonusAllocation
from app.models.user import User


def _bonus_user(db: Session) -> User:
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"hr18_{suffix}",
        email=f"hr18_{suffix}@example.com",
        password_hash="hash",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_team_bonus_allocation_sheet_rejects_total_over_allocation(db_session):
    """HR-18: Excel allocation totals must match the approved team bonus amount."""
    from app.services.bonus.bonus_allocation_parser import parse_allocation_sheet

    user_a = _bonus_user(db_session)
    user_b = _bonus_user(db_session)
    allocation = TeamBonusAllocation(
        project_id=1,
        total_bonus_amount=Decimal("10000.00"),
        allocation_method="manual",
        status="APPROVED",
    )
    db_session.add(allocation)
    db_session.commit()

    df = pd.DataFrame(
        [
            {
                "团队奖金分配ID*": allocation.id,
                "受益人ID*": user_a.id,
                "发放金额*": 15000,
                "发放日期*": "2026-07-04",
            },
            {
                "团队奖金分配ID*": allocation.id,
                "受益人ID*": user_b.id,
                "发放金额*": 15000,
                "发放日期*": "2026-07-04",
            },
        ]
    )

    valid_rows, errors = parse_allocation_sheet(df, db_session)

    assert valid_rows == []
    assert sorted(errors) == [2, 3]
    assert "合计必须等于团队总奖金 10000.00" in errors[2][0]
    assert "当前合计 30000.00" in errors[2][0]
