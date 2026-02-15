# -*- coding: utf-8 -*-
"""
工时分析与预测模块单元测试
包含15+测试用例
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.models.timesheet import Timesheet
from app.models.project import Project
from app.models.user import User
from app.services.timesheet_analytics_service import TimesheetAnalyticsService
from app.services.timesheet_forecast_service import TimesheetForecastService

# 测试数据库
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_timesheet_analytics.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_data(db):
    """创建测试数据"""
    # 创建测试用户
    users = []
    for i in range(1, 6):
        user = User(
            id=i,
            username=f"user{i}",
            name=f"用户{i}",
            email=f"user{i}@test.com",
            department_id=i % 2 + 1,
            hashed_password="test"
        )
        db.add(user)
        users.append(user)
    
    # 创建测试项目
    projects = []
    for i in range(1, 4):
        project = Project(
            id=i,
            code=f"PRJ-{i:03d}",
            name=f"测试项目{i}",
            status="ONGOING"
        )
        db.add(project)
        projects.append(project)
    
    db.commit()
    
    # 创建测试工时记录
    start_date = date.today() - timedelta(days=30)
    for day_offset in range(30):
        work_date = start_date + timedelta(days=day_offset)
        
        for user_id in range(1, 6):
            for project_id in range(1, 3):
                # 正常工时
                timesheet = Timesheet(
                    user_id=user_id,
                    user_name=f"用户{user_id}",
                    department_id=user_id % 2 + 1,
                    department_name=f"部门{user_id % 2 + 1}",
                    project_id=project_id,
                    project_name=f"测试项目{project_id}",
                    work_date=work_date,
                    hours=Decimal('8.0'),
                    overtime_type='NORMAL',
                    status='APPROVED',
                    work_content='测试工作内容'
                )
                db.add(timesheet)
                
                # 部分加班
                if day_offset % 5 == 0 and user_id % 2 == 0:
                    overtime = Timesheet(
                        user_id=user_id,
                        user_name=f"用户{user_id}",
                        department_id=user_id % 2 + 1,
                        department_name=f"部门{user_id % 2 + 1}",
                        project_id=project_id,
                        project_name=f"测试项目{project_id}",
                        work_date=work_date,
                        hours=Decimal('2.0'),
                        overtime_type='OVERTIME',
                        status='APPROVED',
                        work_content='加班工作'
                    )
                    db.add(overtime)
    
    db.commit()
    
    return {
        'users': users,
        'projects': projects,
        'start_date': start_date,
        'end_date': date.today()
    }


# ==================== 分析功能测试（6个） ====================

def test_01_trend_analysis_monthly(db, test_data):
    """测试1：月度工时趋势分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_trend(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    assert result is not None
    assert result.period_type == 'MONTHLY'
    assert result.total_hours > 0
    assert result.trend in ['INCREASING', 'DECREASING', 'STABLE']
    assert result.chart_data is not None
    assert len(result.chart_data.labels) > 0


def test_02_trend_analysis_weekly(db, test_data):
    """测试2：周度工时趋势分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_trend(
        period_type='WEEKLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date'],
        user_ids=[1, 2]
    )
    
    assert result is not None
    assert result.period_type == 'WEEKLY'
    assert result.average_hours > 0


def test_03_workload_analysis(db, test_data):
    """测试3：人员负荷热力图分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_workload(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    assert result is not None
    assert result.heatmap_data is not None
    assert len(result.heatmap_data.rows) > 0
    assert len(result.heatmap_data.columns) > 0
    assert result.statistics['total_users'] > 0
    assert isinstance(result.overload_users, list)


def test_04_efficiency_comparison(db, test_data):
    """测试4：工时效率对比分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_efficiency(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date'],
        project_ids=[1, 2]
    )
    
    assert result is not None
    assert result.actual_hours > 0
    assert result.planned_hours > 0
    assert result.efficiency_rate > 0
    assert len(result.insights) > 0
    assert result.chart_data is not None


def test_05_overtime_statistics(db, test_data):
    """测试5：加班统计分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_overtime(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    assert result is not None
    assert result.total_overtime_hours >= 0
    assert result.overtime_rate >= 0
    assert result.avg_overtime_per_person >= 0
    assert isinstance(result.top_overtime_users, list)
    assert result.overtime_trend is not None


def test_06_department_comparison(db, test_data):
    """测试6：部门工时对比分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_department_comparison(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    assert result is not None
    assert len(result.departments) > 0
    assert len(result.rankings) > 0
    assert result.chart_data is not None
    # 验证部门数据结构
    dept = result.departments[0]
    assert 'department_name' in dept
    assert 'total_hours' in dept
    assert 'user_count' in dept


def test_07_project_distribution(db, test_data):
    """测试7：项目工时分布分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_project_distribution(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    assert result is not None
    assert result.total_projects > 0
    assert result.total_hours > 0
    assert result.pie_chart is not None
    assert len(result.pie_chart.labels) > 0
    assert len(result.project_details) > 0
    assert 0 <= result.concentration_index <= 1


# ==================== 预测功能测试（8个） ====================

def test_08_forecast_historical_average(db, test_data):
    """测试8：历史平均法预测项目工时"""
    service = TimesheetForecastService(db)
    
    result = service.forecast_project_hours(
        project_name='新项目A',
        complexity='MEDIUM',
        team_size=5,
        duration_days=30,
        forecast_method='HISTORICAL_AVERAGE'
    )
    
    assert result is not None
    assert result.forecast_method == 'HISTORICAL_AVERAGE'
    assert result.predicted_hours > 0
    assert result.predicted_hours_min < result.predicted_hours
    assert result.predicted_hours_max > result.predicted_hours
    assert result.confidence_level > 0
    assert isinstance(result.recommendations, list)


def test_09_forecast_linear_regression(db, test_data):
    """测试9：线性回归预测项目工时"""
    service = TimesheetForecastService(db)
    
    result = service.forecast_project_hours(
        project_name='新项目B',
        complexity='HIGH',
        team_size=8,
        duration_days=45,
        forecast_method='LINEAR_REGRESSION'
    )
    
    assert result is not None
    assert result.forecast_method == 'LINEAR_REGRESSION'
    assert result.predicted_hours > 0
    assert result.algorithm_params is not None
    assert 'method' in result.algorithm_params


def test_10_forecast_trend(db, test_data):
    """测试10：趋势预测法预测项目工时"""
    service = TimesheetForecastService(db)
    
    result = service.forecast_project_hours(
        project_name='新项目C',
        complexity='LOW',
        team_size=3,
        duration_days=20,
        forecast_method='TREND_FORECAST'
    )
    
    assert result is not None
    assert result.forecast_method == 'TREND_FORECAST'
    assert result.predicted_hours > 0


def test_11_forecast_completion(db, test_data):
    """测试11：项目完工时间预测"""
    service = TimesheetForecastService(db)
    
    result = service.forecast_completion(
        project_id=1,
        forecast_method='TREND_FORECAST'
    )
    
    assert result is not None
    assert result.project_id == 1
    assert result.current_consumed_hours > 0
    assert result.predicted_hours >= result.current_consumed_hours
    assert result.remaining_hours >= 0
    assert result.predicted_completion_date is not None
    assert result.predicted_days_remaining >= 0
    assert result.forecast_curve is not None
    assert isinstance(result.risk_factors, list)


def test_12_workload_alert_high(db, test_data):
    """测试12：人员高负荷预警"""
    service = TimesheetForecastService(db)
    
    alerts = service.forecast_workload_alert(
        user_ids=[2, 4],
        forecast_days=30
    )
    
    assert isinstance(alerts, list)
    # 即使没有预警，也应该返回列表
    if len(alerts) > 0:
        alert = alerts[0]
        assert alert.user_id is not None
        assert alert.workload_saturation >= 0
        assert alert.alert_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert isinstance(alert.recommendations, list)


def test_13_workload_alert_filter(db, test_data):
    """测试13：按级别过滤负荷预警"""
    service = TimesheetForecastService(db)
    
    alerts = service.forecast_workload_alert(
        alert_level='CRITICAL',
        forecast_days=30
    )
    
    assert isinstance(alerts, list)
    # 验证所有预警都是CRITICAL级别
    for alert in alerts:
        assert alert.alert_level == 'CRITICAL'


def test_14_gap_analysis(db, test_data):
    """测试14：工时缺口分析"""
    service = TimesheetForecastService(db)
    
    result = service.analyze_gap(
        period_type='MONTHLY',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30)
    )
    
    assert result is not None
    assert result.required_hours >= 0
    assert result.available_hours >= 0
    assert result.gap_hours is not None
    assert isinstance(result.departments, list)
    assert isinstance(result.projects, list)
    assert isinstance(result.recommendations, list)
    assert result.chart_data is not None


def test_15_gap_analysis_with_filters(db, test_data):
    """测试15：按部门和项目的缺口分析"""
    service = TimesheetForecastService(db)
    
    result = service.analyze_gap(
        period_type='MONTHLY',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        department_ids=[1],
        project_ids=[1, 2]
    )
    
    assert result is not None
    assert result.gap_rate is not None


# ==================== 边界情况测试（3个） ====================

def test_16_empty_date_range(db):
    """测试16：空日期范围"""
    service = TimesheetAnalyticsService(db)
    
    # 未来日期，没有数据
    future_start = date.today() + timedelta(days=100)
    future_end = date.today() + timedelta(days=130)
    
    result = service.analyze_trend(
        period_type='MONTHLY',
        start_date=future_start,
        end_date=future_end
    )
    
    assert result is not None
    assert result.total_hours == 0


def test_17_single_user_analysis(db, test_data):
    """测试17：单用户分析"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_workload(
        period_type='MONTHLY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date'],
        user_ids=[1]
    )
    
    assert result is not None
    assert result.statistics['total_users'] >= 1


def test_18_forecast_with_invalid_method(db):
    """测试18：无效的预测方法"""
    service = TimesheetForecastService(db)
    
    with pytest.raises(ValueError):
        service.forecast_project_hours(
            project_name='测试项目',
            complexity='MEDIUM',
            team_size=5,
            duration_days=30,
            forecast_method='INVALID_METHOD'
        )


# ==================== 数据完整性测试（2个） ====================

def test_19_chart_data_structure(db, test_data):
    """测试19：图表数据结构完整性"""
    service = TimesheetAnalyticsService(db)
    
    result = service.analyze_trend(
        period_type='DAILY',
        start_date=test_data['start_date'],
        end_date=test_data['end_date']
    )
    
    # 验证图表数据结构
    assert result.chart_data is not None
    assert hasattr(result.chart_data, 'labels')
    assert hasattr(result.chart_data, 'datasets')
    assert len(result.chart_data.datasets) > 0
    
    # 验证数据集结构
    dataset = result.chart_data.datasets[0]
    assert 'label' in dataset
    assert 'data' in dataset
    assert isinstance(dataset['data'], list)


def test_20_forecast_confidence_range(db, test_data):
    """测试20：预测置信度范围验证"""
    service = TimesheetForecastService(db)
    
    result = service.forecast_project_hours(
        project_name='测试项目',
        complexity='MEDIUM',
        team_size=5,
        duration_days=30,
        forecast_method='HISTORICAL_AVERAGE'
    )
    
    # 验证置信度在合理范围内
    assert 0 <= result.confidence_level <= 100
    
    # 验证预测范围合理
    assert result.predicted_hours_min <= result.predicted_hours
    assert result.predicted_hours <= result.predicted_hours_max


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
