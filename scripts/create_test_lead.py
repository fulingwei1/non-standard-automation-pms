#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试线索数据
"""

import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_session
from app.models.enums import LeadStatusEnum
from app.models.sales import Lead
from app.models.user import User


def create_test_lead():
    """创建测试线索"""
    db = get_session()
    try:
        # 检查是否已有测试线索
        existing = db.query(Lead).filter(Lead.lead_code == "LD-TEST-001").first()
        if existing:
            print(f"测试线索已存在: ID={existing.id}")
            return existing.id

        # 获取admin用户
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("❌ 未找到admin用户")
            return None

        # 创建测试线索
        lead = Lead(
            lead_code="LD-TEST-001",
            source="测试",
            customer_name="测试客户",
            industry="新能源",
            contact_name="张总",
            contact_phone="13800138000",
            demand_summary="电池测试设备需求",
            owner_id=admin.id,
            status=LeadStatusEnum.NEW.value
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        print(f"✅ 创建测试线索成功: ID={lead.id}, Code={lead.lead_code}")
        return lead.id
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    create_test_lead()






