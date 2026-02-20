# -*- coding: utf-8 -*-
"""
project_relations_service.py 的增强单元测试

覆盖所有核心方法和边界条件
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services import project_relations_service


class TestGetMaterialTransferRelations(unittest.TestCase):
    """测试 get_material_transfer_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1

    def test_get_outbound_transfers_success(self):
        """测试获取出库转移成功"""
        # Mock 出库转移记录
        transfer_mock = MagicMock()
        transfer_mock.from_project_id = 1
        transfer_mock.to_project_id = 2
        transfer_mock.status = 'APPROVED'
        transfer_mock.transfer_no = 'T001'
        transfer_mock.material_code = 'M001'
        transfer_mock.material_name = '测试物料'
        transfer_mock.transfer_qty = 100

        # Mock 目标项目
        to_project_mock = MagicMock()
        to_project_mock.id = 2
        to_project_mock.project_code = 'P002'
        to_project_mock.project_name = '目标项目'

        # 第一次调用返回出库转移，第二次返回空（入库）
        self.db_mock.query().filter().all.side_effect = [[transfer_mock], []]
        self.db_mock.query().filter().first.return_value = to_project_mock

        result = project_relations_service.get_material_transfer_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_OUT')
        self.assertEqual(result[0]['related_project_id'], 2)
        self.assertEqual(result[0]['strength'], 'MEDIUM')

    def test_get_inbound_transfers_success(self):
        """测试获取入库转移成功"""
        transfer_mock = MagicMock()
        transfer_mock.from_project_id = 2
        transfer_mock.to_project_id = 1
        transfer_mock.status = 'EXECUTED'
        transfer_mock.transfer_no = 'T002'
        transfer_mock.material_code = 'M002'
        transfer_mock.material_name = '入库物料'
        transfer_mock.transfer_qty = 50

        from_project_mock = MagicMock()
        from_project_mock.id = 2
        from_project_mock.project_code = 'P002'
        from_project_mock.project_name = '来源项目'

        # 第一次调用返回空（出库），第二次返回入库
        self.db_mock.query().filter().all.side_effect = [[], [transfer_mock]]
        self.db_mock.query().filter().first.return_value = from_project_mock

        result = project_relations_service.get_material_transfer_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'MATERIAL_TRANSFER_IN')

    def test_filter_by_relation_type(self):
        """测试按关系类型过滤"""
        result = project_relations_service.get_material_transfer_relations(
            self.db_mock, self.project_id, 'SHARED_RESOURCE'
        )

        self.assertEqual(len(result), 0)

    def test_no_transfers_found(self):
        """测试没有转移记录"""
        self.db_mock.query().filter().all.return_value = []

        result = project_relations_service.get_material_transfer_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(len(result), 0)

    def test_transfer_without_target_project(self):
        """测试转移记录没有目标项目"""
        transfer_mock = MagicMock()
        transfer_mock.from_project_id = 1
        transfer_mock.to_project_id = None

        # 出库和入库都返回一个没有目标项目的转移记录
        self.db_mock.query().filter().all.side_effect = [[transfer_mock], []]

        result = project_relations_service.get_material_transfer_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(len(result), 0)


