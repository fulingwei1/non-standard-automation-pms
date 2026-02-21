# -*- coding: utf-8 -*-
"""
MachineCustomService 单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open, AsyncMock
from decimal import Decimal
from datetime import datetime
from pathlib import Path as FilePath
from io import BytesIO

from fastapi import HTTPException, UploadFile

from app.services.machine_custom.service import MachineCustomService, DOC_TYPE_PERMISSION_MAP


class TestMachineCustomService(unittest.TestCase):
    """测试 MachineCustomService"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = MachineCustomService(self.mock_db)
        
        # 创建mock的机台对象
        self.mock_machine = MagicMock()
        self.mock_machine.id = 1
        self.mock_machine.machine_code = "MC001"
        self.mock_machine.machine_name = "测试机台"
        self.mock_machine.machine_no = "MN001"
        self.mock_machine.project_id = 100
        self.mock_machine.progress_pct = Decimal("0")
        
        # 创建mock的用户对象
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.username = "testuser"


    # ========== update_machine_progress 测试 ==========

    @patch('app.services.machine_service.ProjectAggregationService')
    @patch('app.utils.db_helpers.save_obj')
    def test_update_machine_progress_success(self, mock_save_obj, mock_aggregation_service_class):
        """测试成功更新机台进度"""
        # 准备
        mock_aggregation_service = MagicMock()
        mock_aggregation_service_class.return_value = mock_aggregation_service
        
        new_progress = Decimal("75.5")
        
        # 执行
        result = self.service.update_machine_progress(self.mock_machine, new_progress)
        
        # 验证
        self.assertEqual(self.mock_machine.progress_pct, new_progress)
        mock_save_obj.assert_called_once_with(self.mock_db, self.mock_machine)
        mock_aggregation_service_class.assert_called_once_with(self.mock_db)
        mock_aggregation_service.update_project_aggregation.assert_called_once_with(100)
        self.assertEqual(result, self.mock_machine)

    @patch('app.services.machine_service.ProjectAggregationService')
    @patch('app.utils.db_helpers.save_obj')
    def test_update_machine_progress_zero(self, mock_save_obj, mock_aggregation_service_class):
        """测试更新进度为0"""
        mock_aggregation_service = MagicMock()
        mock_aggregation_service_class.return_value = mock_aggregation_service
        
        result = self.service.update_machine_progress(self.mock_machine, Decimal("0"))
        
        self.assertEqual(self.mock_machine.progress_pct, Decimal("0"))
        mock_save_obj.assert_called_once()

    @patch('app.services.machine_service.ProjectAggregationService')
    @patch('app.utils.db_helpers.save_obj')
    def test_update_machine_progress_hundred(self, mock_save_obj, mock_aggregation_service_class):
        """测试更新进度为100"""
        mock_aggregation_service = MagicMock()
        mock_aggregation_service_class.return_value = mock_aggregation_service
        
        result = self.service.update_machine_progress(self.mock_machine, Decimal("100"))
        
        self.assertEqual(self.mock_machine.progress_pct, Decimal("100"))


    # ========== get_machine_bom_list 测试 ==========

    def test_get_machine_bom_list_success(self):
        """测试成功获取BOM列表"""
        # 准备mock BOM数据
        mock_bom1 = MagicMock()
        mock_bom1.id = 1
        mock_bom1.bom_no = "BOM001"
        mock_bom1.bom_name = "主BOM"
        mock_bom1.version = "V1.0"
        mock_bom1.is_latest = True
        mock_bom1.status = "APPROVED"
        mock_bom1.total_items = 50
        mock_bom1.total_amount = Decimal("10000.50")
        
        mock_bom2 = MagicMock()
        mock_bom2.id = 2
        mock_bom2.bom_no = "BOM002"
        mock_bom2.bom_name = "备用BOM"
        mock_bom2.version = "V1.1"
        mock_bom2.is_latest = False
        mock_bom2.status = "DRAFT"
        mock_bom2.total_items = 30
        mock_bom2.total_amount = None  # 测试None的情况
        
        # 配置mock查询
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_bom1, mock_bom2]
        
        # 执行
        result = self.service.get_machine_bom_list(1)
        
        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["bom_no"], "BOM001")
        self.assertEqual(result[0]["total_amount"], 10000.50)
        self.assertEqual(result[1]["bom_no"], "BOM002")
        self.assertEqual(result[1]["total_amount"], 0)  # None转为0

    def test_get_machine_bom_list_empty(self):
        """测试空BOM列表"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []
        
        result = self.service.get_machine_bom_list(1)
        
        self.assertEqual(result, [])


    # ========== check_document_permission 测试 ==========

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_has_permission(self, mock_check_permission):
        """测试有权限的情况"""
        mock_check_permission.return_value = True
        
        result = self.service.check_document_permission(self.mock_user, "CIRCUIT_DIAGRAM")
        
        self.assertTrue(result)
        mock_check_permission.assert_called_once_with(
            self.mock_user, 
            "machine:doc_circuit", 
            self.mock_db
        )

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_no_permission(self, mock_check_permission):
        """测试无权限的情况"""
        mock_check_permission.return_value = False
        
        result = self.service.check_document_permission(self.mock_user, "PLC_PROGRAM")
        
        self.assertFalse(result)

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_unknown_type(self, mock_check_permission):
        """测试未知文档类型（应使用默认权限）"""
        mock_check_permission.return_value = True
        
        result = self.service.check_document_permission(self.mock_user, "UNKNOWN_TYPE")
        
        mock_check_permission.assert_called_once_with(
            self.mock_user, 
            "machine:doc_other",  # 默认权限
            self.mock_db
        )

    @patch('app.core.auth.check_permission')
    def test_check_document_permission_case_insensitive(self, mock_check_permission):
        """测试文档类型不区分大小写"""
        mock_check_permission.return_value = True
        
        result = self.service.check_document_permission(self.mock_user, "circuit_diagram")
        
        # 应该被转为大写后查找
        mock_check_permission.assert_called_once_with(
            self.mock_user, 
            "machine:doc_circuit", 
            self.mock_db
        )


    # ========== upload_document 测试 ==========

    @patch('app.core.auth.check_permission')
    @patch('app.utils.db_helpers.save_obj')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.machine_custom.service.FilePath')
    def test_upload_document_success(self, mock_filepath_class, mock_file, mock_save_obj, mock_check_permission):
        """测试成功上传文档"""
        # 准备
        mock_check_permission.return_value = True
        
        # Mock UploadFile
        file_content = b"test file content"
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.read = AsyncMock(return_value=file_content)
        
        # Mock FilePath行为
        mock_path = MagicMock()
        mock_path.suffix = ".pdf"
        mock_path.parent.mkdir = MagicMock()
        mock_path.relative_to.return_value = FilePath("documents/machines/1/test.pdf")
        mock_filepath_class.return_value = mock_path
        
        # 执行
        import asyncio
        result = asyncio.run(self.service.upload_document(
            machine=self.mock_machine,
            file=mock_upload_file,
            doc_type="CIRCUIT_DIAGRAM",
            user=self.mock_user,
            doc_name="测试文档",
            version="1.0"
        ))
        
        # 验证
        mock_check_permission.assert_called_once()
        mock_save_obj.assert_called_once()
        
        # 验证保存的文档对象
        saved_doc = mock_save_obj.call_args[0][1]
        self.assertEqual(saved_doc.doc_type, "CIRCUIT_DIAGRAM")
        self.assertEqual(saved_doc.doc_name, "测试文档")
        self.assertEqual(saved_doc.machine_id, 1)

    @patch('app.core.auth.check_permission')
    def test_upload_document_invalid_type(self, mock_check_permission):
        """测试无效的文档类型"""
        mock_check_permission.return_value = True
        
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.pdf"
        
        import asyncio
        with self.assertRaises(HTTPException) as context:
            asyncio.run(self.service.upload_document(
                machine=self.mock_machine,
                file=mock_upload_file,
                doc_type="INVALID_TYPE",
                user=self.mock_user
            ))
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("无效的文档类型", context.exception.detail)

    @patch('app.core.auth.check_permission')
    def test_upload_document_no_permission(self, mock_check_permission):
        """测试没有上传权限"""
        mock_check_permission.return_value = False
        
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.pdf"
        
        import asyncio
        with self.assertRaises(HTTPException) as context:
            asyncio.run(self.service.upload_document(
                machine=self.mock_machine,
                file=mock_upload_file,
                doc_type="CIRCUIT_DIAGRAM",
                user=self.mock_user
            ))
        
        self.assertEqual(context.exception.status_code, 403)

    @patch('app.core.auth.check_permission')
    @patch('builtins.open', new_callable=mock_open)
    @patch('app.services.machine_custom.service.FilePath')
    def test_upload_document_file_save_error(self, mock_filepath_class, mock_file, mock_check_permission):
        """测试文件保存失败"""
        mock_check_permission.return_value = True
        
        # Mock文件写入失败
        mock_file.side_effect = IOError("Disk full")
        
        mock_upload_file = AsyncMock(spec=UploadFile)
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.read = AsyncMock(return_value=b"content")
        
        mock_path = MagicMock()
        mock_path.suffix = ".pdf"
        mock_path.parent.mkdir = MagicMock()
        mock_filepath_class.return_value = mock_path
        
        import asyncio
        with self.assertRaises(HTTPException) as context:
            asyncio.run(self.service.upload_document(
                machine=self.mock_machine,
                file=mock_upload_file,
                doc_type="CIRCUIT_DIAGRAM",
                user=self.mock_user
            ))
        
        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("文件保存失败", context.exception.detail)


    # ========== get_machine_documents 测试 ==========

    @patch('app.core.auth.check_permission')
    def test_get_machine_documents_grouped(self, mock_check_permission):
        """测试获取文档列表（按类型分组）"""
        mock_check_permission.return_value = True
        
        # Mock文档
        mock_doc1 = MagicMock()
        mock_doc1.doc_type = "CIRCUIT_DIAGRAM"
        mock_doc1.id = 1
        
        mock_doc2 = MagicMock()
        mock_doc2.doc_type = "CIRCUIT_DIAGRAM"
        mock_doc2.id = 2
        
        mock_doc3 = MagicMock()
        mock_doc3.doc_type = "PLC_PROGRAM"
        mock_doc3.id = 3
        
        # Mock query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_doc1, mock_doc2, mock_doc3]
        
        # 执行
        result = self.service.get_machine_documents(
            machine=self.mock_machine,
            user=self.mock_user,
            group_by_type=True
        )
        
        # 验证
        self.assertEqual(result["machine_id"], 1)
        self.assertEqual(result["total_count"], 3)
        self.assertIn("CIRCUIT_DIAGRAM", result["documents_by_type"])
        self.assertIn("PLC_PROGRAM", result["documents_by_type"])

    @patch('app.core.auth.check_permission')
    def test_get_machine_documents_not_grouped(self, mock_check_permission):
        """测试获取文档列表（不分组）"""
        mock_check_permission.return_value = True
        
        mock_doc1 = MagicMock()
        mock_doc1.doc_type = "CIRCUIT_DIAGRAM"
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_doc1]
        
        result = self.service.get_machine_documents(
            machine=self.mock_machine,
            user=self.mock_user,
            group_by_type=False
        )
        
        self.assertIn("documents", result)
        self.assertNotIn("documents_by_type", result)

    @patch('app.core.auth.check_permission')
    def test_get_machine_documents_filtered_by_permission(self, mock_check_permission):
        """测试文档权限过滤"""
        # 只允许访问CIRCUIT_DIAGRAM
        def check_perm_side_effect(user, perm_code, db):
            return perm_code == "machine:doc_circuit"
        
        mock_check_permission.side_effect = check_perm_side_effect
        
        mock_doc1 = MagicMock()
        mock_doc1.doc_type = "CIRCUIT_DIAGRAM"
        
        mock_doc2 = MagicMock()
        mock_doc2.doc_type = "PLC_PROGRAM"
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_doc1, mock_doc2]
        
        result = self.service.get_machine_documents(
            machine=self.mock_machine,
            user=self.mock_user,
            group_by_type=False
        )
        
        # 应该只返回1个文档（有权限的）
        self.assertEqual(result["total_count"], 1)


    # ========== get_document_download_path 测试 ==========

    @patch('app.core.auth.check_permission')
    @patch('app.services.machine_custom.service.FilePath')
    @patch('app.services.machine_custom.service.settings')
    def test_get_document_download_path_success(self, mock_settings, mock_filepath_class, mock_check_permission):
        """测试成功获取下载路径"""
        mock_check_permission.return_value = True
        
        # Mock document
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        mock_document.file_path = "documents/machines/1/test.pdf"
        mock_document.file_name = "test.pdf"
        
        # Mock paths
        mock_upload_dir = MagicMock()
        mock_settings.UPLOAD_DIR = "/uploads"
        
        mock_file_path = MagicMock()
        mock_file_path.is_absolute.return_value = False
        mock_file_path.resolve.return_value = MagicMock()
        mock_file_path.resolve.return_value.exists.return_value = True
        mock_file_path.resolve.return_value.relative_to.return_value = FilePath("documents/machines/1/test.pdf")
        
        mock_filepath_class.side_effect = [mock_file_path, MagicMock()]
        
        # 执行
        file_path, file_name = self.service.get_document_download_path(mock_document, self.mock_user)
        
        # 验证
        self.assertEqual(file_name, "test.pdf")
        mock_check_permission.assert_called_once()

    @patch('app.core.auth.check_permission')
    def test_get_document_download_path_no_permission(self, mock_check_permission):
        """测试没有下载权限"""
        mock_check_permission.return_value = False
        
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_document_download_path(mock_document, self.mock_user)
        
        self.assertEqual(context.exception.status_code, 403)

    @patch('app.core.auth.check_permission')
    @patch('app.services.machine_custom.service.FilePath')
    @patch('app.services.machine_custom.service.settings')
    def test_get_document_download_path_file_not_exists(self, mock_settings, mock_filepath_class, mock_check_permission):
        """测试文件不存在"""
        mock_check_permission.return_value = True
        
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        mock_document.file_path = "documents/machines/1/test.pdf"
        
        mock_settings.UPLOAD_DIR = "/uploads"
        
        mock_file_path = MagicMock()
        mock_file_path.is_absolute.return_value = False
        mock_file_path.resolve.return_value = MagicMock()
        mock_file_path.resolve.return_value.exists.return_value = False
        mock_file_path.resolve.return_value.relative_to.return_value = FilePath("documents/machines/1/test.pdf")
        
        mock_filepath_class.side_effect = [mock_file_path, MagicMock()]
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_document_download_path(mock_document, self.mock_user)
        
        self.assertEqual(context.exception.status_code, 404)

    @patch('app.core.auth.check_permission')
    @patch('app.services.machine_custom.service.FilePath')
    @patch('app.services.machine_custom.service.settings')
    def test_get_document_download_path_security_check(self, mock_settings, mock_filepath_class, mock_check_permission):
        """测试路径安全检查（防止目录遍历攻击）"""
        mock_check_permission.return_value = True
        
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        mock_document.file_path = "../../etc/passwd"
        
        mock_settings.UPLOAD_DIR = "/uploads"
        
        mock_file_path = MagicMock()
        mock_file_path.is_absolute.return_value = False
        mock_file_path.resolve.return_value = MagicMock()
        mock_file_path.resolve.return_value.relative_to.side_effect = ValueError("Not in upload dir")
        
        mock_upload_dir = MagicMock()
        mock_upload_dir.resolve.return_value = MagicMock()
        
        mock_filepath_class.side_effect = [mock_file_path, mock_upload_dir]
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_document_download_path(mock_document, self.mock_user)
        
        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("访问被拒绝", context.exception.detail)


    # ========== get_document_versions 测试 ==========

    @patch('app.core.auth.check_permission')
    def test_get_document_versions_by_doc_no(self, mock_check_permission):
        """测试通过doc_no获取版本列表"""
        mock_check_permission.return_value = True
        
        # Mock document
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        mock_document.machine_id = 1
        mock_document.doc_no = "DOC001"
        mock_document.doc_name = "测试文档"
        
        # Mock versions
        mock_v1 = MagicMock()
        mock_v1.doc_type = "CIRCUIT_DIAGRAM"
        mock_v2 = MagicMock()
        mock_v2.doc_type = "CIRCUIT_DIAGRAM"
        
        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_v1, mock_v2]
        
        result = self.service.get_document_versions(mock_document, self.mock_user)
        
        self.assertEqual(len(result), 2)

    @patch('app.core.auth.check_permission')
    def test_get_document_versions_by_doc_name(self, mock_check_permission):
        """测试通过doc_name获取版本列表（没有doc_no时）"""
        mock_check_permission.return_value = True
        
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        mock_document.machine_id = 1
        mock_document.doc_no = None  # 没有doc_no
        mock_document.doc_name = "测试文档"
        
        mock_v1 = MagicMock()
        mock_v1.doc_type = "CIRCUIT_DIAGRAM"
        
        mock_query = MagicMock()
        mock_filter1 = MagicMock()
        mock_filter2 = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = [mock_v1]
        
        result = self.service.get_document_versions(mock_document, self.mock_user)
        
        self.assertEqual(len(result), 1)

    @patch('app.core.auth.check_permission')
    def test_get_document_versions_no_permission(self, mock_check_permission):
        """测试没有查看版本权限"""
        mock_check_permission.return_value = False
        
        mock_document = MagicMock()
        mock_document.doc_type = "CIRCUIT_DIAGRAM"
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_document_versions(mock_document, self.mock_user)
        
        self.assertEqual(context.exception.status_code, 403)


    # ========== get_service_history 测试 ==========

    @patch('app.services.machine_custom.service.apply_pagination')
    def test_get_service_history_success(self, mock_apply_pagination):
        """测试成功获取服务历史"""
        # Mock service records
        mock_record1 = MagicMock()
        mock_record1.id = 1
        mock_record1.record_no = "SR001"
        mock_record1.service_type = "MAINTENANCE"
        mock_record1.service_date = datetime(2024, 1, 15)
        mock_record1.service_content = "定期保养"
        mock_record1.service_result = "正常"
        mock_record1.issues_found = None
        mock_record1.solution_provided = None
        mock_record1.duration_hours = Decimal("2.5")
        mock_record1.service_engineer_name = "工程师A"
        mock_record1.customer_satisfaction = 5
        mock_record1.customer_feedback = "很满意"
        mock_record1.location = "客户现场"
        mock_record1.created_at = datetime(2024, 1, 15, 10, 0)
        
        mock_record2 = MagicMock()
        mock_record2.id = 2
        mock_record2.record_no = "SR002"
        mock_record2.service_type = "REPAIR"
        mock_record2.service_date = datetime(2024, 2, 10)
        mock_record2.service_content = "故障维修"
        mock_record2.service_result = "已修复"
        mock_record2.issues_found = "电机故障"
        mock_record2.solution_provided = "更换电机"
        mock_record2.duration_hours = Decimal("4.0")
        mock_record2.service_engineer_name = "工程师B"
        mock_record2.customer_satisfaction = 4
        mock_record2.customer_feedback = "满意"
        mock_record2.location = "客户现场"
        mock_record2.created_at = datetime(2024, 2, 10, 14, 0)
        
        # Mock query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 2
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = [mock_record1, mock_record2]
        
        # 执行
        result = self.service.get_service_history(self.mock_machine, page=1, page_size=20)
        
        # 验证
        self.assertEqual(result["machine_id"], 1)
        self.assertEqual(result["machine_no"], "MN001")
        self.assertEqual(result["summary"]["total_records"], 2)
        self.assertEqual(result["summary"]["total_service_hours"], 6.5)
        self.assertEqual(result["summary"]["avg_satisfaction"], 4.5)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["record_no"], "SR001")

    @patch('app.services.machine_custom.service.apply_pagination')
    def test_get_service_history_empty(self, mock_apply_pagination):
        """测试空服务历史"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 0
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = []
        
        result = self.service.get_service_history(self.mock_machine)
        
        self.assertEqual(result["summary"]["total_records"], 0)
        self.assertEqual(result["summary"]["total_service_hours"], 0)
        self.assertIsNone(result["summary"]["avg_satisfaction"])
        self.assertEqual(len(result["items"]), 0)

    @patch('app.services.machine_custom.service.apply_pagination')
    def test_get_service_history_pagination(self, mock_apply_pagination):
        """测试分页功能"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 50
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = []
        
        result = self.service.get_service_history(self.mock_machine, page=2, page_size=10)
        
        # 验证分页参数
        mock_apply_pagination.assert_called_once_with(mock_order, 10, 10)  # offset=10, limit=10
        self.assertEqual(result["pagination"]["page"], 2)
        self.assertEqual(result["pagination"]["page_size"], 10)
        self.assertEqual(result["pagination"]["total"], 50)
        self.assertEqual(result["pagination"]["pages"], 5)

    @patch('app.services.machine_custom.service.apply_pagination')
    def test_get_service_history_no_satisfaction(self, mock_apply_pagination):
        """测试没有满意度评分的情况"""
        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.record_no = "SR001"
        mock_record.service_type = "MAINTENANCE"
        mock_record.service_date = datetime(2024, 1, 15)
        mock_record.service_content = "定期保养"
        mock_record.service_result = "正常"
        mock_record.issues_found = None
        mock_record.solution_provided = None
        mock_record.duration_hours = Decimal("2.5")
        mock_record.service_engineer_name = "工程师A"
        mock_record.customer_satisfaction = None  # 没有评分
        mock_record.customer_feedback = None
        mock_record.location = "客户现场"
        mock_record.created_at = datetime(2024, 1, 15, 10, 0)
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 1
        mock_filter.order_by.return_value = mock_order
        mock_apply_pagination.return_value = mock_order
        mock_order.all.return_value = [mock_record]
        
        result = self.service.get_service_history(self.mock_machine)
        
        self.assertIsNone(result["summary"]["avg_satisfaction"])


class TestDocTypePermissionMap(unittest.TestCase):
    """测试文档类型权限映射"""

    def test_all_doc_types_mapped(self):
        """测试所有定义的文档类型都有权限映射"""
        expected_types = [
            "CIRCUIT_DIAGRAM", "PLC_PROGRAM", "LABELWORK_PROGRAM",
            "VISION_PROGRAM", "MOTION_PROGRAM", "ROBOT_PROGRAM",
            "OPERATION_MANUAL", "DRAWING", "BOM_DOCUMENT",
            "FAT_DOCUMENT", "SAT_DOCUMENT", "OTHER"
        ]
        
        for doc_type in expected_types:
            self.assertIn(doc_type, DOC_TYPE_PERMISSION_MAP)

    def test_permission_codes_format(self):
        """测试权限代码格式正确"""
        for doc_type, perm_code in DOC_TYPE_PERMISSION_MAP.items():
            self.assertTrue(perm_code.startswith("machine:doc_"))


if __name__ == "__main__":
    unittest.main()
