# -*- coding: utf-8 -*-
"""
工程师绩效数据自动采集服务
从各个系统自动提取绩效评价所需的数据
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.work_log import WorkLog
from app.models.project import Project, ProjectMember
from app.models.progress import Task
from app.models.ecn import Ecn
from app.models.material import BomHeader, BomItem
from app.models.engineer_performance import (
    DesignReview, MechanicalDebugIssue, TestBugRecord,
    CodeReviewRecord, ElectricalDrawingVersion, PlcProgramVersion,
    KnowledgeContribution, CodeModule, PlcModuleLibrary
)
from app.models.issue import Issue
from app.models.project_evaluation import ProjectEvaluation


class PerformanceDataCollector:
    """绩效数据自动采集服务"""

    # 积极词汇（用于识别自我评价中的正面内容）
    POSITIVE_KEYWORDS = [
        # 完成类
        '完成', '达成', '实现', '交付', '通过', '验收', '合格', '完成度',
        # 解决类
        '解决', '修复', '处理', '消除', '克服', '攻克', '搞定',
        # 优化类
        '优化', '改进', '提升', '增强', '改善', '完善', '精进',
        # 创新类
        '突破', '创新', '革新', '改进', '升级', '迭代',
        # 协作类
        '分享', '协助', '配合', '支持', '帮助', '指导', '培训', '传授',
        '合作', '协同', '配合', '对接', '沟通', '协调',
        # 成功类
        '成功', '顺利', '高效', '优秀', '出色', '卓越', '完美',
        # 知识分享类
        '分享', '传授', '指导', '培训', '讲解', '演示', '展示',
        # 技术突破类
        '突破', '攻克', '解决难题', '技术突破', '创新方案'
    ]

    # 消极词汇（用于识别自我评价中的负面内容）
    NEGATIVE_KEYWORDS = [
        # 困难类
        '困难', '难题', '挑战', '阻碍', '障碍', '瓶颈', '卡点',
        # 问题类
        '问题', '错误', '失败', '异常', '故障', 'bug', '缺陷',
        # 延期类
        '延期', '延迟', '滞后', '超期', '延误', '推迟',
        # 未完成类
        '未完成', '待完成', '进行中', '未解决', '待处理',
        # 需要帮助类
        '需要支持', '需要帮助', '需要协助', '需要指导', '需要资源',
        # 遇到类
        '遇到', '碰到', '面临', '遭遇', '陷入',
        # 风险类
        '风险', '隐患', '担忧', '担心', '不确定',
        # 不足类
        '待解决', '待改进', '不足', '缺失', '缺少', '不够', '欠缺',
        # 技术难点类
        '技术难点', '技术难题', '技术瓶颈', '技术障碍'
    ]

    # 技术相关关键词
    TECH_KEYWORDS = [
        # 设计类
        '设计', '架构', '方案', '规划', '建模', '绘图', '制图',
        # 开发类
        '开发', '编程', '编码', '实现', '编写', '代码', '程序',
        # 调试类
        '调试', '测试', '验证', '检查', '排查', '定位', '分析',
        # 优化类
        '优化', '重构', '改进', '提升', '性能优化', '效率提升',
        # 技术概念类
        '算法', '模块', '接口', '协议', '框架', '库', '组件',
        # 技术难点类
        '技术难点', '技术突破', '技术攻关', '技术方案', '技术选型'
    ]

    # 协作相关关键词
    COLLABORATION_KEYWORDS = [
        # 配合类
        '配合', '协助', '支持', '帮助', '协作', '协同', '合作',
        # 沟通类
        '沟通', '交流', '讨论', '协商', '对接', '协调', '联络',
        # 会议类
        '会议', '评审', '讨论会', '技术交流', '方案评审',
        # 指导类
        '指导', '培训', '分享', '传授', '讲解', '演示', '展示',
        # 反馈类
        '反馈', '建议', '意见', '评价', '评估'
    ]

    # 问题解决场景关键词（上下文分析用）
    PROBLEM_SOLVING_PATTERNS = [
        r'遇到.*?问题.*?解决',
        r'通过.*?方法.*?解决',
        r'分析.*?原因.*?处理',
        r'定位.*?问题.*?修复',
        r'攻克.*?技术难点',
        r'突破.*?技术瓶颈'
    ]

    # 知识分享场景关键词
    KNOWLEDGE_SHARING_PATTERNS = [
        r'分享.*?经验',
        r'培训.*?团队',
        r'指导.*?新人',
        r'传授.*?技术',
        r'讲解.*?方案',
        r'文档.*?整理'
    ]

    # 技术突破场景关键词
    TECH_BREAKTHROUGH_PATTERNS = [
        r'技术突破',
        r'创新方案',
        r'优化.*?性能',
        r'提升.*?效率',
        r'改进.*?算法',
        r'重构.*?架构'
    ]

    def __init__(self, db: Session):
        self.db = db

    # ==================== 工作日志自我评价提取 ====================

    def extract_self_evaluation_from_work_logs(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        从工作日志中提取自我评价数据（增强版：支持上下文分析）

        Returns:
            {
                'positive_count': int,      # 积极词汇出现次数
                'negative_count': int,       # 消极词汇出现次数
                'tech_mentions': int,        # 技术相关提及次数
                'collaboration_mentions': int, # 协作相关提及次数
                'problem_solving_count': int,  # 问题解决场景次数
                'knowledge_sharing_count': int, # 知识分享场景次数
                'tech_breakthrough_count': int, # 技术突破场景次数
                'total_logs': int,           # 总日志数
                'self_evaluation_score': float  # 自我评价得分（0-100）
            }
        """
        try:
            work_logs = self.db.query(WorkLog).filter(
                WorkLog.user_id == engineer_id,
                WorkLog.work_date.between(start_date, end_date),
                WorkLog.status == 'SUBMITTED'
            ).all()

            if not work_logs:
                return {
                    'positive_count': 0,
                    'negative_count': 0,
                    'tech_mentions': 0,
                    'collaboration_mentions': 0,
                    'problem_solving_count': 0,
                    'knowledge_sharing_count': 0,
                    'tech_breakthrough_count': 0,
                    'total_logs': 0,
                    'self_evaluation_score': 75.0  # 默认值
                }

            positive_count = 0
            negative_count = 0
            tech_mentions = 0
            collaboration_mentions = 0
            problem_solving_count = 0
            knowledge_sharing_count = 0
            tech_breakthrough_count = 0

            for log in work_logs:
                if not log.content:
                    continue
                    
                content = log.content.lower()
                
                # 统计积极词汇
                for keyword in self.POSITIVE_KEYWORDS:
                    positive_count += len(re.findall(keyword, content))
                
                # 统计消极词汇
                for keyword in self.NEGATIVE_KEYWORDS:
                    negative_count += len(re.findall(keyword, content))
                
                # 统计技术相关提及
                for keyword in self.TECH_KEYWORDS:
                    tech_mentions += len(re.findall(keyword, content))
                
                # 统计协作相关提及
                for keyword in self.COLLABORATION_KEYWORDS:
                    collaboration_mentions += len(re.findall(keyword, content))
                
                # 上下文分析：问题解决场景
                for pattern in self.PROBLEM_SOLVING_PATTERNS:
                    if re.search(pattern, content):
                        problem_solving_count += 1
                        positive_count += 2  # 问题解决是积极行为
                        break
                
                # 上下文分析：知识分享场景
                for pattern in self.KNOWLEDGE_SHARING_PATTERNS:
                    if re.search(pattern, content):
                        knowledge_sharing_count += 1
                        positive_count += 2  # 知识分享是积极行为
                        collaboration_mentions += 1
                        break
                
                # 上下文分析：技术突破场景
                for pattern in self.TECH_BREAKTHROUGH_PATTERNS:
                    if re.search(pattern, content):
                        tech_breakthrough_count += 1
                        positive_count += 3  # 技术突破是高度积极行为
                        tech_mentions += 2
                        break

            # 计算自我评价得分（增强版）
            # 基础分75，根据积极/消极词汇比例调整
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                positive_ratio = positive_count / total_keywords
                # 积极比例越高，得分越高（最高+25分）
                base_score = 75.0 + (positive_ratio - 0.5) * 50
            else:
                base_score = 75.0
            
            # 场景加分：问题解决、知识分享、技术突破
            scenario_bonus = 0
            if problem_solving_count > 0:
                scenario_bonus += min(problem_solving_count * 2, 10)  # 最多加10分
            if knowledge_sharing_count > 0:
                scenario_bonus += min(knowledge_sharing_count * 1.5, 8)  # 最多加8分
            if tech_breakthrough_count > 0:
                scenario_bonus += min(tech_breakthrough_count * 3, 12)  # 最多加12分
            
            self_evaluation_score = base_score + scenario_bonus
            self_evaluation_score = max(0, min(100, self_evaluation_score))

            return {
                'positive_count': positive_count,
                'negative_count': negative_count,
                'tech_mentions': tech_mentions,
                'collaboration_mentions': collaboration_mentions,
                'problem_solving_count': problem_solving_count,
                'knowledge_sharing_count': knowledge_sharing_count,
                'tech_breakthrough_count': tech_breakthrough_count,
                'total_logs': len(work_logs),
                'self_evaluation_score': round(self_evaluation_score, 2)
            }
        except Exception as e:
            # 异常处理：返回默认值
            return {
                'positive_count': 0,
                'negative_count': 0,
                'tech_mentions': 0,
                'collaboration_mentions': 0,
                'problem_solving_count': 0,
                'knowledge_sharing_count': 0,
                'tech_breakthrough_count': 0,
                'total_logs': 0,
                'self_evaluation_score': 75.0,
                'error': str(e)
            }

    # ==================== 项目执行数据采集 ====================

    def collect_task_completion_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集任务完成情况数据（增强版：包含异常处理）"""
        try:
            tasks = self.db.query(Task).join(
                ProjectMember, Task.project_id == ProjectMember.project_id
            ).filter(
                ProjectMember.user_id == engineer_id,
                Task.owner_id == engineer_id,
                Task.created_at.between(start_date, end_date)
            ).all()

            if not tasks:
                return {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'on_time_tasks': 0,
                    'completion_rate': 0.0,
                    'on_time_rate': 0.0
                }

            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == 'COMPLETED')
            on_time_tasks = sum(
                1 for t in tasks
                if t.status == 'COMPLETED' and t.actual_end_date
                and t.due_date and t.actual_end_date <= t.due_date
            )

            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
            on_time_rate = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0.0

            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'on_time_tasks': on_time_tasks,
                'completion_rate': round(completion_rate, 2),
                'on_time_rate': round(on_time_rate, 2)
            }
        except Exception as e:
            # 异常时返回默认值
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'on_time_tasks': 0,
                'completion_rate': 0.0,
                'on_time_rate': 0.0,
                'error': str(e)
            }

    def collect_project_participation_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集项目参与情况数据（增强版：包含异常处理）"""
        try:
            projects = self.db.query(Project).join(
                ProjectMember, Project.id == ProjectMember.project_id
            ).filter(
                ProjectMember.user_id == engineer_id,
                Project.created_at.between(start_date, end_date)
            ).all()

            # 获取项目难度和工作量数据
            project_evaluations = {}
            for project in projects:
                try:
                    evaluation = self.db.query(ProjectEvaluation).filter(
                        ProjectEvaluation.project_id == project.id,
                        ProjectEvaluation.status == 'CONFIRMED'
                    ).first()
                    if evaluation:
                        project_evaluations[project.id] = {
                            'difficulty_score': float(evaluation.difficulty_score) if evaluation.difficulty_score else None,
                            'workload_score': float(evaluation.workload_score) if evaluation.workload_score else None
                        }
                except Exception:
                    continue

            return {
                'total_projects': len(projects),
                'project_ids': [p.id for p in projects],
                'project_evaluations': project_evaluations,
                'evaluated_projects': len(project_evaluations)
            }
        except Exception as e:
            return {
                'total_projects': 0,
                'project_ids': [],
                'project_evaluations': {},
                'evaluated_projects': 0,
                'error': str(e)
            }

    # ==================== ECN数据采集 ====================

    def collect_ecn_responsibility_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集ECN责任数据（增强版：包含异常处理）"""
        try:
            # 获取工程师参与的项目
            project_ids = [
                pm.project_id for pm in self.db.query(ProjectMember.project_id).filter(
                    ProjectMember.user_id == engineer_id
                ).all()
            ]

            if not project_ids:
                return {
                    'total_ecn': 0,
                    'responsible_ecn': 0,
                    'ecn_responsibility_rate': 0.0
                }

            # 统计总ECN数
            total_ecn = self.db.query(Ecn).filter(
                Ecn.project_id.in_(project_ids),
                Ecn.created_at.between(start_date, end_date)
            ).count()

            # 统计因设计问题产生的ECN（通过ECN类型判断）
            responsible_ecn = self.db.query(Ecn).filter(
                Ecn.project_id.in_(project_ids),
                Ecn.created_at.between(start_date, end_date),
                Ecn.ecn_type.in_(['DESIGN_CHANGE', 'MECHANICAL_SCHEME', 'ELECTRICAL_SCHEME'])
            ).count()

            ecn_rate = (responsible_ecn / len(project_ids) * 100) if project_ids else 0.0

            return {
                'total_ecn': total_ecn,
                'responsible_ecn': responsible_ecn,
                'ecn_responsibility_rate': round(ecn_rate, 2)
            }
        except Exception as e:
            return {
                'total_ecn': 0,
                'responsible_ecn': 0,
                'ecn_responsibility_rate': 0.0,
                'error': str(e)
            }

    # ==================== BOM数据采集 ====================

    def collect_bom_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集BOM相关数据（增强版：包含异常处理）"""
        try:
            # 获取工程师参与的项目
            project_ids = [
                pm.project_id for pm in self.db.query(ProjectMember.project_id).filter(
                    ProjectMember.user_id == engineer_id
                ).all()
            ]

            if not project_ids:
                return {
                    'total_bom': 0,
                    'on_time_bom': 0,
                    'bom_timeliness_rate': 0.0,
                    'standard_part_rate': 0.0,
                    'reuse_rate': 0.0
                }

            # 统计BOM提交情况
            bom_headers = self.db.query(BomHeader).filter(
                BomHeader.project_id.in_(project_ids),
                BomHeader.created_at.between(start_date, end_date)
            ).all()

            total_bom = len(bom_headers)
            on_time_bom = sum(
                1 for bom in bom_headers
                if bom.due_date and bom.submitted_at
                and bom.submitted_at <= bom.due_date
            )

            bom_timeliness_rate = (on_time_bom / total_bom * 100) if total_bom > 0 else 0.0

            # 统计标准件使用率
            try:
                bom_items = self.db.query(BomItem).join(
                    BomHeader, BomItem.bom_id == BomHeader.id
                ).filter(
                    BomHeader.project_id.in_(project_ids),
                    BomHeader.created_at.between(start_date, end_date)
                ).all()

                if bom_items:
                    standard_items = sum(1 for item in bom_items if getattr(item, 'is_standard', False))
                    standard_part_rate = (standard_items / len(bom_items) * 100)
                else:
                    standard_part_rate = 0.0
            except Exception:
                standard_part_rate = 0.0

            return {
                'total_bom': total_bom,
                'on_time_bom': on_time_bom,
                'bom_timeliness_rate': round(bom_timeliness_rate, 2),
                'standard_part_rate': round(standard_part_rate, 2),
                'reuse_rate': 0.0  # 需要从设计复用记录中统计
            }
        except Exception as e:
            return {
                'total_bom': 0,
                'on_time_bom': 0,
                'bom_timeliness_rate': 0.0,
                'standard_part_rate': 0.0,
                'reuse_rate': 0.0,
                'error': str(e)
            }

    # ==================== 设计评审数据采集 ====================

    def collect_design_review_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集设计评审数据（机械工程师，增强版：包含异常处理）"""
        try:
            reviews = self.db.query(DesignReview).filter(
                DesignReview.designer_id == engineer_id,
                DesignReview.review_date.between(start_date, end_date)
            ).all()

            if not reviews:
                return {
                    'total_reviews': 0,
                    'first_pass_reviews': 0,
                    'first_pass_rate': 0.0
                }

            total_reviews = len(reviews)
            first_pass_reviews = sum(1 for r in reviews if r.is_first_pass)
            first_pass_rate = (first_pass_reviews / total_reviews * 100) if total_reviews > 0 else 0.0

            return {
                'total_reviews': total_reviews,
                'first_pass_reviews': first_pass_reviews,
                'first_pass_rate': round(first_pass_rate, 2)
            }
        except Exception as e:
            return {
                'total_reviews': 0,
                'first_pass_reviews': 0,
                'first_pass_rate': 0.0,
                'error': str(e)
            }

    # ==================== 调试问题数据采集 ====================

    def collect_debug_issue_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集调试问题数据（增强版：包含异常处理）"""
        try:
            # 机械调试问题
            mechanical_issues = self.db.query(MechanicalDebugIssue).filter(
                MechanicalDebugIssue.responsible_id == engineer_id,
                MechanicalDebugIssue.found_date.between(start_date, end_date)
            ).all()

            # 测试Bug记录
            test_bugs = self.db.query(TestBugRecord).filter(
                TestBugRecord.assignee_id == engineer_id,
                TestBugRecord.found_time.between(start_date, end_date)
            ).all()

            # 计算平均修复时长
            resolved_bugs = [b for b in test_bugs if b.status in ('resolved', 'closed')]
            fix_times = [float(b.fix_duration_hours) for b in resolved_bugs if b.fix_duration_hours]
            avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 0.0

            return {
                'mechanical_issues': len(mechanical_issues),
                'test_bugs': len(test_bugs),
                'resolved_bugs': len(resolved_bugs),
                'avg_fix_time': round(avg_fix_time, 2)
            }
        except Exception as e:
            return {
                'mechanical_issues': 0,
                'test_bugs': 0,
                'resolved_bugs': 0,
                'avg_fix_time': 0.0,
                'error': str(e)
            }

    # ==================== 知识贡献数据采集 ====================

    def collect_knowledge_contribution_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """采集知识贡献数据（增强版：包含异常处理）"""
        try:
            contributions = self.db.query(KnowledgeContribution).filter(
                KnowledgeContribution.contributor_id == engineer_id,
                KnowledgeContribution.status == 'approved',
                KnowledgeContribution.created_at.between(start_date, end_date)
            ).all()

            # 统计被引用次数
            total_reuse_count = sum(
                c.reuse_count or 0 for c in contributions
            )

            # 代码模块贡献
            code_modules = self.db.query(CodeModule).filter(
                CodeModule.contributor_id == engineer_id,
                CodeModule.created_at.between(start_date, end_date)
            ).count()

            # PLC模块贡献
            plc_modules = self.db.query(PlcModuleLibrary).filter(
                PlcModuleLibrary.contributor_id == engineer_id,
                PlcModuleLibrary.created_at.between(start_date, end_date)
            ).count()

            return {
                'total_contributions': len(contributions),
                'document_count': sum(1 for c in contributions if c.contribution_type == 'document'),
                'template_count': sum(1 for c in contributions if c.contribution_type == 'template'),
                'module_count': sum(1 for c in contributions if c.contribution_type == 'module'),
                'total_reuse_count': total_reuse_count,
                'code_modules': code_modules,
                'plc_modules': plc_modules
            }
        except Exception as e:
            return {
                'total_contributions': 0,
                'document_count': 0,
                'template_count': 0,
                'module_count': 0,
                'total_reuse_count': 0,
                'code_modules': 0,
                'plc_modules': 0,
                'error': str(e)
            }

    # ==================== 综合数据采集 ====================

    def collect_all_data(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        采集所有绩效数据（增强版：包含统计和监控信息）

        Returns:
            包含所有维度数据和采集统计的字典
        """
        collection_stats = {
            'start_time': datetime.now().isoformat(),
            'success_count': 0,
            'failure_count': 0,
            'missing_data_sources': [],
            'errors': []
        }
        
        data = {}
        
        # 采集各个数据源
        data_sources = {
            'self_evaluation': lambda: self.extract_self_evaluation_from_work_logs(
                engineer_id, start_date, end_date
            ),
            'task_completion': lambda: self.collect_task_completion_data(
                engineer_id, start_date, end_date
            ),
            'project_participation': lambda: self.collect_project_participation_data(
                engineer_id, start_date, end_date
            ),
            'ecn_responsibility': lambda: self.collect_ecn_responsibility_data(
                engineer_id, start_date, end_date
            ),
            'bom_data': lambda: self.collect_bom_data(
                engineer_id, start_date, end_date
            ),
            'design_review': lambda: self.collect_design_review_data(
                engineer_id, start_date, end_date
            ),
            'debug_issue': lambda: self.collect_debug_issue_data(
                engineer_id, start_date, end_date
            ),
            'knowledge_contribution': lambda: self.collect_knowledge_contribution_data(
                engineer_id, start_date, end_date
            )
        }
        
        for source_name, collect_func in data_sources.items():
            try:
                result = collect_func()
                data[source_name] = result
                collection_stats['success_count'] += 1
                
                # 检查数据是否为空或缺失
                if not result or (isinstance(result, dict) and not any(result.values())):
                    collection_stats['missing_data_sources'].append(source_name)
            except Exception as e:
                collection_stats['failure_count'] += 1
                collection_stats['errors'].append({
                    'source': source_name,
                    'error': str(e)
                })
                # 提供默认值
                data[source_name] = {}
        
        collection_stats['end_time'] = datetime.now().isoformat()
        collection_stats['total_sources'] = len(data_sources)
        collection_stats['success_rate'] = round(
            (collection_stats['success_count'] / len(data_sources) * 100), 2
        ) if data_sources else 0.0
        
        return {
            'data': data,
            'statistics': collection_stats,
            'engineer_id': engineer_id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

    def generate_collection_report(
        self,
        engineer_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        生成数据采集报告

        Returns:
            包含采集结果、统计信息、缺失数据分析和建议的报告
        """
        collection_result = self.collect_all_data(engineer_id, start_date, end_date)
        stats = collection_result.get('statistics', {})
        data = collection_result.get('data', {})
        
        # 分析缺失数据原因
        missing_analysis = []
        suggestions = []
        
        # 检查工作日志
        self_eval = data.get('self_evaluation', {})
        if self_eval.get('total_logs', 0) == 0:
            missing_analysis.append({
                'source': '工作日志',
                'reason': '考核周期内无工作日志记录',
                'impact': '无法提取自我评价数据'
            })
            suggestions.append('建议工程师及时填写工作日志')
        
        # 检查项目参与
        project_data = data.get('project_participation', {})
        if project_data.get('total_projects', 0) == 0:
            missing_analysis.append({
                'source': '项目参与',
                'reason': '考核周期内未参与任何项目',
                'impact': '无法计算项目执行相关指标'
            })
            suggestions.append('检查项目成员分配是否正确')
        
        # 检查任务完成情况
        task_data = data.get('task_completion', {})
        if task_data.get('total_tasks', 0) == 0:
            missing_analysis.append({
                'source': '任务完成',
                'reason': '考核周期内无任务记录',
                'impact': '无法计算任务完成率'
            })
            suggestions.append('检查任务分配和记录是否完整')
        
        # 检查设计评审（针对机械工程师）
        design_review = data.get('design_review', {})
        if design_review.get('total_reviews', 0) == 0:
            missing_analysis.append({
                'source': '设计评审',
                'reason': '考核周期内无设计评审记录',
                'impact': '无法计算设计一次通过率'
            })
            suggestions.append('确保设计评审流程完整执行')
        
        # 计算数据完整性得分
        total_sources = len(data)
        available_sources = sum(1 for d in data.values() if d)
        completeness_score = round((available_sources / total_sources * 100), 2) if total_sources > 0 else 0.0
        
        return {
            'engineer_id': engineer_id,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'collection_statistics': stats,
            'data_completeness': {
                'score': completeness_score,
                'total_sources': total_sources,
                'available_sources': available_sources,
                'missing_sources': total_sources - available_sources
            },
            'missing_data_analysis': missing_analysis,
            'suggestions': suggestions,
            'generated_at': datetime.now().isoformat()
        }
