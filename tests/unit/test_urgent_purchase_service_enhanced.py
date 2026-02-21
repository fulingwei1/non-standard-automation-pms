# -*- coding: utf-8 -*-
"""
增强的单元测试：缺料预警自动触发紧急采购服务
目标覆盖率：70%+
测试用例数：30个
"""

import json
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.urgent_purchase_from_shortage_service import (
    auto_trigger_urgent_purchase_for_alerts,
    create_urgent_purchase_request_from_alert,
    get_material_price,
    get_material_supplier,
)


class TestGetMaterialSupplier(unittest.TestCase):
    """测试 get_material_supplier 函数"""

    def setUp(self):
        """测试前的准备工作"""
        self.db_mock = MagicMock()

    def test_get_preferred_supplier(self):
        """测试获取首选供应商"""
        # 模拟首选供应商
        preferred_supplier = Mock()
        preferred_supplier.supplier_id = 100
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = preferred_supplier
        
        result = get_material_supplier(self.db_mock, material_id=1)
        
        self.assertEqual(result, 100)
        self.db_mock.query.assert_called_once()

    def test_get_default_supplier_when_no_preferred(self):
        """测试当没有首选供应商时，获取默认供应商"""
        # 模拟物料对象
        material = Mock()
        material.default_supplier_id = 200
        
        # 创建两个query mock
        first_query_mock = MagicMock()
        first_query_mock.filter.return_value.first.return_value = None  # 首选供应商查询返回None
        
        second_query_mock = MagicMock()
        second_query_mock.filter.return_value.first.return_value = material  # Material查询返回material
        
        # 设置side_effect: 第一次返回首选供应商查询，第二次返回物料查询
        self.db_mock.query.side_effect = [first_query_mock, second_query_mock]
        
        result = get_material_supplier(self.db_mock, material_id=1)
        
        self.assertEqual(result, 200)

    def test_get_first_active_supplier_when_no_default(self):
        """测试当没有默认供应商时，获取第一个活跃供应商"""
        # 准备三次查询的mock
        call_count = [0]
        
        def query_side_effect(model):
            call_count[0] += 1
            mock = MagicMock()
            
            if call_count[0] == 1:  # 首选供应商查询
                mock.filter.return_value.first.return_value = None
            elif call_count[0] == 2:  # Material查询
                material = Mock()
                material.default_supplier_id = None
                mock.filter.return_value.first.return_value = material
            else:  # 活跃供应商查询
                active_supplier = Mock()
                active_supplier.supplier_id = 300
                mock.filter.return_value.first.return_value = active_supplier
            
            return mock
        
        self.db_mock.query.side_effect = query_side_effect
        
        result = get_material_supplier(self.db_mock, material_id=1)
        
        self.assertEqual(result, 300)

    def test_no_supplier_found(self):
        """测试找不到任何供应商的情况"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None
        
        result = get_material_supplier(self.db_mock, material_id=1)
        
        self.assertIsNone(result)

    def test_with_project_id_parameter(self):
        """测试带项目ID参数的调用"""
        preferred_supplier = Mock()
        preferred_supplier.supplier_id = 100
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = preferred_supplier
        
        result = get_material_supplier(self.db_mock, material_id=1, project_id=5)
        
        self.assertEqual(result, 100)


class TestGetMaterialPrice(unittest.TestCase):
    """测试 get_material_price 函数"""

    def setUp(self):
        """测试前的准备工作"""
        self.db_mock = MagicMock()

    def test_get_supplier_price(self):
        """测试获取供应商价格"""
        material_supplier = Mock()
        material_supplier.price = Decimal('100.50')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material_supplier
        
        result = get_material_price(self.db_mock, material_id=1, supplier_id=100)
        
        self.assertEqual(result, Decimal('100.50'))

    def test_get_last_price_when_no_supplier_price(self):
        """测试当没有供应商价格时，获取最近采购价"""
        # 供应商价格查询返回None
        first_query_mock = MagicMock()
        first_query_mock.filter.return_value.first.return_value = None
        
        # 物料对象
        material = Mock()
        material.last_price = Decimal('80.00')
        material.standard_price = Decimal('90.00')
        
        second_query_mock = MagicMock()
        second_query_mock.filter.return_value.first.return_value = material
        
        self.db_mock.query.side_effect = [first_query_mock, second_query_mock]
        
        result = get_material_price(self.db_mock, material_id=1, supplier_id=100)
        
        self.assertEqual(result, Decimal('80.00'))

    def test_get_standard_price_when_no_last_price(self):
        """测试当没有最近采购价时，获取标准价格"""
        material_supplier = Mock()
        material_supplier.price = None
        
        material = Mock()
        material.last_price = Decimal('0')
        material.standard_price = Decimal('90.00')
        
        query_mocks = [MagicMock(), MagicMock()]
        query_mocks[0].filter.return_value.first.return_value = material_supplier
        query_mocks[1].filter.return_value.first.return_value = material
        
        self.db_mock.query.side_effect = query_mocks
        
        result = get_material_price(self.db_mock, material_id=1, supplier_id=100)
        
        self.assertEqual(result, Decimal('90.00'))

    def test_return_zero_when_no_price_found(self):
        """测试找不到任何价格时返回0"""
        material = Mock()
        material.last_price = None
        material.standard_price = Decimal('0')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        result = get_material_price(self.db_mock, material_id=1)
        
        self.assertEqual(result, Decimal(0))

    def test_without_supplier_id(self):
        """测试不指定供应商ID的情况"""
        material = Mock()
        material.last_price = Decimal('75.00')
        material.standard_price = Decimal('90.00')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        result = get_material_price(self.db_mock, material_id=1)
        
        self.assertEqual(result, Decimal('75.00'))

    def test_material_not_found(self):
        """测试物料不存在的情况"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None
        
        result = get_material_price(self.db_mock, material_id=999)
        
        self.assertEqual(result, Decimal(0))


