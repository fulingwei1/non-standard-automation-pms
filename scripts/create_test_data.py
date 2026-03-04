#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建UAT测试数据
包括：测试用户、测试项目、测试任务
"""

import sys

sys.path.insert(0, "/Users/flw/non-standard-automation-pm")

from datetime import date, datetime, timedelta

from app.core.security import get_password_hash
from app.models.base import get_db_session
from app.models.project import Project, ProjectMember
from app.models.task_center import TaskUnified
from app.models.user import User


def create_test_users(db):
    """创建测试用户"""
    print("=" * 70)
    print("创建测试用户...")
    print("=" * 70)

    # 检查用户是否已存在
    existing = db.query(User).filter(User.username.like("test_%")).all()
    if existing:
        print(f"⚠️  发现 {len(existing)} 个测试用户已存在，跳过创建")
        return {user.username: user for user in existing}

    users_data = [
        {
            "username": "test_engineer_mech",
            "real_name": "张工（测试）",
            "department": "机械部",
            "email": "test.mech@example.com",
        },
        {
            "username": "test_engineer_elec",
            "real_name": "李工（测试）",
            "department": "电气部",
            "email": "test.elec@example.com",
        },
        {
            "username": "test_engineer_test",
            "real_name": "王工（测试）",
            "department": "测试部",
            "email": "test.test@example.com",
        },
        {
            "username": "test_pm",
            "real_name": "张经理（测试）",
            "department": "PMO",
            "email": "test.pm@example.com",
        },
        {
            "username": "test_manager",
            "real_name": "赵部长（测试）",
            "department": "机械部",
            "email": "test.manager@example.com",
        },
    ]

    users = {}
    password_hash = get_password_hash("test123")

    for user_data in users_data:
        user = User(
            username=user_data["username"],
            real_name=user_data["real_name"],
            password_hash=password_hash,
            department=user_data["department"],
            email=user_data.get("email"),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(user)
        users[user_data["username"]] = user
        print(f"✅ 创建用户: {user.username} ({user.real_name}) - {user.department}")

    db.flush()  # 获取ID但不提交
    print(f"\n共创建 {len(users)} 个测试用户")
    return users


def create_test_project(db, pm_user):
    """创建测试项目"""
    print("\n" + "=" * 70)
    print("创建测试项目...")
    print("=" * 70)

    # 检查项目是否已存在
    existing = db.query(Project).filter(Project.project_code == "TEST-PJ001").first()
    if existing:
        print(f"⚠️  测试项目已存在: {existing.project_code}")
        return existing

    project = Project(
        project_code="TEST-PJ001",
        project_name="UAT测试项目 - ICT测试设备",
        customer_id=None,  # 测试项目不关联客户
        customer_name="测试客户公司",
        pm_id=pm_user.id,
        project_type="STANDARD",
        stage="S4",  # 加工制造阶段
        status="IN_PROGRESS",
        health="H1",  # 正常
        progress_pct=35.5,
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=60),
        actual_start_date=date.today() - timedelta(days=30),
        budget_amount=500000,
        contract_amount=550000,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    db.add(project)
    db.flush()

    print(f"✅ 创建项目: {project.project_code} - {project.project_name}")
    print(f"   项目经理: {pm_user.real_name}")
    print(f"   当前阶段: {project.stage}")
    print(f"   项目进度: {project.progress_pct}%")

    return project


def create_project_members(db, project, users):
    """创建项目成员"""
    print("\n" + "=" * 70)
    print("添加项目成员...")
    print("=" * 70)

    members_data = [
        {
            "user": users["test_engineer_mech"],
            "roles": ["机械工程师"],
            "allocation_pct": 100,
        },
        {
            "user": users["test_engineer_elec"],
            "roles": ["电气工程师"],
            "allocation_pct": 100,
        },
        {
            "user": users["test_engineer_test"],
            "roles": ["测试工程师"],
            "allocation_pct": 80,
        },
    ]

    for member_data in members_data:
        member = ProjectMember(
            project_id=project.id,
            user_id=member_data["user"].id,
            roles=member_data["roles"],
            allocation_pct=member_data["allocation_pct"],
            is_active=True,
            joined_at=datetime.now(),
        )
        db.add(member)
        print(f"✅ 添加成员: {member_data['user'].real_name} - {', '.join(member_data['roles'])}")

    print(f"\n共添加 {len(members_data)} 个项目成员")


def create_test_tasks(db, project, users):
    """创建测试任务"""
    print("\n" + "=" * 70)
    print("创建测试任务...")
    print("=" * 70)

    tasks_data = [
        # 机械部任务
        {
            "title": "设计机械框架结构",
            "assignee": users["test_engineer_mech"],
            "status": "COMPLETED",
            "progress": 100,
            "priority": "HIGH",
            "estimated_hours": 40,
            "actual_hours": 38,
            "stage": "S2",
        },
        {
            "title": "设计夹具固定方案",
            "assignee": users["test_engineer_mech"],
            "status": "IN_PROGRESS",
            "progress": 60,
            "priority": "HIGH",
            "estimated_hours": 24,
            "actual_hours": 15,
            "stage": "S4",
        },
        {
            "title": "机械零件加工",
            "assignee": users["test_engineer_mech"],
            "status": "IN_PROGRESS",
            "progress": 30,
            "priority": "MEDIUM",
            "estimated_hours": 60,
            "actual_hours": 20,
            "stage": "S4",
        },
        {
            "title": "装配工艺文件编写",
            "assignee": users["test_engineer_mech"],
            "status": "ACCEPTED",
            "progress": 0,
            "priority": "MEDIUM",
            "estimated_hours": 16,
            "stage": "S4",
        },
        {
            "title": "机械部件验收",
            "assignee": users["test_engineer_mech"],
            "status": "PENDING",
            "progress": 0,
            "priority": "LOW",
            "estimated_hours": 8,
            "stage": "S6",
        },
        # 电气部任务
        {
            "title": "电气原理图设计",
            "assignee": users["test_engineer_elec"],
            "status": "COMPLETED",
            "progress": 100,
            "priority": "HIGH",
            "estimated_hours": 48,
            "actual_hours": 50,
            "stage": "S2",
        },
        {
            "title": "PLC程序开发",
            "assignee": users["test_engineer_elec"],
            "status": "IN_PROGRESS",
            "progress": 70,
            "priority": "HIGH",
            "estimated_hours": 80,
            "actual_hours": 56,
            "stage": "S4",
        },
        {
            "title": "电气柜装配",
            "assignee": users["test_engineer_elec"],
            "status": "IN_PROGRESS",
            "progress": 40,
            "priority": "MEDIUM",
            "estimated_hours": 32,
            "actual_hours": 12,
            "stage": "S4",
            "is_delayed": True,
            "delay_reason": "元器件到货延迟3天",
            "delay_responsibility": "供应商",
            "delay_impact_scope": "PROJECT",
            "new_completion_date": date.today() + timedelta(days=5),
        },
        {
            "title": "人机界面设计",
            "assignee": users["test_engineer_elec"],
            "status": "ACCEPTED",
            "progress": 0,
            "priority": "MEDIUM",
            "estimated_hours": 24,
            "stage": "S4",
        },
        # 测试部任务
        {
            "title": "编写测试用例",
            "assignee": users["test_engineer_test"],
            "status": "COMPLETED",
            "progress": 100,
            "priority": "HIGH",
            "estimated_hours": 24,
            "actual_hours": 22,
            "stage": "S5",
        },
        {
            "title": "功能测试执行",
            "assignee": users["test_engineer_test"],
            "status": "IN_PROGRESS",
            "progress": 50,
            "priority": "HIGH",
            "estimated_hours": 40,
            "actual_hours": 20,
            "stage": "S5",
        },
        {
            "title": "性能测试",
            "assignee": users["test_engineer_test"],
            "status": "ACCEPTED",
            "progress": 0,
            "priority": "MEDIUM",
            "estimated_hours": 32,
            "stage": "S5",
        },
        {
            "title": "编写测试报告",
            "assignee": users["test_engineer_test"],
            "status": "PENDING",
            "progress": 0,
            "priority": "MEDIUM",
            "estimated_hours": 16,
            "stage": "S6",
        },
    ]

    task_code_counter = 1
    created_tasks = []

    for task_data in tasks_data:
        task = TaskUnified(
            task_code=f"TEST-TASK-{task_code_counter:03d}",
            title=task_data["title"],
            task_type="PROJECT_TASK",
            project_id=project.id,
            assignee_id=task_data["assignee"].id,
            status=task_data["status"],
            progress=task_data["progress"],
            priority=task_data["priority"],
            estimated_hours=task_data.get("estimated_hours"),
            actual_hours=task_data.get("actual_hours"),
            stage=task_data.get("stage"),
            is_delayed=task_data.get("is_delayed", False),
            delay_reason=task_data.get("delay_reason"),
            delay_responsibility=task_data.get("delay_responsibility"),
            delay_impact_scope=task_data.get("delay_impact_scope"),
            new_completion_date=task_data.get("new_completion_date"),
            plan_start_date=date.today() - timedelta(days=10),
            plan_end_date=date.today() + timedelta(days=10),
            deadline=datetime.now() + timedelta(days=10),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 如果任务已完成，设置完成时间
        if task.status == "COMPLETED":
            task.actual_start_date = date.today() - timedelta(days=15)
            task.actual_end_date = date.today() - timedelta(days=2)
        elif task.status == "IN_PROGRESS":
            task.actual_start_date = date.today() - timedelta(days=5)

        db.add(task)
        created_tasks.append(task)
        task_code_counter += 1

        status_emoji = {
            "COMPLETED": "✅",
            "IN_PROGRESS": "🔄",
            "ACCEPTED": "📝",
            "PENDING": "⏳",
        }.get(task.status, "❓")

        delay_flag = " ⚠️ 延期" if task.is_delayed else ""

        print(f"{status_emoji} {task.task_code}: {task.title}")
        print(
            f"   负责人: {task_data['assignee'].real_name} | "
            f"进度: {task.progress}% | "
            f"优先级: {task.priority}{delay_flag}"
        )

    print(f"\n共创建 {len(created_tasks)} 个测试任务")
    print(f"   ✅ 已完成: {len([t for t in created_tasks if t.status == 'COMPLETED'])}")
    print(f"   🔄 进行中: {len([t for t in created_tasks if t.status == 'IN_PROGRESS'])}")
    print(f"   📝 已接收: {len([t for t in created_tasks if t.status == 'ACCEPTED'])}")
    print(f"   ⏳ 待接收: {len([t for t in created_tasks if t.status == 'PENDING'])}")
    print(f"   ⚠️  延期: {len([t for t in created_tasks if t.is_delayed])}")

    return created_tasks


def update_project_progress(db, project, tasks):
    """更新项目进度（手动计算）"""
    print("\n" + "=" * 70)
    print("更新项目进度...")
    print("=" * 70)

    if not tasks:
        print("⚠️  没有任务，跳过进度更新")
        return

    # 计算项目整体进度
    total_progress = sum(t.progress for t in tasks)
    avg_progress = total_progress / len(tasks)

    project.progress_pct = round(avg_progress, 2)

    print(f"✅ 项目进度已更新: {project.progress_pct}%")
    print(f"   任务总数: {len(tasks)}")
    print(f"   平均进度: {avg_progress:.2f}%")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("UAT测试数据创建脚本")
    print("=" * 70)
    print()

    try:
        with get_db_session() as db:
            # 1. 创建测试用户
            users = create_test_users(db)

            # 2. 创建测试项目
            pm_user = users["test_pm"]
            project = create_test_project(db, pm_user)

            # 3. 添加项目成员
            create_project_members(db, project, users)

            # 4. 创建测试任务
            tasks = create_test_tasks(db, project, users)

            # 5. 更新项目进度
            update_project_progress(db, project, tasks)

            # 提交所有更改
            db.commit()

            print("\n" + "=" * 70)
            print("✅ 测试数据创建成功！")
            print("=" * 70)
            print()
            print("测试账号信息:")
            print("-" * 70)
            for username, user in users.items():
                print(f"用户名: {username:<25} 密码: ********")
                print(f"姓名:   {user.real_name:<25} 部门: {user.department}")
                print()

            print("测试项目信息:")
            print("-" * 70)
            print(f"项目编号: {project.project_code}")
            print(f"项目名称: {project.project_name}")
            print(f"项目进度: {project.progress_pct}%")
            print(f"项目阶段: {project.stage}")
            print(f"任务总数: {len(tasks)}")
            print()

            print("下一步:")
            print("-" * 70)
            print("1. 使用测试账号登录获取JWT token")
            print("2. 运行 ./test_uat_automated.sh 执行自动化测试")
            print("3. 访问 http://localhost:8000/docs 进行手动测试")
            print("4. 参考 UAT_TEST_PLAN.md 执行完整测试用例")
            print()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
