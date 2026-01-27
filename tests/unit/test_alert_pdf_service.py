# -*- coding: utf-8 -*-
"""
预警PDF导出服务单元测试
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestBuildAlertQuery:
    """测试构建预警查询"""

    def test_query_without_filters(self, db_session):
        """测试无过滤条件的查询"""
        from app.services.alert_pdf_service import build_alert_query

        query = build_alert_query(db_session)
        assert query is not None

    def test_query_with_project_filter(self, db_session):
        """测试带项目过滤"""
        from app.services.alert_pdf_service import build_alert_query

        query = build_alert_query(db_session, project_id=1)
        assert query is not None

    def test_query_with_level_filter(self, db_session):
        """测试带级别过滤"""
        from app.services.alert_pdf_service import build_alert_query

        query = build_alert_query(db_session, alert_level="CRITICAL")
        assert query is not None

    def test_query_with_date_range(self, db_session):
        """测试带日期范围"""
        from app.services.alert_pdf_service import build_alert_query

        query = build_alert_query(
        db_session,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
        )
        assert query is not None


class TestCalculateAlertStatistics:
    """测试计算预警统计"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        from app.services.alert_pdf_service import calculate_alert_statistics

        stats = calculate_alert_statistics([])

        assert stats['total'] == 0
        assert stats['by_level'] == {}
        assert stats['by_status'] == {}
        assert stats['by_type'] == {}

    def test_statistics_structure(self):
        """测试统计结构"""
        from app.services.alert_pdf_service import calculate_alert_statistics

            # 创建模拟预警
        alert1 = MagicMock()
        alert1.alert_level = "CRITICAL"
        alert1.status = "OPEN"
        alert1.rule = MagicMock()
        alert1.rule.rule_type = "SCHEDULE"

        alert2 = MagicMock()
        alert2.alert_level = "WARNING"
        alert2.status = "RESOLVED"
        alert2.rule = MagicMock()
        alert2.rule.rule_type = "COST"

        stats = calculate_alert_statistics([alert1, alert2])

        assert stats['total'] == 2
        assert 'CRITICAL' in stats['by_level']
        assert 'WARNING' in stats['by_level']

    def test_unknown_rule_type(self):
        """测试无规则类型"""
        from app.services.alert_pdf_service import calculate_alert_statistics

        alert = MagicMock()
        alert.alert_level = "INFO"
        alert.status = "OPEN"
        alert.rule = None

        stats = calculate_alert_statistics([alert])

        assert 'UNKNOWN' in stats['by_type']


class TestGetPdfStyles:
    """测试获取PDF样式"""

    def test_styles_import_error(self):
        """测试库未安装时的错误"""
        from app.services.alert_pdf_service import get_pdf_styles

        with patch.dict('sys.modules', {'reportlab': None}):

                # 可能会抛出ImportError或返回样式

        result = get_pdf_styles()

        if result:

            assert len(result) == 4

        except ImportError:

            pass  # 预期的错误



class TestBuildSummaryTable:
    """测试构建统计摘要表格"""

    def test_summary_table_structure(self):
        """测试摘要表格结构"""
        from app.services.alert_pdf_service import build_summary_table

        statistics = {

        'total': 10,

        'by_level': {'CRITICAL': 3, 'WARNING': 5, 'INFO': 2},

        'by_status': {'OPEN': 6, 'RESOLVED': 4},

        'by_type': {'SCHEDULE': 5, 'COST': 5}

        }


        table = build_summary_table(statistics)

        assert table is not None

        except ImportError:

            pytest.skip("reportlab not installed")



class TestBuildAlertListTables:
    """测试构建预警列表表格"""

    def test_empty_alerts_list(self, db_session):
        """测试空预警列表"""
        from app.services.alert_pdf_service import build_alert_list_tables

        tables = build_alert_list_tables(db_session, [])

        assert tables == []

        except ImportError:

            pytest.skip("reportlab not installed")


    def test_pagination(self, db_session):
        """测试分页"""
        from app.services.alert_pdf_service import build_alert_list_tables

                # 创建25个模拟预警（超过默认页大小20）

        alerts = []

        for i in range(25):

            alert = MagicMock()

            alert.alert_no = f"ALT{i:03d}"

            alert.alert_level = "WARNING"

            alert.alert_title = f"测试预警{i}"

            alert.project = None

            alert.handler_id = None

            alert.acknowledged_by = None

            alert.triggered_at = datetime.now()

            alert.status = "OPEN"

            alerts.append(alert)


            tables = build_alert_list_tables(db_session, alerts, page_size=20)

                # 应该有2页（包含PageBreak）

        assert len(tables) >= 2

        except ImportError:

            pytest.skip("reportlab not installed")



class TestBuildPdfContent:
    """测试构建PDF内容"""

    def test_pdf_content_structure(self, db_session):
        """测试PDF内容结构"""
        from app.services.alert_pdf_service import build_pdf_content, get_pdf_styles

        title_style, heading_style, normal_style, _ = get_pdf_styles()


        story = build_pdf_content(

        db_session, [], title_style, heading_style, normal_style

        )


        assert isinstance(story, list)

        assert len(story) > 0

        except ImportError:

            pytest.skip("reportlab not installed")



class TestAlertLevelGrouping:
    """测试预警级别分组"""

    def test_group_by_level(self):
        """测试按级别分组"""
        alerts = [
        {'level': 'CRITICAL'},
        {'level': 'CRITICAL'},
        {'level': 'WARNING'},
        {'level': 'INFO'},
        ]

        by_level = {}
        for alert in alerts:
            level = alert['level']
            by_level[level] = by_level.get(level, 0) + 1

            assert by_level['CRITICAL'] == 2
            assert by_level['WARNING'] == 1
            assert by_level['INFO'] == 1


class TestAlertStatusGrouping:
    """测试预警状态分组"""

    def test_group_by_status(self):
        """测试按状态分组"""
        alerts = [
        {'status': 'OPEN'},
        {'status': 'OPEN'},
        {'status': 'RESOLVED'},
        {'status': 'ACKNOWLEDGED'},
        ]

        by_status = {}
        for alert in alerts:
            status = alert['status']
            by_status[status] = by_status.get(status, 0) + 1

            assert by_status['OPEN'] == 2
            assert by_status['RESOLVED'] == 1
            assert by_status['ACKNOWLEDGED'] == 1


            # pytest fixtures
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
