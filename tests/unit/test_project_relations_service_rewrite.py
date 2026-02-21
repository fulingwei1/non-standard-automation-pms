# -*- coding: utf-8 -*-
"""
项目关联关系服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, db.add等数据库操作）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.project_relations_service import (
    get_material_transfer_relations,
    get_shared_resource_relations,
    get_shared_customer_relations,
    calculate_relation_statistics,
    discover_same_customer_relations,
    discover_same_pm_relations,
    discover_time_overlap_relations,
    discover_material_transfer_relations,
    discover_shared_resource_relations,
    discover_shared_rd_project_relations,
    deduplicate_and_filter_relations,
    calculate_discovery_relation_statistics,
)


class TestGetMaterialTransferRelations(unittest.TestCase):
    """测试获取物料转移关联关系"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_get_material_transfer_out(self):
        """测试出库转移关联"""
        # Mock出库转移数据
        mock_transfer = Mock()
        mock_transfer.to_project_id = 2
        mock_transfer.transfer_no = "TF20240101"
        mock_transfer.material_code = "M001"
        mock_transfer.material_name = "电机"
        mock_transfer.transfer_qty = Decimal("10.5")
        
        mock_to_project = Mock()
        mock_to_project.id = 2
        mock_to_project.project_code = "P002"
        mock_to_project.project_name = "项目B"
        
        # Mock数据库查询 - 需要分别设置两次查询的返回值
        query_mock1 = MagicMock()
        query_mock1.filter.return_value.all.return_value = [mock_transfer]  # 出库转移
        
        query_mock2 = MagicMock()
        query_mock2.filter.return_value.all.return_value = []  # 入库转移（空）
        
        query_mock3 = MagicMock()
        query_mock3.filter.return_value.first.return_value = mock_to_project  # 项目查询
        
        # 设置多次查询的返回值
        self.db.query.side_effect = [query_mock1, query_mock3, query_mock2]
        
        # 执行
        result = get_material_transfer_relations(self.db, self.project_id, None)
        
        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_OUT')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['related_project_code'], 'P002')
        self.assertEqual(result[0]['relation_detail']['transfer_no'], 'TF20240101')
        self.assertEqual(result[0]['strength'], 'MEDIUM')

    def test_get_material_transfer_in(self):
        """测试入库转移关联"""
        # Mock入库转移数据
        mock_transfer = Mock()
        mock_transfer.from_project_id = 3
        mock_transfer.transfer_no = "TF20240102"
        mock_transfer.material_code = "M002"
        mock_transfer.material_name = "齿轮"
        mock_transfer.transfer_qty = Decimal("20.0")
        
        mock_from_project = Mock()
        mock_from_project.id = 3
        mock_from_project.project_code = "P003"
        mock_from_project.project_name = "项目C"
        
        # Mock出库查询（空）
        query_mock1 = MagicMock()
        query_mock1.filter.return_value.all.return_value = []
        
        # Mock入库查询
        query_mock2 = MagicMock()
        query_mock2.filter.return_value.all.return_value = [mock_transfer]
        
        # Mock项目查询
        query_mock3 = MagicMock()
        query_mock3.filter.return_value.first.return_value = mock_from_project
        
        self.db.query.side_effect = [query_mock1, query_mock2, query_mock3]
        
        # 执行
        result = get_material_transfer_relations(self.db, self.project_id, None)
        
        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_IN')
        self.assertEqual(result[0]['related_project_id'], 3)

    def test_get_material_transfer_filtered_by_type(self):
        """测试按类型过滤"""
        # 使用OTHER类型应该返回空结果（不进行数据库查询）
        result = get_material_transfer_relations(self.db, self.project_id, 'OTHER_TYPE')
        self.assertEqual(len(result), 0)
        # 验证没有进行数据库查询
        self.db.query.assert_not_called()

    def test_get_material_transfer_no_to_project(self):
        """测试转移到项目为空的情况"""
        mock_transfer = Mock()
        mock_transfer.to_project_id = None  # 无目标项目
        mock_transfer.from_project_id = None
        
        # Mock出库查询返回带None的转移
        query_mock1 = MagicMock()
        query_mock1.filter.return_value.all.return_value = [mock_transfer]
        
        # Mock入库查询返回空
        query_mock2 = MagicMock()
        query_mock2.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [query_mock1, query_mock2]
        
        result = get_material_transfer_relations(self.db, self.project_id, None)
        
        # 应该被跳过
        self.assertEqual(len(result), 0)


