# -*- coding: utf-8 -*-
"""
人员智能匹配服务单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的 mock 策略
2. 只 mock 外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.staff_matching.matching import MatchingEngine
from app.services.staff_matching.base import StaffMatchingBase


class TestStaffMatchingBase(unittest.TestCase):
    """测试基础配置类"""

    def test_dimension_weights_sum(self):
        """测试维度权重之和为1"""
        total = sum(StaffMatchingBase.DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_priority_thresholds_order(self):
        """测试优先级阈值顺序正确"""
        thresholds = StaffMatchingBase.PRIORITY_THRESHOLDS
        self.assertGreater(thresholds['P1'], thresholds['P2'])
        self.assertGreater(thresholds['P2'], thresholds['P3'])
        self.assertGreater(thresholds['P3'], thresholds['P4'])
        self.assertGreater(thresholds['P4'], thresholds['P5'])

    def test_get_priority_threshold_valid(self):
        """测试获取有效优先级阈值"""
        self.assertEqual(StaffMatchingBase.get_priority_threshold('P1'), 85)
        self.assertEqual(StaffMatchingBase.get_priority_threshold('P2'), 75)
        self.assertEqual(StaffMatchingBase.get_priority_threshold('P3'), 65)

    def test_get_priority_threshold_invalid(self):
        """测试无效优先级返回默认值"""
        self.assertEqual(StaffMatchingBase.get_priority_threshold('INVALID'), 65)
        self.assertEqual(StaffMatchingBase.get_priority_threshold(None), 65)

    def test_classify_recommendation_strong(self):
        """测试强烈推荐分类"""
        result = StaffMatchingBase.classify_recommendation(85.0, 65)
        self.assertEqual(result, 'STRONG')

    def test_classify_recommendation_recommended(self):
        """测试推荐分类"""
        result = StaffMatchingBase.classify_recommendation(70.0, 65)
        self.assertEqual(result, 'RECOMMENDED')

    def test_classify_recommendation_acceptable(self):
        """测试可接受分类"""
        result = StaffMatchingBase.classify_recommendation(60.0, 65)
        self.assertEqual(result, 'ACCEPTABLE')

    def test_classify_recommendation_weak(self):
        """测试弱推荐分类"""
        result = StaffMatchingBase.classify_recommendation(50.0, 65)
        self.assertEqual(result, 'WEAK')


class TestMatchingEngine(unittest.TestCase):
    """测试匹配引擎核心逻辑"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.engine = MatchingEngine()

    def _create_mock_staffing_need(self, need_id=1, project_id=100, priority='P2'):
        """创建模拟人员需求对象"""
        need = Mock()
        need.id = need_id
        need.project_id = project_id
        need.priority = priority
        need.role_code = 'ROLE001'
        need.role_name = 'Python开发工程师'
        need.allocation_pct = Decimal('50.0')
        need.required_skills = [
            {'tag_id': 1, 'tag_name': 'Python', 'min_score': 4},
            {'tag_id': 2, 'tag_name': 'Django', 'min_score': 3}
        ]
        need.preferred_skills = [
            {'tag_id': 3, 'tag_name': 'PostgreSQL', 'min_score': 3}
        ]
        need.required_domains = [
            {'tag_id': 10, 'tag_name': '电商领域', 'min_score': 3}
        ]
        need.required_attitudes = [
            {'tag_id': 20, 'tag_name': '责任心', 'min_score': 4}
        ]
        need.status = 'PENDING'
        return need

    def _create_mock_employee(self, emp_id=1, name='张三', code='EMP001'):
        """创建模拟员工对象"""
        employee = Mock()
        employee.id = emp_id
        employee.name = name
        employee.employee_code = code
        employee.department = '研发部'
        employee.is_active = True
        return employee

    def _create_mock_profile(self, employee_id=1, workload=30.0):
        """创建模拟员工档案"""
        profile = Mock()
        profile.id = 1
        profile.employee_id = employee_id
        profile.current_workload_pct = Decimal(str(workload))
        profile.available_hours = Decimal('120.0')
        profile.attitude_score = Decimal('85.0')
        return profile

    def _create_mock_project(self, project_id=100, name='电商平台'):
        """创建模拟项目"""
        project = Mock()
        project.id = project_id
        project.name = name
        return project

    # ========== match_candidates() 测试 ==========

    def test_match_candidates_success(self):
        """测试成功匹配候选人"""
        # Mock人员需求
        staffing_need = self._create_mock_staffing_need()
        
        # Mock项目
        project = self._create_mock_project()
        
        # Mock员工和档案
        employee = self._create_mock_employee()
        profile = self._create_mock_profile()

        # Mock技能评估数据（用于计算得分）
        skill_eval = Mock()
        skill_eval.employee_id = 1
        skill_eval.tag_id = 1
        skill_eval.score = 4
        skill_eval.is_valid = True
        skill_eval.tag = Mock()
        skill_eval.tag.tag_name = 'Python'
        skill_eval.tag.tag_type = 'SKILL'

        # 创建一个通用的空查询mock，返回空列表
        def create_empty_query():
            q = Mock()
            q.filter.return_value.all.return_value = []
            q.join.return_value.filter.return_value.all.return_value = []
            return q
        
        # Mock数据库查询
        need_query = Mock()
        need_query.filter.return_value.first.return_value = staffing_need
        
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        candidate_query = Mock()
        candidate_query.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = [
            (employee, profile)
        ]
        
        # 技能评估查询
        skill_query = Mock()
        skill_query.join.return_value.filter.return_value.all.return_value = [skill_eval]
        
        # 其他所有查询都返回空列表
        empty_queries = [create_empty_query() for _ in range(10)]

        # 设置query的side_effect，按调用顺序返回不同的mock
        self.db.query.side_effect = [
            need_query,  # 查询人员需求
            project_query,  # 查询项目
            candidate_query,  # 查询候选员工
            skill_query,  # 技能评估
        ] + empty_queries  # 其他所有查询

        # 执行匹配
        result = MatchingEngine.match_candidates(
            db=self.db,
            staffing_need_id=1,
            top_n=5
        )

        # 验证结果结构
        self.assertIn('request_id', result)
        self.assertEqual(result['staffing_need_id'], 1)
        self.assertEqual(result['project_id'], 100)
        self.assertEqual(result['project_name'], '电商平台')
        self.assertEqual(result['role_code'], 'ROLE001')
        self.assertEqual(result['priority'], 'P2')
        
        # 验证候选人列表
        self.assertGreater(len(result['candidates']), 0)
        candidate = result['candidates'][0]
        self.assertEqual(candidate['employee_id'], 1)
        self.assertEqual(candidate['employee_name'], '张三')
        self.assertEqual(candidate['rank'], 1)
        self.assertIn('total_score', candidate)
        self.assertIn('dimension_scores', candidate)
        
        # 验证数据库操作
        self.db.add.assert_called()  # 添加了匹配日志
        self.db.commit.assert_called()  # 提交了事务

    def test_match_candidates_staffing_need_not_found(self):
        """测试人员需求不存在"""
        # Mock查询返回None
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock

        # 应该抛出ValueError
        with self.assertRaises(ValueError) as context:
            MatchingEngine.match_candidates(
                db=self.db,
                staffing_need_id=999
            )
        
        self.assertIn('人员需求不存在', str(context.exception))

    def test_match_candidates_no_candidates(self):
        """测试无候选人情况"""
        staffing_need = self._create_mock_staffing_need()
        project = self._create_mock_project()

        # Mock查询
        need_query = Mock()
        need_query.filter.return_value.first.return_value = staffing_need
        
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        # 无候选员工
        candidate_query = Mock()
        candidate_query.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = []

        self.db.query.side_effect = [
            need_query,
            project_query,
            candidate_query
        ]

        result = MatchingEngine.match_candidates(
            db=self.db,
            staffing_need_id=1
        )

        # 验证返回空候选人列表
        self.assertEqual(len(result['candidates']), 0)
        self.assertEqual(result['total_candidates'], 0)
        self.assertEqual(result['qualified_count'], 0)

    def test_match_candidates_with_top_n(self):
        """测试限制返回候选人数量"""
        staffing_need = self._create_mock_staffing_need()
        project = self._create_mock_project()
        
        # 创建3个候选人
        employees = [
            (self._create_mock_employee(1, '张三', 'EMP001'), self._create_mock_profile(1)),
            (self._create_mock_employee(2, '李四', 'EMP002'), self._create_mock_profile(2)),
            (self._create_mock_employee(3, '王五', 'EMP003'), self._create_mock_profile(3)),
        ]

        need_query = Mock()
        need_query.filter.return_value.first.return_value = staffing_need
        
        project_query = Mock()
        project_query.filter.return_value.first.return_value = project
        
        candidate_query = Mock()
        candidate_query.outerjoin.return_value.filter.return_value.filter.return_value.all.return_value = employees

        # Mock评估数据查询（返回空列表简化）
        empty_query = Mock()
        empty_query.join.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []

        self.db.query.side_effect = [
            need_query,
            project_query,
            candidate_query,
        ] + [empty_query] * 20  # 足够的空查询mock

        result = MatchingEngine.match_candidates(
            db=self.db,
            staffing_need_id=1,
            top_n=2  # 只返回前2名
        )

        # 应该只返回2个候选人
        self.assertEqual(len(result['candidates']), 2)
        # 但总候选人数应该是3
        self.assertEqual(result['total_candidates'], 3)

    # ========== _get_candidate_employees() 测试 ==========

    def test_get_candidate_employees_exclude_overloaded(self):
        """测试排除超负荷员工"""
        staffing_need = self._create_mock_staffing_need()
        staffing_need.allocation_pct = Decimal('50.0')

        # 创建员工：一个负载30%（可用），一个负载80%（超负荷）
        emp1 = self._create_mock_employee(1, '张三')
        prof1 = self._create_mock_profile(1, 30.0)
        
        emp2 = self._create_mock_employee(2, '李四')
        prof2 = self._create_mock_profile(2, 80.0)

        # Mock查询，filter会被调用两次（is_active和workload）
        query_mock = Mock()
        filter1 = Mock()
        filter2 = Mock()
        
        query_mock.outerjoin.return_value.filter.return_value = filter1
        filter1.filter.return_value = filter2
        filter2.all.return_value = [(emp1, prof1)]  # 只返回未超负荷的

        self.db.query.return_value = query_mock

        result = MatchingEngine._get_candidate_employees(
            db=self.db,
            staffing_need=staffing_need,
            include_overloaded=False
        )

        # 应该只返回负载低的员工
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0].id, 1)

    def test_get_candidate_employees_include_overloaded(self):
        """测试包含超负荷员工"""
        staffing_need = self._create_mock_staffing_need()

        emp1 = self._create_mock_employee(1, '张三')
        prof1 = self._create_mock_profile(1, 30.0)
        
        emp2 = self._create_mock_employee(2, '李四')
        prof2 = self._create_mock_profile(2, 80.0)

        query_mock = Mock()
        filter1 = Mock()
        
        query_mock.outerjoin.return_value.filter.return_value = filter1
        filter1.all.return_value = [(emp1, prof1), (emp2, prof2)]

        self.db.query.return_value = query_mock

        result = MatchingEngine._get_candidate_employees(
            db=self.db,
            staffing_need=staffing_need,
            include_overloaded=True
        )

        # 应该返回所有员工
        self.assertEqual(len(result), 2)

    def test_get_candidate_employees_no_profile(self):
        """测试员工无档案的情况"""
        staffing_need = self._create_mock_staffing_need()

        emp = self._create_mock_employee(1, '张三')
        
        query_mock = Mock()
        filter1 = Mock()
        filter2 = Mock()
        
        query_mock.outerjoin.return_value.filter.return_value = filter1
        filter1.filter.return_value = filter2
        filter2.all.return_value = [(emp, None)]  # 无档案

        self.db.query.return_value = query_mock

        result = MatchingEngine._get_candidate_employees(
            db=self.db,
            staffing_need=staffing_need,
            include_overloaded=False
        )

        # 无档案的员工应该被包含（假设可用）
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0][1])

    # ========== _calculate_candidate_scores() 测试 ==========

    def test_calculate_candidate_scores_all_dimensions(self):
        """测试计算所有维度得分"""
        employee = self._create_mock_employee()
        profile = self._create_mock_profile()
        staffing_need = self._create_mock_staffing_need()

        # Mock各种评估数据查询
        empty_query = Mock()
        empty_query.join.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []

        self.db.query.return_value = empty_query

        scores = MatchingEngine._calculate_candidate_scores(
            db=self.db,
            employee=employee,
            profile=profile,
            staffing_need=staffing_need
        )

        # 验证所有维度存在
        self.assertIn('skill', scores)
        self.assertIn('domain', scores)
        self.assertIn('attitude', scores)
        self.assertIn('quality', scores)
        self.assertIn('workload', scores)
        self.assertIn('special', scores)
        self.assertIn('total', scores)
        
        # 验证得分范围
        for key in ['skill', 'domain', 'attitude', 'quality', 'workload', 'special']:
            self.assertGreaterEqual(scores[key], 0)
            self.assertLessEqual(scores[key], 100)
        
        # 验证总分是加权和
        expected_total = (
            scores['skill'] * 0.30 +
            scores['domain'] * 0.15 +
            scores['attitude'] * 0.20 +
            scores['quality'] * 0.15 +
            scores['workload'] * 0.15 +
            scores['special'] * 0.05
        )
        self.assertAlmostEqual(scores['total'], expected_total, places=2)

    def test_calculate_candidate_scores_no_profile(self):
        """测试无档案时的得分计算"""
        employee = self._create_mock_employee()
        staffing_need = self._create_mock_staffing_need()

        empty_query = Mock()
        empty_query.join.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []

        self.db.query.return_value = empty_query

        scores = MatchingEngine._calculate_candidate_scores(
            db=self.db,
            employee=employee,
            profile=None,  # 无档案
            staffing_need=staffing_need
        )

        # 应该仍然能计算得分（使用默认值）
        self.assertIn('total', scores)
        self.assertGreater(scores['total'], 0)

    def test_calculate_candidate_scores_high_workload(self):
        """测试高负载员工得分较低"""
        employee = self._create_mock_employee()
        profile_high = self._create_mock_profile(1, 90.0)  # 90%负载
        profile_low = self._create_mock_profile(1, 20.0)   # 20%负载
        staffing_need = self._create_mock_staffing_need()
        staffing_need.allocation_pct = Decimal('50.0')

        empty_query = Mock()
        empty_query.join.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []

        self.db.query.return_value = empty_query

        scores_high = MatchingEngine._calculate_candidate_scores(
            db=self.db, employee=employee, profile=profile_high, staffing_need=staffing_need
        )
        
        scores_low = MatchingEngine._calculate_candidate_scores(
            db=self.db, employee=employee, profile=profile_low, staffing_need=staffing_need
        )

        # 低负载员工的工作负载分应该更高
        self.assertGreater(scores_low['workload'], scores_high['workload'])


