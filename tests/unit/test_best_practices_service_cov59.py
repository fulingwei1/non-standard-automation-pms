# -*- coding: utf-8 -*-
"""
最佳实践服务单元测试
测试覆盖率目标: 59%
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from typing import Any

from app.services.best_practices import BestPracticesService
from app.common.pagination import PaginationParams


class TestBestPracticesService(unittest.TestCase):
    """最佳实践服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = BestPracticesService(self.mock_db)

    def test_init(self):
        """测试服务初始化"""
        service = BestPracticesService(self.mock_db)
        self.assertEqual(service.db, self.mock_db)

    def test_get_popular_practices_success(self):
        """测试获取热门最佳实践成功"""
        # 模拟分页参数
        pagination = PaginationParams(page=1, page_size=10)

        # 模拟数据库返回
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.review_id = 100
        mock_row.project_id = 200
        mock_row.title = "测试最佳实践"
        mock_row.description = "测试描述"
        mock_row.context = "测试上下文"
        mock_row.implementation = "测试实施"
        mock_row.benefits = "测试收益"
        mock_row.category = "技术"
        mock_row.tags = "tag1,tag2"
        mock_row.is_reusable = 1
        mock_row.applicable_project_types = "web"
        mock_row.applicable_stages = "开发"
        mock_row.validation_status = "APPROVED"
        mock_row.reuse_count = 5
        mock_row.status = "ACTIVE"
        mock_row.created_at = datetime.now()
        mock_row.updated_at = datetime.now()
        mock_row.project_code = "PROJ001"
        mock_row.project_name = "测试项目"

        # 设置 execute 返回值
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # 总数
        mock_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        items, total = self.service.get_popular_practices(pagination)

        # 验证结果
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], 1)
        self.assertEqual(items[0]["title"], "测试最佳实践")
        self.assertTrue(self.mock_db.execute.called)

    def test_get_popular_practices_with_category(self):
        """测试带分类筛选的热门实践获取"""
        pagination = PaginationParams(page=1, page_size=10)

        # 模拟数据库返回
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.fetchall.return_value = []

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        items, total = self.service.get_popular_practices(pagination, category="技术")

        # 验证结果
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_practices_success(self):
        """测试获取最佳实践列表成功"""
        pagination = PaginationParams(page=1, page_size=10)

        # 模拟数据库返回
        mock_row = MagicMock()
        mock_row.id = 2
        mock_row.review_id = 101
        mock_row.project_id = 201
        mock_row.title = "实践2"
        mock_row.description = "描述2"
        mock_row.context = None
        mock_row.implementation = None
        mock_row.benefits = None
        mock_row.category = "管理"
        mock_row.tags = None
        mock_row.is_reusable = 1
        mock_row.applicable_project_types = None
        mock_row.applicable_stages = None
        mock_row.validation_status = "PENDING"
        mock_row.reuse_count = 0
        mock_row.status = "ACTIVE"
        mock_row.created_at = datetime.now()
        mock_row.updated_at = datetime.now()
        mock_row.project_code = "PROJ002"
        mock_row.project_name = "项目2"

        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_result.fetchall.return_value = [mock_row]

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        items, total = self.service.get_practices(pagination)

        # 验证结果
        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], 2)

    def test_get_practices_with_filters(self):
        """测试带多个筛选条件的实践列表获取"""
        pagination = PaginationParams(page=1, page_size=5)

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_result.fetchall.return_value = []

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        items, total = self.service.get_practices(
            pagination,
            project_id=100,
            category="技术",
            validation_status="APPROVED",
            search="测试",
        )

        # 验证结果
        self.assertEqual(total, 0)
        self.assertEqual(len(items), 0)

    def test_get_practice_by_id_found(self):
        """测试根据ID获取实践成功"""
        # 模拟数据库返回
        mock_row = MagicMock()
        mock_row.id = 3
        mock_row.review_id = 102
        mock_row.project_id = 202
        mock_row.title = "实践3"
        mock_row.description = "描述3"
        mock_row.context = "上下文3"
        mock_row.implementation = "实施3"
        mock_row.benefits = "收益3"
        mock_row.category = "流程"
        mock_row.tags = "tag3"
        mock_row.is_reusable = 1
        mock_row.applicable_project_types = "app"
        mock_row.applicable_stages = "测试"
        mock_row.validation_status = "APPROVED"
        mock_row.reuse_count = 10
        mock_row.status = "ACTIVE"
        mock_row.created_at = datetime.now()
        mock_row.updated_at = datetime.now()
        mock_row.project_code = "PROJ003"
        mock_row.project_name = "项目3"

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        practice = self.service.get_practice_by_id(3)

        # 验证结果
        self.assertIsNotNone(practice)
        self.assertEqual(practice["id"], 3)
        self.assertEqual(practice["title"], "实践3")

    def test_get_practice_by_id_not_found(self):
        """测试根据ID获取不存在的实践"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        practice = self.service.get_practice_by_id(999)

        # 验证结果
        self.assertIsNone(practice)

    def test_apply_practice_success(self):
        """测试应用最佳实践成功"""
        # 模拟实践存在
        mock_practice = MagicMock()
        mock_practice.id = 1
        mock_practice.reuse_count = 5

        # 模拟项目存在
        mock_project = MagicMock()
        mock_project.id = 100

        mock_result1 = MagicMock()
        mock_result1.fetchone.return_value = mock_practice

        mock_result2 = MagicMock()
        mock_result2.fetchone.return_value = mock_project

        # 设置不同的返回值
        self.mock_db.execute.side_effect = [mock_result1, mock_result2, MagicMock()]

        # 调用方法
        result = self.service.apply_practice(1, 100)

        # 验证结果
        self.assertTrue(result)
        self.mock_db.commit.assert_called_once()

    def test_apply_practice_not_found(self):
        """测试应用不存在的最佳实践"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None

        self.mock_db.execute.return_value = mock_result

        # 调用方法，应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.apply_practice(999, 100)

        self.assertEqual(str(context.exception), "最佳实践不存在")

    def test_apply_practice_project_not_found(self):
        """测试应用实践到不存在的项目"""
        # 模拟实践存在
        mock_practice = MagicMock()
        mock_practice.id = 1

        mock_result1 = MagicMock()
        mock_result1.fetchone.return_value = mock_practice

        # 模拟项目不存在
        mock_result2 = MagicMock()
        mock_result2.fetchone.return_value = None

        self.mock_db.execute.side_effect = [mock_result1, mock_result2]

        # 调用方法，应该抛出异常
        with self.assertRaises(ValueError) as context:
            self.service.apply_practice(1, 999)

        self.assertEqual(str(context.exception), "目标项目不存在")

    def test_create_practice_success(self):
        """测试创建最佳实践成功"""
        # 模拟插入结果
        mock_result = MagicMock()
        mock_result.lastrowid = 10

        self.mock_db.execute.return_value = mock_result

        # 调用方法
        practice = self.service.create_practice(
            review_id=100,
            project_id=200,
            title="新实践",
            description="新描述",
            context="新上下文",
            implementation="新实施",
            benefits="新收益",
            category="新分类",
            tags="tag1,tag2",
            is_reusable=True,
            applicable_project_types="web",
            applicable_stages="开发,测试",
        )

        # 验证结果
        self.assertEqual(practice["id"], 10)
        self.assertEqual(practice["title"], "新实践")
        self.assertEqual(practice["review_id"], 100)
        self.assertEqual(practice["project_id"], 200)
        self.assertEqual(practice["validation_status"], "PENDING")
        self.assertEqual(practice["reuse_count"], 0)
        self.assertEqual(practice["status"], "ACTIVE")
        self.mock_db.commit.assert_called_once()

    def test_row_to_dict(self):
        """测试行转字典功能"""
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.review_id = 100
        mock_row.project_id = 200
        mock_row.title = "测试"
        mock_row.description = "描述"
        mock_row.context = "上下文"
        mock_row.implementation = "实施"
        mock_row.benefits = "收益"
        mock_row.category = "分类"
        mock_row.tags = "tags"
        mock_row.is_reusable = 1
        mock_row.applicable_project_types = "web"
        mock_row.applicable_stages = "开发"
        mock_row.validation_status = None  # 测试默认值
        mock_row.reuse_count = None  # 测试默认值
        mock_row.status = None  # 测试默认值
        mock_row.created_at = datetime.now()
        mock_row.updated_at = datetime.now()
        mock_row.project_code = "CODE"
        mock_row.project_name = "名称"

        result = self.service._row_to_dict(mock_row)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["validation_status"], "PENDING")
        self.assertEqual(result["reuse_count"], 0)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertTrue(result["is_reusable"])


if __name__ == "__main__":
    unittest.main()
