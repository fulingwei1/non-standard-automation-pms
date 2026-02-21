# -*- coding: utf-8 -*-
"""
工时审批适配器单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.approval_engine.adapters.timesheet import TimesheetApprovalAdapter
from app.models.timesheet import Timesheet
from app.models.approval import ApprovalInstance


class TestTimesheetAdapterCore(unittest.TestCase):
    """测试核心适配器方法"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock()
        self.adapter = TimesheetApprovalAdapter(self.db)
        self.entity_id = 1
        self.instance = MagicMock(spec=ApprovalInstance)

    # ========== get_entity() 测试 ==========

    def test_get_entity_success(self):
        """测试成功获取工时实体"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = self.entity_id
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity(self.entity_id)

        self.assertEqual(result, mock_timesheet)
        self.db.query.assert_called_once_with(Timesheet)

    def test_get_entity_not_found(self):
        """测试获取不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity(self.entity_id)

        self.assertIsNone(result)

    # ========== get_entity_data() 测试 ==========

    def test_get_entity_data_basic(self):
        """测试获取基础工时数据"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-001",
            status="DRAFT",
            user_id=100,
            user_name="张三",
            hours=Decimal("8.0"),
            overtime_type="NORMAL"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证基础字段
        self.assertEqual(result["timesheet_no"], "TS-2024-001")
        self.assertEqual(result["status"], "DRAFT")
        self.assertEqual(result["user_id"], 100)
        self.assertEqual(result["user_name"], "张三")
        self.assertEqual(result["hours"], 8.0)
        self.assertEqual(result["overtime_type"], "NORMAL")
        self.assertFalse(result["is_overtime"])

    def test_get_entity_data_with_project(self):
        """测试获取包含项目信息的工时数据"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-002",
            project_id=10,
            project_code="PRJ-001",
            project_name="测试项目"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证项目信息
        self.assertEqual(result["project_id"], 10)
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "测试项目")

    def test_get_entity_data_with_department(self):
        """测试获取包含部门信息的工时数据"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-003",
            department_id=5,
            department_name="研发部"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证部门信息
        self.assertEqual(result["department_id"], 5)
        self.assertEqual(result["department_name"], "研发部")

    def test_get_entity_data_with_task(self):
        """测试获取包含任务信息的工时数据"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-004",
            task_name="开发功能模块",
            work_content="完成用户认证模块开发"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证任务信息
        self.assertEqual(result["task_name"], "开发功能模块")
        self.assertEqual(result["work_content"], "完成用户认证模块开发")

    def test_get_entity_data_with_work_date(self):
        """测试包含工作日期的数据"""
        work_date = datetime(2024, 1, 15)
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-005",
            work_date=work_date
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期被转换为ISO格式
        self.assertEqual(result["work_date"], work_date.isoformat())

    def test_get_entity_data_work_date_none(self):
        """测试工作日期为None的情况"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-006",
            work_date=None
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证日期为None时返回None
        self.assertIsNone(result["work_date"])

    def test_get_entity_data_overtime_weekday(self):
        """测试工作日加班工时"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-007",
            hours=Decimal("10.0"),
            overtime_type="WEEKDAY"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证加班标记
        self.assertEqual(result["overtime_type"], "WEEKDAY")
        self.assertTrue(result["is_overtime"])

    def test_get_entity_data_overtime_weekend(self):
        """测试周末加班工时"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-008",
            hours=Decimal("8.0"),
            overtime_type="WEEKEND"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证加班标记
        self.assertEqual(result["overtime_type"], "WEEKEND")
        self.assertTrue(result["is_overtime"])

    def test_get_entity_data_overtime_holiday(self):
        """测试节假日加班工时"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-009",
            hours=Decimal("8.0"),
            overtime_type="HOLIDAY"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证加班标记
        self.assertEqual(result["overtime_type"], "HOLIDAY")
        self.assertTrue(result["is_overtime"])

    def test_get_entity_data_hours_none(self):
        """测试工时为None的情况"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-010",
            hours=None
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证hours为None时返回0
        self.assertEqual(result["hours"], 0)

    def test_get_entity_data_hours_decimal(self):
        """测试Decimal类型的工时"""
        mock_timesheet = self._create_mock_timesheet(
            timesheet_no="TS-2024-011",
            hours=Decimal("7.5")
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.adapter.get_entity_data(self.entity_id)

        # 验证Decimal被转换为float
        self.assertEqual(result["hours"], 7.5)
        self.assertIsInstance(result["hours"], float)

    def test_get_entity_data_not_found(self):
        """测试获取不存在工时记录的数据"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.adapter.get_entity_data(self.entity_id)

        # 应返回空字典
        self.assertEqual(result, {})

    # ========== on_submit() 测试 ==========

    def test_on_submit_success(self):
        """测试成功提交审批"""
        mock_timesheet = self._create_mock_timesheet(status="DRAFT")
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        self.adapter.on_submit(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_timesheet.status, "SUBMITTED")
        # 验证submit_time被设置（不验证具体时间，因为是实时生成的）
        self.assertIsNotNone(mock_timesheet.submit_time)
        self.db.flush.assert_called_once()

    def test_on_submit_timesheet_not_found(self):
        """测试提交不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_submit(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_approved() 测试 ==========

    def test_on_approved_success(self):
        """测试成功审批通过"""
        mock_timesheet = self._create_mock_timesheet(status="SUBMITTED")
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        self.adapter.on_approved(self.entity_id, self.instance)

        # 验证状态更改
        self.assertEqual(mock_timesheet.status, "APPROVED")
        # 验证approve_time被设置（不验证具体时间，因为是实时生成的）
        self.assertIsNotNone(mock_timesheet.approve_time)
        self.db.flush.assert_called_once()

    def test_on_approved_timesheet_not_found(self):
        """测试审批通过不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_approved(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_rejected() 测试 ==========

    def test_on_rejected_success(self):
        """测试成功驳回审批"""
        mock_timesheet = self._create_mock_timesheet(status="SUBMITTED")
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 验证状态更改为REJECTED
        self.assertEqual(mock_timesheet.status, "REJECTED")
        self.db.flush.assert_called_once()

    def test_on_rejected_timesheet_not_found(self):
        """测试驳回不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_rejected(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== on_withdrawn() 测试 ==========

    def test_on_withdrawn_success(self):
        """测试成功撤回审批"""
        mock_timesheet = self._create_mock_timesheet(
            status="SUBMITTED",
            submit_time=datetime(2024, 1, 15, 10, 0, 0)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 验证状态恢复为DRAFT，提交时间清空
        self.assertEqual(mock_timesheet.status, "DRAFT")
        self.assertIsNone(mock_timesheet.submit_time)
        self.db.flush.assert_called_once()

    def test_on_withdrawn_timesheet_not_found(self):
        """测试撤回不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        self.adapter.on_withdrawn(self.entity_id, self.instance)

        # 不应该调用flush
        self.db.flush.assert_not_called()

    # ========== get_title() 测试 ==========

    def test_get_title_basic(self):
        """测试生成基础标题"""
        work_date = datetime(2024, 1, 15)
        mock_timesheet = self._create_mock_timesheet(
            user_name="张三",
            work_date=work_date
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, "工时审批 - 张三 2024-01-15")

    def test_get_title_no_work_date(self):
        """测试没有工作日期的标题"""
        mock_timesheet = self._create_mock_timesheet(
            user_name="李四",
            work_date=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        title = self.adapter.get_title(self.entity_id)

        # 日期为空时date_str应该是空字符串
        self.assertEqual(title, "工时审批 - 李四 ")

    def test_get_title_timesheet_not_found(self):
        """测试生成不存在工时记录的标题"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        title = self.adapter.get_title(self.entity_id)

        self.assertEqual(title, f"工时审批 - #{self.entity_id}")

    # ========== get_summary() 测试 ==========

    def test_get_summary_basic(self):
        """测试生成基础摘要"""
        work_date = datetime(2024, 1, 15)
        mock_timesheet = self._create_mock_timesheet(
            user_name="张三",
            work_date=work_date,
            hours=Decimal("8.0"),
            overtime_type="NORMAL"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # 验证摘要包含关键信息
        self.assertIn("员工: 张三", summary)
        self.assertIn("日期: 2024-01-15", summary)
        self.assertIn("工时: 8.0小时", summary)
        # 正常工时不应包含加班信息
        self.assertNotIn("加班", summary)

    def test_get_summary_with_project(self):
        """测试生成包含项目的摘要"""
        mock_timesheet = self._create_mock_timesheet(
            user_name="李四",
            work_date=datetime(2024, 1, 16),
            hours=Decimal("7.5"),
            project_name="测试项目A"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # 验证包含项目信息
        self.assertIn("项目: 测试项目A", summary)

    def test_get_summary_with_overtime(self):
        """测试生成包含加班的摘要"""
        mock_timesheet = self._create_mock_timesheet(
            user_name="王五",
            work_date=datetime(2024, 1, 17),
            hours=Decimal("10.0"),
            overtime_type="WEEKDAY"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # 验证包含加班信息
        self.assertIn("加班: WEEKDAY", summary)

    def test_get_summary_complete_info(self):
        """测试生成包含完整信息的摘要"""
        mock_timesheet = self._create_mock_timesheet(
            user_name="赵六",
            work_date=datetime(2024, 1, 18),
            hours=Decimal("8.0"),
            project_name="项目B",
            overtime_type="WEEKEND"
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # 验证所有信息都存在
        self.assertIn("员工: 赵六", summary)
        self.assertIn("日期: 2024-01-18", summary)
        self.assertIn("工时: 8.0小时", summary)
        self.assertIn("项目: 项目B", summary)
        self.assertIn("加班: WEEKEND", summary)

        # 验证使用 " | " 分隔
        self.assertIn(" | ", summary)

    def test_get_summary_missing_user_name(self):
        """测试缺少用户名的摘要"""
        mock_timesheet = self._create_mock_timesheet(
            user_name=None,
            work_date=datetime(2024, 1, 19),
            hours=Decimal("8.0")
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # 用户名为None时不应包含员工信息
        self.assertNotIn("员工:", summary)

    def test_get_summary_missing_hours(self):
        """测试缺少工时的摘要"""
        mock_timesheet = self._create_mock_timesheet(
            user_name="测试",
            work_date=datetime(2024, 1, 20),
            hours=None
        )

        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        summary = self.adapter.get_summary(self.entity_id)

        # hours为None时返回0，不应包含工时信息（因为get_entity_data返回的hours会是0）
        # 但由于代码检查的是data.get("hours")，0也会被认为是falsy，所以不会添加
        self.assertNotIn("工时:", summary)

    def test_get_summary_not_found(self):
        """测试生成不存在工时记录的摘要"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        summary = self.adapter.get_summary(self.entity_id)

        # 应返回空字符串
        self.assertEqual(summary, "")

    # ========== validate_submit() 测试 ==========

    def test_validate_submit_success_from_draft(self):
        """测试从草稿状态成功验证提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("8.0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_success_from_rejected(self):
        """测试从驳回状态成功验证提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="REJECTED",
            hours=Decimal("7.5"),
            work_date=datetime(2024, 1, 16)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_timesheet_not_found(self):
        """测试验证不存在的工时记录"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "工时记录不存在")

    def test_validate_submit_invalid_status_submitted(self):
        """测试已提交状态不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="SUBMITTED",
            hours=Decimal("8.0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)
        self.assertIn("SUBMITTED", error)

    def test_validate_submit_invalid_status_approved(self):
        """测试已审批状态不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="APPROVED",
            hours=Decimal("8.0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertIn("不允许提交审批", error)

    def test_validate_submit_hours_none(self):
        """测试工时为None不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=None,
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "工时必须大于0")

    def test_validate_submit_hours_zero(self):
        """测试工时为0不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "工时必须大于0")

    def test_validate_submit_hours_negative(self):
        """测试工时为负数不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("-2.0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "工时必须大于0")

    def test_validate_submit_no_work_date(self):
        """测试缺少工作日期不允许提交"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("8.0"),
            work_date=None
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertFalse(valid)
        self.assertEqual(error, "请填写工作日期")

    def test_validate_submit_minimum_valid_hours(self):
        """测试最小有效工时（0.1小时）"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("0.1"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    def test_validate_submit_large_hours(self):
        """测试大工时值（24小时）"""
        mock_timesheet = self._create_mock_timesheet(
            status="DRAFT",
            hours=Decimal("24.0"),
            work_date=datetime(2024, 1, 15)
        )
        self.db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        valid, error = self.adapter.validate_submit(self.entity_id)

        self.assertTrue(valid)
        self.assertEqual(error, "")

    # ========== 辅助方法 ==========

    def _create_mock_timesheet(self, **kwargs):
        """创建模拟工时对象"""
        mock_timesheet = MagicMock(spec=Timesheet)

        # 设置默认值
        defaults = {
            'id': self.entity_id,
            'timesheet_no': 'TS-001',
            'status': 'DRAFT',
            'user_id': 1,
            'user_name': '测试用户',
            'department_id': None,
            'department_name': None,
            'project_id': None,
            'project_code': None,
            'project_name': None,
            'task_name': None,
            'work_date': datetime(2024, 1, 15),
            'hours': Decimal("8.0"),
            'overtime_type': 'NORMAL',
            'work_content': None,
            'submit_time': None,
            'approve_time': None,
        }

        # 合并自定义值
        defaults.update(kwargs)

        # 设置属性
        for key, value in defaults.items():
            setattr(mock_timesheet, key, value)

        return mock_timesheet


class TestAdapterEntityType(unittest.TestCase):
    """测试适配器类属性"""

    def test_entity_type(self):
        """测试entity_type类属性"""
        self.assertEqual(TimesheetApprovalAdapter.entity_type, "TIMESHEET")


if __name__ == '__main__':
    unittest.main()