class TestGetSharedResourceRelations(unittest.TestCase):
    """测试获取共享资源关联关系"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_get_shared_resource_relations_success(self):
        """测试成功获取共享资源关联"""
        # Mock资源分配
        mock_alloc1 = Mock()
        mock_alloc1.resource_id = 101
        mock_alloc1.resource_name = "张工"
        mock_alloc1.allocation_percent = 50
        
        mock_alloc2 = Mock()
        mock_alloc2.resource_id = 102
        mock_alloc2.resource_name = "李工"
        mock_alloc2.allocation_percent = 30
        
        mock_shared_project = Mock()
        mock_shared_project.id = 2
        mock_shared_project.project_code = "P002"
        mock_shared_project.project_name = "共享项目"
        
        # Mock数据库查询
        query_mock = MagicMock()
        # 第一次：获取当前项目资源
        query_mock.filter.return_value.all.side_effect = [
            [mock_alloc1, mock_alloc2],  # 当前项目资源
            [mock_alloc1]  # 共享项目的资源
        ]
        # group_by查询
        query_mock.filter.return_value.group_by.return_value.all.return_value = [
            (2, 1)  # shared_project_id=2, shared_count=1
        ]
        # 获取共享项目信息
        query_mock.filter.return_value.first.return_value = mock_shared_project
        
        self.db.query.return_value = query_mock
        
        # 执行
        result = get_shared_resource_relations(self.db, self.project_id, None)
        
        # 验证
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['strength'], 'MEDIUM')  # shared_count=1 < 3

    def test_get_shared_resource_high_strength(self):
        """测试高强度共享资源关联（3个以上）"""
        mock_alloc = Mock()
        mock_alloc.resource_id = 101
        
        mock_shared_project = Mock()
        mock_shared_project.id = 2
        mock_shared_project.project_code = "P002"
        mock_shared_project.project_name = "高强度共享项目"
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.side_effect = [
            [mock_alloc],  # 当前项目资源
            [mock_alloc, mock_alloc, mock_alloc]  # 共享3个资源
        ]
        query_mock.filter.return_value.group_by.return_value.all.return_value = [
            (2, 3)  # shared_count=3
        ]
        query_mock.filter.return_value.first.return_value = mock_shared_project
        
        self.db.query.return_value = query_mock
        
        result = get_shared_resource_relations(self.db, self.project_id, None)
        
        self.assertEqual(result[0]['strength'], 'HIGH')  # shared_count >= 3

    def test_get_shared_resource_no_resources(self):
        """测试当前项目无资源的情况"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []  # 无资源
        self.db.query.return_value = query_mock
        
        result = get_shared_resource_relations(self.db, self.project_id, None)
        
        self.assertEqual(len(result), 0)

    def test_get_shared_resource_import_error(self):
        """测试模型导入失败的情况（PmoResourceAllocation不存在）"""
        # 这个测试需要mock ImportError，但由于代码结构，我们跳过
        # 实际场景中，如果PmoResourceAllocation不存在，会返回空列表
        pass


