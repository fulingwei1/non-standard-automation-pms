#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 presales-project 迁移数据到现有项目管理系统

将 presales-project/presales-evaluation-system 中的评估数据迁移到现有系统
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_session, init_db
from app.models.enums import (
    AssessmentDecisionEnum,
    AssessmentSourceTypeEnum,
    AssessmentStatusEnum,
)
from app.models.project import Customer
from app.models.sales import (
    AIClarification,
    FailureCase,
    Lead,
    LeadRequirementDetail,
    OpenItem,
    Opportunity,
    RequirementFreeze,
    ScoringRule,
    TechnicalAssessment,
)
from app.models.user import User


def migrate_scoring_rules(source_db_path: str, target_db_session):
    """迁移评分规则"""
    print("迁移评分规则...")

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    cursor = source_conn.cursor()

    rules = cursor.execute("SELECT * FROM ScoringRule WHERE isActive = 1").fetchall()

    for rule in rules:
        # 检查是否已存在
        existing = target_db_session.query(ScoringRule).filter(
            ScoringRule.version == rule['version']
        ).first()

        if not existing:
            new_rule = ScoringRule(
                version=rule['version'],
                rules_json=rule['rulesJson'],
                is_active=True,
                description=rule.get('description'),
                created_by=None  # 需要映射用户ID
            )
            target_db_session.add(new_rule)
            print(f"  迁移评分规则: {rule['version']}")

    target_db_session.commit()
    source_conn.close()


def migrate_failure_cases(source_db_path: str, target_db_session, user_id_map: Dict[str, int]):
    """迁移失败案例"""
    print("迁移失败案例...")

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    cursor = source_conn.cursor()

    cases = cursor.execute("SELECT * FROM FailureCase").fetchall()

    for case in cases:
        # 检查是否已存在
        existing = target_db_session.query(FailureCase).filter(
            FailureCase.case_code == case['caseCode']
        ).first()

        if not existing:
            created_by = user_id_map.get(case.get('createdById')) if case.get('createdById') else None

            new_case = FailureCase(
                case_code=case['caseCode'],
                project_name=case['projectName'],
                industry=case['industry'],
                product_types=case.get('productTypes'),
                processes=case.get('processes'),
                takt_time_s=case.get('taktTimeS'),
                annual_volume=case.get('annualVolume'),
                budget_status=case.get('budgetStatus'),
                customer_project_status=case.get('customerProjectStatus'),
                spec_status=case.get('specStatus'),
                price_sensitivity=case.get('priceSensitivity'),
                delivery_months=case.get('deliveryMonths'),
                failure_tags=case['failureTags'],
                core_failure_reason=case['coreFailureReason'],
                early_warning_signals=case['earlyWarningSignals'],
                final_result=case.get('finalResult'),
                lesson_learned=case['lessonLearned'],
                keywords=case['keywords'],
                created_by=created_by
            )
            target_db_session.add(new_case)
            print(f"  迁移失败案例: {case['caseCode']}")

    target_db_session.commit()
    source_conn.close()


def migrate_assessments(source_db_path: str, target_db_session,
                       user_id_map: Dict[str, int],
                       project_to_lead_map: Dict[str, int],
                       project_to_opp_map: Dict[str, int]):
    """迁移评估结果"""
    print("迁移技术评估...")

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    cursor = source_conn.cursor()

    evaluations = cursor.execute("SELECT * FROM Evaluation").fetchall()

    for eval_data in evaluations:
        project_id = eval_data['projectId']

        # 尝试映射到线索或商机
        source_type = None
        source_id = None

        if project_id in project_to_lead_map:
            source_type = AssessmentSourceTypeEnum.LEAD.value
            source_id = project_to_lead_map[project_id]
        elif project_id in project_to_opp_map:
            source_type = AssessmentSourceTypeEnum.OPPORTUNITY.value
            source_id = project_to_opp_map[project_id]
        else:
            print(f"  跳过评估（无法映射项目）: {eval_data.get('id')}")
            continue

        evaluator_id = user_id_map.get(eval_data.get('evaluatorId')) if eval_data.get('evaluatorId') else None

        # 映射决策建议
        decision_map = {
            '推荐立项': AssessmentDecisionEnum.RECOMMEND.value,
            '有条件立项': AssessmentDecisionEnum.CONDITIONAL.value,
            '暂缓': AssessmentDecisionEnum.DEFER.value,
            '不建议立项': AssessmentDecisionEnum.NOT_RECOMMEND.value
        }
        decision = decision_map.get(eval_data['decision'], AssessmentDecisionEnum.DEFER.value)

        new_assessment = TechnicalAssessment(
            source_type=source_type,
            source_id=source_id,
            evaluator_id=evaluator_id,
            status=AssessmentStatusEnum.COMPLETED.value,
            total_score=eval_data['totalScore'],
            dimension_scores=eval_data.get('dimensionScores'),
            veto_triggered=eval_data.get('vetoTriggered', False),
            veto_rules=eval_data.get('vetoRules'),
            decision=decision,
            risks=eval_data.get('risks'),
            similar_cases=eval_data.get('similarCases'),
            ai_analysis=eval_data.get('aiAnalysis'),
            conditions=eval_data.get('conditions'),
            evaluated_at=datetime.fromisoformat(eval_data['createdAt'].replace('Z', '+00:00')) if eval_data.get('createdAt') else None
        )

        target_db_session.add(new_assessment)
        target_db_session.flush()

        # 更新来源对象的评估关联
        if source_type == AssessmentSourceTypeEnum.LEAD.value:
            lead = target_db_session.query(Lead).filter(Lead.id == source_id).first()
            if lead:
                lead.assessment_id = new_assessment.id
                lead.assessment_status = AssessmentStatusEnum.COMPLETED.value
        elif source_type == AssessmentSourceTypeEnum.OPPORTUNITY.value:
            opp = target_db_session.query(Opportunity).filter(Opportunity.id == source_id).first()
            if opp:
                opp.assessment_id = new_assessment.id
                opp.assessment_status = AssessmentStatusEnum.COMPLETED.value

        print(f"  迁移评估: {eval_data.get('id')} -> {source_type}:{source_id}")

    target_db_session.commit()
    source_conn.close()


