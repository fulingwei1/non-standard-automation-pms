# -*- coding: utf-8 -*-
"""
任务导入器测试
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import date, timedelta

from app.services.unified_import.task_importer import TaskImporter
from app.models.progress import Task
from app.models.user import User


class TestTaskImporter:
    """任务导入器测试"""

    def test_import_task_data_success(self, db_session, test_user, test_project):
        """测试成功导入任务数据"""
        # 创建负责人用户
        owner = User(
            id=2,
            username="owner",
            email="owner@example.com",
            password_hash="hashed",
            real_name="负责人",
            is_active=True,
        )
        db_session.add(owner)
        db_session.commit()

        df = pd.DataFrame({
            "任务名称*": ["任务A", "任务B"],
            "项目编码*": [test_project.project_code, test_project.project_code],
            "负责人*": ["负责人", "负责人"],
            "阶段": ["S1", "S2"],
            "计划开始日期": [date.today(), date.today() + timedelta(days=1)],
            "计划结束日期": [date.today() + timedelta(days=10), date.today() + timedelta(days=20)],
            "权重(%)": [50, 50],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id, update_existing=False
        )

        assert imported_count == 2
        assert updated_count == 0
        assert len(failed_rows) == 0

    def test_import_task_data_missing_columns(self, db_session, test_user):
        """测试缺少必需列"""
        df = pd.DataFrame({
            "任务名称*": ["任务A"],
            # 缺少 "项目编码*"
        })

        with pytest.raises(Exception) as exc_info:
            TaskImporter.import_task_data(db_session, df, test_user.id)

        assert "缺少必需的列" in str(exc_info.value)

    def test_import_task_data_missing_required_fields(self, db_session, test_user, test_project):
        """测试缺少必填字段"""
        df = pd.DataFrame({
            "任务名称*": [""],  # 空任务名
            "项目编码*": [test_project.project_code],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "必填项" in failed_rows[0]["error"]

    def test_import_task_data_project_not_found(self, db_session, test_user):
        """测试项目不存在"""
        df = pd.DataFrame({
            "任务名称*": ["任务A"],
            "项目编码*": ["NONEXISTENT"],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "未找到项目" in failed_rows[0]["error"]

    def test_import_task_data_duplicate(self, db_session, test_user, test_project):
        """测试重复任务"""
        # 先创建一个任务
        task = Task(
            project_id=test_project.id,
            task_name="已存在任务",
            stage="S1",
            status="TODO",
            progress_percent=0,
        )
        db_session.add(task)
        db_session.commit()

        # 尝试导入相同任务
        df = pd.DataFrame({
            "任务名称*": ["已存在任务"],
            "项目编码*": [test_project.project_code],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id, update_existing=False
        )

        assert imported_count == 0
        assert len(failed_rows) == 1
        assert "已存在" in failed_rows[0]["error"]

    def test_import_task_data_update_existing(self, db_session, test_user, test_project):
        """测试更新已存在的任务"""
        # 先创建一个任务
        task = Task(
            project_id=test_project.id,
            task_name="待更新任务",
            stage="S1",
            status="TODO",
            progress_percent=0,
            weight=Decimal("0.5"),
        )
        db_session.add(task)
        db_session.commit()

        # 更新导入
        df = pd.DataFrame({
            "任务名称*": ["待更新任务"],
            "项目编码*": [test_project.project_code],
            "阶段": ["S2"],
            "权重(%)": [80],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id, update_existing=True
        )

        assert imported_count == 0
        assert updated_count == 1

    def test_import_task_data_with_invalid_date(self, db_session, test_user, test_project):
        """测试无效日期格式"""
        df = pd.DataFrame({
            "任务名称*": ["任务A"],
            "项目编码*": [test_project.project_code],
            "计划开始日期": ["invalid-date"],
            "计划结束日期": ["another-invalid"],
        })

        imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
            db_session, df, test_user.id
        )

        # 无效日期会被忽略，但任务应该创建成功
        assert imported_count == 1
        assert len(failed_rows) == 0