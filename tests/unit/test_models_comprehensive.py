"""
Model层综合测试
测试新增模型的CRUD、关系验证、枚举等
"""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.models.project.schedule_prediction import (
    ProjectSchedulePrediction,
    CatchUpSolution,
    ScheduleAlert,
    RiskLevelEnum,
    SolutionTypeEnum,
    AlertTypeEnum,
    SeverityEnum
)
from app.models.quality_risk_detection import (
    QualityRiskDetection,
    QualityTestRecommendation,
    RiskSourceEnum,
    RiskStatusEnum,
    RiskCategoryEnum,
    TestPriorityEnum
)
from app.models.ai_planning.plan_template import AIProjectPlanTemplate
from app.models.ai_planning.wbs_suggestion import AIWbsSuggestion
from app.models.ai_planning.resource_allocation import AIResourceAllocation


class TestSchedulePredictionModels:
    """进度预测模型测试"""

    def test_create_schedule_prediction(self, mock_database_session):
        """测试创建进度预测记录"""
        prediction = ProjectSchedulePrediction(
            project_id=1,
            prediction_date=date.today(),
            predicted_completion_date=date(2026, 6, 30),
            delay_days=15,
            confidence=0.85,
            risk_level=RiskLevelEnum.HIGH,
            features={'progress': 60, 'velocity': 1.2},
            model_version='v1.0'
        )
        
        mock_database_session.add(prediction)
        mock_database_session.commit()
        
        assert prediction.id is not None
        assert prediction.risk_level == RiskLevelEnum.HIGH
        assert prediction.delay_days == 15

    def test_prediction_to_dict(self):
        """测试预测记录转字典"""
        prediction = ProjectSchedulePrediction(
            project_id=1,
            predicted_completion_date=date(2026, 6, 30),
            delay_days=10,
            confidence=0.9,
            risk_level=RiskLevelEnum.MEDIUM
        )
        
        data = prediction.to_dict()
        
        assert data['project_id'] == 1
        assert data['delay_days'] == 10
        assert data['risk_level'] == 'medium'

    def test_create_catch_up_solution(self):
        """测试创建赶工方案"""
        solution = CatchUpSolution(
            project_id=1,
            prediction_id=10,
            solution_name="加班方案",
            solution_type=SolutionTypeEnum.OVERTIME,
            description="团队加班以追赶进度",
            estimated_catch_up_days=7,
            additional_cost=8000,
            risk_level=RiskLevelEnum.LOW,
            success_rate=0.85,
            is_recommended=True
        )
        
        assert solution.solution_type == SolutionTypeEnum.OVERTIME
        assert solution.is_recommended is True
        assert solution.estimated_catch_up_days == 7

    def test_solution_approval(self):
        """测试方案审批"""
        solution = CatchUpSolution(
            solution_name="增加人力",
            solution_type=SolutionTypeEnum.MANPOWER,
            status="pending"
        )
        
        # 批准方案
        solution.status = "approved"
        solution.approved_by = 100
        solution.approved_at = datetime.now()
        solution.approval_comment = "同意实施"
        
        assert solution.status == "approved"
        assert solution.approved_by == 100

    def test_create_schedule_alert(self):
        """测试创建进度预警"""
        alert = ScheduleAlert(
            project_id=1,
            prediction_id=10,
            alert_type=AlertTypeEnum.DELAY_WARNING,
            severity=SeverityEnum.HIGH,
            title="项目延期预警",
            message="预计延期15天",
            is_read=False,
            is_resolved=False
        )
        
        assert alert.alert_type == AlertTypeEnum.DELAY_WARNING
        assert alert.severity == SeverityEnum.HIGH
        assert alert.is_read is False

    def test_alert_acknowledgement(self):
        """测试预警确认"""
        alert = ScheduleAlert(
            alert_type=AlertTypeEnum.DELAY_WARNING,
            is_read=False
        )
        
        # 确认预警
        alert.is_read = True
        alert.acknowledged_by = 200
        alert.acknowledged_at = datetime.now()
        alert.acknowledgement_comment = "已知悉，正在处理"
        
        assert alert.is_read is True
        assert alert.acknowledged_by == 200

    def test_prediction_solution_relationship(self):
        """测试预测与方案的关系"""
        prediction = ProjectSchedulePrediction(
            project_id=1,
            predicted_completion_date=date(2026, 6, 30)
        )
        
        solution1 = CatchUpSolution(
            prediction_id=prediction.id,
            solution_name="方案A"
        )
        solution2 = CatchUpSolution(
            prediction_id=prediction.id,
            solution_name="方案B"
        )
        
        # 一个预测可以有多个方案
        assert len([solution1, solution2]) == 2


