# -*- coding: utf-8 -*-
"""
项目关联关系服务增强测试

覆盖 app/services/project_relations_service.py 的所有核心方法
测试策略：只mock外部依赖，构造真实数据对象让业务逻辑真正执行
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services import project_relations_service


class TestGetMaterialTransferRelations(unittest.TestCase):
    """测试 get_material_transfer_relations 方法"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.project_id = 1

    def test_get_material_transfer_relations_outbound(self):
        """测试获取出库物料转移关联"""
        # 构造真实的 MaterialTransfer 对象
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = self.project_id
        mock_transfer.to_project_id = 2
        mock_transfer.status = 'APPROVED'
        mock_transfer.transfer_no = 'MT001'
        mock_transfer.material_code = 'MAT001'
        mock_transfer.material_name = '物料A'
        mock_transfer.transfer_qty = Decimal('10.5')

        # 构造目标项目对象
        mock_to_project = MagicMock()
        mock_to_project.id = 2
        mock_to_project.project_code = 'PRJ002'
        mock_to_project.project_name = '目标项目'

        # Mock数据库查询 - 使用side_effect分别处理出库和入库查询
        query_mock = MagicMock()
        # 第一次all()调用：返回出库转移
        # 第二次all()调用：返回空的入库转移
        query_mock.filter.return_value.all.side_effect = [[mock_transfer], []]
        query_mock.filter.return_value.first.return_value = mock_to_project
        self.db.query.return_value = query_mock

        # 执行测试
        result = project_relations_service.get_material_transfer_relations(
            self.db, self.project_id, None
        )

        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_OUT')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['related_project_code'], 'PRJ002')
        self.assertEqual(result[0]['relation_detail']['transfer_no'], 'MT001')
        self.assertEqual(result[0]['relation_detail']['transfer_qty'], 10.5)
        self.assertEqual(result[0]['strength'], 'MEDIUM')

    def test_get_material_transfer_relations_inbound(self):
        """测试获取入库物料转移关联"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = 3
        mock_transfer.to_project_id = self.project_id
        mock_transfer.status = 'EXECUTED'
        mock_transfer.transfer_no = 'MT002'
        mock_transfer.material_code = 'MAT002'
        mock_transfer.material_name = '物料B'
        mock_transfer.transfer_qty = Decimal('20.0')

        mock_from_project = MagicMock()
        mock_from_project.id = 3
        mock_from_project.project_code = 'PRJ003'
        mock_from_project.project_name = '来源项目'

        # Mock数据库查询 - 第一次调用返回空（出库），第二次返回入库转移
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [],  # 出库转移为空
            [mock_transfer]  # 入库转移
        ]
        self.db.query.return_value.filter.return_value.first.return_value = mock_from_project

        result = project_relations_service.get_material_transfer_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_IN')
        self.assertEqual(result[0]['related_project_id'], 3)
        self.assertEqual(result[0]['related_project_code'], 'PRJ003')

    def test_get_material_transfer_relations_with_type_filter(self):
        """测试使用类型过滤器"""
        result = project_relations_service.get_material_transfer_relations(
            self.db, self.project_id, 'SHARED_RESOURCE'
        )
        self.assertEqual(len(result), 0)

    def test_get_material_transfer_relations_no_to_project(self):
        """测试目标项目ID为空的情况"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = self.project_id
        mock_transfer.to_project_id = None
        mock_transfer.status = 'APPROVED'

        query_mock = MagicMock()
        # 出库转移：返回一个to_project_id为None的转移
        # 入库转移：返回空
        query_mock.filter.return_value.all.side_effect = [[mock_transfer], []]
        self.db.query.return_value = query_mock

        result = project_relations_service.get_material_transfer_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 0)

    def test_get_material_transfer_relations_project_not_found(self):
        """测试目标项目不存在的情况"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = self.project_id
        mock_transfer.to_project_id = 999
        mock_transfer.status = 'APPROVED'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = project_relations_service.get_material_transfer_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 0)


class TestGetSharedResourceRelations(unittest.TestCase):
    """测试 get_shared_resource_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_get_shared_resource_relations_success(self, mock_allocation_class):
        """测试成功获取共享资源关联"""
        # 构造当前项目的资源分配
        mock_alloc1 = MagicMock()
        mock_alloc1.resource_id = 101
        mock_alloc2 = MagicMock()
        mock_alloc2.resource_id = 102

        # 构造共享项目的资源分配
        mock_shared_alloc = MagicMock()
        mock_shared_alloc.resource_id = 101
        mock_shared_alloc.resource_name = '资源A'
        mock_shared_alloc.allocation_percent = 50

        # 构造共享项目
        mock_shared_project = MagicMock()
        mock_shared_project.id = 2
        mock_shared_project.project_code = 'PRJ002'
        mock_shared_project.project_name = '共享项目'

        # 创建多个query mock实例，避免side_effect被复用
        alloc_query_mock = MagicMock()
        alloc_query_mock.filter.return_value.all.return_value = [mock_alloc1, mock_alloc2]

        stats_query_mock = MagicMock()
        stats_query_mock.filter.return_value.group_by.return_value.all.return_value = [(2, 2)]

        project_query_mock = MagicMock()
        project_query_mock.filter.return_value.first.return_value = mock_shared_project

        resources_query_mock = MagicMock()
        resources_query_mock.filter.return_value.all.return_value = [mock_shared_alloc]

        # 设置db.query返回不同的mock
        self.db.query.side_effect = [
            alloc_query_mock,      # 第一次query：当前项目资源
            stats_query_mock,      # 第二次query：共享项目统计
            project_query_mock,    # 第三次query：获取共享项目详情
            resources_query_mock   # 第四次query：获取共享资源详情
        ]

        result = project_relations_service.get_shared_resource_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['strength'], 'MEDIUM')

    def test_get_shared_resource_relations_with_type_filter(self):
        """测试使用类型过滤器"""
        result = project_relations_service.get_shared_resource_relations(
            self.db, self.project_id, 'MATERIAL_TRANSFER'
        )
        self.assertEqual(len(result), 0)

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_get_shared_resource_relations_no_resources(self, mock_allocation_class):
        """测试当前项目无资源分配"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        result = project_relations_service.get_shared_resource_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 0)

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_get_shared_resource_relations_high_strength(self, mock_allocation_class):
        """测试高强度共享资源关联（>=3个共享资源）"""
        mock_alloc = MagicMock()
        mock_alloc.resource_id = 101

        mock_shared_project = MagicMock()
        mock_shared_project.id = 2
        mock_shared_project.project_code = 'PRJ002'
        mock_shared_project.project_name = '共享项目'

        # 创建多个query mock实例
        alloc_query_mock = MagicMock()
        alloc_query_mock.filter.return_value.all.return_value = [mock_alloc]

        stats_query_mock = MagicMock()
        stats_query_mock.filter.return_value.group_by.return_value.all.return_value = [(2, 3)]

        project_query_mock = MagicMock()
        project_query_mock.filter.return_value.first.return_value = mock_shared_project

        resources_query_mock = MagicMock()
        resources_query_mock.filter.return_value.all.return_value = []

        self.db.query.side_effect = [
            alloc_query_mock,
            stats_query_mock,
            project_query_mock,
            resources_query_mock
        ]

        result = project_relations_service.get_shared_resource_relations(
            self.db, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['strength'], 'HIGH')


class TestGetSharedCustomerRelations(unittest.TestCase):
    """测试 get_shared_customer_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_get_shared_customer_relations_success(self):
        """测试成功获取共享客户关联"""
        # 构造当前项目
        mock_project = MagicMock()
        mock_project.customer_id = 100
        mock_project.customer_name = '客户A'

        # 构造共享客户的其他项目
        mock_related_project = MagicMock()
        mock_related_project.id = 2
        mock_related_project.project_code = 'PRJ002'
        mock_related_project.project_name = '相关项目'
        mock_related_project.is_active = True

        self.db.query.return_value.filter.return_value.all.return_value = [mock_related_project]

        result = project_relations_service.get_shared_customer_relations(
            self.db, mock_project, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_CUSTOMER')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['relation_detail']['customer_id'], 100)
        self.assertEqual(result[0]['strength'], 'LOW')

    def test_get_shared_customer_relations_no_customer(self):
        """测试项目无客户ID"""
        mock_project = MagicMock()
        mock_project.customer_id = None

        result = project_relations_service.get_shared_customer_relations(
            self.db, mock_project, self.project_id, None
        )

        self.assertEqual(len(result), 0)

    def test_get_shared_customer_relations_with_type_filter(self):
        """测试使用类型过滤器"""
        mock_project = MagicMock()
        mock_project.customer_id = 100

        result = project_relations_service.get_shared_customer_relations(
            self.db, mock_project, self.project_id, 'MATERIAL_TRANSFER'
        )

        self.assertEqual(len(result), 0)


class TestCalculateRelationStatistics(unittest.TestCase):
    """测试 calculate_relation_statistics 方法"""

    def test_calculate_relation_statistics_empty(self):
        """测试空关联列表"""
        result = project_relations_service.calculate_relation_statistics([])

        self.assertEqual(result['total_relations'], 0)
        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_strength']['HIGH'], 0)
        self.assertEqual(result['by_strength']['MEDIUM'], 0)
        self.assertEqual(result['by_strength']['LOW'], 0)

    def test_calculate_relation_statistics_mixed(self):
        """测试混合类型关联统计"""
        relations = [
            {'type': 'MATERIAL_TRANSFER_OUT', 'strength': 'MEDIUM'},
            {'type': 'MATERIAL_TRANSFER_IN', 'strength': 'MEDIUM'},
            {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
            {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
            {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
        ]

        result = project_relations_service.calculate_relation_statistics(relations)

        self.assertEqual(result['total_relations'], 5)
        self.assertEqual(result['by_type']['MATERIAL_TRANSFER_OUT'], 1)
        self.assertEqual(result['by_type']['MATERIAL_TRANSFER_IN'], 1)
        self.assertEqual(result['by_type']['SHARED_RESOURCE'], 1)
        self.assertEqual(result['by_type']['SHARED_CUSTOMER'], 2)
        self.assertEqual(result['by_strength']['HIGH'], 1)
        self.assertEqual(result['by_strength']['MEDIUM'], 2)
        self.assertEqual(result['by_strength']['LOW'], 2)

    def test_calculate_relation_statistics_single_type(self):
        """测试单一类型统计"""
        relations = [
            {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
            {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
        ]

        result = project_relations_service.calculate_relation_statistics(relations)

        self.assertEqual(result['total_relations'], 2)
        self.assertEqual(result['by_type']['SHARED_RESOURCE'], 2)
        self.assertEqual(result['by_strength']['HIGH'], 2)


class TestDiscoverSameCustomerRelations(unittest.TestCase):
    """测试 discover_same_customer_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_same_customer_relations_success(self):
        """测试成功发现相同客户关联"""
        mock_project = MagicMock()
        mock_project.customer_id = 100
        mock_project.customer_name = '客户A'

        mock_related = MagicMock()
        mock_related.id = 2
        mock_related.project_code = 'PRJ002'
        mock_related.project_name = '相关项目'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_related]

        result = project_relations_service.discover_same_customer_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_CUSTOMER')
        self.assertEqual(result[0]['confidence'], 0.8)
        self.assertIn('相同客户', result[0]['reason'])

    def test_discover_same_customer_relations_no_customer(self):
        """测试无客户ID"""
        mock_project = MagicMock()
        mock_project.customer_id = None

        result = project_relations_service.discover_same_customer_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverSamePmRelations(unittest.TestCase):
    """测试 discover_same_pm_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_same_pm_relations_success(self):
        """测试成功发现相同PM关联"""
        mock_project = MagicMock()
        mock_project.pm_id = 50
        mock_project.pm_name = '张三'

        mock_related = MagicMock()
        mock_related.id = 2
        mock_related.project_code = 'PRJ002'
        mock_related.project_name = '相关项目'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_related]

        result = project_relations_service.discover_same_pm_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_PM')
        self.assertEqual(result[0]['confidence'], 0.7)
        self.assertIn('相同项目经理', result[0]['reason'])

    def test_discover_same_pm_relations_no_pm(self):
        """测试无PM ID"""
        mock_project = MagicMock()
        mock_project.pm_id = None

        result = project_relations_service.discover_same_pm_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverTimeOverlapRelations(unittest.TestCase):
    """测试 discover_time_overlap_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_time_overlap_relations_success(self):
        """测试成功发现时间重叠关联"""
        mock_project = MagicMock()
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 6, 30)

        mock_related = MagicMock()
        mock_related.id = 2
        mock_related.project_code = 'PRJ002'
        mock_related.project_name = '重叠项目'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_related]

        result = project_relations_service.discover_time_overlap_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'TIME_OVERLAP')
        self.assertEqual(result[0]['confidence'], 0.6)

    def test_discover_time_overlap_relations_no_dates(self):
        """测试无计划日期"""
        mock_project = MagicMock()
        mock_project.planned_start_date = None
        mock_project.planned_end_date = date(2024, 6, 30)

        result = project_relations_service.discover_time_overlap_relations(
            self.db, mock_project, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverMaterialTransferRelations(unittest.TestCase):
    """测试 discover_material_transfer_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    def test_discover_material_transfer_relations_outbound(self):
        """测试发现出库物料转移关联"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = self.project_id
        mock_transfer.to_project_id = 2
        mock_transfer.material_name = '物料A'

        mock_related_project = MagicMock()
        mock_related_project.id = 2
        mock_related_project.project_code = 'PRJ002'
        mock_related_project.project_name = '目标项目'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        self.db.query.return_value.filter.return_value.first.return_value = mock_related_project

        result = project_relations_service.discover_material_transfer_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'MATERIAL_TRANSFER')
        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertIn('物料转移', result[0]['reason'])

    def test_discover_material_transfer_relations_inbound(self):
        """测试发现入库物料转移关联"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = 3
        mock_transfer.to_project_id = self.project_id
        mock_transfer.material_name = '物料B'

        mock_related_project = MagicMock()
        mock_related_project.id = 3
        mock_related_project.project_code = 'PRJ003'
        mock_related_project.project_name = '来源项目'

        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]
        self.db.query.return_value.filter.return_value.first.return_value = mock_related_project

        result = project_relations_service.discover_material_transfer_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['related_project_id'], 3)

    def test_discover_material_transfer_relations_no_related_project(self):
        """测试关联项目ID为空"""
        mock_transfer = MagicMock()
        mock_transfer.from_project_id = self.project_id
        mock_transfer.to_project_id = None

        self.db.query.return_value.filter.return_value.all.return_value = [mock_transfer]

        result = project_relations_service.discover_material_transfer_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverSharedResourceRelations(unittest.TestCase):
    """测试 discover_shared_resource_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_discover_shared_resource_relations_success(self, mock_allocation_class):
        """测试成功发现共享资源关联"""
        mock_alloc = MagicMock()
        mock_alloc.resource_id = 101

        mock_related_project = MagicMock()
        mock_related_project.id = 2
        mock_related_project.project_code = 'PRJ002'
        mock_related_project.project_name = '共享项目'

        # 创建多个query mock实例
        alloc_query_mock = MagicMock()
        alloc_query_mock.filter.return_value.all.return_value = [mock_alloc]

        shared_query_mock = MagicMock()
        shared_query_mock.filter.return_value.distinct.return_value.all.return_value = [(2,)]

        project_query_mock = MagicMock()
        project_query_mock.filter.return_value.first.return_value = mock_related_project

        self.db.query.side_effect = [
            alloc_query_mock,
            shared_query_mock,
            project_query_mock
        ]

        result = project_relations_service.discover_shared_resource_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['confidence'], 0.75)

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_discover_shared_resource_relations_no_resources(self, mock_allocation_class):
        """测试无资源分配"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        result = project_relations_service.discover_shared_resource_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverSharedRdProjectRelations(unittest.TestCase):
    """测试 discover_shared_rd_project_relations 方法"""

    def setUp(self):
        self.db = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.RdProject', create=True)
    def test_discover_shared_rd_project_relations_success(self, mock_rd_class):
        """测试成功发现共享研发项目关联"""
        mock_rd_project = MagicMock()
        mock_rd_project.id = 10
        mock_rd_project.project_name = '研发项目A'

        mock_other_rd = MagicMock()
        mock_other_rd.linked_project_id = 2

        mock_related_project = MagicMock()
        mock_related_project.id = 2
        mock_related_project.project_code = 'PRJ002'
        mock_related_project.project_name = '关联项目'

        # 创建多个query mock实例
        linked_rd_query_mock = MagicMock()
        linked_rd_query_mock.filter.return_value.all.return_value = [mock_rd_project]

        other_rd_query_mock = MagicMock()
        other_rd_query_mock.filter.return_value.all.return_value = [mock_other_rd]

        project_query_mock = MagicMock()
        project_query_mock.filter.return_value.first.return_value = mock_related_project

        self.db.query.side_effect = [
            linked_rd_query_mock,
            other_rd_query_mock,
            project_query_mock
        ]

        result = project_relations_service.discover_shared_rd_project_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RD_PROJECT')
        self.assertEqual(result[0]['confidence'], 0.85)

    @patch('app.services.project_relations_service.RdProject', create=True)
    def test_discover_shared_rd_project_relations_no_rd_projects(self, mock_rd_class):
        """测试无关联研发项目"""
        query_mock = MagicMock()
        query_mock.filter.return_value.all.return_value = []
        self.db.query.return_value = query_mock

        result = project_relations_service.discover_shared_rd_project_relations(
            self.db, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDeduplicateAndFilterRelations(unittest.TestCase):
    """测试 deduplicate_and_filter_relations 方法"""

    def test_deduplicate_and_filter_relations_basic(self):
        """测试基本去重和过滤"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.8, 'relation_type': 'TYPE_A'},
            {'related_project_id': 3, 'confidence': 0.6, 'relation_type': 'TYPE_B'},
            {'related_project_id': 4, 'confidence': 0.3, 'relation_type': 'TYPE_C'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(relations, 0.5)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[1]['related_project_id'], 3)

    def test_deduplicate_and_filter_relations_duplicate_keep_higher(self):
        """测试去重时保留高置信度"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.7, 'relation_type': 'TYPE_A'},
            {'related_project_id': 2, 'confidence': 0.9, 'relation_type': 'TYPE_B'},
            {'related_project_id': 2, 'confidence': 0.5, 'relation_type': 'TYPE_C'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(relations, 0.5)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertEqual(result[0]['relation_type'], 'TYPE_B')

    def test_deduplicate_and_filter_relations_sorted_by_confidence(self):
        """测试结果按置信度排序"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.6, 'relation_type': 'TYPE_A'},
            {'related_project_id': 3, 'confidence': 0.9, 'relation_type': 'TYPE_B'},
            {'related_project_id': 4, 'confidence': 0.7, 'relation_type': 'TYPE_C'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(relations, 0.5)

        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertEqual(result[1]['confidence'], 0.7)
        self.assertEqual(result[2]['confidence'], 0.6)

    def test_deduplicate_and_filter_relations_all_filtered(self):
        """测试所有关联被过滤"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.3, 'relation_type': 'TYPE_A'},
            {'related_project_id': 3, 'confidence': 0.4, 'relation_type': 'TYPE_B'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(relations, 0.5)

        self.assertEqual(len(result), 0)


class TestCalculateDiscoveryRelationStatistics(unittest.TestCase):
    """测试 calculate_discovery_relation_statistics 方法"""

    def test_calculate_discovery_relation_statistics_empty(self):
        """测试空关联列表"""
        result = project_relations_service.calculate_discovery_relation_statistics([])

        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_confidence_range']['high'], 0)
        self.assertEqual(result['by_confidence_range']['medium'], 0)
        self.assertEqual(result['by_confidence_range']['low'], 0)

    def test_calculate_discovery_relation_statistics_mixed(self):
        """测试混合置信度统计"""
        relations = [
            {'relation_type': 'MATERIAL_TRANSFER', 'confidence': 0.9},
            {'relation_type': 'SHARED_RESOURCE', 'confidence': 0.75},
            {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.8},
            {'relation_type': 'SAME_PM', 'confidence': 0.7},
            {'relation_type': 'TIME_OVERLAP', 'confidence': 0.4},
        ]

        result = project_relations_service.calculate_discovery_relation_statistics(relations)

        self.assertEqual(result['by_type']['MATERIAL_TRANSFER'], 1)
        self.assertEqual(result['by_type']['SHARED_RESOURCE'], 1)
        self.assertEqual(result['by_confidence_range']['high'], 2)  # >= 0.8
        self.assertEqual(result['by_confidence_range']['medium'], 2)  # 0.5 <= x < 0.8
        self.assertEqual(result['by_confidence_range']['low'], 1)  # < 0.5

    def test_calculate_discovery_relation_statistics_boundary_values(self):
        """测试边界值统计"""
        relations = [
            {'relation_type': 'TYPE_A', 'confidence': 0.8},  # 边界：high
            {'relation_type': 'TYPE_B', 'confidence': 0.79},  # medium
            {'relation_type': 'TYPE_C', 'confidence': 0.5},  # 边界：medium
            {'relation_type': 'TYPE_D', 'confidence': 0.49},  # low
        ]

        result = project_relations_service.calculate_discovery_relation_statistics(relations)

        self.assertEqual(result['by_confidence_range']['high'], 1)
        self.assertEqual(result['by_confidence_range']['medium'], 2)
        self.assertEqual(result['by_confidence_range']['low'], 1)


if __name__ == '__main__':
    unittest.main()
