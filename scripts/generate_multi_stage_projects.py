#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成多阶段项目完整测试数据脚本
生成S1-S9各个阶段的项目，让项目看板有完整的数据展示

使用方法:
    python3 scripts/generate_multi_stage_projects.py
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.organization import Employee
from app.models.progress import Task
from app.models.project import (
    Customer,
    Machine,
    Project,
    ProjectMilestone,
    ProjectPaymentPlan,
)
from app.models.sales import Contract, Lead, Opportunity, Quote, QuoteVersion
from app.models.user import User

# 项目阶段配置：S1-S9，每个阶段生成1-2个项目
STAGE_CONFIGS = [
    {
        "stage": "S1",
        "status": "ST01",
        "health": "H1",
        "progress": 5,
        "count": 2,
        "name_prefix": "需求进入",
        "description": "项目刚签单，需求确认阶段"
    },
    {
        "stage": "S2",
        "status": "ST05",
        "health": "H1",
        "progress": 15,
        "count": 2,
        "name_prefix": "方案设计",
        "description": "正在进行方案设计和评审"
    },
    {
        "stage": "S3",
        "status": "ST13",
        "health": "H1",
        "progress": 30,
        "count": 2,
        "name_prefix": "采购备料",
        "description": "BOM已发布，正在采购物料"
    },
    {
        "stage": "S4",
        "status": "ST16",
        "health": "H1",
        "progress": 50,
        "count": 2,
        "name_prefix": "加工制造",
        "description": "物料到齐，正在进行机加工和钣金"
    },
    {
        "stage": "S5",
        "status": "ST20",
        "health": "H1",
        "progress": 70,
        "count": 2,
        "name_prefix": "装配调试",
        "description": "机械装配完成，正在进行电气调试"
    },
    {
        "stage": "S6",
        "status": "ST23",
        "health": "H1",
        "progress": 85,
        "count": 1,
        "name_prefix": "出厂验收",
        "description": "调试完成，等待FAT验收"
    },
    {
        "stage": "S7",
        "status": "ST25",
        "health": "H1",
        "progress": 90,
        "count": 1,
        "name_prefix": "包装发运",
        "description": "FAT通过，正在包装准备发货"
    },
    {
        "stage": "S8",
        "status": "ST27",
        "health": "H1",
        "progress": 95,
        "count": 1,
        "name_prefix": "现场安装",
        "description": "设备已发货，现场安装调试中"
    },
    {
        "stage": "S9",
        "status": "ST30",
        "health": "H4",
        "progress": 100,
        "count": 1,
        "name_prefix": "质保结项",
        "description": "SAT通过，项目已结项，进入质保期"
    }
]

# 设备类型列表
EQUIPMENT_TYPES = ["ICT", "FCT", "EOL", "AGING", "VISION", "ASSEMBLY", "BURN_IN"]

# 行业列表
INDUSTRIES = ["新能源汽车电子", "消费电子", "半导体", "通信设备", "工业自动化"]

# 客户名称模板
CUSTOMER_NAMES = [
    "深圳智行新能源汽车电子有限公司",
    "东莞华强电子科技有限公司",
    "苏州精密测试设备有限公司",
    "上海半导体测试技术有限公司",
    "北京智能装备制造有限公司",
    "广州自动化系统集成有限公司",
    "杭州视觉检测技术有限公司",
    "成都工业自动化设备有限公司",
    "武汉电子测试设备有限公司",
    "西安智能制造科技有限公司"
]


def get_or_create_users(db):
    """获取或创建用户"""
    users = {}

    # 获取现有用户或创建
    user_configs = [
        {"username": "sales_zhang", "name": "张销售", "dept": "销售部", "role": "销售经理"},
        {"username": "pm_li", "name": "李项目经理", "dept": "项目部", "role": "项目经理"},
        {"username": "mech_wang", "name": "王机械工程师", "dept": "技术部", "role": "机械工程师"},
        {"username": "elec_zhao", "name": "赵电气工程师", "dept": "技术部", "role": "电气工程师"},
        {"username": "soft_chen", "name": "陈软件工程师", "dept": "技术部", "role": "软件工程师"},
    ]

    for config in user_configs:
        user = db.query(User).filter(User.username == config["username"]).first()
        if not user:
            from app.core.security import get_password_hash

            # 创建员工
            emp = db.query(Employee).filter(Employee.employee_code == config["username"].upper().replace("_", "")).first()
            if not emp:
                emp = Employee(
                    employee_code=config["username"].upper().replace("_", ""),
                    name=config["name"],
                    department=config["dept"],
                    role=config["role"]
                )
                db.add(emp)
                db.flush()

            user = User(
                employee_id=emp.id,
                username=config["username"],
                real_name=config["name"],
                email=f"{config['username']}@company.com",
                password_hash=get_password_hash("123456"),
                is_active=True
            )
            db.add(user)
            db.flush()

        users[config["username"].split("_")[0]] = user

    return users