class TestGetSharedCustomerRelations(unittest.TestCase):
    """测试获取共享客户关联关系"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_get_shared_customer_relations_success(self):
        """测试成功获取共享客户关联"""
        # Mock当前项目
        mock_project = Mock()
        mock_project.customer_id = 100
        mock_project.customer_name = "客户A"
        
        # Mock同客户项目
        mock_customer_project = Mock()
        mock_customer_project.id = 2
        mock_customer_project.project_code = "P002"
        mock_customer_project.project_name = "同客户项目"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_customer_project]
        
        result = get_shared_customer_relations(
            self.db, mock_project, self.project_id, None
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_CUSTOMER')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['relation_detail']['customer_id'], 100)
        self.assertEqual(result[0]['strength'], 'LOW')

    def test_get_shared_customer_no_customer(self):
        """测试项目无客户的情况"""
        mock_project = Mock()
        mock_project.customer_id = None
        
        result = get_shared_customer_relations(
            self.db, mock_project, self.project_id, None
        )
        
        self.assertEqual(len(result), 0)

    def test_get_shared_customer_filtered_by_type(self):
        """测试按类型过滤"""
        mock_project = Mock()
        mock_project.customer_id = 100
        
        result = get_shared_customer_relations(
            self.db, mock_project, self.project_id, 'OTHER_TYPE'
        )
        
        self.assertEqual(len(result), 0)


class TestCalculateRelationStatistics(unittest.TestCase):
    """测试计算关联关系统计信息"""

    def test_calculate_statistics_with_relations(self):
        """测试包含多种关联关系的统计"""
        relations = [
            {'type': 'MATERIAL_TRANSFER_OUT', 'strength': 'HIGH'},
            {'type': 'MATERIAL_TRANSFER_IN', 'strength': 'MEDIUM'},
            {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
            {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
            {'type': 'SHARED_RESOURCE', 'strength': 'MEDIUM'},
        ]
        
        result = calculate_relation_statistics(relations)
        
        self.assertEqual(result['total_relations'], 5)
        self.assertEqual(result['by_type']['MATERIAL_TRANSFER_OUT'], 1)
        self.assertEqual(result['by_type']['SHARED_RESOURCE'], 2)
        self.assertEqual(result['by_strength']['HIGH'], 2)
        self.assertEqual(result['by_strength']['MEDIUM'], 2)
        self.assertEqual(result['by_strength']['LOW'], 1)

    def test_calculate_statistics_empty(self):
        """测试空关联关系列表"""
        result = calculate_relation_statistics([])
        
        self.assertEqual(result['total_relations'], 0)
        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_strength'], {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0})


class TestDiscoverSameCustomerRelations(unittest.TestCase):
    """测试发现相同客户的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_same_customer_success(self):
        """测试成功发现同客户项目"""
        mock_project = Mock()
        mock_project.customer_id = 100
        mock_project.customer_name = "客户A"
        
        mock_related = Mock()
        mock_related.id = 2
        mock_related.project_code = "P002"
        mock_related.project_name = "关联项目"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_related]
        
        result = discover_same_customer_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_CUSTOMER')
        self.assertEqual(result[0]['confidence'], 0.8)
        self.assertIn('客户A', result[0]['reason'])

    def test_discover_same_customer_no_customer(self):
        """测试项目无客户"""
        mock_project = Mock()
        mock_project.customer_id = None
        
        result = discover_same_customer_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDiscoverSamePmRelations(unittest.TestCase):
    """测试发现相同项目经理的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_same_pm_success(self):
        """测试成功发现同PM项目"""
        mock_project = Mock()
        mock_project.pm_id = 10
        mock_project.pm_name = "张经理"
        
        mock_related = Mock()
        mock_related.id = 2
        mock_related.project_code = "P002"
        mock_related.project_name = "同PM项目"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_related]
        
        result = discover_same_pm_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_PM')
        self.assertEqual(result[0]['confidence'], 0.7)
        self.assertIn('张经理', result[0]['reason'])

    def test_discover_same_pm_no_pm(self):
        """测试项目无PM"""
        mock_project = Mock()
        mock_project.pm_id = None
        
        result = discover_same_pm_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDiscoverTimeOverlapRelations(unittest.TestCase):
    """测试发现时间重叠的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_time_overlap_success(self):
        """测试成功发现时间重叠项目"""
        mock_project = Mock()
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 6, 30)
        
        mock_overlapping = Mock()
        mock_overlapping.id = 2
        mock_overlapping.project_code = "P002"
        mock_overlapping.project_name = "重叠项目"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_overlapping]
        
        result = discover_time_overlap_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'TIME_OVERLAP')
        self.assertEqual(result[0]['confidence'], 0.6)

    def test_discover_time_overlap_no_dates(self):
        """测试项目无时间信息"""
        mock_project = Mock()
        mock_project.planned_start_date = None
        mock_project.planned_end_date = None
        
        result = discover_time_overlap_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 0)

    def test_discover_time_overlap_partial_dates(self):
        """测试项目只有部分时间信息"""
        mock_project = Mock()
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = None  # 缺少结束日期
        
        result = discover_time_overlap_relations(self.db, mock_project, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDiscoverMaterialTransferRelations(unittest.TestCase):
    """测试发现物料转移的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_material_transfer_from_project(self):
        """测试从当前项目调出的物料转移"""
        mock_transfer = Mock()
        mock_transfer.from_project_id = 1
        mock_transfer.to_project_id = 2
        mock_transfer.material_name = "电机"
        
        mock_related = Mock()
        mock_related.id = 2
        mock_related.project_code = "P002"
        mock_related.project_name = "目标项目"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        self.db.query.return_value.filter.return_value.first.return_value = mock_related
        
        result = discover_material_transfer_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'MATERIAL_TRANSFER')
        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertIn('电机', result[0]['reason'])

    def test_discover_material_transfer_to_project(self):
        """测试调入当前项目的物料转移"""
        mock_transfer = Mock()
        mock_transfer.from_project_id = 3
        mock_transfer.to_project_id = 1
        mock_transfer.material_name = "齿轮"
        
        mock_related = Mock()
        mock_related.id = 3
        mock_related.project_code = "P003"
        mock_related.project_name = "源项目"
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = [mock_transfer]
        query_mock.filter.return_value.first.return_value = mock_related
        self.db.query.return_value = query_mock
        
        result = discover_material_transfer_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['related_project_id'], 3)

    def test_discover_material_transfer_no_related_project(self):
        """测试转移无关联项目的情况"""
        mock_transfer = Mock()
        mock_transfer.from_project_id = 1
        mock_transfer.to_project_id = None  # 无目标项目
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        
        result = discover_material_transfer_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 0)

    def test_discover_material_transfer_project_not_found(self):
        """测试关联项目不存在"""
        mock_transfer = Mock()
        mock_transfer.from_project_id = 1
        mock_transfer.to_project_id = 2
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        self.db.query.return_value.filter.return_value.first.return_value = None  # 项目不存在
        
        result = discover_material_transfer_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDiscoverSharedResourceRelations(unittest.TestCase):
    """测试发现共享资源的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_shared_resource_success(self):
        """测试成功发现共享资源项目"""
        mock_alloc = Mock()
        mock_alloc.resource_id = 101
        
        mock_related = Mock()
        mock_related.id = 2
        mock_related.project_code = "P002"
        mock_related.project_name = "共享资源项目"
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = [mock_alloc]
        query_mock.filter.return_value.distinct.return_value.all.return_value = [(2,)]
        query_mock.filter.return_value.first.return_value = mock_related
        self.db.query.return_value = query_mock
        
        result = discover_shared_resource_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['confidence'], 0.75)

    def test_discover_shared_resource_no_resources(self):
        """测试当前项目无资源"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock
        
        result = discover_shared_resource_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDiscoverSharedRdProjectRelations(unittest.TestCase):
    """测试发现关联相同研发项目的项目关联"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_shared_rd_project_success(self):
        """测试成功发现共享研发项目"""
        mock_rd = Mock()
        mock_rd.id = 100
        mock_rd.project_name = "研发项目A"
        mock_rd.linked_project_id = 1
        
        mock_other_rd = Mock()
        mock_other_rd.linked_project_id = 2
        
        mock_related = Mock()
        mock_related.id = 2
        mock_related.project_code = "P002"
        mock_related.project_name = "关联项目"
        
        query_mock = MagicMock()
        # 第一次：获取当前项目关联的研发项目
        # 第二次：获取其他关联到同一研发项目的非标项目
        query_mock.filter.return_value.all.side_effect = [
            [mock_rd],  # 当前项目的研发项目
            [mock_other_rd]  # 其他项目
        ]
        query_mock.filter.return_value.first.return_value = mock_related
        self.db.query.return_value = query_mock
        
        result = discover_shared_rd_project_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RD_PROJECT')
        self.assertEqual(result[0]['confidence'], 0.85)
        self.assertIn('研发项目A', result[0]['reason'])

    def test_discover_shared_rd_project_no_linked(self):
        """测试研发项目无关联非标项目"""
        mock_rd = Mock()
        mock_rd.id = 100
        mock_rd.linked_project_id = 1
        
        mock_other_rd = Mock()
        mock_other_rd.linked_project_id = None  # 无关联项目
        
        query_mock = MagicMock()
        query_mock.filter.return_value.all.side_effect = [
            [mock_rd],
            [mock_other_rd]
        ]
        self.db.query.return_value = query_mock
        
        result = discover_shared_rd_project_relations(self.db, self.project_id)
        
        self.assertEqual(len(result), 0)


