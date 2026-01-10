#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为项目添加丰富的真实数据
为"北京智能装备ICT测试设备项目"（PJ250114）添加完整的历史数据
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.project import (
    Project, ProjectStage, ProjectMilestone, ProjectMember, 
    ProjectCost, ProjectDocument, ProjectStatusLog, Machine
)
from app.models.progress import Task
from app.models.pmo import PmoProjectRisk
from app.models.issue import Issue
from app.models.user import User
from app.models.organization import Department
# 暂时不导入这些，先添加基础数据


def enrich_project_data():
    """为项目添加丰富的数据"""
    with get_db_session() as db:
        # 查找项目
        project = db.query(Project).filter(Project.project_code == 'PJ250114').first()
        if not project:
            print("❌ 项目未找到")
            return
        
        print(f"✓ 找到项目: {project.project_name} (ID: {project.id})")
        
        # 获取一些用户作为团队成员
        users = db.query(User).filter(User.is_active == True).limit(10).all()
        if not users:
            print("❌ 未找到可用用户")
            return
        
        pm = db.query(User).filter(User.id == project.pm_id).first()
        if not pm:
            pm = users[0]
        
        print(f"✓ 项目经理: {pm.real_name or pm.username}")
        
        # 计算项目时间线（从2024年1月开始，到2024年12月结束）
        project_start = date(2024, 1, 15)
        project_end = date(2024, 12, 20)
        
        # 1. 添加项目阶段数据（S1-S9）
        print("\n📋 添加项目阶段数据...")
        stage_configs = [
            ("S1", "需求进入", 1, project_start, date(2024, 1, 31)),
            ("S2", "方案设计", 2, date(2024, 2, 1), date(2024, 3, 15)),
            ("S3", "采购备料", 3, date(2024, 3, 16), date(2024, 5, 31)),
            ("S4", "加工制造", 4, date(2024, 6, 1), date(2024, 7, 31)),
            ("S5", "装配调试", 5, date(2024, 8, 1), date(2024, 9, 15)),
            ("S6", "出厂验收", 6, date(2024, 9, 16), date(2024, 10, 10)),
            ("S7", "包装发运", 7, date(2024, 10, 11), date(2024, 10, 25)),
            ("S8", "现场安装", 8, date(2024, 10, 26), date(2024, 11, 30)),
            ("S9", "质保结项", 9, date(2024, 12, 1), project_end),
        ]
        
        for stage_code, stage_name, order, start_date, end_date in stage_configs:
            existing = db.query(ProjectStage).filter(
                ProjectStage.project_id == project.id,
                ProjectStage.stage_code == stage_code
            ).first()
            
            if not existing:
                stage = ProjectStage(
                    project_id=project.id,
                    stage_code=stage_code,
                    stage_name=stage_name,
                    stage_order=order,
                    planned_start_date=start_date,
                    planned_end_date=end_date,
                    actual_start_date=start_date,
                    actual_end_date=end_date,
                    progress_pct=100 if stage_code in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'] else 0,
                    status="COMPLETED" if stage_code in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'] else "PENDING",
                    description=f"{stage_name}阶段已完成",
                    is_active=True
                )
                db.add(stage)
                print(f"  ✓ 添加阶段: {stage_code} - {stage_name}")
        
        # 2. 添加项目成员（使用原始SQL避免外键约束问题）
        print("\n👥 添加项目成员...")
        member_roles = [
            ("项目经理", 100, project_start, project_end),
            ("机械工程师", 80, date(2024, 2, 1), date(2024, 8, 31)),
            ("电气工程师", 80, date(2024, 2, 1), date(2024, 8, 31)),
            ("软件工程师", 60, date(2024, 3, 1), date(2024, 9, 30)),
            ("测试工程师", 50, date(2024, 6, 1), date(2024, 10, 31)),
            ("采购专员", 30, date(2024, 3, 1), date(2024, 6, 30)),
            ("质量工程师", 40, date(2024, 7, 1), date(2024, 11, 30)),
        ]
        
        from sqlalchemy import text
        
        for i, (role_name, allocation, start_date, end_date) in enumerate(member_roles):
            if i >= len(users):
                break
            
            user = users[i] if i > 0 else pm  # 第一个是项目经理
            
            # 检查是否已存在
            existing = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id
            ).first()
            
            if not existing:
                # 检查角色是否存在，如果不存在则创建
                role_result = db.execute(text("SELECT id FROM roles WHERE role_code = :role_code"), {"role_code": role_name}).first()
                if not role_result:
                    # 创建角色
                    db.execute(text("""
                        INSERT INTO roles (role_code, role_name, data_scope, is_system, created_at)
                        VALUES (:role_code, :role_name, 'PROJECT', 0, CURRENT_TIMESTAMP)
                    """), {"role_code": role_name, "role_name": role_name})
                    db.flush()
                
                # 使用原始SQL插入，设置role_code为NULL避免外键约束
                try:
                    db.execute(text("""
                        INSERT INTO project_members 
                        (project_id, user_id, role_code, allocation_pct, start_date, end_date, is_active, remark, created_by, created_at, updated_at)
                        VALUES (:project_id, :user_id, :role_code, :allocation_pct, :start_date, :end_date, 1, :remark, :created_by, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """), {
                        "project_id": project.id,
                        "user_id": user.id,
                        "role_code": role_name,
                        "allocation_pct": allocation,
                        "start_date": start_date,
                        "end_date": end_date,
                        "remark": f"负责{role_name}相关工作",
                        "created_by": pm.id
                    })
                    print(f"  ✓ 添加成员: {user.real_name or user.username} - {role_name}")
                except Exception as e:
                    print(f"  ⚠️ 跳过成员 {user.real_name or user.username}: {str(e)}")
        
        # 3. 添加里程碑
        print("\n🎯 添加里程碑...")
        milestone_data = [
            ("M001", "需求确认完成", "GATE", date(2024, 1, 31), date(2024, 1, 31), "COMPLETED", True),
            ("M002", "方案设计评审通过", "GATE", date(2024, 3, 15), date(2024, 3, 18), "COMPLETED", True),
            ("M003", "BOM发布", "DELIVERY", date(2024, 4, 15), date(2024, 4, 20), "COMPLETED", True),
            ("M004", "首付款到账", "PAYMENT", date(2024, 4, 30), date(2024, 5, 5), "COMPLETED", True),
            ("M005", "机械加工完成", "DELIVERY", date(2024, 7, 31), date(2024, 8, 5), "COMPLETED", True),
            ("M006", "电气装配完成", "DELIVERY", date(2024, 8, 31), date(2024, 9, 3), "COMPLETED", True),
            ("M007", "软件调试完成", "DELIVERY", date(2024, 9, 15), date(2024, 9, 18), "COMPLETED", True),
            ("M008", "FAT验收通过", "GATE", date(2024, 10, 10), date(2024, 10, 12), "COMPLETED", True),
            ("M009", "设备发货", "DELIVERY", date(2024, 10, 25), date(2024, 10, 28), "COMPLETED", True),
            ("M010", "SAT验收通过", "GATE", date(2024, 11, 30), date(2024, 12, 2), "COMPLETED", True),
            ("M011", "尾款到账", "PAYMENT", date(2024, 12, 15), date(2024, 12, 18), "COMPLETED", True),
            ("M012", "项目结项", "CUSTOM", date(2024, 12, 20), date(2024, 12, 20), "COMPLETED", True),
        ]
        
        for code, name, mtype, planned, actual, status, is_key in milestone_data:
            existing = db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == project.id,
                ProjectMilestone.milestone_code == code
            ).first()
            
            if not existing:
                milestone = ProjectMilestone(
                    project_id=project.id,
                    milestone_code=code,
                    milestone_name=name,
                    milestone_type=mtype,
                    planned_date=planned,
                    actual_date=actual,
                    status=status,
                    is_key=is_key,
                    owner_id=pm.id,
                    remark=f"{name}里程碑"
                )
                db.add(milestone)
                print(f"  ✓ 添加里程碑: {code} - {name}")
        
        # 4. 添加成本数据
        print("\n💰 添加成本数据...")
        cost_data = [
            ("机械加工", "MANUFACTURING", 185000.00, date(2024, 6, 15), "机械件加工费用"),
            ("电气元件", "MATERIAL", 125000.00, date(2024, 4, 20), "电气元件采购费用"),
            ("标准件采购", "MATERIAL", 85000.00, date(2024, 5, 10), "标准件采购费用"),
            ("外协加工", "OUTSOURCING", 65000.00, date(2024, 7, 5), "外协件加工费用"),
            ("人工成本", "LABOR", 180000.00, date(2024, 9, 30), "项目团队人工成本"),
            ("差旅费", "TRAVEL", 25000.00, date(2024, 11, 15), "现场安装差旅费用"),
            ("测试费用", "TESTING", 35000.00, date(2024, 9, 20), "测试验证费用"),
            ("包装运输", "LOGISTICS", 15000.00, date(2024, 10, 20), "包装运输费用"),
        ]
        
        total_cost = Decimal('0')
        for cost_type, category, amount, cost_date, remark in cost_data:
            cost = ProjectCost(
                project_id=project.id,
                cost_type=category,
                cost_category=cost_type,
                amount=Decimal(str(amount)),
                cost_date=cost_date,
                description=remark,
                created_by=pm.id
            )
            db.add(cost)
            total_cost += Decimal(str(amount))
            print(f"  ✓ 添加成本: {cost_type} - ¥{amount:,.2f}")
        
        # 更新项目实际成本
        project.actual_cost = total_cost
        print(f"  ✓ 项目总成本: ¥{total_cost:,.2f}")
        
        # 5. 添加文档
        print("\n📄 添加项目文档...")
        doc_data = [
            ("项目需求规格书", "REQUIREMENT", "1.0", "APPROVED", date(2024, 1, 25)),
            ("技术方案设计书", "DESIGN", "2.1", "APPROVED", date(2024, 3, 10)),
            ("BOM清单", "BOM", "1.0", "APPROVED", date(2024, 4, 15)),
            ("机械加工图纸", "DRAWING", "3.0", "APPROVED", date(2024, 5, 20)),
            ("电气原理图", "DRAWING", "2.0", "APPROVED", date(2024, 6, 10)),
            ("软件设计文档", "DESIGN", "1.5", "APPROVED", date(2024, 6, 25)),
            ("测试计划", "TEST", "1.0", "APPROVED", date(2024, 8, 15)),
            ("FAT验收报告", "REPORT", "1.0", "APPROVED", date(2024, 10, 12)),
            ("SAT验收报告", "REPORT", "1.0", "APPROVED", date(2024, 12, 2)),
            ("用户操作手册", "MANUAL", "1.0", "APPROVED", date(2024, 11, 20)),
            ("项目总结报告", "REPORT", "1.0", "APPROVED", date(2024, 12, 18)),
        ]
        
        for doc_name, doc_type, version, status, doc_date in doc_data:
            existing = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project.id,
                ProjectDocument.doc_name == doc_name
            ).first()
            
            if not existing:
                doc = ProjectDocument(
                    project_id=project.id,
                    doc_name=doc_name,
                    doc_type=doc_type,
                    version=version,
                    status=status,
                    file_path=f"/documents/projects/{project.id}/{doc_name}_{version}.pdf",
                    file_name=f"{doc_name}_{version}.pdf",
                    uploaded_by=pm.id
                )
                doc.created_at = datetime.combine(doc_date, datetime.min.time())
                db.add(doc)
                print(f"  ✓ 添加文档: {doc_name} v{version}")
        
        # 6. 添加任务
        print("\n✅ 添加项目任务...")
        task_data = [
            ("需求调研", "需求进入阶段需求调研工作", "COMPLETED", date(2024, 1, 20), date(2024, 1, 25), users[1].id if len(users) > 1 else pm.id),
            ("方案设计", "完成技术方案设计", "COMPLETED", date(2024, 2, 5), date(2024, 3, 10), users[1].id if len(users) > 1 else pm.id),
            ("BOM编制", "编制物料清单", "COMPLETED", date(2024, 3, 20), date(2024, 4, 15), users[5].id if len(users) > 5 else pm.id),
            ("物料采购", "执行物料采购", "COMPLETED", date(2024, 4, 16), date(2024, 5, 31), users[5].id if len(users) > 5 else pm.id),
            ("机械加工", "机械件加工制造", "COMPLETED", date(2024, 6, 1), date(2024, 7, 31), users[1].id if len(users) > 1 else pm.id),
            ("电气装配", "电气系统装配", "COMPLETED", date(2024, 8, 1), date(2024, 8, 31), users[2].id if len(users) > 2 else pm.id),
            ("软件开发", "软件开发与调试", "COMPLETED", date(2024, 8, 5), date(2024, 9, 15), users[3].id if len(users) > 3 else pm.id),
            ("系统联调", "系统联调测试", "COMPLETED", date(2024, 9, 1), date(2024, 9, 10), users[4].id if len(users) > 4 else pm.id),
            ("FAT验收", "出厂验收测试", "COMPLETED", date(2024, 9, 16), date(2024, 10, 10), users[4].id if len(users) > 4 else pm.id),
            ("设备发货", "设备包装发运", "COMPLETED", date(2024, 10, 11), date(2024, 10, 25), users[5].id if len(users) > 5 else pm.id),
            ("现场安装", "现场安装调试", "COMPLETED", date(2024, 10, 26), date(2024, 11, 25), users[1].id if len(users) > 1 else pm.id),
            ("SAT验收", "现场验收测试", "COMPLETED", date(2024, 11, 26), date(2024, 11, 30), users[4].id if len(users) > 4 else pm.id),
            ("培训交付", "用户培训与交付", "COMPLETED", date(2024, 12, 1), date(2024, 12, 10), pm.id),
            ("项目结项", "项目总结与结项", "COMPLETED", date(2024, 12, 11), date(2024, 12, 20), pm.id),
        ]
        
        for task_name, description, status, start_date, end_date, assignee_id in task_data:
            existing = db.query(Task).filter(
                Task.project_id == project.id,
                Task.task_name == task_name
            ).first()
            
            if not existing:
                task = Task(
                    project_id=project.id,
                    task_name=task_name,
                    status="DONE" if status == "COMPLETED" else "TODO",
                    plan_start=start_date,
                    plan_end=end_date,
                    actual_start=start_date,
                    actual_end=end_date,
                    owner_id=assignee_id,
                    progress_percent=100 if status == "COMPLETED" else 0
                )
                # 使用block_reason字段存储描述（如果没有description字段）
                if description:
                    task.block_reason = description
                db.add(task)
                print(f"  ✓ 添加任务: {task_name}")
        
        # 7. 添加状态变更日志
        print("\n📝 添加状态变更日志...")
        status_logs = [
            ("STAGE_CHANGE", "S1", "S2", date(2024, 2, 1), "进入方案设计阶段"),
            ("STAGE_CHANGE", "S2", "S3", date(2024, 3, 16), "进入采购备料阶段"),
            ("STAGE_CHANGE", "S3", "S4", date(2024, 6, 1), "进入加工制造阶段"),
            ("STAGE_CHANGE", "S4", "S5", date(2024, 8, 1), "进入装配调试阶段"),
            ("STAGE_CHANGE", "S5", "S6", date(2024, 9, 16), "进入出厂验收阶段"),
            ("STAGE_CHANGE", "S6", "S7", date(2024, 10, 11), "进入包装发运阶段"),
            ("STAGE_CHANGE", "S7", "S8", date(2024, 10, 26), "进入现场安装阶段"),
            ("STAGE_CHANGE", "S8", "S9", date(2024, 12, 1), "进入质保结项阶段"),
            ("HEALTH_CHANGE", "H1", "H2", date(2024, 5, 15), "物料到货延迟，进度有风险"),
            ("HEALTH_CHANGE", "H2", "H1", date(2024, 5, 25), "物料到货，风险解除"),
            ("HEALTH_CHANGE", "H1", "H2", date(2024, 8, 20), "软件调试遇到技术难点"),
            ("HEALTH_CHANGE", "H2", "H1", date(2024, 9, 5), "技术问题已解决"),
        ]
        
        for change_type, old_value, new_value, change_date, remark in status_logs:
            log = ProjectStatusLog(
                project_id=project.id,
                change_type=change_type,
                changed_at=datetime.combine(change_date, datetime.min.time()),
                changed_by=pm.id,
                change_reason=remark
            )
            # 根据变更类型设置对应的字段
            if change_type == "STAGE_CHANGE":
                log.old_stage = old_value
                log.new_stage = new_value
            elif change_type == "STATUS_CHANGE":
                log.old_status = old_value
                log.new_status = new_value
            elif change_type == "HEALTH_CHANGE":
                log.old_health = old_value
                log.new_health = new_value
            db.add(log)
        
        print(f"  ✓ 添加 {len(status_logs)} 条状态日志")
        
        # 8. 添加风险记录（暂时跳过，因为外键定义有问题）
        print("\n⚠️ 添加项目风险...")
        print("  ⚠️ 跳过风险数据（外键定义问题）")
        # risk_data = [
        #     ("物料到货延迟", "MEDIUM", "OPEN", date(2024, 5, 10), "部分关键物料供应商交期延迟", "与供应商协商加急，寻找备选供应商", "RESOLVED", date(2024, 5, 25)),
        #     ("软件调试难点", "HIGH", "OPEN", date(2024, 8, 15), "软件调试过程中发现技术难点", "组织技术攻关，寻求外部技术支持", "RESOLVED", date(2024, 9, 5)),
        #     ("现场安装环境", "LOW", "OPEN", date(2024, 10, 20), "现场安装环境与预期有差异", "提前到现场勘察，调整安装方案", "RESOLVED", date(2024, 11, 5)),
        # ]
        
        # 9. 添加问题记录
        print("\n🐛 添加项目问题...")
        issue_data = [
            ("机械加工精度问题", "机械加工件精度未达到要求", "RESOLVED", date(2024, 7, 10), "重新加工", users[1].id if len(users) > 1 else pm.id),
            ("电气接线错误", "电气接线图与实际不符", "RESOLVED", date(2024, 8, 15), "修正接线图并重新接线", users[2].id if len(users) > 2 else pm.id),
            ("软件功能异常", "测试发现软件功能异常", "RESOLVED", date(2024, 9, 5), "修复软件bug", users[3].id if len(users) > 3 else pm.id),
            ("测试设备故障", "测试过程中设备出现故障", "RESOLVED", date(2024, 9, 25), "更换测试设备", users[4].id if len(users) > 4 else pm.id),
        ]
        
        for i, (issue_title, description, status, create_date, solution, assignee_id) in enumerate(issue_data):
            issue_no = f"I{project.id:03d}{i+1:03d}"
            # 检查是否已存在
            existing = db.query(Issue).filter(Issue.issue_no == issue_no).first()
            if existing:
                print(f"  ⚠️ 问题已存在: {issue_title}")
                continue
            
            issue = Issue(
                project_id=project.id,
                issue_no=issue_no,
                category="PROJECT",
                issue_type="TECHNICAL",
                severity="MEDIUM",
                title=issue_title,
                description=description,
                status=status,
                priority="MEDIUM",
                assignee_id=assignee_id,
                reporter_id=pm.id,
                report_date=datetime.combine(create_date, datetime.min.time()),
                solution=solution if status == "RESOLVED" else None,
                resolved_at=datetime.combine(create_date + timedelta(days=3), datetime.min.time()) if status == "RESOLVED" else None,
                resolved_by=assignee_id if status == "RESOLVED" else None
            )
            db.add(issue)
            print(f"  ✓ 添加问题: {issue_title}")
        
        # 提交所有更改
        db.commit()
        print("\n✅ 所有数据添加完成！")
        
        # 打印统计信息
        print("\n📊 数据统计:")
        print(f"  阶段: {db.query(ProjectStage).filter(ProjectStage.project_id == project.id).count()}")
        print(f"  里程碑: {db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project.id).count()}")
        print(f"  成员: {db.query(ProjectMember).filter(ProjectMember.project_id == project.id).count()}")
        print(f"  成本记录: {db.query(ProjectCost).filter(ProjectCost.project_id == project.id).count()}")
        print(f"  文档: {db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id).count()}")
        print(f"  任务: {db.query(Task).filter(Task.project_id == project.id).count()}")
        print(f"  状态日志: {db.query(ProjectStatusLog).filter(ProjectStatusLog.project_id == project.id).count()}")
        # print(f"  风险: {db.query(PmoProjectRisk).filter(PmoProjectRisk.project_id == project.id).count()}")
        print(f"  问题: {db.query(Issue).filter(Issue.project_id == project.id).count()}")


if __name__ == "__main__":
    enrich_project_data()