def build_user_id_map(source_db_path: str, target_db_session) -> Dict[str, int]:
    """构建用户ID映射表（presales-project的User ID -> 现有系统的User ID）"""
    print("构建用户ID映射...")

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    cursor = source_conn.cursor()

    source_users = cursor.execute("SELECT * FROM User").fetchall()
    user_id_map = {}

    for source_user in source_users:
        # 尝试通过用户名（pinyin）匹配
        pinyin = source_user.get('pinyin')
        if pinyin:
            target_user = target_db_session.query(User).filter(User.username == pinyin).first()
            if target_user:
                user_id_map[source_user['id']] = target_user.id
                print(f"  映射用户: {pinyin} ({source_user['id']} -> {target_user.id})")

    source_conn.close()
    return user_id_map


def build_project_mapping(source_db_path: str, target_db_session) -> tuple:
    """构建项目映射（presales-project的Project ID -> Lead/Opportunity ID）"""
    print("构建项目映射...")

    source_conn = sqlite3.connect(source_db_path)
    source_conn.row_factory = sqlite3.Row
    cursor = source_conn.cursor()

    projects = cursor.execute("SELECT * FROM Project").fetchall()
    project_to_lead_map = {}
    project_to_opp_map = {}

    for project in projects:
        project_code = project.get('projectCode')
        customer_name = project.get('customerName')

        # 尝试通过客户名称和项目编码匹配线索或商机
        if customer_name:
            # 先查找线索
            lead = target_db_session.query(Lead).filter(
                Lead.customer_name == customer_name
            ).order_by(Lead.created_at.desc()).first()

            if lead:
                project_to_lead_map[project['id']] = lead.id
                continue

            # 再查找商机
            opp = target_db_session.query(Opportunity).join(
                Opportunity.customer
            ).filter(
                Customer.customer_name == customer_name
            ).order_by(Opportunity.created_at.desc()).first()

            if opp:
                project_to_opp_map[project['id']] = opp.id

    source_conn.close()
    return project_to_lead_map, project_to_opp_map


def main():
    """主函数"""
    presales_db_path = project_root / "presales-project" / "presales-evaluation-system" / "prisma" / "dev.db"

    if not presales_db_path.exists():
        print(f"错误: 找不到 presales-project 数据库文件: {presales_db_path}")
        print("请确保 presales-project 数据库文件存在")
        return

    print(f"开始迁移数据...")
    print(f"源数据库: {presales_db_path}")

    # 初始化目标数据库
    init_db()
    target_db = get_session()

    try:
        # 1. 构建用户ID映射
        user_id_map = build_user_id_map(str(presales_db_path), target_db)

        # 2. 构建项目映射
        project_to_lead_map, project_to_opp_map = build_project_mapping(str(presales_db_path), target_db)

        # 3. 迁移评分规则
        migrate_scoring_rules(str(presales_db_path), target_db)

        # 4. 迁移失败案例
        migrate_failure_cases(str(presales_db_path), target_db, user_id_map)

        # 5. 迁移评估结果
        migrate_assessments(str(presales_db_path), target_db, user_id_map,
                          project_to_lead_map, project_to_opp_map)

        print("\n数据迁移完成！")

    except Exception as e:
        print(f"\n迁移过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        target_db.rollback()
    finally:
        target_db.close()


if __name__ == "__main__":
    main()





