# -*- coding: utf-8 -*-
"""项目贡献度服务单元测试 (ProjectContributionService)"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock


def _make_db():
    """创建模拟数据库会话"""
    return MagicMock()


def _make_contribution(**kw):
    """创建模拟贡献度记录"""
    c = MagicMock()
    defaults = dict(
        id=1,
        project_id=1,
        user_id=1,
        period="2024-01",
        task_count=10,
        task_hours=80.0,
        actual_hours=85.0,
        deliverable_count=5,
        issue_count=8,
        issue_resolved=6,
        bonus_amount=Decimal("5000"),
        contribution_score=Decimal("15.5"),
        pm_rating=4,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def _make_user(**kw):
    """创建模拟用户"""
    u = MagicMock()
    defaults = dict(
        id=1,
        username="test_user",
        real_name="测试用户",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(u, k, v)
    
    # 模拟 employee 关系
    employee = MagicMock()
    employee.name = defaults.get('real_name', '测试用户')
    u.employee = employee
    
    return u


def _make_task(**kw):
    """创建模拟任务"""
    t = MagicMock()
    defaults = dict(
        id=1,
        project_id=1,
        assignee_id=1,
        status="COMPLETED",
        estimated_hours=8.0,
        actual_hours=9.0,
        created_at=datetime(2024, 1, 15),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


def _make_document(**kw):
    """创建模拟文档"""
    d = MagicMock()
    defaults = dict(
        id=1,
        project_id=1,
        uploaded_by=1,
        created_at=datetime(2024, 1, 20),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(d, k, v)
    return d


def _make_issue(**kw):
    """创建模拟问题"""
    i = MagicMock()
    defaults = dict(
        id=1,
        project_id=1,
        reporter_id=1,
        status="RESOLVED",
        report_date=datetime(2024, 1, 10),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(i, k, v)
    return i


class TestProjectContributionServiceInit:
    """测试服务初始化"""
    
    def test_init_sets_db(self):
        """测试初始化数据库会话"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        assert svc.db is db
    
    def test_init_creates_bonus_service(self):
        """测试初始化奖金服务"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        assert svc.bonus_service is not None


class TestCalculateMemberContribution:
    """测试计算成员贡献度"""
    
    def test_creates_new_contribution_if_not_exists(self):
        """测试创建新的贡献度记录"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        # 模拟不存在贡献记录
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db.query.return_value = query_mock
        
        # 模拟空任务、文档、问题列表
        query_mock.filter.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        # 验证创建了新记录
        db.add.assert_called_once()
        db.commit.assert_called_once()
    
    def test_updates_existing_contribution(self):
        """测试更新现有贡献度记录"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        existing = _make_contribution()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        
        # 第一次调用返回现有记录，后续调用返回空列表
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return existing
            return []
        
        query_mock.filter.return_value.first.side_effect = side_effect
        query_mock.filter.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        # 验证没有调用add（因为已存在）
        db.add.assert_not_called()
        db.commit.assert_called_once()
    
    def test_calculates_task_statistics(self):
        """测试计算任务统计"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(task_count=0)
        tasks = [
            _make_task(status="COMPLETED", estimated_hours=8.0, actual_hours=9.0),
            _make_task(status="COMPLETED", estimated_hours=6.0, actual_hours=7.0),
            _make_task(status="IN_PROGRESS", estimated_hours=4.0, actual_hours=2.0),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        
        call_results = [contribution, tasks, [], []]
        call_index = [0]
        
        def get_next_result():
            result = call_results[call_index[0]]
            call_index[0] += 1
            return result
        
        query_mock.filter.return_value.first.side_effect = lambda: get_next_result()
        query_mock.filter.return_value.all.side_effect = lambda: get_next_result()
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        assert contribution.task_count == 2  # 只有COMPLETED的任务
        assert contribution.task_hours == 18.0  # 8 + 6 + 4
        assert contribution.actual_hours == 18.0  # 9 + 7 + 2
    
    def test_calculates_deliverable_count(self):
        """测试计算交付物数量"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(deliverable_count=0)
        documents = [
            _make_document(),
            _make_document(),
            _make_document(),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        
        call_results = [contribution, [], documents, []]
        call_index = [0]
        
        def get_next_result():
            result = call_results[call_index[0]]
            call_index[0] += 1
            return result
        
        query_mock.filter.return_value.first.side_effect = lambda: get_next_result()
        query_mock.filter.return_value.all.side_effect = lambda: get_next_result()
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        assert contribution.deliverable_count == 3
    
    def test_calculates_issue_statistics(self):
        """测试计算问题统计"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(issue_count=0, issue_resolved=0)
        issues = [
            _make_issue(status="RESOLVED"),
            _make_issue(status="CLOSED"),
            _make_issue(status="OPEN"),
            _make_issue(status="VERIFIED"),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        
        call_results = [contribution, [], [], issues]
        call_index = [0]
        
        def get_next_result():
            result = call_results[call_index[0]]
            call_index[0] += 1
            return result
        
        query_mock.filter.return_value.first.side_effect = lambda: get_next_result()
        query_mock.filter.return_value.all.side_effect = lambda: get_next_result()
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        assert contribution.issue_count == 4
        assert contribution.issue_resolved == 3  # RESOLVED, CLOSED, VERIFIED
    
    def test_calculates_bonus_amount(self):
        """测试计算奖金金额"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(bonus_amount=Decimal("0"))
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = contribution
        query_mock.filter.return_value.all.return_value = []
        
        # 模拟奖金计算结果
        bonus_calc1 = MagicMock()
        bonus_calc1.calculated_amount = Decimal("3000")
        bonus_calc2 = MagicMock()
        bonus_calc2.calculated_amount = Decimal("2000")
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(
            return_value=[bonus_calc1, bonus_calc2]
        )
        
        result = svc.calculate_member_contribution(1, 1, "2024-01")
        
        assert contribution.bonus_amount == Decimal("5000")
    
    def test_handles_december_period_correctly(self):
        """测试正确处理12月周期"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = contribution
        query_mock.filter.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        # 测试12月周期
        result = svc.calculate_member_contribution(1, 1, "2024-12")
        
        # 验证正确处理了日期范围（12月到次年1月）
        db.commit.assert_called_once()


class TestCalculateContributionScore:
    """测试计算贡献度评分"""
    
    def test_score_with_all_metrics(self):
        """测试所有指标都有值时的评分"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        
        contribution = _make_contribution(
            task_count=10,
            actual_hours=50.0,
            deliverable_count=5,
            issue_resolved=8,
            bonus_amount=Decimal("10000")
        )
        
        score = svc._calculate_contribution_score(contribution)
        
        assert score > 0
        assert isinstance(score, Decimal)
    
    def test_score_with_zero_metrics(self):
        """测试所有指标为零时的评分"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        
        contribution = _make_contribution(
            task_count=0,
            actual_hours=0,
            deliverable_count=0,
            issue_resolved=0,
            bonus_amount=Decimal("0")
        )
        
        score = svc._calculate_contribution_score(contribution)
        
        assert score == Decimal("0")
    
    def test_score_task_count_weight(self):
        """测试任务数量权重（30%）"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        
        contribution = _make_contribution(
            task_count=10,
            actual_hours=0,
            deliverable_count=0,
            issue_resolved=0,
            bonus_amount=Decimal("0")
        )
        
        score = svc._calculate_contribution_score(contribution)
        
        # 10 * 0.3 = 3.0
        assert score == Decimal("3.0")
    
    def test_score_deliverable_weight(self):
        """测试交付物数量权重（20%）"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        svc = ProjectContributionService(db)
        
        contribution = _make_contribution(
            task_count=0,
            actual_hours=0,
            deliverable_count=5,
            issue_resolved=0,
            bonus_amount=Decimal("0")
        )
        
        score = svc._calculate_contribution_score(contribution)
        
        # 5 * 0.2 = 1.0
        assert score == Decimal("1.0")


class TestGetProjectContributions:
    """测试获取项目贡献度列表"""
    
    def test_get_all_contributions_without_period(self):
        """测试获取所有周期的贡献度"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contributions = [
            _make_contribution(period="2024-01", contribution_score=Decimal("10")),
            _make_contribution(period="2024-02", contribution_score=Decimal("15")),
            _make_contribution(period="2024-03", contribution_score=Decimal("12")),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        result = svc.get_project_contributions(1)
        
        assert len(result) == 3
    
    def test_get_contributions_with_period_filter(self):
        """测试按周期过滤贡献度"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contributions = [
            _make_contribution(period="2024-01", contribution_score=Decimal("10")),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        result = svc.get_project_contributions(1, period="2024-01")
        
        # 验证filter被调用了两次（project_id + period）
        assert query_mock.filter.call_count >= 2
    
    def test_contributions_ordered_by_score(self):
        """测试贡献度按评分降序排列"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        svc.get_project_contributions(1)
        
        # 验证调用了order_by
        query_mock.order_by.assert_called_once()


class TestGetUserProjectContributions:
    """测试获取用户项目贡献汇总"""
    
    def test_get_user_contributions_without_period(self):
        """测试获取用户所有贡献"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contributions = [
            _make_contribution(user_id=1, project_id=1),
            _make_contribution(user_id=1, project_id=2),
        ]
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        result = svc.get_user_project_contributions(1)
        
        assert len(result) == 2
    
    def test_get_user_contributions_with_start_period(self):
        """测试按开始周期过滤"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        result = svc.get_user_project_contributions(1, start_period="2024-01")
        
        # 验证filter被调用了多次（user_id + start_period）
        assert query_mock.filter.call_count >= 2
    
    def test_get_user_contributions_with_end_period(self):
        """测试按结束周期过滤"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        result = svc.get_user_project_contributions(1, end_period="2024-12")
        
        assert query_mock.filter.call_count >= 2
    
    def test_get_user_contributions_with_period_range(self):
        """测试按周期范围过滤"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        result = svc.get_user_project_contributions(
            1, start_period="2024-01", end_period="2024-12"
        )
        
        # 验证filter被调用了三次（user_id + start + end）
        assert query_mock.filter.call_count >= 3


class TestRateMemberContribution:
    """测试项目经理评分"""
    
    def test_rate_existing_contribution(self):
        """测试对现有贡献度评分"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(
            contribution_score=Decimal("10"),
            pm_rating=None
        )
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = contribution
        
        svc = ProjectContributionService(db)
        result = svc.rate_member_contribution(1, 1, "2024-01", 5, 100)
        
        assert contribution.pm_rating == 5
        assert contribution.contribution_score == Decimal("10.0")  # 更新后的评分
        db.commit.assert_called_once()
    
    def test_rate_creates_contribution_if_not_exists(self):
        """测试评分时创建不存在的贡献度"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None
        query_mock.filter.return_value.all.return_value = []
        
        svc = ProjectContributionService(db)
        svc.bonus_service.get_project_bonus_calculations = MagicMock(return_value=[])
        
        # 需要先创建贡献度
        result = svc.rate_member_contribution(1, 1, "2024-01", 4, 100)
        
        # 验证调用了add（创建新记录）
        db.add.assert_called()
    
    def test_rating_must_be_between_1_and_5(self):
        """测试评分必须在1-5之间"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        svc = ProjectContributionService(db)
        
        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            svc.rate_member_contribution(1, 1, "2024-01", 0, 100)
        
        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            svc.rate_member_contribution(1, 1, "2024-01", 6, 100)
    
    def test_rating_updates_score_with_weight(self):
        """测试评分按权重更新总评分"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(
            contribution_score=Decimal("10"),
            pm_rating=None
        )
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = contribution
        
        svc = ProjectContributionService(db)
        result = svc.rate_member_contribution(1, 1, "2024-01", 5, 100)
        
        # 计算公式：base_score * 0.7 + pm_score * 0.3
        # pm_rating=5 -> pm_score=10 -> 10 * 0.7 + 10 * 0.3 = 10
        expected_score = Decimal("10") * Decimal("0.7") + Decimal("10") * Decimal("0.3")
        assert contribution.contribution_score == expected_score


class TestGenerateContributionReport:
    """测试生成贡献度报告"""
    
    def test_generate_report_without_period(self):
        """测试生成不指定周期的报告"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        user1 = _make_user(id=1, real_name="张三")
        user2 = _make_user(id=2, real_name="李四")
        
        contributions = [
            _make_contribution(
                user_id=1,
                task_count=10,
                actual_hours=80.0,
                bonus_amount=Decimal("5000"),
                contribution_score=Decimal("15"),
            ),
            _make_contribution(
                user_id=2,
                task_count=8,
                actual_hours=60.0,
                bonus_amount=Decimal("4000"),
                contribution_score=Decimal("12"),
            ),
        ]
        contributions[0].user = user1
        contributions[1].user = user2
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1)
        
        assert report['project_id'] == 1
        assert report['total_members'] == 2
        assert report['total_task_count'] == 18
        assert report['total_hours'] == 140.0
        assert report['total_bonus'] == 9000.0
        assert len(report['contributions']) == 2
        assert len(report['top_contributors']) <= 10
    
    def test_generate_report_with_period(self):
        """测试生成指定周期的报告"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        user1 = _make_user(id=1)
        contribution = _make_contribution(user_id=1)
        contribution.user = user1
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [contribution]
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1, period="2024-01")
        
        assert report['period'] == "2024-01"
    
    def test_report_includes_user_names(self):
        """测试报告包含用户名称"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        user1 = _make_user(id=1, real_name="测试用户", username="testuser")
        contribution = _make_contribution(user_id=1)
        contribution.user = user1
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [contribution]
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1)
        
        assert report['contributions'][0]['user_name'] == "测试用户"
    
    def test_report_handles_missing_user(self):
        """测试报告处理缺失用户信息"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        contribution = _make_contribution(user_id=999)
        contribution.user = None
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [contribution]
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1)
        
        assert report['contributions'][0]['user_name'] == "User 999"
    
    def test_report_top_contributors_limited_to_10(self):
        """测试报告top贡献者限制为10人"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        # 创建15个贡献者
        contributions = []
        for i in range(15):
            user = _make_user(id=i+1)
            contrib = _make_contribution(
                user_id=i+1,
                contribution_score=Decimal(str(15-i))
            )
            contrib.user = user
            contributions.append(contrib)
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1)
        
        assert len(report['top_contributors']) == 10
        assert report['top_contributors'][0]['contribution_score'] >= \
               report['top_contributors'][-1]['contribution_score']
    
    def test_report_calculates_totals_correctly(self):
        """测试报告正确计算汇总数据"""
        from app.services.project_contribution_service import ProjectContributionService
        db = _make_db()
        
        user1 = _make_user(id=1)
        contributions = [
            _make_contribution(
                user_id=1,
                task_count=5,
                actual_hours=40.0,
                bonus_amount=Decimal("2000")
            ),
            _make_contribution(
                user_id=1,
                task_count=7,
                actual_hours=50.0,
                bonus_amount=Decimal("3000")
            ),
        ]
        for c in contributions:
            c.user = user1
        
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = contributions
        
        svc = ProjectContributionService(db)
        report = svc.generate_contribution_report(1)
        
        assert report['total_task_count'] == 12
        assert report['total_hours'] == 90.0
        assert report['total_bonus'] == 5000.0