def create_customer(db, index):
    """创建客户"""
    customer_name = CUSTOMER_NAMES[index % len(CUSTOMER_NAMES)]
    customer_code = f"CUST{250100 + index:03d}"

    # 检查是否已存在
    existing = db.query(Customer).filter(Customer.customer_code == customer_code).first()
    if existing:
        return existing

    customer = Customer(
        customer_code=customer_code,
        customer_name=customer_name,
        short_name=customer_name[:6],
        customer_type="企业客户",
        industry=INDUSTRIES[index % len(INDUSTRIES)],
        scale="大型" if index % 3 == 0 else "中型",
        address=f"深圳市南山区科技园{index}号",
        contact_person=f"王总{index}",
        contact_phone=f"0755-8888{index:04d}",
        contact_email=f"contact{index}@customer.com",
        credit_level="A" if index % 2 == 0 else "B",
        credit_limit=Decimal("5000000.00"),
        payment_terms="30%预付款，60%发货前，10%验收后",
        status="ACTIVE"
    )
    db.add(customer)
    db.flush()
    return customer


def create_sales_flow(db, customer, users, project_index):
    """创建销售流程（简化版，只创建必要的）"""
    # 创建线索
    lead_code = f"LD{250100 + project_index:03d}"
    lead = Lead(
        lead_code=lead_code,
        source="展会" if project_index % 2 == 0 else "网络",
        customer_name=customer.customer_name,
        industry=customer.industry,
        contact_name=customer.contact_person,
        contact_phone=customer.contact_phone,
        demand_summary=f"需要{EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]}测试设备",
        owner_id=users["sales"].id,
        status="CONVERTED"
    )
    db.add(lead)
    db.flush()

    # 创建商机
    opp_code = f"OPP{250100 + project_index:03d}"
    opportunity = Opportunity(
        opp_code=opp_code,
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name=f"{customer.short_name}{EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]}测试设备项目",
        project_type="FIXED_PRICE",
        equipment_type=EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)],
        stage="WON",
        est_amount=Decimal("2000000.00") + Decimal(str(project_index * 100000)),
        owner_id=users["sales"].id,
        gate_status="PASSED"
    )
    db.add(opportunity)
    db.flush()

    # 创建报价（简化）
    quote_code = f"QT{250100 + project_index:03d}"
    quote = Quote(
        quote_code=quote_code,
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        owner_id=users["sales"].id
    )
    db.add(quote)
    db.flush()

    # 创建报价版本
    quote_version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1.0",
        total_price=opportunity.est_amount,
        cost_total=opportunity.est_amount * Decimal("0.75"),
        gross_margin=Decimal("25.00"),
        lead_time_days=120,
        delivery_date=date.today() + timedelta(days=120),
        created_by=users["sales"].id
    )
    db.add(quote_version)
    db.flush()

    quote.current_version_id = quote_version.id
    db.flush()

    # 创建合同
    contract_code = f"CT{250100 + project_index:03d}"
    contract = Contract(
        contract_code=contract_code,
        opportunity_id=opportunity.id,
        quote_version_id=quote_version.id,
        customer_id=customer.id,
        contract_amount=opportunity.est_amount,
        signed_date=date.today() - timedelta(days=180 - project_index * 10),
        status="SIGNED",
        payment_terms_summary="30%预付款，60%发货前，10%验收后",
        owner_id=users["sales"].id
    )
    db.add(contract)
    db.flush()

    return contract


