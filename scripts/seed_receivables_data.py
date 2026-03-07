#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应收账款演示数据种子脚本

为销售应收账款管理页面创建真实数据库演示数据：
- 合同数据
- 发票数据（含不同收款状态）
- 支持账龄分析和逾期展示
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.sales import Contract, Invoice
from app.models.project.customer import Customer
from app.models.user import User
import random


def get_or_create_test_user(db):
    """获取或创建测试用户"""
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            email="admin@example.com",
            real_name="系统管理员",
            department="销售部",
            position="销售经理",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_or_create_customers(db):
    """获取或创建演示客户"""
    customers_data = [
        {"customer_code": "CUST-001", "customer_name": "深圳华为技术有限公司", "industry": "通信设备"},
        {"customer_code": "CUST-002", "customer_name": "东莞新能源科技有限公司", "industry": "新能源"},
        {"customer_code": "CUST-003", "customer_name": "苏州精密制造股份有限公司", "industry": "精密制造"},
        {"customer_code": "CUST-004", "customer_name": "上海汽车电子有限公司", "industry": "汽车电子"},
        {"customer_code": "CUST-005", "customer_name": "杭州智能设备有限公司", "industry": "智能设备"},
        {"customer_code": "CUST-006", "customer_name": "成都航空航天科技公司", "industry": "航空航天"},
        {"customer_code": "CUST-007", "customer_name": "武汉光电子技术有限公司", "industry": "光电子"},
        {"customer_code": "CUST-008", "customer_name": "西安半导体设备有限公司", "industry": "半导体"},
    ]
    
    customers = []
    for cust_data in customers_data:
        customer = db.query(Customer).filter(Customer.customer_name == cust_data["customer_name"]).first()
        if not customer:
            customer = Customer(
                customer_code=cust_data["customer_code"],
                customer_name=cust_data["customer_name"],
                industry=cust_data["industry"],
                contact_person=f"{cust_data['customer_name'][:2]}经理",
                contact_phone=f"138{random.randint(10000000, 99999999)}",
                contact_email=f"contact@{cust_data['customer_name'][:4]}.com",
                status="ACTIVE",
                credit_limit=Decimal("1000000.00"),
            )
            db.add(customer)
            customers.append(customer)
        else:
            customers.append(customer)
    
    db.commit()
    return customers


def create_contracts(db, user, customers):
    """创建演示合同"""
    contracts = []
    
    contract_templates = [
        # 华为系列合同
        {"customer_idx": 0, "name": "ICT 功能测试设备采购合同", "amount": Decimal("1580000.00")},
        {"customer_idx": 0, "name": "5G 基站老化测试系统合同", "amount": Decimal("2350000.00")},
        {"customer_idx": 0, "name": "通信模块烧录设备合同", "amount": Decimal("890000.00")},
        
        # 新能源合同
        {"customer_idx": 1, "name": "电池管理系统测试线合同", "amount": Decimal("3200000.00")},
        {"customer_idx": 1, "name": "充电桩功能测试设备合同", "amount": Decimal("1150000.00")},
        
        # 精密制造合同
        {"customer_idx": 2, "name": "CNC 视觉检测系统合同", "amount": Decimal("780000.00")},
        {"customer_idx": 2, "name": "精密零件 ICT 测试设备合同", "amount": Decimal("920000.00")},
        
        # 汽车电子合同
        {"customer_idx": 3, "name": "汽车 ECU 功能测试台合同", "amount": Decimal("1680000.00")},
        {"customer_idx": 3, "name": "车载电子老化测试线合同", "amount": Decimal("2100000.00")},
        
        # 智能设备合同
        {"customer_idx": 4, "name": "智能家居控制器测试系统合同", "amount": Decimal("1350000.00")},
        
        # 航空航天合同
        {"customer_idx": 5, "name": "航空电子 FCT 测试设备合同", "amount": Decimal("4500000.00")},
        
        # 光电子合同
        {"customer_idx": 6, "name": "光模块功能测试系统合同", "amount": Decimal("1890000.00")},
        
        # 半导体合同
        {"customer_idx": 7, "name": "晶圆探针台测试设备合同", "amount": Decimal("5600000.00")},
    ]
    
    today = date.today()
    
    for i, template in enumerate(contract_templates):
        customer = customers[template["customer_idx"]]
        
        # 检查是否已存在
        existing = db.query(Contract).filter(Contract.contract_code == f"HT-{2025001 + i}").first()
        if existing:
            contracts.append(existing)
            continue
        
        # 创建合同
        contract_date = today - timedelta(days=random.randint(30, 365))
        contract = Contract(
            contract_code=f"HT-{2025001 + i}",
            contract_name=template["name"],
            contract_type="sales",
            customer_id=customer.id,
            total_amount=template["amount"],
            signing_date=contract_date,
            payment_terms="3-6-1",  # 30% 预付款，60% 发货款，10% 质保金
            status="executing",
            sales_owner_id=user.id,
        )
        db.add(contract)
        contracts.append(contract)
    
    db.commit()
    return contracts


