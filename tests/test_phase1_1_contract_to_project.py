#!/usr/bin/env python3
"""
测试脚本：Phase 1.1 合同→项目自动生成功能验证
"""

import sys
import os

# 切换到项目根目录
os.chdir("/Users/flw/non-standard-automation-pm")

# 导入必要模块
sys.path.insert(0, ".")
from app.models.base import get_db_session
from app.models.sales.contracts import Contract
from app.models.project import Project
from app.models.project import ProjectMilestone
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select


def setup_test_data(db):
    """创建测试数据"""

    # 1. 创建测试用户
    try:
        result = db.execute(select(User).filter(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@test.com",
                password_hash=get_password_hash("admin123"),
                real_name="系统管理员",
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            db.flush()
            print("✓ 创建测试用户admin")
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return False

    # 2. 创建测试客户
    try:
        result = db.execute(select(Customer).where(Customer.name == "测试客户A"))
        if not result.scalar_one_or_none():
            customer = Customer(
                customer_code="C001",
                customer_name="测试客户A",
                contact_person="张三",
                contact_phone="13800138000",
                contact_email="zhangsan@test.com",
                address="测试客户A地址",
                is_active=True,
            )
            db.add(customer)
            db.flush()
            print("✓ 创建测试客户")
    except Exception as e:
        print(f"❌ 创建测试客户失败: {e}")
        return False

    # 3. 创建测试合同（含付款节点）
    try:
        import json

        payment_nodes = [
            {
                "name": "首付30%",
                "percentage": 30,
                "due_date": "2026-02-15",
                "description": "合同签订后30天内付款30%",
            },
            {
                "name": "发货70%",
                "percentage": 70,
                "due_date": "2026-04-15",
                "description": "设备发货后70%尾款",
            },
            {
                "name": "验收100%",
                "percentage": 100,
                "due_date": "2026-05-15",
                "description": "验收通过100%尾款",
            },
        ]

        contract = Contract(
            contract_code="TEST20260125001",
            customer_id=customer.id,
            contract_amount=100000.00,
            signed_date="2026-01-25",
            status="SIGNED",
            payment_nodes=json.dumps(payment_nodes, ensure_ascii=False),
            sow_text="测试项目SOW文本",
            acceptance_criteria=json.dumps(
                [
                    {
                        "criteria": "性能测试",
                        "type": "TECHNICAL",
                        "description": "设备性能必须达到X标准",
                    },
                    {
                        "criteria": "功能测试",
                        "type": "FUNCTIONAL",
                        "description": "设备功能必须完整",
                    },
                ],
                ensure_ascii=False,
            ),
            owner_id=admin.id,
        )

        db.add(contract)
        db.flush()
        print("✓ 创建测试合同，含3个付款节点")
        return True

    except Exception as e:
        print(f"❌ 创建测试合同失败: {e}")
        return False

    db.commit()
    return admin


def test_create_project_from_contract(db):
    """测试：从合同创建项目"""

    with get_db_session() as db:
        try:
            # 查询测试合同
            result = db.execute(
                select(Contract)
                .where(Contract.contract_code == "TEST20260125001")
                .options(selectinload(Customer))
            )
            contract = result.scalar_one_or_none()

            if not contract:
                print("❌ 测试合同不存在")
                return False

            print(f"测试合同ID: {contract.id}")
            print(f"合同付款节点: {contract.payment_nodes}")

            # 调用API创建项目
            import requests

            base_url = "http://127.0.0.1:8000/api/v1"

            # 1. 登录获取token
            login_data = {
                "username": "admin",
                "password": "admin123",
            }

            login_response = requests.post(
                f"{base_url}/api/v1/auth/login", json=login_data
            )

            if login_response.status_code != 200:
                print(f"❌ 登录失败：{login_response.text}")
                return False

            token = login_response.json().get("access_token")

            # 2. 调用API创建项目
            create_project_data = {
                "project_name": "TEST-TEST-客户A-自动化项目",
                "customer_id": customer.id,
                "contract_id": contract.id,
            }

            create_project_response = requests.post(
                f"{base_url}/api/v1/sales/contracts/{contract.id}/create-project",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=create_project_data,
            )

            if create_project_response.status_code != 201:
                print(f"❌ 创建项目失败：{create_project_response.text}")
                return False

            result = create_project_response.json()
            project_id = result.get("project_id")

            # 3. 验证项目创建成功
            with get_db_session() as db:
                project = db.query(Project).filter(Project.id == project_id).first()

                if not project:
                    print("❌ 项目未创建")
                    return False

                print("✅ 项目创建成功")
                print(f"项目ID: {project.id}")
                print(f"项目代码: {project.code}")
                print(f"项目金额: {project.amount}")
                print(f"客户ID: {project.customer_id}")
                print(f"合同ID: {project.contract_id}")

                # 验证付款计划和里程碑关联
                payment_plans_result = requests.get(
                    f"{base_url}/api/v1/projects/{project_id}/payment-plans",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                if payment_plans_result.status_code != 200:
                    print(f"❌ 查询收款计划失败：{payment_plans_result.text}")
                    return False

                payment_plans = payment_plans_result.json().get("data", {})

                print(f"✓ 收款计划数量: {len(payment_plans_result.get('count'))}")

                # 验证每个收款计划
                for plan in payment_plans_result.get("data", []):
                    print(f"  收款计划ID: {plan.get('id')}")
                    print(f" 付款节点: {plan.get('node_name')}")
                    print(f"百分比: {plan.get('percentage')}")
                    print(f"金额: {plan.get('amount')}")
                    print(f"里程碑ID: {plan.get('milestone_id')}")

                    # 验证里程碑是否存在
                    milestone = (
                        db.query(ProjectMilestone)
                        .filter(ProjectMilestone.id == plan.get("milestone_id"))
                        .first()
                    )

                    if milestone:
                        print("✓ 里程碑存在")
                    else:
                        print(f"❌ 里程碑不存在: {plan.get('milestone_id')}")

                    # 验证里程碑与收款计划的关联
                    if milestone.payment_plan_id == plan.get("id"):
                        print(f"✓ 里程碑已关联收款计划{plan.get('id')}")
                    else:
                        print(f"❌ 里程碑未关联收款计划: {plan.get('id')}")

            # 4. 验证收款计划字段
            all_plans = (
                db.query(ProjectPaymentPlan)
                .filter(ProjectPaymentPlan.project_id == project_id)
                .all()
            )

            if not all_plans:
                print("❌ 未找到收款计划")
                return False

            print(f"✓ 收款计划总数: {len(all_plans)}")

            # 验证每个收款计划的字段
            for plan in all_plans:
                if plan.milestone_id:
                    print(f"  ✅ 里程碑关联: {plan.id}")
                else:
                    print(f"  ❌ 未关联里程碑: {plan.id}")

            return True

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False

    db.rollback()
    return True


if __name__ == "__main__":
    print("=== Phase 1.1 功能测试 ===")

    # 1. 创建测试数据
    if not setup_test_data(get_db_session()):
        print("❌ 测试数据设置失败")
        sys.exit(1)

    # 2. 执行测试
    test_create_project_from_contract(get_db_session())

    print("\n=== 测试完成 ===")
    sys.exit(0)