def create_project(db, customer, contract, users, stage_config, project_index):
    """创建项目"""
    base_date = date.today() - timedelta(days=180 - project_index * 10)
    equipment_type = EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]

    project_code = f"PJ{250100 + project_index:03d}"
    project_name = f"{customer.short_name}{equipment_type}测试设备项目"

    # 根据阶段计算进度和日期
    {
        "S1": 5, "S2": 20, "S3": 45, "S4": 75, "S5": 105,
        "S6": 130, "S7": 145, "S8": 160, "S9": 180
    }.get(stage_config["stage"], 0)

    planned_start = base_date
    planned_end = base_date + timedelta(days=120)
    actual_start = planned_start

    project = Project(
        project_code=project_code,
        project_name=project_name,
        short_name=f"{customer.short_name[:4]}{equipment_type}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        customer_contact=customer.contact_person,
        customer_phone=customer.contact_phone,
        contract_no=contract.contract_code,
        project_type="FIXED_PRICE",
        product_category=f"{equipment_type}测试设备",
        industry=customer.industry,
        stage=stage_config["stage"],
        status=stage_config["status"],
        health=stage_config["health"],
        progress_pct=Decimal(str(stage_config["progress"])),
        contract_date=contract.signed_date,
        planned_start_date=planned_start,
        planned_end_date=planned_end,
        actual_start_date=actual_start,
        contract_amount=contract.contract_amount,
        budget_amount=contract.contract_amount * Decimal("0.75"),
        pm_id=users["pm"].id,
        pm_name=users["pm"].real_name,
        priority="HIGH" if project_index % 3 == 0 else "NORMAL",
        description=stage_config["description"],
        requirements=f"需要开发{equipment_type}测试设备，满足客户测试需求",
        opportunity_id=contract.opportunity_id,
        contract_id=contract.id
    )
    db.add(project)
    db.flush()

    # 创建里程碑
    create_milestones(db, project, stage_config, base_date)

    # 创建收款计划
    create_payment_plans(db, project, contract, base_date)

    # 创建设备
    machine = create_machine(db, project, equipment_type, stage_config)

    # 创建任务
    create_tasks(db, project, machine, users, stage_config, base_date)

    return project