def create_invoices(db, user, contracts):
    """创建演示发票（应收账款）"""
    invoices = []
    
    today = date.today()
    
    # 为每个合同创建发票
    for contract in contracts:
        contract_amount = contract.total_amount
        
        # 根据付款条款创建多张发票 (3-6-1)
        invoice_plans = [
            {"percentage": 0.3, "days_offset": -30, "description": "预付款"},
            {"percentage": 0.6, "days_offset": 30, "description": "发货款"},
            {"percentage": 0.1, "days_offset": 90, "description": "质保金"},
        ]
        
        for plan in invoice_plans:
            amount = contract_amount * Decimal(str(plan["percentage"]))
            issue_date = contract.signing_date + timedelta(days=plan["days_offset"])
            due_date = issue_date + timedelta(days=30)  # 30 天账期
            
            # 根据逾期天数决定状态
            days_overdue = (today - due_date).days
            
            if days_overdue > 60:
                payment_status = "OVERDUE"
                paid_ratio = 0
            elif days_overdue > 30:
                payment_status = random.choice(["OVERDUE", "PARTIAL"])
                paid_ratio = 0.5 if payment_status == "PARTIAL" else 0
            elif days_overdue > 0:
                payment_status = random.choice(["PENDING", "PARTIAL", "PAID"])
                if payment_status == "PARTIAL":
                    paid_ratio = 0.5
                elif payment_status == "PAID":
                    paid_ratio = 1.0
                else:
                    paid_ratio = 0
            else:
                payment_status = "PENDING"
                paid_ratio = 0
            
            # 检查是否已存在
            invoice_number = f"INV-{contract.contract_code.replace('HT-', '')}-{invoice_plans.index(plan) + 1}"
            existing = db.query(Invoice).filter(Invoice.invoice_code == invoice_number).first()
            if existing:
                invoices.append(existing)
                continue
            
            paid_amount = amount * Decimal(str(paid_ratio))
            
            invoice = Invoice(
                invoice_code=invoice_number,
                contract_id=contract.id,
                amount=amount,
                total_amount=amount,
                paid_amount=paid_amount,
                payment_status=payment_status,
                issue_date=issue_date,
                due_date=due_date,
                remark=f"{contract.contract_name} - {plan['description']}",
                status="ISSUED",
            )
            db.add(invoice)
            invoices.append(invoice)
    
    db.commit()
    
    # 打印统计
    print(f"\n✅ 创建了 {len(invoices)} 张发票")
    status_counts = {}
    for inv in invoices:
        status_counts[inv.payment_status] = status_counts.get(inv.payment_status, 0) + 1
    for status, count in status_counts.items():
        print(f"   - {status}: {count} 张")
    
    return invoices


def main():
    """主函数"""
    print("🌱 开始创建应收账款演示数据...\n")
    
    # 使用 SessionLocal 创建数据库会话
    from app.models.base import SessionLocal
    
    db = SessionLocal()
    
    try:
        # 1. 获取/创建测试用户
        user = get_or_create_test_user(db)
        print(f"✅ 使用用户：{user.real_name} ({user.username})")
        
        # 2. 获取/创建客户
        customers = get_or_create_customers(db)
        print(f"✅ 获取/创建了 {len(customers)} 个客户")
        
        # 3. 创建合同
        contracts = create_contracts(db, user, customers)
        print(f"✅ 获取/创建了 {len(contracts)} 个合同")
        
        # 4. 创建发票（应收账款）
        invoices = create_invoices(db, user, contracts)
        
        # 5. 统计汇总
        total_amount = sum(inv.total_amount or Decimal("0") for inv in invoices)
        total_paid = sum(inv.paid_amount or Decimal("0") for inv in invoices)
        total_unpaid = total_amount - total_paid
        
        print(f"\n📊 应收账款汇总:")
        print(f"   - 应收总额：¥{total_amount:,.2f}")
        print(f"   - 已收金额：¥{total_paid:,.2f}")
        print(f"   - 未收金额：¥{total_unpaid:,.2f}")
        print(f"   - 回款率：{(total_paid/total_amount*100) if total_amount > 0 else 0:.1f}%")
        
        print(f"\n✨ 演示数据创建完成！")
        print(f"   访问 http://localhost:5173/sales/receivables 查看应收账款管理页面")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
