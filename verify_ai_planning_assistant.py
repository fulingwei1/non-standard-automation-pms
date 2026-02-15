#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI项目规划助手 - 快速验证脚本
验证所有核心功能是否正常工作
"""

import sys
import os
import asyncio
from datetime import date

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models import Project, User
from app.models.ai_planning import AIProjectPlanTemplate, AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import (
    AIProjectPlanGenerator,
    AIWbsDecomposer,
    AIResourceOptimizer,
    AIScheduleOptimizer,
    GLMService
)


# 数据库设置
DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")


def print_info(message):
    """打印信息"""
    print(f"ℹ️  {message}")


async def verify_database_tables():
    """验证数据库表是否创建"""
    print_section("1. 验证数据库表")
    
    db = SessionLocal()
    
    try:
        # 检查三张核心表
        tables_to_check = [
            (AIProjectPlanTemplate, "ai_project_plan_templates"),
            (AIWbsSuggestion, "ai_wbs_suggestions"),
            (AIResourceAllocation, "ai_resource_allocations"),
        ]
        
        for model, table_name in tables_to_check:
            try:
                count = db.query(model).count()
                print_success(f"表 {table_name} 存在 (记录数: {count})")
            except Exception as e:
                print_error(f"表 {table_name} 不存在或有错误: {e}")
                return False
        
        return True
        
    finally:
        db.close()


async def verify_glm_service():
    """验证GLM服务"""
    print_section("2. 验证GLM服务")
    
    glm = GLMService()
    
    if glm.is_available():
        print_success("GLM服务可用")
        print_info(f"使用模型: {glm.model}")
    else:
        print_error("GLM服务不可用（将使用规则引擎备用方案）")
    
    return True


async def verify_plan_generator():
    """验证项目计划生成器"""
    print_section("3. 验证项目计划生成器")
    
    db = SessionLocal()
    
    try:
        generator = AIProjectPlanGenerator(db)
        
        print_info("生成测试项目计划...")
        
        template = await generator.generate_plan(
            project_name="验证测试项目",
            project_type="WEB_DEV",
            requirements="开发一个简单的Web应用",
            industry="互联网",
            complexity="MEDIUM",
            use_template=False
        )
        
        if template:
            print_success(f"计划生成成功 (ID: {template.id})")
            print_info(f"  - 预计工期: {template.estimated_duration_days}天")
            print_info(f"  - 预计工时: {template.estimated_effort_hours}小时")
            print_info(f"  - 置信度: {template.confidence_score}%")
            db.commit()
            return True
        else:
            print_error("计划生成失败")
            return False
            
    except Exception as e:
        print_error(f"计划生成异常: {e}")
        db.rollback()
        return False
    finally:
        db.close()


async def verify_wbs_decomposer():
    """验证WBS分解器"""
    print_section("4. 验证WBS分解器")
    
    db = SessionLocal()
    
    try:
        # 创建测试项目
        project = Project(
            project_code="VERIFY_WBS_001",
            project_name="WBS验证项目",
            project_type="WEB_DEV",
            status="ST01"
        )
        db.add(project)
        db.commit()
        
        decomposer = AIWbsDecomposer(db)
        
        print_info(f"分解项目 (ID: {project.id})...")
        
        suggestions = await decomposer.decompose_project(
            project_id=project.id,
            max_level=2
        )
        
        if suggestions and len(suggestions) > 0:
            print_success(f"WBS分解成功 (生成 {len(suggestions)} 个任务)")
            
            level_1 = [s for s in suggestions if s.wbs_level == 1]
            level_2 = [s for s in suggestions if s.wbs_level == 2]
            critical = [s for s in suggestions if s.is_critical_path]
            
            print_info(f"  - 一级任务: {len(level_1)}个")
            print_info(f"  - 二级任务: {len(level_2)}个")
            print_info(f"  - 关键路径任务: {len(critical)}个")
            
            db.commit()
            return True
        else:
            print_error("WBS分解失败")
            return False
            
    except Exception as e:
        print_error(f"WBS分解异常: {e}")
        db.rollback()
        return False
    finally:
        db.close()


async def verify_resource_optimizer():
    """验证资源优化器"""
    print_section("5. 验证资源优化器")
    
    db = SessionLocal()
    
    try:
        # 确保有测试用户
        user_count = db.query(User).filter(User.is_active == True).count()
        
        if user_count == 0:
            print_info("创建测试用户...")
            test_user = User(
                username="test_dev",
                real_name="测试开发",
                role="开发工程师",
                is_active=True
            )
            db.add(test_user)
            db.commit()
        
        # 获取第一个WBS任务
        wbs = db.query(AIWbsSuggestion).filter(
            AIWbsSuggestion.is_active == True
        ).first()
        
        if not wbs:
            print_error("没有可用的WBS任务")
            return False
        
        optimizer = AIResourceOptimizer(db)
        
        print_info(f"为任务 '{wbs.task_name}' 分配资源...")
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=wbs.id
        )
        
        if allocations and len(allocations) > 0:
            print_success(f"资源分配成功 (推荐 {len(allocations)} 个候选)")
            
            for i, alloc in enumerate(allocations[:3], 1):
                print_info(f"  {i}. 用户ID: {alloc.user_id}, "
                          f"匹配度: {alloc.overall_match_score:.1f}%, "
                          f"类型: {alloc.allocation_type}")
            
            db.commit()
            return True
        else:
            print_error("资源分配失败")
            return False
            
    except Exception as e:
        print_error(f"资源分配异常: {e}")
        db.rollback()
        return False
    finally:
        db.close()


async def verify_schedule_optimizer():
    """验证排期优化器"""
    print_section("6. 验证排期优化器")
    
    db = SessionLocal()
    
    try:
        # 获取有WBS任务的项目
        wbs = db.query(AIWbsSuggestion).filter(
            AIWbsSuggestion.is_active == True
        ).first()
        
        if not wbs:
            print_error("没有可用的WBS任务")
            return False
        
        optimizer = AIScheduleOptimizer(db)
        
        print_info(f"优化项目 (ID: {wbs.project_id}) 的进度排期...")
        
        result = optimizer.optimize_schedule(
            project_id=wbs.project_id,
            start_date=date.today()
        )
        
        if result and 'total_duration_days' in result:
            print_success("排期优化成功")
            print_info(f"  - 总工期: {result['total_duration_days']}天")
            print_info(f"  - 完成日期: {result['end_date']}")
            print_info(f"  - 关键路径长度: {result['critical_path_length']}个任务")
            print_info(f"  - 检测到冲突: {len(result['conflicts'])}个")
            print_info(f"  - 优化建议: {len(result['recommendations'])}条")
            
            return True
        else:
            print_error("排期优化失败")
            return False
            
    except Exception as e:
        print_error(f"排期优化异常: {e}")
        return False
    finally:
        db.close()


async def verify_api_schemas():
    """验证API Schemas"""
    print_section("7. 验证API Schemas")
    
    try:
        from app.schemas.ai_planning import (
            ProjectPlanRequest,
            ProjectPlanResponse,
            WbsDecompositionRequest,
            WbsDecompositionResponse,
            ResourceAllocationRequest,
            ResourceAllocationResponse,
            ScheduleOptimizationRequest,
            ScheduleOptimizationResponse,
        )
        
        schemas = [
            "ProjectPlanRequest",
            "ProjectPlanResponse",
            "WbsDecompositionRequest",
            "WbsDecompositionResponse",
            "ResourceAllocationRequest",
            "ResourceAllocationResponse",
            "ScheduleOptimizationRequest",
            "ScheduleOptimizationResponse",
        ]
        
        for schema in schemas:
            print_success(f"Schema {schema} 已定义")
        
        return True
        
    except Exception as e:
        print_error(f"Schema验证失败: {e}")
        return False


async def main():
    """主验证流程"""
    
    print("\n" + "🚀 " * 20)
    print("  AI项目规划智能助手 - 功能验证")
    print("🚀 " * 20)
    
    results = []
    
    # 1. 验证数据库表
    results.append(await verify_database_tables())
    
    # 2. 验证GLM服务
    results.append(await verify_glm_service())
    
    # 3. 验证项目计划生成器
    results.append(await verify_plan_generator())
    
    # 4. 验证WBS分解器
    results.append(await verify_wbs_decomposer())
    
    # 5. 验证资源优化器
    results.append(await verify_resource_optimizer())
    
    # 6. 验证排期优化器
    results.append(await verify_schedule_optimizer())
    
    # 7. 验证API Schemas
    results.append(await verify_api_schemas())
    
    # 总结
    print_section("验证总结")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print_success("✨ 所有验证通过！系统工作正常。")
        return 0
    else:
        print_error(f"⚠️  有 {total - passed} 项验证失败，请检查日志。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