def create_milestones(db, project, stage_config, base_date):
    """创建里程碑"""
    milestones_config = {
        "S1": [
            {"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "date_offset": 5, "status": "COMPLETED"}
        ],
        "S2": [
            {"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "date_offset": 5, "status": "COMPLETED"},
            {"name": "方案设计完成", "type": "DESIGN_COMPLETED", "date_offset": 20, "status": "COMPLETED"}
        ],
        "S3": [
            {"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "date_offset": 5, "status": "COMPLETED"},
            {"name": "方案设计完成", "type": "DESIGN_COMPLETED", "date_offset": 20, "status": "COMPLETED"},
            {"name": "BOM发布", "type": "BOM_RELEASED", "date_offset": 30, "status": "COMPLETED"},
            {"name": "物料到齐", "type": "MATERIAL_ARRIVED", "date_offset": 45, "status": "IN_PROGRESS"}
        ],
        "S4": [
            {"name": "BOM发布", "type": "BOM_RELEASED", "date_offset": 30, "status": "COMPLETED"},
            {"name": "物料到齐", "type": "MATERIAL_ARRIVED", "date_offset": 45, "status": "COMPLETED"},
            {"name": "机械加工完成", "type": "MACHINING_COMPLETED", "date_offset": 75, "status": "IN_PROGRESS"}
        ],
        "S5": [
            {"name": "机械加工完成", "type": "MACHINING_COMPLETED", "date_offset": 75, "status": "COMPLETED"},
            {"name": "装配完成", "type": "ASSEMBLY_COMPLETED", "date_offset": 90, "status": "COMPLETED"},
            {"name": "调试完成", "type": "DEBUG_COMPLETED", "date_offset": 105, "status": "IN_PROGRESS"}
        ],
        "S6": [
            {"name": "调试完成", "type": "DEBUG_COMPLETED", "date_offset": 105, "status": "COMPLETED"},
            {"name": "FAT验收通过", "type": "FAT_PASS", "date_offset": 130, "status": "PENDING"}
        ],
        "S7": [
            {"name": "FAT验收通过", "type": "FAT_PASS", "date_offset": 130, "status": "COMPLETED"},
            {"name": "发货", "type": "SHIPPED", "date_offset": 145, "status": "PENDING"}
        ],
        "S8": [
            {"name": "发货", "type": "SHIPPED", "date_offset": 145, "status": "COMPLETED"},
            {"name": "SAT验收通过", "type": "SAT_PASS", "date_offset": 160, "status": "IN_PROGRESS"}
        ],
        "S9": [
            {"name": "SAT验收通过", "type": "SAT_PASS", "date_offset": 160, "status": "COMPLETED"},
            {"name": "终验收通过", "type": "FINAL_ACCEPTANCE", "date_offset": 180, "status": "COMPLETED"}
        ]
    }

    milestones_data = milestones_config.get(stage_config["stage"], [])

    for ms_data in milestones_data:
        planned_date = base_date + timedelta(days=ms_data["date_offset"])
        actual_date = planned_date if ms_data["status"] == "COMPLETED" else None

        milestone = ProjectMilestone(
            project_id=project.id,
            milestone_code=f"MS-{project.project_code}-{ms_data['type']}",
            milestone_name=ms_data["name"],
            milestone_type=ms_data["type"],
            planned_date=planned_date,
            actual_date=actual_date,
            reminder_days=7,
            status=ms_data["status"],
            is_key=(ms_data["type"] in ["FAT_PASS", "SAT_PASS", "FINAL_ACCEPTANCE"])
        )
        db.add(milestone)


def create_payment_plans(db, project, contract, base_date):
    """创建收款计划"""
    plans = [
        {
            "payment_name": "预付款",
            "payment_type": "ADVANCE",
            "amount": contract.contract_amount * Decimal("0.30"),
            "date_offset": 0,
            "status": "PAID"
        },
        {
            "payment_name": "发货前付款",
            "payment_type": "BEFORE_SHIPMENT",
            "amount": contract.contract_amount * Decimal("0.60"),
            "date_offset": 145,
            "status": "PENDING"
        },
        {
            "payment_name": "验收后尾款",
            "payment_type": "ACCEPTANCE",
            "amount": contract.contract_amount * Decimal("0.10"),
            "date_offset": 180,
            "status": "PENDING"
        }
    ]

    for idx, plan_data in enumerate(plans, 1):
        planned_date = base_date + timedelta(days=plan_data["date_offset"])
        actual_date = planned_date if plan_data["status"] == "PAID" else None

        payment_plan = ProjectPaymentPlan(
            project_id=project.id,
            contract_id=contract.id,
            payment_no=idx,
            payment_name=plan_data["payment_name"],
            payment_type=plan_data["payment_type"],
            planned_amount=plan_data["amount"],
            planned_date=planned_date,
            actual_date=actual_date,
            status=plan_data["status"]
        )
        db.add(payment_plan)


def create_machine(db, project, equipment_type, stage_config):
    """创建设备"""
    machine = Machine(
        project_id=project.id,
        machine_code=f"PN{project.id:03d}",
        machine_name=f"{project.short_name}-01",
        machine_type=equipment_type,
        specification=f"{equipment_type}测试设备，满足客户测试需求",
        stage=stage_config["stage"],
        status=stage_config["status"],
        health=stage_config["health"],
        planned_start_date=project.planned_start_date,
        planned_end_date=project.planned_end_date,
        actual_start_date=project.actual_start_date
    )
    db.add(machine)
    db.flush()
    return machine


def create_tasks(db, project, machine, users, stage_config, base_date):
    """创建任务"""
    tasks_config = {
        "S1": [
            {"name": "需求调研", "assignee": "pm", "days": 3, "status": "DONE"},
            {"name": "需求确认", "assignee": "pm", "days": 5, "status": "DONE"}
        ],
        "S2": [
            {"name": "需求调研", "assignee": "pm", "days": 3, "status": "DONE"},
            {"name": "方案设计", "assignee": "mech", "days": 15, "status": "DONE"},
            {"name": "电气方案设计", "assignee": "elec", "days": 15, "status": "IN_PROGRESS"}
        ],
        "S3": [
            {"name": "BOM设计", "assignee": "mech", "days": 10, "status": "DONE"},
            {"name": "物料采购", "assignee": "pm", "days": 20, "status": "IN_PROGRESS"}
        ],
        "S4": [
            {"name": "机械加工", "assignee": "mech", "days": 30, "status": "IN_PROGRESS"},
            {"name": "钣金加工", "assignee": "mech", "days": 25, "status": "IN_PROGRESS"}
        ],
        "S5": [
            {"name": "机械装配", "assignee": "mech", "days": 15, "status": "DONE"},
            {"name": "电气接线", "assignee": "elec", "days": 10, "status": "DONE"},
            {"name": "程序调试", "assignee": "soft", "days": 15, "status": "IN_PROGRESS"}
        ],
        "S6": [
            {"name": "功能测试", "assignee": "soft", "days": 10, "status": "DONE"},
            {"name": "FAT验收准备", "assignee": "pm", "days": 5, "status": "IN_PROGRESS"}
        ],
        "S7": [
            {"name": "FAT验收", "assignee": "pm", "days": 5, "status": "DONE"},
            {"name": "包装准备", "assignee": "pm", "days": 3, "status": "IN_PROGRESS"}
        ],
        "S8": [
            {"name": "设备发货", "assignee": "pm", "days": 1, "status": "DONE"},
            {"name": "现场安装", "assignee": "elec", "days": 10, "status": "IN_PROGRESS"}
        ],
        "S9": [
            {"name": "SAT验收", "assignee": "pm", "days": 5, "status": "DONE"},
            {"name": "项目结项", "assignee": "pm", "days": 1, "status": "DONE"}
        ]
    }

    tasks_data = tasks_config.get(stage_config["stage"], [])
    user_map = {"pm": users["pm"], "mech": users["mech"], "elec": users["elec"], "soft": users["soft"]}

    for task_data in tasks_data:
        plan_start = base_date
        plan_end = base_date + timedelta(days=task_data["days"])
        actual_end = plan_end if task_data["status"] == "DONE" else None

        task = Task(
            project_id=project.id,
            machine_id=machine.id,
            milestone_id=None,  # 不关联里程碑，简化处理
            task_name=task_data["name"],
            stage=stage_config["stage"],
            status=task_data["status"],
            owner_id=user_map[task_data["assignee"]].id,
            plan_start=plan_start,
            plan_end=plan_end,
            actual_start=plan_start,
            actual_end=actual_end,
            progress_percent=100 if task_data["status"] == "DONE" else 50
        )
        db.add(task)


def main():
    """主函数"""
    print("=" * 60)
    print("生成多阶段项目完整测试数据")
    print("=" * 60)

    with get_db_session() as db:
        try:
            # 1. 获取或创建用户
            print("\n1. 准备用户数据...")
            users = get_or_create_users(db)
            print(f"   ✓ 已准备 {len(users)} 个用户")

            # 2. 生成各个阶段的项目
            project_index = 0
            all_projects = []

            for stage_config in STAGE_CONFIGS:
                print(f"\n2. 生成 {stage_config['stage']} 阶段项目 ({stage_config['name_prefix']})...")

                for i in range(stage_config["count"]):
                    project_index += 1

                    # 创建客户
                    customer = create_customer(db, project_index)

                    # 创建销售流程
                    contract = create_sales_flow(db, customer, users, project_index)

                    # 创建项目
                    project = create_project(db, customer, contract, users, stage_config, project_index)
                    all_projects.append(project)

                    print(f"   ✓ 创建项目: {project.project_code} - {project.project_name} "
                          f"(阶段: {project.stage}, 进度: {project.progress_pct}%)")

            db.commit()

            print("\n" + "=" * 60)
            print("数据生成完成！")
            print("=" * 60)
            print(f"\n生成的项目概览：")
            print(f"  总计: {len(all_projects)} 个项目")

            # 按阶段统计
            stage_stats = {}
            for project in all_projects:
                stage = project.stage
                if stage not in stage_stats:
                    stage_stats[stage] = 0
                stage_stats[stage] += 1

            print(f"\n各阶段项目数量：")
            for stage in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
                count = stage_stats.get(stage, 0)
                print(f"  {stage}: {count} 个项目")

            print(f"\n数据已保存到数据库！")
            print(f"现在可以在项目看板查看完整的数据展示。")

        except Exception as e:
            db.rollback()
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