class TestGetSharedResourceRelations(unittest.TestCase):
    """测试 get_shared_resource_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_get_shared_resources_success(self, mock_pmo):
        """测试获取共享资源成功"""
        # Mock 当前项目的资源分配
        alloc1 = MagicMock()
        alloc1.resource_id = 101
        alloc1.status = 'ACTIVE'

        # Mock 共享项目的资源分配
        shared_alloc = MagicMock()
        shared_alloc.resource_id = 101
        shared_alloc.resource_name = '测试资源'
        shared_alloc.allocation_percent = 50

        # Mock 共享项目
        shared_project = MagicMock()
        shared_project.id = 2
        shared_project.project_code = 'P002'
        shared_project.project_name = '共享项目'

        # 设置查询返回值
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.side_effect = [
            [alloc1],  # 当前项目资源
            [shared_alloc]  # 共享项目资源详情
        ]
        query_mock.filter.return_value.group_by.return_value.all.return_value = [(2, 1)]
        query_mock.filter.return_value.first.return_value = shared_project

        result = project_relations_service.get_shared_resource_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['strength'], 'MEDIUM')

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_high_strength_shared_resources(self, mock_pmo):
        """测试高强度共享资源（3个及以上）"""
        alloc1 = MagicMock()
        alloc1.resource_id = 101

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = [alloc1]
        query_mock.filter.return_value.group_by.return_value.all.return_value = [(2, 3)]

        shared_project = MagicMock()
        shared_project.id = 2
        shared_project.project_code = 'P002'
        shared_project.project_name = '共享项目'
        query_mock.filter.return_value.first.return_value = shared_project

        result = project_relations_service.get_shared_resource_relations(
            self.db_mock, self.project_id, None
        )

        self.assertEqual(result[0]['strength'], 'HIGH')

    def test_no_resources_allocated(self):
        """测试项目没有分配资源"""
        with patch('app.services.project_relations_service.PmoResourceAllocation', create=True):
            self.db_mock.query.return_value.filter.return_value.all.return_value = []

            result = project_relations_service.get_shared_resource_relations(
                self.db_mock, self.project_id, None
            )

            self.assertEqual(len(result), 0)

    def test_filter_by_wrong_relation_type(self):
        """测试按错误的关系类型过滤"""
        result = project_relations_service.get_shared_resource_relations(
            self.db_mock, self.project_id, 'MATERIAL_TRANSFER'
        )

        self.assertEqual(len(result), 0)


class TestGetSharedCustomerRelations(unittest.TestCase):
    """测试 get_shared_customer_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1
        self.project_mock = MagicMock()

    def test_get_shared_customer_success(self):
        """测试获取共享客户成功"""
        self.project_mock.customer_id = 100
        self.project_mock.customer_name = '测试客户'

        customer_project = MagicMock()
        customer_project.id = 2
        customer_project.project_code = 'P002'
        customer_project.project_name = '客户其他项目'

        self.db_mock.query().filter().all.return_value = [customer_project]

        result = project_relations_service.get_shared_customer_relations(
            self.db_mock, self.project_mock, self.project_id, None
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'SHARED_CUSTOMER')
        self.assertEqual(result[0]['strength'], 'LOW')

    def test_no_customer_id(self):
        """测试项目没有客户ID"""
        self.project_mock.customer_id = None

        result = project_relations_service.get_shared_customer_relations(
            self.db_mock, self.project_mock, self.project_id, None
        )

        self.assertEqual(len(result), 0)

    def test_filter_by_relation_type(self):
        """测试按关系类型过滤"""
        self.project_mock.customer_id = 100

        result = project_relations_service.get_shared_customer_relations(
            self.db_mock, self.project_mock, self.project_id, 'MATERIAL_TRANSFER'
        )

        self.assertEqual(len(result), 0)