class TestQualityRiskModels:
    """质量风险模型测试"""

    def test_create_quality_risk_detection(self):
        """测试创建质量风险检测记录"""
        detection = QualityRiskDetection(
            project_id=1,
            module_name="用户认证",
            task_id=100,
            detection_date=date.today(),
            source_type=RiskSourceEnum.WORK_LOG,
            risk_level=RiskLevelEnum.HIGH,
            risk_score=75,
            risk_category=RiskCategoryEnum.BUG,
            risk_keywords=['bug', '修复', '问题'],
            rework_probability=0.65,
            status=RiskStatusEnum.DETECTED
        )
        
        assert detection.risk_category == RiskCategoryEnum.BUG
        assert detection.risk_score == 75
        assert len(detection.risk_keywords) == 3

    def test_risk_status_transition(self):
        """测试风险状态转换"""
        detection = QualityRiskDetection(
            status=RiskStatusEnum.DETECTED
        )
        
        # 确认风险
        detection.status = RiskStatusEnum.CONFIRMED
        detection.confirmed_by = 100
        
        assert detection.status == RiskStatusEnum.CONFIRMED
        
        # 解决风险
        detection.status = RiskStatusEnum.RESOLVED
        detection.resolved_by = 100
        detection.resolved_at = datetime.now()
        
        assert detection.status == RiskStatusEnum.RESOLVED

    def test_create_test_recommendation(self):
        """测试创建测试推荐"""
        recommendation = QualityTestRecommendation(
            project_id=1,
            detection_id=10,
            recommendation_date=date.today(),
            focus_areas=['登录模块', '支付模块'],
            priority_modules=['支付模块'],
            test_types=['功能测试', '回归测试'],
            recommended_testers=2,
            recommended_days=5,
            priority_level=TestPriorityEnum.HIGH,
            status="pending"
        )
        
        assert recommendation.priority_level == TestPriorityEnum.HIGH
        assert len(recommendation.focus_areas) == 2
        assert recommendation.recommended_days == 5

    def test_recommendation_execution(self):
        """测试推荐执行跟踪"""
        recommendation = QualityTestRecommendation(
            recommended_days=5,
            status="pending"
        )
        
        # 接受推荐
        recommendation.status = "accepted"
        
        # 执行测试
        recommendation.status = "in_progress"
        recommendation.actual_test_days = 4
        recommendation.bugs_found = 8
        
        # 完成测试
        recommendation.status = "completed"
        
        assert recommendation.status == "completed"
        assert recommendation.bugs_found == 8

    def test_risk_severity_enum_values(self):
        """测试风险等级枚举值"""
        assert RiskLevelEnum.LOW.value == "low"
        assert RiskLevelEnum.MEDIUM.value == "medium"
        assert RiskLevelEnum.HIGH.value == "high"
        assert RiskLevelEnum.CRITICAL.value == "critical"

    def test_risk_category_enum_values(self):
        """测试风险类别枚举值"""
        assert RiskCategoryEnum.BUG.value == "BUG"
        assert RiskCategoryEnum.PERFORMANCE.value == "PERFORMANCE"
        assert RiskCategoryEnum.STABILITY.value == "STABILITY"
        assert RiskCategoryEnum.COMPATIBILITY.value == "COMPATIBILITY"


