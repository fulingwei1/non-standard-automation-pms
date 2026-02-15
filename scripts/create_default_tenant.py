#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认租户脚本
用于在数据迁移前创建默认租户

Usage:
    python scripts/create_default_tenant.py
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from sqlalchemy import text

from app.models.base import get_db_session, get_engine
from app.models.tenant import Tenant, TenantStatus, TenantPlan

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_default_tenant(db):
    """
    创建默认租户
    
    Args:
        db: 数据库会话
        
    Returns:
        Tenant: 创建的租户对象
    """
    tenant_code = "jinkaibo"
    
    # 检查租户是否已存在
    existing_tenant = db.query(Tenant).filter(
        Tenant.tenant_code == tenant_code
    ).first()
    
    if existing_tenant:
        logger.info(f"默认租户已存在: {existing_tenant.tenant_code} (ID: {existing_tenant.id})")
        return existing_tenant
    
    # 创建新租户
    tenant = Tenant(
        tenant_code=tenant_code,
        tenant_name="金凯博自动化测试",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.ENTERPRISE.value,
        max_users=-1,  # 无限制
        max_roles=-1,  # 无限制
        max_storage_gb=100,
        contact_name="系统管理员",
        contact_email="admin@jinkaibo.com",
        contact_phone="",
        expired_at=None,  # 永不过期
        settings={
            "is_default": True,
            "created_by_migration": True,
            "migration_date": datetime.now().isoformat()
        }
    )
    
    db.add(tenant)
    db.flush()
    
    logger.info(f"✅ 创建默认租户成功: {tenant.tenant_code} (ID: {tenant.id})")
    logger.info(f"   租户名称: {tenant.tenant_name}")
    logger.info(f"   套餐类型: {tenant.plan_type}")
    logger.info(f"   状态: {tenant.status}")
    
    return tenant


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始创建默认租户")
    logger.info("=" * 60)
    
    try:
        # 获取数据库引擎
        engine = get_engine()
        logger.info(f"数据库: {engine.url}")
        
        # 检查 tenants 表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "tenants" not in tables:
            logger.error("❌ tenants 表不存在，请先执行数据库迁移")
            return False
        
        # 创建默认租户
        with get_db_session() as db:
            tenant = create_default_tenant(db)
            
            if tenant:
                logger.info("")
                logger.info("=" * 60)
                logger.info("✅ 默认租户创建成功！")
                logger.info("=" * 60)
                logger.info(f"租户ID: {tenant.id}")
                logger.info(f"租户编码: {tenant.tenant_code}")
                logger.info(f"租户名称: {tenant.tenant_name}")
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ 创建默认租户失败")
                return False
                
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
