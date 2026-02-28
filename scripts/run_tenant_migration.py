#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租户数据迁移主脚本

完整的迁移流程：
1. 创建默认租户
2. 迁移数据
3. 验证数据
4. 生成报告

Usage:
    python scripts/run_tenant_migration.py [--dry-run] [--skip-verification]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect
from app.models.base import get_db_session, get_engine

# 导入子脚本功能
# 由于这些是脚本文件，我们需要直接调用它们的函数
# 先导入必要的模块

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationOrchestrator:
    """迁移流程编排器"""
    
    def __init__(self, dry_run: bool = False, skip_verification: bool = False):
        self.dry_run = dry_run
        self.skip_verification = skip_verification
        self.start_time = datetime.now()
        self.report = {
            'start_time': self.start_time.isoformat(),
            'dry_run': dry_run,
            'steps': [],
            'success': False,
            'error': None
        }
    
    def add_step_result(self, step_name: str, success: bool, details: Dict = None):
        """添加步骤结果"""
        step = {
            'name': step_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.report['steps'].append(step)
        return success
    
    def step_create_tenant(self) -> bool:
        """步骤1: 创建默认租户"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📝 步骤 1/4: 创建默认租户")
        logger.info("=" * 70)
        
        try:
            # 导入并执行创建租户函数
            from app.models.tenant import Tenant, TenantStatus, TenantPlan
            
            with get_db_session() as db:
                # 检查租户是否已存在
                tenant_code = "jinkaibo"
                tenant = db.query(Tenant).filter(
                    Tenant.tenant_code == tenant_code
                ).first()
                
                if not tenant:
                    # 创建新租户
                    tenant = Tenant(
                        tenant_code=tenant_code,
                        tenant_name="金凯博自动化测试",
                        status=TenantStatus.ACTIVE.value,
                        plan_type=TenantPlan.ENTERPRISE.value,
                        max_users=-1,
                        max_roles=-1,
                        max_storage_gb=100,
                        contact_name="系统管理员",
                        contact_email="admin@jinkaibo.com",
                        expired_at=None,
                        settings={
                            "is_default": True,
                            "created_by_migration": True,
                            "migration_date": datetime.now().isoformat()
                        }
                    )
                    db.add(tenant)
                    db.flush()
                    logger.info(f"✅ 创建默认租户: {tenant.tenant_code} (ID: {tenant.id})")
                else:
                    logger.info(f"✅ 默认租户已存在: {tenant.tenant_code} (ID: {tenant.id})")
                
                details = {
                    'tenant_id': tenant.id,
                    'tenant_code': tenant.tenant_code,
                    'tenant_name': tenant.tenant_name
                }
                
                self.add_step_result('create_tenant', True, details)
                return True
                
        except Exception as e:
            logger.error(f"❌ 创建租户失败: {e}", exc_info=True)
            self.add_step_result('create_tenant', False, {'error': str(e)})
            return False
    
    def step_migrate_data(self) -> bool:
        """步骤2: 迁移数据"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📦 步骤 2/4: 迁移数据到默认租户")
        logger.info("=" * 70)
        
        try:
            # 获取租户ID
            from app.models.tenant import Tenant
            
            with get_db_session() as db:
                tenant = db.query(Tenant).filter(
                    Tenant.tenant_code == "jinkaibo"
                ).first()
                
                if not tenant:
                    logger.error("❌ 未找到默认租户")
                    return False
                
                tenant_id = tenant.id
                logger.info(f"使用租户: {tenant.tenant_code} (ID: {tenant_id})")
            
            # 导入并执行迁移
            import subprocess
            
            cmd = [sys.executable, 'scripts/migrate_to_default_tenant.py']
            if self.dry_run:
                cmd.append('--dry-run')
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 输出迁移日志
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    logger.info(line)
            
            if result.returncode != 0:
                if result.stderr:
                    logger.error(result.stderr)
                self.add_step_result('migrate_data', False, {'error': 'Migration script failed'})
                return False
            
            self.add_step_result('migrate_data', True, {})
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据迁移失败: {e}", exc_info=True)
            self.add_step_result('migrate_data', False, {'error': str(e)})
            return False
    
    def step_verify_data(self) -> bool:
        """步骤3: 验证数据"""
        if self.skip_verification:
            logger.info("")
            logger.info("⏭️  跳过数据验证")
            self.add_step_result('verify_data', True, {'skipped': True})
            return True
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🔍 步骤 3/4: 验证数据完整性")
        logger.info("=" * 70)
        
        try:
            # 导入并执行验证
            import subprocess
            
            result = subprocess.run(
                [sys.executable, 'scripts/verify_tenant_migration.py'],
                capture_output=True,
                text=True
            )
            
            # 输出验证日志
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    logger.info(line)
            
            success = (result.returncode == 0)
            
            if not success and result.stderr:
                logger.error(result.stderr)
            
            self.add_step_result('verify_data', success, {})
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 数据验证失败: {e}", exc_info=True)
            self.add_step_result('verify_data', False, {'error': str(e)})
            return False
    
    def step_generate_report(self):
        """步骤4: 生成报告"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📄 步骤 4/4: 生成迁移报告")
        logger.info("=" * 70)
        
        self.report['end_time'] = datetime.now().isoformat()
        self.report['duration_seconds'] = (datetime.now() - self.start_time).total_seconds()
        
        # 判断整体成功
        all_steps_success = all(step['success'] for step in self.report['steps'])
        self.report['success'] = all_steps_success and not self.dry_run
        
        # 保存报告
        report_dir = Path(__file__).parent.parent / 'data'
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'tenant_migration_report_{timestamp}.json'
        report_path = report_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ 迁移报告已保存: {report_path}")
        
        self.add_step_result('generate_report', True, {'report_path': str(report_path)})
    
    def run(self) -> bool:
        """运行完整的迁移流程"""
        logger.info("=" * 70)
        logger.info("🚀 租户数据迁移流程启动")
        logger.info("=" * 70)
        
        if self.dry_run:
            logger.info("")
            logger.info("🔍 运行模式: DRY-RUN（预览模式，不会修改数据）")
        else:
            logger.info("")
            logger.info("⚡ 运行模式: 正式迁移")
            logger.info("")
            logger.warning("⚠️  此操作将修改数据库，请确保已备份！")
            logger.info("")
            
            response = input("确认继续？输入 'YES' 继续: ")
            if response != 'YES':
                logger.info("已取消迁移")
                return False
        
        try:
            # 检查数据库
            engine = get_engine()
            logger.info(f"数据库: {engine.url}")
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'tenants' not in tables:
                logger.error("❌ tenants 表不存在，请先执行数据库迁移")
                return False
            
            # 步骤1: 创建默认租户
            if not self.step_create_tenant():
                logger.error("❌ 步骤1失败，停止迁移")
                return False
            
            # 步骤2: 迁移数据
            if not self.step_migrate_data():
                logger.error("❌ 步骤2失败，停止迁移")
                return False
            
            # 步骤3: 验证数据
            if not self.step_verify_data():
                logger.error("❌ 步骤3失败")
                if not self.dry_run:
                    logger.warning("")
                    logger.warning("⚠️  验证失败！建议执行回滚:")
                    logger.warning("   python scripts/rollback_tenant_migration.py --confirm")
                return False
            
            # 步骤4: 生成报告
            self.step_generate_report()
            
            # 打印最终结果
            logger.info("")
            logger.info("=" * 70)
            if self.dry_run:
                logger.info("✅ 迁移预览完成！")
                logger.info("")
                logger.info("要执行实际迁移，请运行:")
                logger.info("   python scripts/run_tenant_migration.py")
            else:
                logger.info("🎉 数据迁移成功完成！")
                logger.info("")
                logger.info("下一步:")
                logger.info("  1. 检查迁移报告")
                logger.info("  2. 测试应用功能")
                logger.info("  3. 如有问题，可使用回滚脚本")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移流程发生错误: {e}", exc_info=True)
            self.report['error'] = str(e)
            self.step_generate_report()
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='租户数据迁移主流程')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行迁移')
    parser.add_argument('--skip-verification', action='store_true', help='跳过数据验证步骤')
    args = parser.parse_args()
    
    # 创建编排器并运行
    orchestrator = MigrationOrchestrator(
        dry_run=args.dry_run,
        skip_verification=args.skip_verification
    )
    
    success = orchestrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