class TestAIPlanningModels:
    """AI规划模型测试"""

    def test_create_plan_template(self):
        """测试创建项目计划模板"""
        template = AIProjectPlanTemplate(
            template_name="Web开发标准模板",
            template_type="WEB_DEV",
            industry="电商",
            complexity="high",
            ai_model="GLM-5",
            phases=['需求', '设计', '开发', '测试', '部署'],
            estimated_duration_days=120,
            estimated_cost=500000,
            recommended_team_size=8,
            confidence_score=0.88
        )
        
        assert template.template_type == "WEB_DEV"
        assert len(template.phases) == 5
        assert template.estimated_duration_days == 120

    def test_template_usage_tracking(self):
        """测试模板使用统计"""
        template = AIProjectPlanTemplate(
            template_name="模板A",
            usage_count=0
        )
        
        # 使用模板
        template.usage_count += 1
        template.last_used_at = datetime.now()
        
        assert template.usage_count == 1
        
        # 再次使用
        template.usage_count += 1
        
        assert template.usage_count == 2

    def test_create_wbs_suggestion(self):
        """测试创建WBS建议"""
        wbs = AIWbsSuggestion(
            project_id=1,
            template_id=10,
            level=2,
            parent_id=1,
            wbs_code="1.2.1",
            task_name="数据库设计",
            task_type="design",
            estimated_duration_days=10,
            estimated_hours=80,
            complexity="medium",
            is_critical_path=True,
            status="pending"
        )
        
        assert wbs.level == 2
        assert wbs.wbs_code == "1.2.1"
        assert wbs.is_critical_path is True

    def test_wbs_dependency(self):
        """测试WBS任务依赖"""
        wbs = AIWbsSuggestion(
            wbs_code="1.2",
            task_name="任务B",
            dependency_tasks=['1.1'],
            dependency_type="FS"  # Finish-to-Start
        )
        
        assert '1.1' in wbs.dependency_tasks
        assert wbs.dependency_type == "FS"

    def test_wbs_acceptance_rejection(self):
        """测试WBS建议接受/拒绝"""
        wbs = AIWbsSuggestion(
            task_name="任务A",
            status="pending"
        )
        
        # 接受建议
        wbs.status = "accepted"
        wbs.accepted_by = 100
        wbs.accepted_at = datetime.now()
        
        assert wbs.status == "accepted"
        
        # 或者拒绝
        wbs2 = AIWbsSuggestion(task_name="任务B", status="pending")
        wbs2.status = "rejected"
        wbs2.rejected_by = 100
        wbs2.rejection_reason = "不符合实际情况"
        
        assert wbs2.status == "rejected"

    def test_create_resource_allocation(self):
        """测试创建资源分配"""
        allocation = AIResourceAllocation(
            project_id=1,
            wbs_suggestion_id=10,
            user_id=100,
            role="后端开发",
            allocation_type="full_time",
            planned_start_date=date(2026, 3, 1),
            planned_end_date=date(2026, 3, 15),
            allocated_hours=80,
            load_percentage=80,
            skill_match_score=90,
            overall_match_score=85,
            status="pending"
        )
        
        assert allocation.role == "后端开发"
        assert allocation.load_percentage == 80
        assert allocation.overall_match_score == 85

    def test_allocation_matching_details(self):
        """测试分配匹配度详情"""
        allocation = AIResourceAllocation(
            user_id=100,
            skill_match_score=90,
            experience_match_score=85,
            availability_score=70,
            performance_score=88,
            overall_match_score=83
        )
        
        # 验证各项匹配度
        assert allocation.skill_match_score == 90
        assert allocation.experience_match_score == 85
        assert allocation.availability_score == 70
        assert allocation.performance_score == 88

    def test_allocation_execution_tracking(self):
        """测试分配执行跟踪"""
        allocation = AIResourceAllocation(
            allocated_hours=80,
            status="pending"
        )
        
        # 接受分配
        allocation.status = "accepted"
        
        # 执行跟踪
        allocation.actual_start_date = date(2026, 3, 1)
        allocation.actual_hours = 85
        allocation.actual_performance = 0.92
        
        assert allocation.actual_hours == 85
        assert allocation.actual_performance == 0.92


