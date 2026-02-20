# -*- coding: utf-8 -*-
"""
项目关系服务增强测试

测试覆盖:
- 物料转移关联关系管理
- 共享资源关联关系
- 客户关联关系
- 项目发现机制
- 关系统计计算
- 异常处理
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from decimal import Decimal

from app.services import project_relations_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def sample_project():
    """示例项目"""
    project = Mock()
    project.id = 1
    project.project_code = "P001"
    project.project_name = "测试项目"
    project.customer_id = 100
    project.customer_name = "客户A"
    project.pm_id = 200
    project.pm_name = "张三"
    project.planned_start_date = datetime(2024, 1, 1)
    project.planned_end_date = datetime(2024, 6, 30)
    project.is_active = True
    return project


@pytest.fixture
def sample_material_transfer():
    """示例物料转移"""
    transfer = Mock()
    transfer.transfer_no = "MT001"
    transfer.material_code = "MAT001"
    transfer.material_name = "物料A"
    transfer.transfer_qty = Decimal("100.5")
    transfer.status = "APPROVED"
    transfer.from_project_id = 1
    transfer.to_project_id = 2
    return transfer


@pytest.fixture
def sample_related_project():
    """示例关联项目"""
    project = Mock()
    project.id = 2
    project.project_code = "P002"
    project.project_name = "关联项目"
    project.customer_id = 100
    project.customer_name = "客户A"
    project.is_active = True
    return project


# ============================================================================
# get_material_transfer_relations 测试 (8个测试)
# ============================================================================

def test_get_material_transfer_relations_outbound(mock_db, sample_material_transfer, sample_related_project):
    """测试获取出库物料转移关联"""
    project_id = 1
    
    mock_db.query().filter().all.return_value = [sample_material_transfer]
    mock_db.query().filter().first.return_value = sample_related_project
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert len(result) == 2  # 1个出库 + 1个入库查询
    assert result[0]['type'] == 'MATERIAL_TRANSFER_OUT'
    assert result[0]['related_project_id'] == 2
    assert result[0]['related_project_code'] == 'P002'
    assert result[0]['relation_detail']['transfer_no'] == 'MT001'
    assert result[0]['strength'] == 'MEDIUM'


def test_get_material_transfer_relations_inbound(mock_db):
    """测试获取入库物料转移关联"""
    project_id = 2
    transfer = Mock()
    transfer.transfer_no = "MT002"
    transfer.material_code = "MAT002"
    transfer.material_name = "物料B"
    transfer.transfer_qty = Decimal("50.0")
    transfer.status = "EXECUTED"
    transfer.from_project_id = 1
    transfer.to_project_id = 2
    
    from_project = Mock()
    from_project.id = 1
    from_project.project_code = "P001"
    from_project.project_name = "源项目"
    
    # 第一次调用返回空（出库），第二次返回转移记录（入库）
    mock_db.query().filter().all.side_effect = [[], [transfer]]
    mock_db.query().filter().first.return_value = from_project
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert len(result) == 1
    assert result[0]['type'] == 'MATERIAL_TRANSFER_IN'
    assert result[0]['related_project_id'] == 1
    assert result[0]['relation_detail']['material_name'] == '物料B'


def test_get_material_transfer_relations_filter_by_type(mock_db):
    """测试按类型过滤物料转移关联"""
    project_id = 1
    
    # 指定不匹配的类型
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, 'SHARED_RESOURCE'
    )
    
    assert result == []


def test_get_material_transfer_relations_match_type(mock_db, sample_material_transfer, sample_related_project):
    """测试按匹配类型获取物料转移关联"""
    project_id = 1
    
    mock_db.query().filter().all.return_value = [sample_material_transfer]
    mock_db.query().filter().first.return_value = sample_related_project
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, 'MATERIAL_TRANSFER'
    )
    
    assert len(result) > 0


def test_get_material_transfer_relations_no_target_project(mock_db):
    """测试物料转移无目标项目"""
    project_id = 1
    transfer = Mock()
    transfer.to_project_id = None
    transfer.from_project_id = 1
    transfer.status = "APPROVED"
    
    mock_db.query().filter().all.return_value = [transfer]
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert len(result) == 0


def test_get_material_transfer_relations_project_not_found(mock_db, sample_material_transfer):
    """测试关联项目未找到"""
    project_id = 1
    
    mock_db.query().filter().all.return_value = [sample_material_transfer]
    mock_db.query().filter().first.return_value = None
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert len(result) == 0


def test_get_material_transfer_relations_decimal_conversion(mock_db, sample_related_project):
    """测试物料数量的Decimal转换"""
    project_id = 1
    transfer = Mock()
    transfer.transfer_no = "MT003"
    transfer.material_code = "MAT003"
    transfer.material_name = "物料C"
    transfer.transfer_qty = Decimal("123.456")
    transfer.status = "APPROVED"
    transfer.from_project_id = 1
    transfer.to_project_id = 2
    
    mock_db.query().filter().all.return_value = [transfer]
    mock_db.query().filter().first.return_value = sample_related_project
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert result[0]['relation_detail']['transfer_qty'] == 123.456
    assert isinstance(result[0]['relation_detail']['transfer_qty'], float)


def test_get_material_transfer_relations_empty_result(mock_db):
    """测试无物料转移关联"""
    project_id = 1
    
    mock_db.query().filter().all.return_value = []
    
    result = project_relations_service.get_material_transfer_relations(
        mock_db, project_id, None
    )
    
    assert result == []


# ============================================================================
# get_shared_resource_relations 测试 (6个测试)
# ============================================================================

def test_get_shared_resource_relations_success(mock_db, sample_related_project):
    """测试获取共享资源关联成功"""
    project_id = 1
    
    # Mock资源分配
    alloc1 = Mock()
    alloc1.resource_id = 101
    alloc1.resource_name = "资源A"
    alloc1.allocation_percent = 50
    
    alloc2 = Mock()
    alloc2.resource_id = 102
    alloc2.resource_name = "资源B"
    alloc2.allocation_percent = 30
    
    with patch('app.services.project_relations_service.PmoResourceAllocation') as MockAlloc:
        mock_db.query().filter().all.side_effect = [
            [alloc1, alloc2],  # project_resources
            [alloc1, alloc2]   # shared_resources
        ]
        mock_db.query().filter().group_by().all.return_value = [(2, 2)]
        mock_db.query().filter().first.return_value = sample_related_project
        
        result = project_relations_service.get_shared_resource_relations(
            mock_db, project_id, None
        )
        
        assert len(result) == 1
        assert result[0]['type'] == 'SHARED_RESOURCE'
        assert result[0]['related_project_id'] == 2
        assert result[0]['relation_detail']['shared_resource_count'] == 2
        assert len(result[0]['relation_detail']['shared_resources']) == 2
        assert result[0]['strength'] == 'MEDIUM'


def test_get_shared_resource_relations_high_strength(mock_db, sample_related_project):
    """测试高强度共享资源关联（>=3个资源）"""
    project_id = 1
    
    allocs = [Mock(resource_id=i, resource_name=f"资源{i}", allocation_percent=50) for i in range(101, 105)]
    
    with patch('app.services.project_relations_service.PmoResourceAllocation'):
        mock_db.query().filter().all.side_effect = [allocs, allocs]
        mock_db.query().filter().group_by().all.return_value = [(2, 4)]
        mock_db.query().filter().first.return_value = sample_related_project
        
        result = project_relations_service.get_shared_resource_relations(
            mock_db, project_id, None
        )
        
        assert result[0]['strength'] == 'HIGH'


def test_get_shared_resource_relations_filter_by_type(mock_db):
    """测试按类型过滤共享资源关联"""
    project_id = 1
    
    result = project_relations_service.get_shared_resource_relations(
        mock_db, project_id, 'MATERIAL_TRANSFER'
    )
    
    assert result == []


def test_get_shared_resource_relations_no_resources(mock_db):
    """测试无共享资源"""
    project_id = 1
    
    with patch('app.services.project_relations_service.PmoResourceAllocation'):
        mock_db.query().filter().all.return_value = []
        
        result = project_relations_service.get_shared_resource_relations(
            mock_db, project_id, None
        )
        
        assert result == []


def test_get_shared_resource_relations_import_error(mock_db):
    """测试PmoResourceAllocation不存在时的处理"""
    project_id = 1
    
    # 模拟ImportError
    with patch('app.services.project_relations_service.PmoResourceAllocation', side_effect=ImportError):
        result = project_relations_service.get_shared_resource_relations(
            mock_db, project_id, None
        )
        
        assert result == []


def test_get_shared_resource_relations_project_not_found(mock_db):
    """测试共享项目未找到"""
    project_id = 1
    
    alloc = Mock(resource_id=101)
    
    with patch('app.services.project_relations_service.PmoResourceAllocation'):
        mock_db.query().filter().all.return_value = [alloc]
        mock_db.query().filter().group_by().all.return_value = [(2, 1)]
        mock_db.query().filter().first.return_value = None
        
        result = project_relations_service.get_shared_resource_relations(
            mock_db, project_id, None
        )
        
        assert result == []


# ============================================================================
# get_shared_customer_relations 测试 (5个测试)
# ============================================================================

def test_get_shared_customer_relations_success(mock_db, sample_project, sample_related_project):
    """测试获取共享客户关联成功"""
    project_id = 1
    
    mock_db.query().filter().all.return_value = [sample_related_project]
    
    result = project_relations_service.get_shared_customer_relations(
        mock_db, sample_project, project_id, None
    )
    
    assert len(result) == 1
    assert result[0]['type'] == 'SHARED_CUSTOMER'
    assert result[0]['related_project_id'] == 2
    assert result[0]['relation_detail']['customer_name'] == '客户A'
    assert result[0]['strength'] == 'LOW'


def test_get_shared_customer_relations_no_customer(mock_db):
    """测试项目无客户ID"""
    project = Mock()
    project.customer_id = None
    
    result = project_relations_service.get_shared_customer_relations(
        mock_db, project, 1, None
    )
    
    assert result == []


def test_get_shared_customer_relations_filter_by_type(mock_db, sample_project):
    """测试按类型过滤共享客户关联"""
    result = project_relations_service.get_shared_customer_relations(
        mock_db, sample_project, 1, 'MATERIAL_TRANSFER'
    )
    
    assert result == []


def test_get_shared_customer_relations_multiple_projects(mock_db, sample_project):
    """测试多个共享客户项目"""
    project1 = Mock(id=2, project_code="P002", project_name="项目2", is_active=True)
    project2 = Mock(id=3, project_code="P003", project_name="项目3", is_active=True)
    
    mock_db.query().filter().all.return_value = [project1, project2]
    
    result = project_relations_service.get_shared_customer_relations(
        mock_db, sample_project, 1, None
    )
    
    assert len(result) == 2


def test_get_shared_customer_relations_empty(mock_db, sample_project):
    """测试无共享客户项目"""
    mock_db.query().filter().all.return_value = []
    
    result = project_relations_service.get_shared_customer_relations(
        mock_db, sample_project, 1, None
    )
    
    assert result == []


# ============================================================================
# calculate_relation_statistics 测试 (3个测试)
# ============================================================================

def test_calculate_relation_statistics_success():
    """测试计算关联统计成功"""
    relations = [
        {'type': 'MATERIAL_TRANSFER_OUT', 'strength': 'MEDIUM'},
        {'type': 'MATERIAL_TRANSFER_IN', 'strength': 'MEDIUM'},
        {'type': 'SHARED_RESOURCE', 'strength': 'HIGH'},
        {'type': 'SHARED_RESOURCE', 'strength': 'MEDIUM'},
        {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
    ]
    
    result = project_relations_service.calculate_relation_statistics(relations)
    
    assert result['total_relations'] == 5
    assert result['by_type']['MATERIAL_TRANSFER_OUT'] == 1
    assert result['by_type']['MATERIAL_TRANSFER_IN'] == 1
    assert result['by_type']['SHARED_RESOURCE'] == 2
    assert result['by_type']['SHARED_CUSTOMER'] == 1
    assert result['by_strength']['HIGH'] == 1
    assert result['by_strength']['MEDIUM'] == 3
    assert result['by_strength']['LOW'] == 1


def test_calculate_relation_statistics_empty():
    """测试空关联统计"""
    result = project_relations_service.calculate_relation_statistics([])
    
    assert result['total_relations'] == 0
    assert result['by_type'] == {}
    assert result['by_strength']['HIGH'] == 0
    assert result['by_strength']['MEDIUM'] == 0
    assert result['by_strength']['LOW'] == 0


def test_calculate_relation_statistics_single_type():
    """测试单一类型关联统计"""
    relations = [
        {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
        {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
    ]
    
    result = project_relations_service.calculate_relation_statistics(relations)
    
    assert result['total_relations'] == 2
    assert result['by_type']['SHARED_CUSTOMER'] == 2
    assert result['by_strength']['LOW'] == 2


# ============================================================================
# discover_same_customer_relations 测试 (3个测试)
# ============================================================================

def test_discover_same_customer_relations_success(mock_db, sample_project):
    """测试发现相同客户关联成功"""
    related = Mock()
    related.id = 2
    related.project_code = "P002"
    related.project_name = "关联项目"
    related.is_active = True
    
    mock_db.query().filter().all.return_value = [related]
    
    result = project_relations_service.discover_same_customer_relations(
        mock_db, sample_project, 1
    )
    
    assert len(result) == 1
    assert result[0]['relation_type'] == 'SAME_CUSTOMER'
    assert result[0]['confidence'] == 0.8
    assert '客户A' in result[0]['reason']


def test_discover_same_customer_relations_no_customer(mock_db):
    """测试无客户ID时发现"""
    project = Mock(customer_id=None)
    
    result = project_relations_service.discover_same_customer_relations(
        mock_db, project, 1
    )
    
    assert result == []


def test_discover_same_customer_relations_empty(mock_db, sample_project):
    """测试无相同客户项目"""
    mock_db.query().filter().all.return_value = []
    
    result = project_relations_service.discover_same_customer_relations(
        mock_db, sample_project, 1
    )
    
    assert result == []


# ============================================================================
# discover_same_pm_relations 测试 (3个测试)
# ============================================================================

def test_discover_same_pm_relations_success(mock_db, sample_project):
    """测试发现相同PM关联成功"""
    related = Mock()
    related.id = 3
    related.project_code = "P003"
    related.project_name = "PM项目"
    related.is_active = True
    
    mock_db.query().filter().all.return_value = [related]
    
    result = project_relations_service.discover_same_pm_relations(
        mock_db, sample_project, 1
    )
    
    assert len(result) == 1
    assert result[0]['relation_type'] == 'SAME_PM'
    assert result[0]['confidence'] == 0.7
    assert '张三' in result[0]['reason']


def test_discover_same_pm_relations_no_pm(mock_db):
    """测试无PM时发现"""
    project = Mock(pm_id=None)
    
    result = project_relations_service.discover_same_pm_relations(
        mock_db, project, 1
    )
    
    assert result == []


def test_discover_same_pm_relations_multiple(mock_db, sample_project):
    """测试多个相同PM项目"""
    projects = [
        Mock(id=i, project_code=f"P{i}", project_name=f"项目{i}", is_active=True)
        for i in range(2, 5)
    ]
    
    mock_db.query().filter().all.return_value = projects
    
    result = project_relations_service.discover_same_pm_relations(
        mock_db, sample_project, 1
    )
    
    assert len(result) == 3


# ============================================================================
# discover_time_overlap_relations 测试 (4个测试)
# ============================================================================

def test_discover_time_overlap_relations_success(mock_db, sample_project):
    """测试发现时间重叠关联成功"""
    overlapping = Mock()
    overlapping.id = 4
    overlapping.project_code = "P004"
    overlapping.project_name = "重叠项目"
    overlapping.is_active = True
    
    mock_db.query().filter().all.return_value = [overlapping]
    
    result = project_relations_service.discover_time_overlap_relations(
        mock_db, sample_project, 1
    )
    
    assert len(result) == 1
    assert result[0]['relation_type'] == 'TIME_OVERLAP'
    assert result[0]['confidence'] == 0.6


def test_discover_time_overlap_relations_no_dates(mock_db):
    """测试无计划日期时发现"""
    project = Mock()
    project.planned_start_date = None
    project.planned_end_date = None
    
    result = project_relations_service.discover_time_overlap_relations(
        mock_db, project, 1
    )
    
    assert result == []


def test_discover_time_overlap_relations_partial_dates(mock_db):
    """测试部分日期缺失"""
    project = Mock()
    project.planned_start_date = datetime(2024, 1, 1)
    project.planned_end_date = None
    
    result = project_relations_service.discover_time_overlap_relations(
        mock_db, project, 1
    )
    
    assert result == []


def test_discover_time_overlap_relations_empty(mock_db, sample_project):
    """测试无重叠项目"""
    mock_db.query().filter().all.return_value = []
    
    result = project_relations_service.discover_time_overlap_relations(
        mock_db, sample_project, 1
    )
    
    assert result == []


# ============================================================================
# discover_material_transfer_relations 测试 (3个测试)
# ============================================================================

def test_discover_material_transfer_relations_success(mock_db):
    """测试发现物料转移关联成功"""
    transfer = Mock()
    transfer.from_project_id = 1
    transfer.to_project_id = 2
    transfer.material_name = "物料X"
    transfer.status = "APPROVED"
    
    related = Mock()
    related.id = 2
    related.project_code = "P002"
    related.project_name = "目标项目"
    
    mock_db.query().filter().all.return_value = [transfer]
    mock_db.query().filter().first.return_value = related
    
    result = project_relations_service.discover_material_transfer_relations(
        mock_db, 1
    )
    
    assert len(result) == 1
    assert result[0]['relation_type'] == 'MATERIAL_TRANSFER'
    assert result[0]['confidence'] == 0.9
    assert '物料X' in result[0]['reason']


def test_discover_material_transfer_relations_bidirectional(mock_db):
    """测试双向物料转移"""
    transfer_out = Mock()
    transfer_out.from_project_id = 1
    transfer_out.to_project_id = 2
    transfer_out.material_name = "物料A"
    transfer_out.status = "APPROVED"
    
    transfer_in = Mock()
    transfer_in.from_project_id = 3
    transfer_in.to_project_id = 1
    transfer_in.material_name = "物料B"
    transfer_in.status = "EXECUTED"
    
    project2 = Mock(id=2, project_code="P002", project_name="项目2")
    project3 = Mock(id=3, project_code="P003", project_name="项目3")
    
    mock_db.query().filter().all.return_value = [transfer_out, transfer_in]
    mock_db.query().filter().first.side_effect = [project2, project3]
    
    result = project_relations_service.discover_material_transfer_relations(
        mock_db, 1
    )
    
    assert len(result) == 2


def test_discover_material_transfer_relations_project_not_found(mock_db):
    """测试关联项目未找到"""
    transfer = Mock()
    transfer.from_project_id = 1
    transfer.to_project_id = 2
    transfer.status = "APPROVED"
    
    mock_db.query().filter().all.return_value = [transfer]
    mock_db.query().filter().first.return_value = None
    
    result = project_relations_service.discover_material_transfer_relations(
        mock_db, 1
    )
    
    assert result == []


# ============================================================================
# discover_shared_resource_relations 测试 (3个测试)
# ============================================================================

def test_discover_shared_resource_relations_success(mock_db):
    """测试发现共享资源关联成功"""
    alloc = Mock(resource_id=101)
    
    related = Mock()
    related.id = 2
    related.project_code = "P002"
    related.project_name = "共享项目"
    
    with patch('app.services.project_relations_service.PmoResourceAllocation'):
        mock_db.query().filter().all.return_value = [alloc]
        mock_db.query().filter().distinct().all.return_value = [(2,)]
        mock_db.query().filter().first.return_value = related
        
        result = project_relations_service.discover_shared_resource_relations(
            mock_db, 1
        )
        
        assert len(result) == 1
        assert result[0]['relation_type'] == 'SHARED_RESOURCE'
        assert result[0]['confidence'] == 0.75


def test_discover_shared_resource_relations_no_resources(mock_db):
    """测试无共享资源"""
    with patch('app.services.project_relations_service.PmoResourceAllocation'):
        mock_db.query().filter().all.return_value = []
        
        result = project_relations_service.discover_shared_resource_relations(
            mock_db, 1
        )
        
        assert result == []


def test_discover_shared_resource_relations_import_error(mock_db):
    """测试模块导入错误"""
    result = project_relations_service.discover_shared_resource_relations(
        mock_db, 1
    )
    
    # 应该捕获ImportError并返回空列表
    assert result == []


# ============================================================================
# discover_shared_rd_project_relations 测试 (3个测试)
# ============================================================================

def test_discover_shared_rd_project_relations_success(mock_db):
    """测试发现共享研发项目关联成功"""
    rd_project = Mock()
    rd_project.id = 1001
    rd_project.project_name = "研发项目X"
    rd_project.linked_project_id = 1
    
    other_rd = Mock()
    other_rd.id = 1001
    other_rd.linked_project_id = 2
    
    related = Mock()
    related.id = 2
    related.project_code = "P002"
    related.project_name = "研发关联项目"
    
    with patch('app.services.project_relations_service.RdProject'):
        mock_db.query().filter().all.side_effect = [[rd_project], [other_rd]]
        mock_db.query().filter().first.return_value = related
        
        result = project_relations_service.discover_shared_rd_project_relations(
            mock_db, 1
        )
        
        assert len(result) == 1
        assert result[0]['relation_type'] == 'SHARED_RD_PROJECT'
        assert result[0]['confidence'] == 0.85


def test_discover_shared_rd_project_relations_no_linked(mock_db):
    """测试无关联的研发项目"""
    with patch('app.services.project_relations_service.RdProject'):
        mock_db.query().filter().all.return_value = []
        
        result = project_relations_service.discover_shared_rd_project_relations(
            mock_db, 1
        )
        
        assert result == []


def test_discover_shared_rd_project_relations_import_error(mock_db):
    """测试RdProject模块不存在"""
    result = project_relations_service.discover_shared_rd_project_relations(
        mock_db, 1
    )
    
    # 应该捕获ImportError并返回空列表
    assert result == []


# ============================================================================
# deduplicate_and_filter_relations 测试 (4个测试)
# ============================================================================

def test_deduplicate_and_filter_relations_success():
    """测试去重和过滤成功"""
    relations = [
        {'related_project_id': 2, 'confidence': 0.8, 'reason': 'A'},
        {'related_project_id': 3, 'confidence': 0.9, 'reason': 'B'},
        {'related_project_id': 2, 'confidence': 0.7, 'reason': 'C'},  # 重复，置信度低
        {'related_project_id': 4, 'confidence': 0.4, 'reason': 'D'},  # 低于阈值
    ]
    
    result = project_relations_service.deduplicate_and_filter_relations(
        relations, min_confidence=0.5
    )
    
    assert len(result) == 2
    assert result[0]['related_project_id'] == 3  # 最高置信度
    assert result[0]['confidence'] == 0.9
    assert result[1]['related_project_id'] == 2
    assert result[1]['confidence'] == 0.8


def test_deduplicate_and_filter_relations_keep_highest():
    """测试保留最高置信度的重复项"""
    relations = [
        {'related_project_id': 2, 'confidence': 0.6, 'reason': 'A'},
        {'related_project_id': 2, 'confidence': 0.9, 'reason': 'B'},
        {'related_project_id': 2, 'confidence': 0.7, 'reason': 'C'},
    ]
    
    result = project_relations_service.deduplicate_and_filter_relations(
        relations, min_confidence=0.5
    )
    
    assert len(result) == 1
    assert result[0]['confidence'] == 0.9


def test_deduplicate_and_filter_relations_filter_low_confidence():
    """测试过滤低置信度"""
    relations = [
        {'related_project_id': 2, 'confidence': 0.3, 'reason': 'A'},
        {'related_project_id': 3, 'confidence': 0.4, 'reason': 'B'},
    ]
    
    result = project_relations_service.deduplicate_and_filter_relations(
        relations, min_confidence=0.5
    )
    
    assert result == []


def test_deduplicate_and_filter_relations_empty():
    """测试空输入"""
    result = project_relations_service.deduplicate_and_filter_relations(
        [], min_confidence=0.5
    )
    
    assert result == []


# ============================================================================
# calculate_discovery_relation_statistics 测试 (3个测试)
# ============================================================================

def test_calculate_discovery_relation_statistics_success():
    """测试计算发现关联统计成功"""
    relations = [
        {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.8},
        {'relation_type': 'SAME_CUSTOMER', 'confidence': 0.9},
        {'relation_type': 'SAME_PM', 'confidence': 0.7},
        {'relation_type': 'MATERIAL_TRANSFER', 'confidence': 0.9},
        {'relation_type': 'TIME_OVERLAP', 'confidence': 0.4},
    ]
    
    result = project_relations_service.calculate_discovery_relation_statistics(
        relations
    )
    
    assert result['by_type']['SAME_CUSTOMER'] == 2
    assert result['by_type']['SAME_PM'] == 1
    assert result['by_type']['MATERIAL_TRANSFER'] == 1
    assert result['by_type']['TIME_OVERLAP'] == 1
    assert result['by_confidence_range']['high'] == 3  # >= 0.8
    assert result['by_confidence_range']['medium'] == 1  # 0.7
    assert result['by_confidence_range']['low'] == 1  # 0.4


def test_calculate_discovery_relation_statistics_empty():
    """测试空关联统计"""
    result = project_relations_service.calculate_discovery_relation_statistics([])
    
    assert result['by_type'] == {}
    assert result['by_confidence_range']['high'] == 0
    assert result['by_confidence_range']['medium'] == 0
    assert result['by_confidence_range']['low'] == 0


def test_calculate_discovery_relation_statistics_edge_confidence():
    """测试边界置信度分类"""
    relations = [
        {'relation_type': 'A', 'confidence': 0.8},   # high
        {'relation_type': 'B', 'confidence': 0.79},  # medium
        {'relation_type': 'C', 'confidence': 0.5},   # medium
        {'relation_type': 'D', 'confidence': 0.49},  # low
    ]
    
    result = project_relations_service.calculate_discovery_relation_statistics(
        relations
    )
    
    assert result['by_confidence_range']['high'] == 1
    assert result['by_confidence_range']['medium'] == 2
    assert result['by_confidence_range']['low'] == 1
