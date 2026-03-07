#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为项目生成演示成本数据
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import date, timedelta
from decimal import Decimal

from app.models.base import get_db_session
from app.models.project import Machine, Project, ProjectCost
from app.models.user import User

# 成本类型和分类配置
COST_TYPES = {
    "MATERIAL": ["标准件采购", "电气元件", "机械件采购", "气动元件", "传感器", "线缆", "连接器"],
    "MANUFACTURING": ["机械加工", "钣金加工", "表面处理", "焊接", "装配", "调试"],
    "OUTSOURCING": ["外协加工", "外协装配", "外协测试", "外协设计"],
    "LABOR": ["人工成本", "设计工时", "调试工时", "测试工时"],
    "TRAVEL": ["差旅费", "住宿费", "交通费", "餐费"],
    "OTHER": ["设备租赁", "工具费用", "检测费用", "认证费用", "其他费用"],
}


def generate_cost_no(project_code: str, index: int) -> str:
    """生成成本编号"""
    return f"{project_code}-COST-{index:04d}"


def generate_demo_costs(project_id: int = 14):
    """为指定项目生成演示成本数据"""
    with get_db_session() as db:
        # 检查项目
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"❌ 项目ID {project_id} 不存在")
            return

        print(f"✓ 项目: {project.project_name} ({project.project_code})")

        # 获取管理员用户作为创建人
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("❌ 未找到管理员用户")
            return

        # 获取项目的机台（如果有）
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        machine_ids = [m.id for m in machines] if machines else [None]

        # 检查现有成本记录数
        existing_count = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).count()
        print(f"  现有成本记录: {existing_count} 条")

        # 项目时间范围
        start_date = project.planned_start_date or date(2024, 1, 15)
        end_date = project.planned_end_date or date(2024, 12, 20)
        project_duration = (end_date - start_date).days

        # 生成成本数据（补充到30条左右）
        new_costs = []
        target_count = 30
        to_add = max(0, target_count - existing_count)

        if to_add == 0:
            print(f"  ✓ 成本记录已足够（{existing_count}条），无需添加")
            return

        print(f"  将添加 {to_add} 条新的成本记录...")

        for i in range(to_add):
            # 随机选择成本类型和分类
            cost_type = random.choice(list(COST_TYPES.keys()))
            cost_category = random.choice(COST_TYPES[cost_type])

            # 随机日期（在项目时间范围内）
            days_offset = random.randint(0, project_duration)
            cost_date = start_date + timedelta(days=days_offset)

            # 根据成本类型生成合理的金额
            if cost_type == "MATERIAL":
                amount = Decimal(random.randint(5000, 150000))
            elif cost_type == "MANUFACTURING":
                amount = Decimal(random.randint(10000, 200000))
            elif cost_type == "OUTSOURCING":
                amount = Decimal(random.randint(20000, 100000))
            elif cost_type == "LABOR":
                amount = Decimal(random.randint(5000, 50000))
            elif cost_type == "TRAVEL":
                amount = Decimal(random.randint(500, 5000))
            else:
                amount = Decimal(random.randint(1000, 20000))

            # 税额（约6%）
            tax_amount = Decimal(amount * Decimal("0.06")).quantize(Decimal("0.01"))

            # 随机选择机台（30%概率关联机台）
            machine_id = (
                random.choice(machine_ids) if random.random() < 0.3 and machine_ids else None
            )

            # 生成描述
            descriptions = {
                "MATERIAL": [
                    f"采购{cost_category}用于项目生产",
                    f"项目所需{cost_category}采购",
                    f"{cost_category}采购费用",
                ],
                "MANUFACTURING": [
                    f"{cost_category}加工费用",
                    f"项目{cost_category}工序费用",
                    f"{cost_category}制造费用",
                ],
                "OUTSOURCING": [
                    f"{cost_category}外协费用",
                    f"委托外协进行{cost_category}",
                    f"{cost_category}外包费用",
                ],
                "LABOR": [
                    f"{cost_category}工时费用",
                    f"项目{cost_category}",
                    f"{cost_category}人工成本",
                ],
                "TRAVEL": [
                    f"项目{cost_category}",
                    f"{cost_category}报销",
                    f"出差{cost_category}",
                ],
                "OTHER": [
                    f"{cost_category}",
                    f"项目{cost_category}支出",
                    f"{cost_category}费用",
                ],
            }
            description = random.choice(descriptions.get(cost_type, ["项目成本"]))

            # 创建成本记录
            cost = ProjectCost(
                project_id=project_id,
                machine_id=machine_id,
                cost_type=cost_type,
                cost_category=cost_category,
                amount=amount,
                tax_amount=tax_amount,
                cost_date=cost_date,
                description=description,
                created_by=admin.id,
            )
            new_costs.append(cost)

        # 批量添加
        db.add_all(new_costs)

        # 更新项目实际成本
        total_new_cost = sum(c.amount for c in new_costs)
        project.actual_cost = (project.actual_cost or Decimal("0")) + total_new_cost

        db.commit()

        print(f"  ✓ 成功添加 {len(new_costs)} 条成本记录")
        print(f"  ✓ 新增成本总额: ¥{total_new_cost:,.2f}")
        print(f"  ✓ 项目累计实际成本: ¥{project.actual_cost:,.2f}")

        # 统计信息
        all_costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
        print(f"\n📊 成本统计:")
        print(f"  总记录数: {len(all_costs)} 条")

        # 按类型统计
        type_stats = {}
        for cost in all_costs:
            type_stats[cost.cost_type] = type_stats.get(cost.cost_type, Decimal("0")) + cost.amount

        print(f"  按类型统计:")
        for cost_type, total in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
            print(
                f"    {cost_type}: ¥{total:,.2f} ({len([c for c in all_costs if c.cost_type == cost_type])}条)"
            )


if __name__ == "__main__":
    generate_demo_costs(project_id=14)
