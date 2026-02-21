# -*- coding: utf-8 -*-
"""
最佳实践服务单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.best_practices.best_practices_service import BestPracticesService
from app.common.pagination import get_pagination_params


class MockRow:
    """模拟数据库行对象"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBestPracticesService(unittest.TestCase):
    """最佳实践服务测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = BestPracticesService(self.mock_db)

    # ========== get_popular_practices() 测试 ==========

    def test_get_popular_practices_success(self):
        """测试获取热门实践（无分类筛选）"""
        # 模拟数据库返回
        mock_rows = [
            MockRow(
                id=1,
                review_id=101,
                project_id=201,
                title="高效代码审查",
                description="提升代码质量",
                context="团队协作",
                implementation="使用工具",
                benefits="减少bug",
                category="代码质量",
                tags="code,review",
                is_reusable=1,
                applicable_project_types="web",
                applicable_stages="开发",
                validation_status="VALIDATED",
                reuse_count=10,
                status="ACTIVE",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 2),
                project_code="PRJ-001",
                project_name="测试项目A",
            ),
            MockRow(
                id=2,
                review_id=102,
                project_id=202,
                title="自动化测试",
                description="提升测试效率",
                context="质量保证",
                implementation="pytest框架",
                benefits="快速反馈",
                category="测试",
                tags="test,automation",
                is_reusable=1,
                applicable_project_types="all",
                applicable_stages="测试",
                validation_status="VALIDATED",
                reuse_count=5,
                status="ACTIVE",
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 4),
                project_code="PRJ-002",
                project_name="测试项目B",
            ),
        ]

        # Mock count查询（总数）
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        # Mock数据查询
        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = mock_rows

        # 配置db.execute按调用顺序返回
        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_popular_practices(pagination)

        # 验证结果
        self.assertEqual(total, 2)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], 1)
        self.assertEqual(items[0]["title"], "高效代码审查")
        self.assertEqual(items[0]["reuse_count"], 10)
        self.assertEqual(items[1]["id"], 2)

        # 验证调用了2次execute（count + data）
        self.assertEqual(self.mock_db.execute.call_count, 2)

    def test_get_popular_practices_with_category(self):
        """测试获取热门实践（带分类筛选）"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_row = MockRow(
            id=1,
            review_id=101,
            project_id=201,
            title="代码规范",
            description="统一代码风格",
            context=None,
            implementation=None,
            benefits=None,
            category="代码质量",
            tags=None,
            is_reusable=1,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="PENDING",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            project_code="PRJ-001",
            project_name="测试项目",
        )

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_popular_practices(pagination, category="代码质量")

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "代码质量")

    def test_get_popular_practices_empty_result(self):
        """测试获取热门实践（空结果）"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = []

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_popular_practices(pagination)

        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_popular_practices_pagination(self):
        """测试分页参数正确传递"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = []

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=3, page_size=20)  # offset=40
        self.service.get_popular_practices(pagination)

        # 检查最后一次execute调用的参数
        last_call_args = self.mock_db.execute.call_args_list[1]
        params = last_call_args[0][1]
        self.assertEqual(params["page_size"], 20)
        self.assertEqual(params["offset"], 40)

    # ========== get_practices() 测试 ==========

    def test_get_practices_no_filters(self):
        """测试获取实践列表（无筛选）"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_row = MockRow(
            id=1,
            review_id=101,
            project_id=201,
            title="测试实践",
            description="描述",
            context=None,
            implementation=None,
            benefits=None,
            category=None,
            tags=None,
            is_reusable=0,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="PENDING",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            project_code="PRJ-001",
            project_name="项目A",
        )

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_practices(pagination)

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], 1)

    def test_get_practices_with_project_id(self):
        """测试按项目ID筛选"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_row = MockRow(
            id=1,
            review_id=101,
            project_id=999,
            title="项目专属实践",
            description="描述",
            context=None,
            implementation=None,
            benefits=None,
            category=None,
            tags=None,
            is_reusable=0,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="PENDING",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            project_code="PRJ-999",
            project_name="特定项目",
        )

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_practices(pagination, project_id=999)

        self.assertEqual(total, 1)
        self.assertEqual(items[0]["project_id"], 999)

    def test_get_practices_with_all_filters(self):
        """测试所有筛选条件组合"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_row = MockRow(
            id=1,
            review_id=101,
            project_id=201,
            title="综合筛选",
            description="包含关键词测试",
            context=None,
            implementation=None,
            benefits=None,
            category="测试",
            tags=None,
            is_reusable=1,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="VALIDATED",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            project_code="PRJ-001",
            project_name="项目A",
        )

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_practices(
            pagination,
            project_id=201,
            category="测试",
            validation_status="VALIDATED",
            search="关键词",
        )

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)

        # 验证参数传递
        last_call_args = self.mock_db.execute.call_args_list[1]
        params = last_call_args[0][1]
        self.assertEqual(params["project_id"], 201)
        self.assertEqual(params["category"], "测试")
        self.assertEqual(params["validation_status"], "VALIDATED")
        self.assertEqual(params["search"], "%关键词%")

    # ========== get_practice_by_id() 测试 ==========

    def test_get_practice_by_id_found(self):
        """测试获取实践详情（存在）"""
        mock_row = MockRow(
            id=123,
            review_id=101,
            project_id=201,
            title="详情测试",
            description="描述内容",
            context="上下文",
            implementation="实施方法",
            benefits="收益说明",
            category="分类",
            tags="tag1,tag2",
            is_reusable=1,
            applicable_project_types="web,mobile",
            applicable_stages="开发,测试",
            validation_status="VALIDATED",
            reuse_count=15,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 2),
            project_code="PRJ-001",
            project_name="测试项目",
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        self.mock_db.execute.return_value = mock_result

        result = self.service.get_practice_by_id(123)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 123)
        self.assertEqual(result["title"], "详情测试")
        self.assertEqual(result["reuse_count"], 15)
        self.assertTrue(result["is_reusable"])

    def test_get_practice_by_id_not_found(self):
        """测试获取实践详情（不存在）"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        self.mock_db.execute.return_value = mock_result

        result = self.service.get_practice_by_id(999)

        self.assertIsNone(result)

    # ========== apply_practice() 测试 ==========

    def test_apply_practice_success(self):
        """测试应用最佳实践（成功）"""
        # Mock实践存在检查
        mock_practice_row = MockRow(id=1, reuse_count=5)
        mock_practice_result = MagicMock()
        mock_practice_result.fetchone.return_value = mock_practice_row

        # Mock项目存在检查
        mock_project_row = MockRow(id=201)
        mock_project_result = MagicMock()
        mock_project_result.fetchone.return_value = mock_project_row

        # Mock更新操作
        mock_update_result = MagicMock()

        self.mock_db.execute.side_effect = [
            mock_practice_result,
            mock_project_result,
            mock_update_result,
        ]

        result = self.service.apply_practice(
            practice_id=1, target_project_id=201, notes="测试应用"
        )

        self.assertTrue(result)
        self.mock_db.commit.assert_called_once()

    def test_apply_practice_not_found(self):
        """测试应用最佳实践（实践不存在）"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        self.mock_db.execute.return_value = mock_result

        with self.assertRaises(ValueError) as context:
            self.service.apply_practice(practice_id=999, target_project_id=201)

        self.assertEqual(str(context.exception), "最佳实践不存在")

    def test_apply_practice_project_not_found(self):
        """测试应用最佳实践（目标项目不存在）"""
        # Mock实践存在
        mock_practice_row = MockRow(id=1, reuse_count=5)
        mock_practice_result = MagicMock()
        mock_practice_result.fetchone.return_value = mock_practice_row

        # Mock项目不存在
        mock_project_result = MagicMock()
        mock_project_result.fetchone.return_value = None

        self.mock_db.execute.side_effect = [mock_practice_result, mock_project_result]

        with self.assertRaises(ValueError) as context:
            self.service.apply_practice(practice_id=1, target_project_id=999)

        self.assertEqual(str(context.exception), "目标项目不存在")

    # ========== create_practice() 测试 ==========

    def test_create_practice_full_fields(self):
        """测试创建最佳实践（完整字段）"""
        mock_result = MagicMock()
        mock_result.lastrowid = 100

        self.mock_db.execute.return_value = mock_result

        result = self.service.create_practice(
            review_id=101,
            project_id=201,
            title="新实践",
            description="描述",
            context="上下文",
            implementation="实施",
            benefits="收益",
            category="分类",
            tags="tag1,tag2",
            is_reusable=True,
            applicable_project_types="web",
            applicable_stages="开发",
        )

        # 验证返回值
        self.assertEqual(result["id"], 100)
        self.assertEqual(result["title"], "新实践")
        self.assertEqual(result["review_id"], 101)
        self.assertEqual(result["project_id"], 201)
        self.assertEqual(result["validation_status"], "PENDING")
        self.assertEqual(result["reuse_count"], 0)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertTrue(result["is_reusable"])

        # 验证提交
        self.mock_db.commit.assert_called_once()

    def test_create_practice_minimal_fields(self):
        """测试创建最佳实践（最小字段）"""
        mock_result = MagicMock()
        mock_result.lastrowid = 200

        self.mock_db.execute.return_value = mock_result

        result = self.service.create_practice(
            review_id=102, project_id=202, title="最小实践", description="简单描述"
        )

        self.assertEqual(result["id"], 200)
        self.assertEqual(result["title"], "最小实践")
        self.assertIsNone(result["context"])
        self.assertIsNone(result["implementation"])
        self.assertIsNone(result["benefits"])
        self.assertIsNone(result["category"])
        self.assertIsNone(result["tags"])
        self.assertTrue(result["is_reusable"])  # 默认值

    def test_create_practice_not_reusable(self):
        """测试创建不可复用的最佳实践"""
        mock_result = MagicMock()
        mock_result.lastrowid = 300

        self.mock_db.execute.return_value = mock_result

        result = self.service.create_practice(
            review_id=103,
            project_id=203,
            title="项目专属",
            description="不可复用",
            is_reusable=False,
        )

        self.assertFalse(result["is_reusable"])

    # ========== _row_to_dict() 测试 ==========

    def test_row_to_dict_full_data(self):
        """测试行转字典（完整数据）"""
        mock_row = MockRow(
            id=1,
            review_id=101,
            project_id=201,
            title="测试",
            description="描述",
            context="上下文",
            implementation="实施",
            benefits="收益",
            category="分类",
            tags="tag1,tag2",
            is_reusable=1,
            applicable_project_types="web",
            applicable_stages="开发",
            validation_status="VALIDATED",
            reuse_count=10,
            status="ACTIVE",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 2, 12, 30, 0),
            project_code="PRJ-001",
            project_name="项目A",
        )

        result = self.service._row_to_dict(mock_row)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["review_id"], 101)
        self.assertEqual(result["project_id"], 201)
        self.assertEqual(result["title"], "测试")
        self.assertEqual(result["description"], "描述")
        self.assertEqual(result["context"], "上下文")
        self.assertEqual(result["implementation"], "实施")
        self.assertEqual(result["benefits"], "收益")
        self.assertEqual(result["category"], "分类")
        self.assertEqual(result["tags"], "tag1,tag2")
        self.assertTrue(result["is_reusable"])
        self.assertEqual(result["applicable_project_types"], "web")
        self.assertEqual(result["applicable_stages"], "开发")
        self.assertEqual(result["validation_status"], "VALIDATED")
        self.assertEqual(result["reuse_count"], 10)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["created_at"], datetime(2024, 1, 1, 10, 0, 0))
        self.assertEqual(result["updated_at"], datetime(2024, 1, 2, 12, 30, 0))
        self.assertEqual(result["project_code"], "PRJ-001")
        self.assertEqual(result["project_name"], "项目A")

    def test_row_to_dict_with_nulls(self):
        """测试行转字典（包含NULL值）"""
        mock_row = MockRow(
            id=2,
            review_id=102,
            project_id=202,
            title="简单实践",
            description="描述",
            context=None,
            implementation=None,
            benefits=None,
            category=None,
            tags=None,
            is_reusable=0,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status=None,  # 测试默认值
            reuse_count=None,  # 测试默认值
            status=None,  # 测试默认值
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            project_code="PRJ-002",
            project_name="项目B",
        )

        result = self.service._row_to_dict(mock_row)

        self.assertIsNone(result["context"])
        self.assertIsNone(result["implementation"])
        self.assertIsNone(result["benefits"])
        self.assertIsNone(result["category"])
        self.assertIsNone(result["tags"])
        self.assertFalse(result["is_reusable"])  # 0 -> False
        self.assertEqual(result["validation_status"], "PENDING")  # 默认值
        self.assertEqual(result["reuse_count"], 0)  # 默认值
        self.assertEqual(result["status"], "ACTIVE")  # 默认值

    def test_row_to_dict_is_reusable_conversion(self):
        """测试is_reusable字段的布尔转换"""
        # 测试1（真值）
        row1 = MockRow(
            id=1,
            review_id=1,
            project_id=1,
            title="t",
            description="d",
            context=None,
            implementation=None,
            benefits=None,
            category=None,
            tags=None,
            is_reusable=1,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="PENDING",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_code="P1",
            project_name="P1",
        )
        result1 = self.service._row_to_dict(row1)
        self.assertTrue(result1["is_reusable"])
        self.assertIsInstance(result1["is_reusable"], bool)

        # 测试0（假值）
        row2 = MockRow(
            id=2,
            review_id=2,
            project_id=2,
            title="t",
            description="d",
            context=None,
            implementation=None,
            benefits=None,
            category=None,
            tags=None,
            is_reusable=0,
            applicable_project_types=None,
            applicable_stages=None,
            validation_status="PENDING",
            reuse_count=0,
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_code="P2",
            project_name="P2",
        )
        result2 = self.service._row_to_dict(row2)
        self.assertFalse(result2["is_reusable"])
        self.assertIsInstance(result2["is_reusable"], bool)


class TestBestPracticesServiceEdgeCases(unittest.TestCase):
    """边界情况和异常测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = BestPracticesService(self.mock_db)

    def test_get_popular_practices_count_returns_none(self):
        """测试count返回None的情况"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = None  # 返回None

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = []

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_popular_practices(pagination)

        self.assertEqual(total, 0)  # None -> 0
        self.assertEqual(len(items), 0)

    def test_get_practices_count_returns_none(self):
        """测试get_practices的count返回None"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = None

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = []

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=1, page_size=10)
        items, total = self.service.get_practices(pagination)

        self.assertEqual(total, 0)

    def test_apply_practice_datetime_now(self):
        """测试apply_practice使用datetime.now()"""
        mock_practice_row = MockRow(id=1, reuse_count=5)
        mock_practice_result = MagicMock()
        mock_practice_result.fetchone.return_value = mock_practice_row

        mock_project_row = MockRow(id=201)
        mock_project_result = MagicMock()
        mock_project_result.fetchone.return_value = mock_project_row

        mock_update_result = MagicMock()

        self.mock_db.execute.side_effect = [
            mock_practice_result,
            mock_project_result,
            mock_update_result,
        ]

        with patch("app.services.best_practices.best_practices_service.datetime") as mock_datetime:
            fixed_time = datetime(2024, 6, 15, 10, 30, 0)
            mock_datetime.now.return_value = fixed_time

            result = self.service.apply_practice(
                practice_id=1, target_project_id=201
            )

            self.assertTrue(result)

            # 验证传递了正确的时间
            update_call = self.mock_db.execute.call_args_list[2]
            params = update_call[0][1]
            self.assertEqual(params["now"], fixed_time)

    def test_create_practice_datetime_now(self):
        """测试create_practice使用datetime.now()"""
        mock_result = MagicMock()
        mock_result.lastrowid = 100

        self.mock_db.execute.return_value = mock_result

        with patch("app.services.best_practices.best_practices_service.datetime") as mock_datetime:
            fixed_time = datetime(2024, 6, 15, 10, 30, 0)
            mock_datetime.now.return_value = fixed_time

            result = self.service.create_practice(
                review_id=101, project_id=201, title="时间测试", description="测试"
            )

            self.assertEqual(result["created_at"], fixed_time)
            self.assertEqual(result["updated_at"], fixed_time)

    def test_large_pagination_offset(self):
        """测试大偏移量分页"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1000

        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = []

        self.mock_db.execute.side_effect = [mock_count_result, mock_data_result]

        pagination = get_pagination_params(page=100, page_size=50)  # offset=4950
        items, total = self.service.get_popular_practices(pagination)

        # 验证offset计算正确
        last_call_args = self.mock_db.execute.call_args_list[1]
        params = last_call_args[0][1]
        self.assertEqual(params["offset"], 4950)


if __name__ == "__main__":
    unittest.main()