class TestCreateUrgentPurchaseRequestFromAlert(unittest.TestCase):
    """测试 create_urgent_purchase_request_from_alert 函数"""

    def setUp(self):
        """测试前的准备工作"""
        self.db_mock = MagicMock()
        self.generate_request_no_func = Mock(return_value='PR20260221001')

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    @patch('app.services.urgent_purchase_from_shortage_service.get_material_price')
    def test_create_purchase_request_success(self, mock_get_price, mock_get_supplier):
        """测试成功创建采购申请"""
        # 模拟预警对象
        alert = Mock()
        alert.id = 1
        alert.alert_no = 'AL20260221001'
        alert.target_id = 10
        alert.target_no = 'MAT001'
        alert.target_name = '测试物料'
        alert.project_id = 5
        alert.alert_level = 'level3'
        alert.alert_data = json.dumps({
            'material_code': 'MAT001',
            'material_name': '测试物料',
            'shortage_qty': 100,
            'required_date': '2026-03-01',
            'specification': '规格说明',
            'impact_description': '影响生产'
        })
        
        # 模拟物料对象
        material = Mock()
        material.id = 10
        material.unit = 'PCS'
        
        # 模拟供应商和价格
        mock_get_supplier.return_value = 200
        mock_get_price.return_value = Decimal('50.00')
        
        # 模拟数据库查询
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        # 模拟PurchaseRequest的构造
        with patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequest') as MockPR, \
             patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequestItem') as MockPRI:
            
            request_instance = Mock()
            request_instance.id = 1
            request_instance.request_no = 'PR20260221001'
            MockPR.return_value = request_instance
            
            result = create_urgent_purchase_request_from_alert(
                db=self.db_mock,
                alert=alert,
                current_user_id=1,
                generate_request_no_func=self.generate_request_no_func
            )
            
            self.assertIsNotNone(result)
            self.db_mock.add.assert_called()
            self.db_mock.commit.assert_called_once()
            self.db_mock.refresh.assert_called_once()

    def test_alert_without_material_id(self):
        """测试预警没有物料ID的情况"""
        alert = Mock()
        alert.target_id = None
        alert.alert_no = 'AL20260221002'
        alert.alert_data = '{}'
        
        result = create_urgent_purchase_request_from_alert(
            db=self.db_mock,
            alert=alert,
            current_user_id=1,
            generate_request_no_func=self.generate_request_no_func
        )
        
        self.assertIsNone(result)

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    def test_material_not_found(self, mock_get_supplier):
        """测试物料不存在的情况"""
        alert = Mock()
        alert.id = 1
        alert.alert_no = 'AL20260221003'
        alert.target_id = 999
        alert.alert_data = json.dumps({
            'shortage_qty': 100
        })
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = None
        
        result = create_urgent_purchase_request_from_alert(
            db=self.db_mock,
            alert=alert,
            current_user_id=1,
            generate_request_no_func=self.generate_request_no_func
        )
        
        self.assertIsNone(result)

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    def test_no_supplier_found(self, mock_get_supplier):
        """测试找不到供应商的情况"""
        alert = Mock()
        alert.id = 1
        alert.alert_no = 'AL20260221004'
        alert.target_id = 10
        alert.target_no = 'MAT001'
        alert.project_id = 5
        alert.alert_data = json.dumps({
            'shortage_qty': 100,
            'impact_description': '影响生产'
        })
        
        material = Mock()
        material.id = 10
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        mock_get_supplier.return_value = None
        
        result = create_urgent_purchase_request_from_alert(
            db=self.db_mock,
            alert=alert,
            current_user_id=1,
            generate_request_no_func=self.generate_request_no_func
        )
        
        self.assertIsNone(result)
        self.db_mock.commit.assert_called_once()  # 更新预警状态

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    @patch('app.services.urgent_purchase_from_shortage_service.get_material_price')
    def test_alert_data_as_dict(self, mock_get_price, mock_get_supplier):
        """测试alert_data为字典类型的情况"""
        alert = Mock()
        alert.id = 1
        alert.alert_no = 'AL20260221005'
        alert.target_id = 10
        alert.target_no = 'MAT001'
        alert.target_name = '测试物料'
        alert.project_id = 5
        alert.alert_level = 'CRITICAL'
        alert.alert_data = {  # 直接是字典
            'shortage_qty': 50,
            'required_date': '2026-03-15',
        }
        
        material = Mock()
        material.id = 10
        material.unit = 'KG'
        
        mock_get_supplier.return_value = 200
        mock_get_price.return_value = Decimal('30.00')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        with patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequest') as MockPR, \
             patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequestItem'):
            
            request_instance = Mock()
            request_instance.id = 1
            MockPR.return_value = request_instance
            
            result = create_urgent_purchase_request_from_alert(
                db=self.db_mock,
                alert=alert,
                current_user_id=1,
                generate_request_no_func=self.generate_request_no_func
            )
            
            self.assertIsNotNone(result)

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    def test_exception_handling(self, mock_get_supplier):
        """测试异常处理"""
        alert = Mock()
        alert.alert_no = 'AL20260221006'
        
        # 模拟异常
        mock_get_supplier.side_effect = Exception('数据库错误')
        
        result = create_urgent_purchase_request_from_alert(
            db=self.db_mock,
            alert=alert,
            current_user_id=1,
            generate_request_no_func=self.generate_request_no_func
        )
        
        self.assertIsNone(result)
        self.db_mock.rollback.assert_called_once()

    @patch('app.services.urgent_purchase_from_shortage_service.get_material_supplier')
    @patch('app.services.urgent_purchase_from_shortage_service.get_material_price')
    def test_invalid_json_alert_data(self, mock_get_price, mock_get_supplier):
        """测试alert_data为无效JSON的情况"""
        alert = Mock()
        alert.id = 1
        alert.alert_no = 'AL20260221007'
        alert.target_id = 10
        alert.target_no = 'MAT001'
        alert.target_name = '测试物料'
        alert.project_id = 5
        alert.alert_data = 'invalid json {{'  # 无效JSON
        
        material = Mock()
        material.id = 10
        material.unit = 'PCS'
        
        mock_get_supplier.return_value = 200
        mock_get_price.return_value = Decimal('25.00')
        
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.first.return_value = material
        
        with patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequest') as MockPR, \
             patch('app.services.urgent_purchase_from_shortage_service.PurchaseRequestItem'):
            
            request_instance = Mock()
            request_instance.id = 1
            MockPR.return_value = request_instance
            
            result = create_urgent_purchase_request_from_alert(
                db=self.db_mock,
                alert=alert,
                current_user_id=1,
                generate_request_no_func=self.generate_request_no_func
            )
            
            # 应该使用空字典作为默认值
            self.assertIsNotNone(result)


