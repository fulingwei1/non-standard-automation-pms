#!/usr/bin/env python3
"""
演示数据生成脚本 - 跨部门进度展示
生成3个项目的演示数据，包括多个部门的任务
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.base import get_db_session
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task_center import TaskUnified
from app.models.organization import Employee
from app.core.security import get_password_hash

def create_demo_employees(db: Session):
    """先创建员工记录（Employee表）"""
    employees = []

    # 检查是否已存在演示员工
    existing = db.query(Employee).filter(Employee.employee_code.like('EMP00%')).first()
    if existing:
        print("演示员工已存在，跳过创建")
        return db.query(Employee).filter(Employee.employee_code.like('EMP00%')).all()

    # 创建员工记录
    employee_data = [
        {'code': 'EMP001', 'name': '张工', 'department': '机械部', 'role': '机械工程师'},
        {'code': 'EMP002', 'name': '李工', 'department': '机械部', 'role': '机械工程师'},
        {'code': 'EMP003', 'name': '王工', 'department': '电气部', 'role': '电气工程师'},
        {'code': 'EMP004', 'name': '赵工', 'department': '电气部', 'role': '电气工程师'},
        {'code': 'EMP005', 'name': '孙工', 'department': '软件部', 'role': '软件工程师'},
        {'code': 'EMP006', 'name': '周工', 'department': '软件部', 'role': '软件工程师'},
        {'code': 'EMP007', 'name': '刘经理', 'department': 'PMO', 'role': '项目经理'},
    ]

    for emp_data in employee_data:
        employee = Employee(
            employee_code=emp_data['code'],
            name=emp_data['name'],
            department=emp_data['department'],
            role=emp_data['role'],
            is_active=True
        )
        db.add(employee)
        employees.append(employee)

    db.commit()
    print(f"✅ 创建了 {len(employees)} 个演示员工")
    return employees

def create_demo_users(db: Session):
    """创建演示用户（各部门工程师）"""
    users = []

    # 检查是否已存在演示用户
    existing = db.query(User).filter(User.username.like('demo_%')).first()
    if existing:
        print("演示用户已存在，跳过创建")
        return db.query(User).filter(User.username.like('demo_%')).all()

    # 创建各部门工程师
    demo_users_data = [
        # 机械部
        {'username': 'demo_mech_zhang', 'real_name': '张工', 'department': '机械部', 'employee_code': 'EMP001'},
        {'username': 'demo_mech_li', 'real_name': '李工', 'department': '机械部', 'employee_code': 'EMP002'},

        # 电气部
        {'username': 'demo_elec_wang', 'real_name': '王工', 'department': '电气部', 'employee_code': 'EMP003'},
        {'username': 'demo_elec_zhao', 'real_name': '赵工', 'department': '电气部', 'employee_code': 'EMP004'},

        # 软件部
        {'username': 'demo_soft_sun', 'real_name': '孙工', 'department': '软件部', 'employee_code': 'EMP005'},
        {'username': 'demo_soft_zhou', 'real_name': '周工', 'department': '软件部', 'employee_code': 'EMP006'},

        # 项目经理
        {'username': 'demo_pm_liu', 'real_name': '刘经理', 'department': 'PMO', 'employee_code': 'EMP007'},
    ]

    password_hash = get_password_hash("demo123")

    for user_data in demo_users_data:
        # 根据employee_code查找Employee的id
        employee = db.query(Employee).filter(Employee.employee_code == user_data['employee_code']).first()
        if not employee:
            print(f"⚠️  警告: 找不到员工 {user_data['employee_code']}，跳过创建用户 {user_data['username']}")
            continue

        user = User(
            username=user_data['username'],
            real_name=user_data['real_name'],
            password_hash=password_hash,
            department=user_data['department'],
            employee_id=employee.id,  # 使用Employee的主键id
            is_active=True,
            email=f"{user_data['username']}@example.com"
        )
        db.add(user)
        users.append(user)

    db.commit()
    print(f"✅ 创建了 {len(users)} 个演示用户")
    return users

def create_demo_projects(db: Session):
    """创建3个演示项目"""
    projects = []

    # 检查是否已存在演示项目
    existing = db.query(Project).filter(Project.project_code.like('DEMO%')).first()
    if existing:
        print("演示项目已存在，跳过创建")
        return db.query(Project).filter(Project.project_code.like('DEMO%')).all()

    projects_data = [
        {
            'project_code': 'DEMO001',
            'name': 'BMS老化测试设备',
            'customer_name': '华为技术有限公司',
            'contract_amount': 850000,
            'stage': 'S4',
            'health': 'H2',
            'progress_pct': 45.67,
        },
        {
            'project_code': 'DEMO002',
            'name': 'EOL功能测试设备',
            'customer_name': '比亚迪汽车',
            'contract_amount': 1200000,
            'stage': 'S5',
            'health': 'H1',
            'progress_pct': 72.30,
        },
        {
            'project_code': 'DEMO003',
            'name': 'ICT测试设备',
            'customer_name': '宁德时代',
            'contract_amount': 650000,
            'stage': 'S3',
            'health': 'H3',
            'progress_pct': 28.50,
        },
    ]

    for proj_data in projects_data:
        project = Project(
            project_code=proj_data['project_code'],
            project_name=proj_data['name'],
            customer_name=proj_data['customer_name'],
            contract_amount=proj_data['contract_amount'],
            stage=proj_data['stage'],
            health=proj_data['health'],
            progress_pct=proj_data['progress_pct'],
            planned_start_date=datetime.now().date() - timedelta(days=60),
            planned_end_date=datetime.now().date() + timedelta(days=90),
            is_active=True
        )
        db.add(project)
        projects.append(project)

    db.commit()
    print(f"✅ 创建了 {len(projects)} 个演示项目")
    return projects

def create_demo_tasks(db: Session, projects, users):
    """为每个项目创建跨部门任务"""
    tasks = []

    # 检查是否已存在演示任务
    existing = db.query(TaskUnified).filter(TaskUnified.title.like('DEMO%')).first()
    if existing:
        print("演示任务已存在，跳过创建")
        return db.query(TaskUnified).filter(TaskUnified.title.like('DEMO%')).all()

    # 按部门分组用户
    users_by_dept = {}
    for user in users:
        if user.department not in users_by_dept:
            users_by_dept[user.department] = []
        users_by_dept[user.department].append(user)

    # 为每个项目创建任务
    for project in projects:
        task_templates = []

        # 项目1: BMS老化测试设备 (H2 - 有风险)
        if project.project_code == 'DEMO001':
            task_templates = [
                # 机械部任务
                {'title': 'DEMO-主框架结构设计', 'dept': '机械部', 'progress': 100, 'status': 'COMPLETED', 'hours': 24},
                {'title': 'DEMO-传动机构设计', 'dept': '机械部', 'progress': 80, 'status': 'IN_PROGRESS', 'hours': 20},
                {'title': 'DEMO-装配图纸绘制', 'dept': '机械部', 'progress': 60, 'status': 'IN_PROGRESS', 'hours': 16},
                {'title': 'DEMO-BOM清单整理', 'dept': '机械部', 'progress': 30, 'status': 'IN_PROGRESS', 'hours': 8, 'delay': 2},
                {'title': 'DEMO-机械零件加工', 'dept': '机械部', 'progress': 0, 'status': 'ACCEPTED', 'hours': 40},

                # 电气部任务
                {'title': 'DEMO-电气原理图设计', 'dept': '电气部', 'progress': 100, 'status': 'COMPLETED', 'hours': 20},
                {'title': 'DEMO-PLC程序开发', 'dept': '电气部', 'progress': 65, 'status': 'IN_PROGRESS', 'hours': 32, 'delay': 3},
                {'title': 'DEMO-配电柜装配', 'dept': '电气部', 'progress': 40, 'status': 'IN_PROGRESS', 'hours': 16},
                {'title': 'DEMO-电气接线', 'dept': '电气部', 'progress': 0, 'status': 'ACCEPTED', 'hours': 24},

                # 软件部任务
                {'title': 'DEMO-上位机软件开发', 'dept': '软件部', 'progress': 75, 'status': 'IN_PROGRESS', 'hours': 40},
                {'title': 'DEMO-测试流程编程', 'dept': '软件部', 'progress': 50, 'status': 'IN_PROGRESS', 'hours': 24},
                {'title': 'DEMO-数据采集程序', 'dept': '软件部', 'progress': 20, 'status': 'IN_PROGRESS', 'hours': 16},
                {'title': 'DEMO-报表生成功能', 'dept': '软件部', 'progress': 0, 'status': 'ACCEPTED', 'hours': 12},
            ]

        # 项目2: EOL功能测试设备 (H1 - 正常)
        elif project.project_code == 'DEMO002':
            task_templates = [
                # 机械部任务
                {'title': 'DEMO-测试台架设计', 'dept': '机械部', 'progress': 100, 'status': 'COMPLETED', 'hours': 32},
                {'title': 'DEMO-夹具机构设计', 'dept': '机械部', 'progress': 100, 'status': 'COMPLETED', 'hours': 24},
                {'title': 'DEMO-导轨滑台装配', 'dept': '机械部', 'progress': 85, 'status': 'IN_PROGRESS', 'hours': 20},
                {'title': 'DEMO-机械调试', 'dept': '机械部', 'progress': 60, 'status': 'IN_PROGRESS', 'hours': 16},

                # 电气部任务
                {'title': 'DEMO-控制系统设计', 'dept': '电气部', 'progress': 100, 'status': 'COMPLETED', 'hours': 28},
                {'title': 'DEMO-传感器选型安装', 'dept': '电气部', 'progress': 90, 'status': 'IN_PROGRESS', 'hours': 12},
                {'title': 'DEMO-电气调试', 'dept': '电气部', 'progress': 70, 'status': 'IN_PROGRESS', 'hours': 20},

                # 软件部任务
                {'title': 'DEMO-测试软件开发', 'dept': '软件部', 'progress': 95, 'status': 'IN_PROGRESS', 'hours': 48},
                {'title': 'DEMO-通讯协议对接', 'dept': '软件部', 'progress': 80, 'status': 'IN_PROGRESS', 'hours': 24},
                {'title': 'DEMO-数据库设计', 'dept': '软件部', 'progress': 100, 'status': 'COMPLETED', 'hours': 16},
            ]

        # 项目3: ICT测试设备 (H3 - 阻塞)
        elif project.project_code == 'DEMO003':
            task_templates = [
                # 机械部任务
                {'title': 'DEMO-整机框架设计', 'dept': '机械部', 'progress': 80, 'status': 'IN_PROGRESS', 'hours': 28},
                {'title': 'DEMO-探针治具设计', 'dept': '机械部', 'progress': 40, 'status': 'IN_PROGRESS', 'hours': 32, 'delay': 5},
                {'title': 'DEMO-气动系统设计', 'dept': '机械部', 'progress': 25, 'status': 'IN_PROGRESS', 'hours': 20, 'delay': 4},
                {'title': 'DEMO-机械零件采购', 'dept': '机械部', 'progress': 10, 'status': 'IN_PROGRESS', 'hours': 8, 'delay': 7},

                # 电气部任务
                {'title': 'DEMO-电气方案设计', 'dept': '电气部', 'progress': 60, 'status': 'IN_PROGRESS', 'hours': 24},
                {'title': 'DEMO-继电器选型', 'dept': '电气部', 'progress': 30, 'status': 'IN_PROGRESS', 'hours': 12, 'delay': 3},
                {'title': 'DEMO-配线图绘制', 'dept': '电气部', 'progress': 20, 'status': 'IN_PROGRESS', 'hours': 16},
                {'title': 'DEMO-开关电源选型', 'dept': '电气部', 'progress': 0, 'status': 'ACCEPTED', 'hours': 8},

                # 软件部任务
                {'title': 'DEMO-ICT测试程序', 'dept': '软件部', 'progress': 45, 'status': 'IN_PROGRESS', 'hours': 40},
                {'title': 'DEMO-夹具定位算法', 'dept': '软件部', 'progress': 20, 'status': 'IN_PROGRESS', 'hours': 24, 'delay': 6},
                {'title': 'DEMO-界面设计', 'dept': '软件部', 'progress': 15, 'status': 'IN_PROGRESS', 'hours': 16},
                {'title': 'DEMO-不良品统计', 'dept': '软件部', 'progress': 0, 'status': 'ACCEPTED', 'hours': 12},
            ]

        # 创建任务
        for i, task_template in enumerate(task_templates):
            dept = task_template['dept']
            if dept in users_by_dept and users_by_dept[dept]:
                # 轮流分配给该部门的用户
                assignee = users_by_dept[dept][i % len(users_by_dept[dept])]

                # 计算日期
                plan_start = datetime.now().date() - timedelta(days=30)
                delay_days = task_template.get('delay', 0)
                plan_end = datetime.now().date() - timedelta(days=5)  # 原计划5天前结束
                actual_start = plan_start if task_template['status'] != 'ACCEPTED' else None

                # 如果有延期，设置新的完成日期
                is_delayed = delay_days > 0
                new_completion_date = plan_end + timedelta(days=delay_days) if is_delayed else None

                # 生成唯一的task_code
                task_code = f"{project.project_code}-T{(i+1):03d}"

                task = TaskUnified(
                    task_code=task_code,  # 添加task_code
                    task_type='DESIGN',  # 添加task_type
                    project_id=project.id,
                    title=task_template['title'],
                    description=f"{task_template['title']} - 演示任务",
                    status=task_template['status'],
                    priority='MEDIUM',
                    progress=task_template['progress'],
                    estimated_hours=task_template['hours'],
                    actual_hours=task_template['hours'] * task_template['progress'] / 100,
                    plan_start_date=plan_start,
                    plan_end_date=plan_end,
                    actual_start_date=actual_start,
                    assignee_id=assignee.id,
                    source_type='PROJECT',
                    source_id=project.id,
                    source_name=project.project_name,  # 使用project_name
                    assignee_name=assignee.real_name,
                    is_delayed=is_delayed,
                    new_completion_date=new_completion_date,
                    deadline=datetime.combine(plan_end, datetime.min.time()) if plan_end else None,
                )
                db.add(task)
                tasks.append(task)

    db.commit()
    print(f"✅ 创建了 {len(tasks)} 个演示任务")
    return tasks

def create_project_members(db: Session, projects, users):
    """为项目添加成员关联"""
    members = []

    # 检查是否已存在项目成员
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id.in_([p.id for p in projects])
    ).first()
    if existing:
        print("项目成员关联已存在，跳过创建")
        return db.query(ProjectMember).filter(
            ProjectMember.project_id.in_([p.id for p in projects])
        ).all()

    # 找到项目经理用户
    pm_user = db.query(User).filter(User.username == 'demo_pm_liu').first()

    # 为每个项目添加所有工程师和项目经理作为成员
    for project in projects:
        # 添加项目经理
        if pm_user:
            pm_member = ProjectMember(
                project_id=project.id,
                user_id=pm_user.id,
                role_code='PM',
                allocation_pct=50,
                is_active=True
            )
            db.add(pm_member)
            members.append(pm_member)

        # 添加所有工程师作为项目成员
        for user in users:
            if user.username != 'demo_pm_liu':  # 跳过项目经理
                member = ProjectMember(
                    project_id=project.id,
                    user_id=user.id,
                    role_code='ENGINEER',
                    allocation_pct=80,
                    is_active=True
                )
                db.add(member)
                members.append(member)

    db.commit()
    print(f"✅ 创建了 {len(members)} 个项目成员关联")
    return members

def main():
    """主函数"""
    print("=" * 60)
    print("跨部门进度演示数据生成脚本")
    print("=" * 60)
    print()

    with get_db_session() as db:
        # 0. 先创建员工记录
        print("0. 创建演示员工记录...")
        employees = create_demo_employees(db)

        # 1. 创建用户
        print("\n1. 创建演示用户...")
        users = create_demo_users(db)

        # 2. 创建项目
        print("\n2. 创建演示项目...")
        projects = create_demo_projects(db)

        # 3. 创建任务
        print("\n3. 创建跨部门任务...")
        tasks = create_demo_tasks(db, projects, users)

        # 4. 创建项目成员关联
        print("\n4. 创建项目成员关联...")
        members = create_project_members(db, projects, users)

        print("\n" + "=" * 60)
        print("✅ 演示数据生成完成!")
        print("=" * 60)
        print()
        print("生成的数据:")
        print(f"  - 用户: {len(users)} 个")
        print(f"  - 项目: {len(projects)} 个")
        print(f"  - 任务: {len(tasks)} 个")
        print(f"  - 项目成员: {len(members)} 个")
        print()
        print("项目详情:")
        for proj in projects:
            task_count = db.query(TaskUnified).filter(TaskUnified.project_id == proj.id).count()
            print(f"  - {proj.project_code}: {proj.project_name}")
            print(f"    健康度: {proj.health}, 进度: {proj.progress_pct}%, 任务数: {task_count}")
        print()
        print("您可以访问以下API查看跨部门进度:")
        for proj in projects:
            print(f"  - GET /api/v1/engineers/projects/{proj.id}/progress-visibility")
        print()
        print("前端访问: http://localhost:5173")
        print("  1. 登录账号: demo_pm_liu / demo123")
        print("  2. 访问 PMO驾驶舱")
        print("  3. 在\"跨部门进度视图\"中选择项目")
        print()

if __name__ == "__main__":
    main()