class TestScoreCalculatorIntegration(unittest.TestCase):
    """测试各维度得分计算器的集成"""

    def setUp(self):
        self.db = MagicMock()

    def test_skill_score_with_matched_skills(self):
        """测试技能匹配得分"""
        from app.services.staff_matching.score_calculators import SkillScoreCalculator
        
        # Mock技能评估数据
        eval1 = Mock()
        eval1.employee_id = 1
        eval1.tag_id = 1
        eval1.score = 5  # 满分
        eval1.is_valid = True
        eval1.tag = Mock()
        eval1.tag.tag_name = 'Python'
        
        query_mock = Mock()
        query_mock.join.return_value.filter.return_value.all.return_value = [eval1]
        self.db.query.return_value = query_mock

        profile = Mock()
        required_skills = [
            {'tag_id': 1, 'tag_name': 'Python', 'min_score': 4}
        ]
        preferred_skills = []

        result = SkillScoreCalculator.calculate_skill_score(
            db=self.db,
            employee_id=1,
            profile=profile,
            required_skills=required_skills,
            preferred_skills=preferred_skills
        )

        # 技能完全匹配应该得高分
        self.assertGreater(result['score'], 70)
        self.assertIn('Python', result['matched'])
        self.assertEqual(len(result['missing']), 0)

    def test_skill_score_no_requirements(self):
        """测试无技能要求时的基础分"""
        from app.services.staff_matching.score_calculators import SkillScoreCalculator

        result = SkillScoreCalculator.calculate_skill_score(
            db=self.db,
            employee_id=1,
            profile=None,
            required_skills=[],
            preferred_skills=[]
        )

        # 无要求应该给基础分60
        self.assertEqual(result['score'], 60.0)

    def test_workload_score_fully_available(self):
        """测试完全可用的工作负载分"""
        from app.services.staff_matching.score_calculators import WorkloadScoreCalculator

        profile = Mock()
        profile.current_workload_pct = Decimal('30.0')

        score = WorkloadScoreCalculator.calculate_workload_score(
            profile=profile,
            required_allocation=50.0
        )

        # 完全可用应该得满分
        self.assertEqual(score, 100.0)

    def test_workload_score_overloaded(self):
        """测试超负荷时的工作负载分"""
        from app.services.staff_matching.score_calculators import WorkloadScoreCalculator

        profile = Mock()
        profile.current_workload_pct = Decimal('100.0')

        score = WorkloadScoreCalculator.calculate_workload_score(
            profile=profile,
            required_allocation=50.0
        )

        # 超负荷应该得0分
        self.assertEqual(score, 0.0)

    def test_quality_score_no_performance(self):
        """测试无绩效记录时的质量分"""
        from app.services.staff_matching.score_calculators import QualityScoreCalculator

        query_mock = Mock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        score = QualityScoreCalculator.calculate_quality_score(
            db=self.db,
            employee_id=1
        )

        # 无绩效记录应该给基础分60
        self.assertEqual(score, 60.0)

    def test_quality_score_with_performance(self):
        """测试有绩效记录时的质量分"""
        from app.services.staff_matching.score_calculators import QualityScoreCalculator

        # Mock绩效数据
        perf = Mock()
        perf.employee_id = 1
        perf.contribution_level = 'CORE'
        perf.performance_score = Decimal('90.0')
        perf.quality_score = Decimal('85.0')
        perf.collaboration_score = Decimal('88.0')

        query_mock = Mock()
        query_mock.filter.return_value.all.return_value = [perf]
        self.db.query.return_value = query_mock

        score = QualityScoreCalculator.calculate_quality_score(
            db=self.db,
            employee_id=1
        )

        # 有高绩效应该得高分
        self.assertGreater(score, 80)

    def test_domain_score_no_requirements(self):
        """测试无领域要求时的基础分"""
        from app.services.staff_matching.score_calculators import DomainScoreCalculator

        score = DomainScoreCalculator.calculate_domain_score(
            db=self.db,
            employee_id=1,
            profile=None,
            required_domains=[]
        )

        # 无要求应该给基础分60
        self.assertEqual(score, 60.0)

    def test_attitude_score_from_profile(self):
        """测试从档案获取态度分"""
        from app.services.staff_matching.score_calculators import AttitudeScoreCalculator

        profile = Mock()
        profile.attitude_score = Decimal('85.0')

        empty_query = Mock()
        empty_query.join.return_value.filter.return_value.all.return_value = []
        empty_query.filter.return_value.all.return_value = []
        self.db.query.return_value = empty_query

        score = AttitudeScoreCalculator.calculate_attitude_score(
            db=self.db,
            employee_id=1,
            profile=profile,
            required_attitudes=[]
        )

        # 应该使用档案中的态度分
        self.assertEqual(score, 85.0)

    def test_special_score_no_abilities(self):
        """测试无特殊能力时的基础分"""
        from app.services.staff_matching.score_calculators import SpecialScoreCalculator

        query_mock = Mock()
        query_mock.join.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        score = SpecialScoreCalculator.calculate_special_score(
            db=self.db,
            employee_id=1,
            profile=None
        )

        # 无特殊能力应该给基础分50
        self.assertEqual(score, 50.0)


if __name__ == '__main__':
    unittest.main()