class TestAutoTriggerUrgentPurchaseForAlerts(unittest.TestCase):
    """测试 auto_trigger_urgent_purchase_for_alerts 函数"""

    def setUp(self):
        """测试前的准备工作"""
        self.db_mock = MagicMock()

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_auto_trigger_with_default_levels(self, mock_generate_no):
        """测试使用默认预警级别自动触发"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            # 模拟预警记录
            alert1 = Mock()
            alert1.alert_no = 'AL001'
            alert1.target_no = 'MAT001'
            alert1.alert_data = json.dumps({})
            
            alert2 = Mock()
            alert2.alert_no = 'AL002'
            alert2.target_no = 'MAT002'
            alert2.alert_data = json.dumps({})
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert1, alert2]
            
            # 模拟成功创建采购申请
            request1 = Mock()
            request1.request_no = 'PR001'
            request2 = Mock()
            request2.request_no = 'PR002'
            
            mock_create_request.side_effect = [request1, request2]
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(result['checked_count'], 2)
            self.assertEqual(result['created_count'], 2)
            self.assertEqual(result['skipped_count'], 0)
            self.assertEqual(result['failed_count'], 0)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_skip_alerts_with_existing_po(self, mock_generate_no):
        """测试跳过已有采购申请的预警"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert = Mock()
            alert.alert_no = 'AL003'
            alert.target_no = 'MAT003'
            alert.alert_data = json.dumps({
                'related_po_no': 'PR20260220001'  # 已有采购申请
            })
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert]
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(result['checked_count'], 1)
            self.assertEqual(result['skipped_count'], 1)
            self.assertEqual(result['created_count'], 0)
            mock_create_request.assert_not_called()

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_handle_creation_failure(self, mock_generate_no):
        """测试处理创建失败的情况"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert = Mock()
            alert.alert_no = 'AL004'
            alert.target_no = 'MAT004'
            alert.alert_data = json.dumps({})
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert]
            
            # 模拟创建失败
            mock_create_request.return_value = None
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(result['checked_count'], 1)
            self.assertEqual(result['failed_count'], 1)
            self.assertEqual(result['created_count'], 0)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_custom_alert_levels(self, mock_generate_no):
        """测试使用自定义预警级别"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = []
        
        result = auto_trigger_urgent_purchase_for_alerts(
            self.db_mock,
            alert_levels=['CRITICAL', 'URGENT']
        )
        
        self.assertEqual(result['checked_count'], 0)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_custom_user_id(self, mock_generate_no):
        """测试使用自定义用户ID"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = []
        
        result = auto_trigger_urgent_purchase_for_alerts(
            self.db_mock,
            current_user_id=999
        )
        
        self.assertIsNotNone(result)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_mixed_results(self, mock_generate_no):
        """测试混合结果（成功、跳过、失败）"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert1 = Mock()
            alert1.alert_no = 'AL005'
            alert1.target_no = 'MAT005'
            alert1.alert_data = json.dumps({})
            
            alert2 = Mock()
            alert2.alert_no = 'AL006'
            alert2.target_no = 'MAT006'
            alert2.alert_data = json.dumps({'related_po_no': 'PR001'})
            
            alert3 = Mock()
            alert3.alert_no = 'AL007'
            alert3.target_no = 'MAT007'
            alert3.alert_data = json.dumps({})
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert1, alert2, alert3]
            
            # 第一个成功，第二个跳过，第三个失败
            request = Mock()
            request.request_no = 'PR002'
            mock_create_request.side_effect = [request, None]
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(result['checked_count'], 3)
            self.assertEqual(result['created_count'], 1)
            self.assertEqual(result['skipped_count'], 1)
            self.assertEqual(result['failed_count'], 1)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_exception_in_query(self, mock_generate_no):
        """测试查询异常的情况"""
        self.db_mock.query.side_effect = Exception('数据库连接失败')
        
        result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
        
        self.assertIn('error', result)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_no_alerts_found(self, mock_generate_no):
        """测试没有找到符合条件的预警"""
        query_mock = self.db_mock.query.return_value
        query_mock.filter.return_value.all.return_value = []
        
        result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
        
        self.assertEqual(result['checked_count'], 0)
        self.assertEqual(result['created_count'], 0)
        self.assertEqual(result['skipped_count'], 0)
        self.assertEqual(result['failed_count'], 0)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_alert_data_invalid_json(self, mock_generate_no):
        """测试预警数据为无效JSON的情况"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert = Mock()
            alert.alert_no = 'AL008'
            alert.target_no = 'MAT008'
            alert.alert_data = 'invalid json'
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert]
            
            request = Mock()
            request.request_no = 'PR003'
            mock_create_request.return_value = request
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            # 应该能够处理无效JSON，使用空字典作为默认值
            self.assertEqual(result['checked_count'], 1)
            self.assertEqual(result['created_count'], 1)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_alert_data_as_none(self, mock_generate_no):
        """测试alert_data为None的情况"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert = Mock()
            alert.alert_no = 'AL009'
            alert.target_no = 'MAT009'
            alert.alert_data = None
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert]
            
            request = Mock()
            request.request_no = 'PR004'
            mock_create_request.return_value = request
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(result['checked_count'], 1)
            self.assertEqual(result['created_count'], 1)

    @patch('app.api.v1.endpoints.purchase.utils.generate_request_no', return_value='PR_MOCK')
    def test_result_details_format(self, mock_generate_no):
        """测试结果详情的格式"""
        with patch('app.services.urgent_purchase_from_shortage_service.create_urgent_purchase_request_from_alert') as mock_create_request:
            alert = Mock()
            alert.alert_no = 'AL010'
            alert.target_no = 'MAT010'
            alert.alert_data = json.dumps({})
            
            query_mock = self.db_mock.query.return_value
            query_mock.filter.return_value.all.return_value = [alert]
            
            request = Mock()
            request.request_no = 'PR005'
            mock_create_request.return_value = request
            
            result = auto_trigger_urgent_purchase_for_alerts(self.db_mock)
            
            self.assertEqual(len(result['details']), 1)
            detail = result['details'][0]
            self.assertEqual(detail['alert_no'], 'AL010')
            self.assertEqual(detail['material_code'], 'MAT010')
            self.assertEqual(detail['request_no'], 'PR005')
            self.assertEqual(detail['status'], 'created')


if __name__ == '__main__':
    unittest.main()