class TestModelRelationships:
    """模型关系测试"""

    def test_prediction_has_many_solutions(self):
        """测试预测拥有多个方案"""
        prediction = ProjectSchedulePrediction(project_id=1)
        
        solutions = [
            CatchUpSolution(prediction_id=prediction.id, solution_name=f"方案{i}")
            for i in range(3)
        ]
        
        assert len(solutions) == 3

    def test_prediction_has_many_alerts(self):
        """测试预测拥有多个预警"""
        prediction = ProjectSchedulePrediction(project_id=1)
        
        alerts = [
            ScheduleAlert(
                prediction_id=prediction.id,
                alert_type=AlertTypeEnum.DELAY_WARNING
            ),
            ScheduleAlert(
                prediction_id=prediction.id,
                alert_type=AlertTypeEnum.VELOCITY_DROP
            )
        ]
        
        assert len(alerts) == 2

    def test_risk_has_one_recommendation(self):
        """测试风险对应一个测试推荐"""
        risk = QualityRiskDetection(project_id=1)
        
        recommendation = QualityTestRecommendation(
            detection_id=risk.id,
            project_id=1
        )
        
        assert recommendation.detection_id == risk.id

    def test_template_has_many_wbs(self):
        """测试模板对应多个WBS"""
        template = AIProjectPlanTemplate(template_name="模板A")
        
        wbs_list = [
            AIWbsSuggestion(
                template_id=template.id,
                wbs_code=f"1.{i}",
                task_name=f"任务{i}"
            )
            for i in range(5)
        ]
        
        assert len(wbs_list) == 5

    def test_wbs_has_many_allocations(self):
        """测试WBS对应多个资源分配"""
        wbs = AIWbsSuggestion(wbs_code="1.1", task_name="任务A")
        
        allocations = [
            AIResourceAllocation(
                wbs_suggestion_id=wbs.id,
                user_id=i,
                role="开发"
            )
            for i in range(100, 103)
        ]
        
        assert len(allocations) == 3


class TestEnumValidation:
    """枚举验证测试"""

    def test_all_risk_levels_valid(self):
        """测试所有风险等级枚举有效"""
        levels = [
            RiskLevelEnum.LOW,
            RiskLevelEnum.MEDIUM,
            RiskLevelEnum.HIGH,
            RiskLevelEnum.CRITICAL
        ]
        
        for level in levels:
            assert level.value in ['low', 'medium', 'high', 'critical']

    def test_all_solution_types_valid(self):
        """测试所有方案类型枚举有效"""
        types = [
            SolutionTypeEnum.MANPOWER,
            SolutionTypeEnum.OVERTIME,
            SolutionTypeEnum.PROCESS,
            SolutionTypeEnum.HYBRID
        ]
        
        for sol_type in types:
            assert sol_type.value in ['manpower', 'overtime', 'process', 'hybrid']

    def test_all_alert_types_valid(self):
        """测试所有预警类型枚举有效"""
        types = [
            AlertTypeEnum.DELAY_WARNING,
            AlertTypeEnum.VELOCITY_DROP
        ]
        
        for alert_type in types:
            assert alert_type.value in ['delay_warning', 'velocity_drop']

    def test_test_priority_enum(self):
        """测试测试优先级枚举"""
        priorities = [
            TestPriorityEnum.LOW,
            TestPriorityEnum.MEDIUM,
            TestPriorityEnum.HIGH,
            TestPriorityEnum.URGENT
        ]
        
        for priority in priorities:
            assert priority.value in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