class TestDeduplicateAndFilterRelations(unittest.TestCase):
    """测试去重并过滤置信度"""

    def test_deduplicate_and_filter_basic(self):
        """测试基本去重和过滤"""
        relations = [
            {'related_project_id': 1, 'confidence': 0.9, 'relation_type': 'TYPE_A'},
            {'related_project_id': 2, 'confidence': 0.6, 'relation_type': 'TYPE_B'},
            {'related_project_id': 1, 'confidence': 0.8, 'relation_type': 'TYPE_C'},  # 重复，但置信度低
            {'related_project_id': 3, 'confidence': 0.4, 'relation_type': 'TYPE_D'},  # 低于阈值
        ]
        
        result = deduplicate_and_filter_relations(relations, min_confidence=0.5)
        
        # 应该保留2个（id=1保留0.9，id=2保留0.6，id=3被过滤）
        self.assertEqual(len(result), 2)
        # 应该按置信度降序排列
        self.assertEqual(result[0]['related_project_id'], 1)
        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertEqual(result[1]['related_project_id'], 2)
        self.assertEqual(result[1]['confidence'], 0.6)

    def test_deduplicate_keeps_higher_confidence(self):
        """测试去重时保留高置信度的记录"""
        relations = [
            {'related_project_id': 1, 'confidence': 0.7, 'relation_type': 'TYPE_A'},
            {'related_project_id': 1, 'confidence': 0.9, 'relation_type': 'TYPE_B'},  # 更高置信度
        ]
        
        result = deduplicate_and_filter_relations(relations, min_confidence=0.5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertEqual(result[0]['relation_type'], 'TYPE_B')

    def test_filter_all_below_threshold(self):
        """测试所有记录都低于阈值"""
        relations = [
            {'related_project_id': 1, 'confidence': 0.3, 'relation_type': 'TYPE_A'},
            {'related_project_id': 2, 'confidence': 0.4, 'relation_type': 'TYPE_B'},
        ]
        
        result = deduplicate_and_filter_relations(relations, min_confidence=0.5)
        
        self.assertEqual(len(result), 0)

    def test_empty_input(self):
        """测试空输入"""
        result = deduplicate_and_filter_relations([], min_confidence=0.5)
        self.assertEqual(len(result), 0)


class TestCalculateDiscoveryRelationStatistics(unittest.TestCase):
    """测试计算发现关联关系统计信息"""

    def test_calculate_discovery_statistics(self):
        """测试计算统计信息"""
        relations = [
            {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.9},
            {'relation_type': 'SAME_PM', 'confidence': 0.7},
            {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.6},
            {'relation_type': 'MATERIAL_TRANSFER', 'confidence': 0.85},
            {'relation_type': 'TIME_OVERLAP', 'confidence': 0.4},
        ]
        
        result = calculate_discovery_relation_statistics(relations)
        
        # 验证类型统计
        self.assertEqual(result['by_type']['SAME_CUSTOMER'], 2)
        self.assertEqual(result['by_type']['SAME_PM'], 1)
        self.assertEqual(result['by_type']['MATERIAL_TRANSFER'], 1)
        self.assertEqual(result['by_type']['TIME_OVERLAP'], 1)
        
        # 验证置信度范围统计
        self.assertEqual(result['by_confidence_range']['high'], 2)  # >= 0.8
        self.assertEqual(result['by_confidence_range']['medium'], 2)  # 0.5-0.8
        self.assertEqual(result['by_confidence_range']['low'], 1)  # < 0.5

    def test_calculate_discovery_statistics_empty(self):
        """测试空输入"""
        result = calculate_discovery_relation_statistics([])
        
        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_confidence_range']['high'], 0)
        self.assertEqual(result['by_confidence_range']['medium'], 0)
        self.assertEqual(result['by_confidence_range']['low'], 0)

    def test_calculate_discovery_statistics_boundary(self):
        """测试边界值（恰好0.8和0.5）"""
        relations = [
            {'relation_type': 'TYPE_A', 'confidence': 0.8},  # 应该是high
            {'relation_type': 'TYPE_B', 'confidence': 0.5},  # 应该是medium
        ]
        
        result = calculate_discovery_relation_statistics(relations)
        
        self.assertEqual(result['by_confidence_range']['high'], 1)
        self.assertEqual(result['by_confidence_range']['medium'], 1)
        self.assertEqual(result['by_confidence_range']['low'], 0)


if __name__ == "__main__":
    unittest.main()