class TestCalculateRelationStatistics(unittest.TestCase):
    """测试 calculate_relation_statistics 函数"""

    def test_calculate_empty_relations(self):
        """测试空关系列表"""
        result = project_relations_service.calculate_relation_statistics([])

        self.assertEqual(result['total_relations'], 0)
        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_strength']['HIGH'], 0)

    def test_calculate_mixed_relations(self):
        """测试混合关系统计"""
        relations = [
            {'type': 'MATERIAL_TRANSFER_OUT', 'strength': 'HIGH'},
            {'type': 'MATERIAL_TRANSFER_IN', 'strength': 'MEDIUM'},
            {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
            {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
        ]

        result = project_relations_service.calculate_relation_statistics(relations)

        self.assertEqual(result['total_relations'], 4)
        self.assertEqual(result['by_type']['MATERIAL_TRANSFER_OUT'], 1)
        self.assertEqual(result['by_strength']['HIGH'], 2)
        self.assertEqual(result['by_strength']['MEDIUM'], 1)
        self.assertEqual(result['by_strength']['LOW'], 1)


class TestDiscoverSameCustomerRelations(unittest.TestCase):
    """测试 discover_same_customer_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1
        self.project_mock = MagicMock()

    def test_discover_same_customer_success(self):
        """测试发现相同客户成功"""
        self.project_mock.customer_id = 100
        self.project_mock.customer_name = '测试客户'

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = '相关项目'
        related_project.is_active = True

        self.db_mock.query().filter().all.return_value = [related_project]

        result = project_relations_service.discover_same_customer_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_CUSTOMER')
        self.assertEqual(result[0]['confidence'], 0.8)

    def test_no_customer_id(self):
        """测试没有客户ID"""
        self.project_mock.customer_id = None

        result = project_relations_service.discover_same_customer_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverSamePmRelations(unittest.TestCase):
    """测试 discover_same_pm_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1
        self.project_mock = MagicMock()

    def test_discover_same_pm_success(self):
        """测试发现相同PM成功"""
        self.project_mock.pm_id = 10
        self.project_mock.pm_name = '张三'

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = 'PM其他项目'

        self.db_mock.query().filter().all.return_value = [related_project]

        result = project_relations_service.discover_same_pm_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SAME_PM')
        self.assertEqual(result[0]['confidence'], 0.7)

    def test_no_pm_id(self):
        """测试没有PM ID"""
        self.project_mock.pm_id = None

        result = project_relations_service.discover_same_pm_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverTimeOverlapRelations(unittest.TestCase):
    """测试 discover_time_overlap_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1
        self.project_mock = MagicMock()

    def test_discover_time_overlap_success(self):
        """测试发现时间重叠成功"""
        self.project_mock.planned_start_date = datetime(2024, 1, 1)
        self.project_mock.planned_end_date = datetime(2024, 12, 31)

        overlapping_project = MagicMock()
        overlapping_project.id = 2
        overlapping_project.project_code = 'P002'
        overlapping_project.project_name = '重叠项目'

        self.db_mock.query().filter().all.return_value = [overlapping_project]

        result = project_relations_service.discover_time_overlap_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'TIME_OVERLAP')
        self.assertEqual(result[0]['confidence'], 0.6)

    def test_no_dates(self):
        """测试没有日期信息"""
        self.project_mock.planned_start_date = None
        self.project_mock.planned_end_date = None

        result = project_relations_service.discover_time_overlap_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 0)

    def test_missing_end_date(self):
        """测试缺少结束日期"""
        self.project_mock.planned_start_date = datetime(2024, 1, 1)
        self.project_mock.planned_end_date = None

        result = project_relations_service.discover_time_overlap_relations(
            self.db_mock, self.project_mock, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverMaterialTransferRelations(unittest.TestCase):
    """测试 discover_material_transfer_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1

    def test_discover_outbound_transfer(self):
        """测试发现出库转移"""
        transfer_mock = MagicMock()
        transfer_mock.from_project_id = 1
        transfer_mock.to_project_id = 2
        transfer_mock.status = 'APPROVED'
        transfer_mock.material_name = '测试物料'

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = '目标项目'

        self.db_mock.query().filter().all.return_value = [transfer_mock]
        self.db_mock.query().filter().first.return_value = related_project

        result = project_relations_service.discover_material_transfer_relations(
            self.db_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'MATERIAL_TRANSFER')
        self.assertEqual(result[0]['confidence'], 0.9)

    def test_discover_inbound_transfer(self):
        """测试发现入库转移"""
        transfer_mock = MagicMock()
        transfer_mock.from_project_id = 2
        transfer_mock.to_project_id = 1
        transfer_mock.status = 'EXECUTED'
        transfer_mock.material_name = '入库物料'

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = '来源项目'

        self.db_mock.query().filter().all.return_value = [transfer_mock]
        self.db_mock.query().filter().first.return_value = related_project

        result = project_relations_service.discover_material_transfer_relations(
            self.db_mock, self.project_id
        )

        self.assertEqual(len(result), 1)

    def test_no_transfers(self):
        """测试没有转移记录"""
        self.db_mock.query().filter().all.return_value = []

        result = project_relations_service.discover_material_transfer_relations(
            self.db_mock, self.project_id
        )

        self.assertEqual(len(result), 0)


class TestDiscoverSharedResourceRelations(unittest.TestCase):
    """测试 discover_shared_resource_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.PmoResourceAllocation', create=True)
    def test_discover_shared_resources(self, mock_pmo):
        """测试发现共享资源"""
        alloc = MagicMock()
        alloc.resource_id = 101

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = '共享项目'

        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = [alloc]
        query_mock.filter.return_value.distinct.return_value.all.return_value = [(2,)]
        query_mock.filter.return_value.first.return_value = related_project

        result = project_relations_service.discover_shared_resource_relations(
            self.db_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RESOURCE')
        self.assertEqual(result[0]['confidence'], 0.75)


class TestDeduplicateAndFilterRelations(unittest.TestCase):
    """测试 deduplicate_and_filter_relations 函数"""

    def test_deduplicate_relations(self):
        """测试去重关系"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.8, 'relation_type': 'SAME_CUSTOMER'},
            {'related_project_id': 2, 'confidence': 0.9, 'relation_type': 'MATERIAL_TRANSFER'},
            {'related_project_id': 3, 'confidence': 0.7, 'relation_type': 'SAME_PM'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(
            relations, min_confidence=0.5
        )

        self.assertEqual(len(result), 2)
        # 项目2应该保留置信度更高的
        self.assertEqual(result[0]['confidence'], 0.9)

    def test_filter_by_min_confidence(self):
        """测试按最小置信度过滤"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.8, 'relation_type': 'SAME_CUSTOMER'},
            {'related_project_id': 3, 'confidence': 0.4, 'relation_type': 'SAME_PM'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(
            relations, min_confidence=0.5
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['related_project_id'], 2)

    def test_sort_by_confidence(self):
        """测试按置信度排序"""
        relations = [
            {'related_project_id': 2, 'confidence': 0.6, 'relation_type': 'A'},
            {'related_project_id': 3, 'confidence': 0.9, 'relation_type': 'B'},
            {'related_project_id': 4, 'confidence': 0.7, 'relation_type': 'C'},
        ]

        result = project_relations_service.deduplicate_and_filter_relations(
            relations, min_confidence=0.5
        )

        self.assertEqual(result[0]['confidence'], 0.9)
        self.assertEqual(result[1]['confidence'], 0.7)
        self.assertEqual(result[2]['confidence'], 0.6)


class TestCalculateDiscoveryRelationStatistics(unittest.TestCase):
    """测试 calculate_discovery_relation_statistics 函数"""

    def test_calculate_empty_relations(self):
        """测试空关系统计"""
        result = project_relations_service.calculate_discovery_relation_statistics([])

        self.assertEqual(result['by_type'], {})
        self.assertEqual(result['by_confidence_range']['high'], 0)
        self.assertEqual(result['by_confidence_range']['medium'], 0)
        self.assertEqual(result['by_confidence_range']['low'], 0)

    def test_calculate_statistics(self):
        """测试统计计算"""
        relations = [
            {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.9},
            {'relation_type': 'SAME_PM', 'confidence': 0.7},
            {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.8},
            {'relation_type': 'TIME_OVERLAP', 'confidence': 0.4},
        ]

        result = project_relations_service.calculate_discovery_relation_statistics(relations)

        self.assertEqual(result['by_type']['SAME_CUSTOMER'], 2)
        self.assertEqual(result['by_type']['SAME_PM'], 1)
        self.assertEqual(result['by_confidence_range']['high'], 2)
        self.assertEqual(result['by_confidence_range']['medium'], 1)
        self.assertEqual(result['by_confidence_range']['low'], 1)


class TestDiscoverSharedRdProjectRelations(unittest.TestCase):
    """测试 discover_shared_rd_project_relations 函数"""

    def setUp(self):
        self.db_mock = MagicMock()
        self.project_id = 1

    @patch('app.services.project_relations_service.RdProject', create=True)
    def test_discover_shared_rd_project(self, mock_rd):
        """测试发现共享研发项目"""
        rd_project = MagicMock()
        rd_project.id = 100
        rd_project.project_name = '研发项目A'

        other_rd = MagicMock()
        other_rd.linked_project_id = 2

        related_project = MagicMock()
        related_project.id = 2
        related_project.project_code = 'P002'
        related_project.project_name = '关联项目'

        query_mock = self.db_mock.query.return_value
        # 第一次查询返回研发项目
        query_mock.filter.return_value.all.side_effect = [
            [rd_project],
            [other_rd]
        ]
        query_mock.filter.return_value.first.return_value = related_project

        result = project_relations_service.discover_shared_rd_project_relations(
            self.db_mock, self.project_id
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['relation_type'], 'SHARED_RD_PROJECT')
        self.assertEqual(result[0]['confidence'], 0.85)

    def test_no_linked_rd_projects(self):
        """测试没有关联的研发项目"""
        with patch('app.services.project_relations_service.RdProject', create=True):
            self.db_mock.query.return_value.filter.return_value.all.return_value = []

            result = project_relations_service.discover_shared_rd_project_relations(
                self.db_mock, self.project_id
            )

            self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
