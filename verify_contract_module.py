#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
合同管理模块快速验证脚本

用法：
    python verify_contract_module.py
"""

import sys
from decimal import Decimal
from datetime import date

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.sales.contracts import Contract, ContractTerm, ContractApproval
from app.schemas.sales.contract_enhanced import ContractCreate, ContractTermCreate
from app.services.sales.contract_enhanced import ContractEnhancedService


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")


def print_info(message: str):
    """打印信息"""
    print(f"ℹ️  {message}")


def verify_contract_crud(db: Session):
    """验证合同CRUD功能"""
    print("\n" + "="*50)
    print("📋 测试合同CRUD功能")
    print("="*50)
    
    try:
        # 1. 创建合同
        print_info("1. 测试创建合同...")
        contract_data = ContractCreate(
            contract_name="【测试】自动化设备采购合同",
            contract_type="sales",
            customer_id=1,
            total_amount=Decimal("120000.00"),
            received_amount=Decimal("0.00"),
            signing_date=date.today(),
            contract_period=12,
            payment_terms="分3期付款",
            sales_owner_id=1,
        )
        contract = ContractEnhancedService.create_contract(db, contract_data, user_id=1)
        print_success(f"创建合同成功：{contract.contract_code}")
        
        # 2. 查询合同
        print_info("2. 测试查询合同...")
        found = ContractEnhancedService.get_contract(db, contract.id)
        assert found is not None
        assert found.contract_name == contract_data.contract_name
        print_success(f"查询合同成功：ID={found.id}")
        
        # 3. 列表查询
        print_info("3. 测试列表查询...")
        contracts, total = ContractEnhancedService.get_contracts(db, limit=10)
        assert total >= 1
        print_success(f"查询列表成功：共{total}个合同")
        
        # 4. 统计功能
        print_info("4. 测试统计功能...")
        stats = ContractEnhancedService.get_contract_stats(db)
        assert stats.total_count >= 1
        print_success(f"统计成功：草稿{stats.draft_count}个，总金额{stats.total_amount}元")
        
        return contract
        
    except Exception as e:
        print_error(f"CRUD测试失败: {str(e)}")
        raise


def verify_contract_terms(db: Session, contract: Contract):
    """验证合同条款功能"""
    print("\n" + "="*50)
    print("📝 测试合同条款功能")
    print("="*50)
    
    try:
        # 1. 添加条款
        print_info("1. 测试添加条款...")
        term_data = ContractTermCreate(
            term_type="payment",
            term_content="首付30%，发货前40%，验收后30%"
        )
        term = ContractEnhancedService.add_term(db, contract.id, term_data)
        print_success(f"添加条款成功：{term.term_type}")
        
        # 2. 查询条款
        print_info("2. 测试查询条款...")
        terms = ContractEnhancedService.get_terms(db, contract.id)
        assert len(terms) >= 1
        print_success(f"查询成功：共{len(terms)}个条款")
        
        # 3. 更新条款
        print_info("3. 测试更新条款...")
        updated = ContractEnhancedService.update_term(db, term.id, "更新后的条款内容")
        assert updated.term_content == "更新后的条款内容"
        print_success("更新条款成功")
        
    except Exception as e:
        print_error(f"条款测试失败: {str(e)}")
        raise


def verify_approval_flow(db: Session, contract: Contract):
    """验证审批流程"""
    print("\n" + "="*50)
    print("✅ 测试审批流程")
    print("="*50)
    
    try:
        # 1. 提交审批
        print_info("1. 测试提交审批...")
        contract = ContractEnhancedService.submit_for_approval(db, contract.id, user_id=1)
        assert contract.status == "approving"
        print_success(f"提交审批成功，状态：{contract.status}")
        
        # 2. 查看审批记录
        print_info("2. 测试查看审批记录...")
        approvals = db.query(ContractApproval).filter(
            ContractApproval.contract_id == contract.id
        ).all()
        assert len(approvals) >= 1
        print_success(f"查看成功：共{len(approvals)}级审批")
        
        # 3. 审批通过
        print_info("3. 测试审批通过...")
        approval = approvals[0]
        contract = ContractEnhancedService.approve_contract(
            db, contract.id, approval.id, user_id=2, opinion="同意"
        )
        print_success(f"审批通过，合同状态：{contract.status}")
        
        # 4. 验证审批流程分级
        print_info("4. 测试审批流程分级...")
        
        # 小额合同（<10万）
        small_contract = ContractEnhancedService.create_contract(
            db,
            ContractCreate(
                contract_name="小额合同",
                contract_type="sales",
                customer_id=1,
                total_amount=Decimal("80000.00"),
            ),
            user_id=1
        )
        small_contract = ContractEnhancedService.submit_for_approval(
            db, small_contract.id, user_id=1
        )
        small_approvals = db.query(ContractApproval).filter(
            ContractApproval.contract_id == small_contract.id
        ).all()
        assert len(small_approvals) == 1
        assert small_approvals[0].approval_role == "sales_manager"
        print_success("小额合同审批流程正确（1级：销售经理）")
        
        # 中额合同（10-50万）
        medium_contract = ContractEnhancedService.create_contract(
            db,
            ContractCreate(
                contract_name="中额合同",
                contract_type="sales",
                customer_id=1,
                total_amount=Decimal("300000.00"),
            ),
            user_id=1
        )
        medium_contract = ContractEnhancedService.submit_for_approval(
            db, medium_contract.id, user_id=1
        )
        medium_approvals = db.query(ContractApproval).filter(
            ContractApproval.contract_id == medium_contract.id
        ).all()
        assert len(medium_approvals) == 1
        assert medium_approvals[0].approval_role == "sales_director"
        print_success("中额合同审批流程正确（1级：销售总监）")
        
        # 大额合同（>50万）
        large_contract = ContractEnhancedService.create_contract(
            db,
            ContractCreate(
                contract_name="大额合同",
                contract_type="sales",
                customer_id=1,
                total_amount=Decimal("800000.00"),
            ),
            user_id=1
        )
        large_contract = ContractEnhancedService.submit_for_approval(
            db, large_contract.id, user_id=1
        )
        large_approvals = db.query(ContractApproval).filter(
            ContractApproval.contract_id == large_contract.id
        ).all()
        assert len(large_approvals) == 3
        assert large_approvals[0].approval_role == "sales_director"
        assert large_approvals[1].approval_role == "finance_director"
        assert large_approvals[2].approval_role == "general_manager"
        print_success("大额合同审批流程正确（3级：销售总监→财务总监→总经理）")
        
    except Exception as e:
        print_error(f"审批流程测试失败: {str(e)}")
        raise


def verify_status_flow(db: Session, contract: Contract):
    """验证状态流转"""
    print("\n" + "="*50)
    print("🔄 测试状态流转")
    print("="*50)
    
    try:
        # 假设已经审批通过
        contract.status = "approved"
        db.commit()
        
        # 1. 已审批 -> 已签署
        print_info("1. 测试：已审批 -> 已签署")
        contract = ContractEnhancedService.mark_as_signed(db, contract.id)
        assert contract.status == "signed"
        print_success("状态流转成功：signed")
        
        # 2. 已签署 -> 执行中
        print_info("2. 测试：已签署 -> 执行中")
        contract = ContractEnhancedService.mark_as_executing(db, contract.id)
        assert contract.status == "executing"
        print_success("状态流转成功：executing")
        
        # 3. 执行中 -> 已完成
        print_info("3. 测试：执行中 -> 已完成")
        contract = ContractEnhancedService.mark_as_completed(db, contract.id)
        assert contract.status == "completed"
        print_success("状态流转成功：completed")
        
    except Exception as e:
        print_error(f"状态流转测试失败: {str(e)}")
        raise


def cleanup(db: Session):
    """清理测试数据"""
    print("\n" + "="*50)
    print("🧹 清理测试数据")
    print("="*50)
    
    try:
        # 删除所有测试合同
        test_contracts = db.query(Contract).filter(
            Contract.contract_name.like("%【测试】%")
        ).all()
        
        for contract in test_contracts:
            db.delete(contract)
        
        db.commit()
        print_success(f"清理完成：删除了{len(test_contracts)}个测试合同")
        
    except Exception as e:
        print_error(f"清理失败: {str(e)}")
        db.rollback()


def main():
    """主函数"""
    print("\n" + "="*50)
    print("🚀 合同管理模块验证脚本")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 1. 验证CRUD
        contract = verify_contract_crud(db)
        
        # 2. 验证条款管理
        verify_contract_terms(db, contract)
        
        # 3. 验证审批流程
        verify_approval_flow(db, contract)
        
        # 4. 验证状态流转
        verify_status_flow(db, contract)
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！")
        print("="*50)
        
        print("\n📊 测试总结：")
        print("  ✅ 合同CRUD功能正常")
        print("  ✅ 条款管理功能正常")
        print("  ✅ 审批流程正常（支持分级）")
        print("  ✅ 状态流转正常")
        
    except Exception as e:
        print("\n" + "="*50)
        print(f"❌ 测试失败: {str(e)}")
        print("="*50)
        sys.exit(1)
        
    finally:
        # 清理测试数据
        cleanup(db)
        db.close()


if __name__ == "__main__":
    main()
