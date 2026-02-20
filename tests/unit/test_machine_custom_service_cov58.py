# -*- coding: utf-8 -*-
"""
机台定制服务单元测试

覆盖 MachineCustomService 的核心业务逻辑
"""

import unittest
from decimal import Decimal
from pathlib import Path as FilePath
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
from datetime import datetime

from fastapi import HTTPException, UploadFile

from app.services.machine_custom.service import MachineCustomService


class TestMachineCustomService(unittest.TestCase):
    """机台定制服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = MachineCustomService(self.db)

    def test_update_machine_progress_success(self):
        """测试更新机台进度成功"""
        # 准备数据
        machine = MagicMock()
        machine.project_id = 1
        machine.progress_pct = Decimal("0")
        new_progress = Decimal("75.5")

        # Mock save_obj
        with patch("app.services.machine_custom.service.save_obj") as mock_save:
            with patch("app.services.machine_custom.service.ProjectAggregationService") as MockAggService:
                mock_agg_service = MockAggService.return_value
                
                # 执行
                result = self.service.update_machine_progress(machine, new_progress)
                
                # 验证
                self.assertEqual(machine.progress_pct, new_progress)
                mock_save.assert_called_once_with(self.db, machine)
                MockAggService.assert_called_once_with(self.db)
                mock_agg_service.update_project_aggregation.assert_called_once_with(1)
                self.assertEqual(result, machine)

    def test_get_machine_bom_list_success(self):
        """测试获取机台BOM列表成功"""
        # 准备mock BOM数据
        mock_bom1 = MagicMock()
        mock_bom1.id = 1
        mock_bom1.bom_no = "BOM-001"
        mock_bom1.bom_name = "主BOM"
        mock_bom1.version = "1.0"
        mock_bom1.is_latest = True
        mock_bom1.status = "APPROVED"
        mock_bom1.total_items = 10
        mock_bom1.total_amount = Decimal("5000.50")

        mock_bom2 = MagicMock()
        mock_bom2.id = 2
        mock_bom2.bom_no = "BOM-002"
        mock_bom2.bom_name = "副BOM"
        mock_bom2.version = "1.1"
        mock_bom2.is_latest = False
        mock_bom2.status = "DRAFT"
        mock_bom2.total_items = 5
        mock_bom2.total_amount = None

        mock_query = self.db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_bom1, mock_bom2
        ]

        # 执行
        result = self.service.get_machine_bom_list(machine_id=100)

        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["bom_no"], "BOM-001")
        self.assertEqual(result[0]["total_amount"], 5000.50)
        self.assertEqual(result[1]["total_amount"], 0)

    def test_check_document_permission_granted(self):
        """测试文档权限检查 - 有权限"""
        user = MagicMock()
        doc_type = "CIRCUIT_DIAGRAM"

        with patch("app.services.machine_custom.service.check_permission") as mock_check:
            mock_check.return_value = True
            
            result = self.service.check_document_permission(user, doc_type)
            
            self.assertTrue(result)
            mock_check.assert_called_once_with(user, "machine:doc_circuit", self.db)

    def test_check_document_permission_denied(self):
        """测试文档权限检查 - 无权限"""
        user = MagicMock()
        doc_type = "PLC_PROGRAM"

        with patch("app.services.machine_custom.service.check_permission") as mock_check:
            mock_check.return_value = False
            
            result = self.service.check_document_permission(user, doc_type)
            
            self.assertFalse(result)
            mock_check.assert_called_once_with(user, "machine:doc_plc", self.db)

    @patch("app.services.machine_custom.service.save_obj")
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.services.machine_custom.service.FilePath")
    async def test_upload_document_success(self, mock_path_class, mock_file, mock_save):
        """测试上传文档成功"""
        # 准备数据
        machine = MagicMock()
        machine.id = 10
        machine.project_id = 1

        file = MagicMock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        file.read = AsyncMock(return_value=b"fake file content")

        user = MagicMock()
        user.id = 5

        # Mock路径
        mock_file_path = MagicMock()
        mock_file_path.suffix = ".pdf"
        mock_file_path.parent.mkdir = MagicMock()
        mock_path_class.return_value = mock_file_path

        # Mock权限检查
        with patch.object(self.service, "check_document_permission", return_value=True):
            with patch("app.services.machine_custom.service.uuid.uuid4", return_value="test-uuid"):
                with patch("app.services.machine_custom.service.settings") as mock_settings:
                    mock_settings.UPLOAD_DIR = "/upload"
                    mock_file_path.relative_to.return_value = FilePath("documents/machines/10/test-uuid.pdf")
                    
                    # 执行
                    result = await self.service.upload_document(
                        machine=machine,
                        file=file,
                        doc_type="CIRCUIT_DIAGRAM",
                        user=user,
                        version="1.0"
                    )
                    
                    # 验证
                    self.assertIsNotNone(result)
                    mock_save.assert_called_once()
                    file.read.assert_called_once()

    @patch("app.services.machine_custom.service.save_obj")
    async def test_upload_document_invalid_type(self, mock_save):
        """测试上传文档 - 无效类型"""
        machine = MagicMock()
        file = MagicMock()
        user = MagicMock()

        with self.assertRaises(HTTPException) as context:
            await self.service.upload_document(
                machine=machine,
                file=file,
                doc_type="INVALID_TYPE",
                user=user
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("无效的文档类型", context.exception.detail)

    @patch("app.services.machine_custom.service.save_obj")
    async def test_upload_document_permission_denied(self, mock_save):
        """测试上传文档 - 权限不足"""
        machine = MagicMock()
        file = MagicMock()
        user = MagicMock()

        with patch.object(self.service, "check_document_permission", return_value=False):
            with self.assertRaises(HTTPException) as context:
                await self.service.upload_document(
                    machine=machine,
                    file=file,
                    doc_type="CIRCUIT_DIAGRAM",
                    user=user
                )
            
            self.assertEqual(context.exception.status_code, 403)
            self.assertIn("没有权限", context.exception.detail)

    def test_get_machine_documents_grouped(self):
        """测试获取机台文档列表 - 按类型分组"""
        machine = MagicMock()
        machine.id = 10
        machine.machine_code = "M-001"
        machine.machine_name = "测试机台"

        user = MagicMock()

        # Mock文档数据
        doc1 = MagicMock()
        doc1.doc_type = "CIRCUIT_DIAGRAM"
        doc2 = MagicMock()
        doc2.doc_type = "CIRCUIT_DIAGRAM"
        doc3 = MagicMock()
        doc3.doc_type = "PLC_PROGRAM"

        mock_query = self.db.query.return_value
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            doc1, doc2, doc3
        ]

        with patch.object(self.service, "check_document_permission", return_value=True):
            with patch("app.services.machine_custom.service.ProjectDocumentResponse") as MockResponse:
                MockResponse.model_validate.side_effect = lambda x: x
                
                result = self.service.get_machine_documents(
                    machine=machine,
                    user=user,
                    group_by_type=True
                )
                
                self.assertEqual(result["machine_id"], 10)
                self.assertEqual(result["total_count"], 3)
                self.assertIn("documents_by_type", result)
                self.assertEqual(len(result["documents_by_type"]["CIRCUIT_DIAGRAM"]), 2)
                self.assertEqual(len(result["documents_by_type"]["PLC_PROGRAM"]), 1)

    def test_get_document_download_path_success(self):
        """测试获取文档下载路径成功"""
        document = MagicMock()
        document.doc_type = "CIRCUIT_DIAGRAM"
        document.file_path = "documents/test.pdf"
        document.file_name = "test.pdf"

        user = MagicMock()

        with patch.object(self.service, "check_document_permission", return_value=True):
            with patch("app.services.machine_custom.service.FilePath") as MockPath:
                with patch("app.services.machine_custom.service.settings") as mock_settings:
                    mock_settings.UPLOAD_DIR = "/upload"
                    
                    mock_file = MagicMock()
                    mock_file.is_absolute.return_value = False
                    mock_file.exists.return_value = True
                    mock_file.resolve.return_value = mock_file
                    mock_file.relative_to.return_value = mock_file
                    
                    mock_upload = MagicMock()
                    mock_upload.resolve.return_value = mock_upload
                    
                    MockPath.side_effect = [mock_file, mock_upload]
                    
                    path, filename = self.service.get_document_download_path(document, user)
                    
                    self.assertEqual(filename, "test.pdf")

    def test_get_document_download_path_permission_denied(self):
        """测试获取文档下载路径 - 权限不足"""
        document = MagicMock()
        document.doc_type = "CIRCUIT_DIAGRAM"
        user = MagicMock()

        with patch.object(self.service, "check_document_permission", return_value=False):
            with self.assertRaises(HTTPException) as context:
                self.service.get_document_download_path(document, user)
            
            self.assertEqual(context.exception.status_code, 403)

    def test_get_document_versions_success(self):
        """测试获取文档版本列表成功"""
        document = MagicMock()
        document.machine_id = 10
        document.doc_type = "CIRCUIT_DIAGRAM"
        document.doc_no = "DOC-001"

        user = MagicMock()

        # Mock版本数据
        v1 = MagicMock()
        v1.doc_type = "CIRCUIT_DIAGRAM"
        v2 = MagicMock()
        v2.doc_type = "CIRCUIT_DIAGRAM"

        mock_query = self.db.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            v1, v2
        ]

        with patch.object(self.service, "check_document_permission", return_value=True):
            result = self.service.get_document_versions(document, user)
            
            self.assertEqual(len(result), 2)

    def test_get_service_history_success(self):
        """测试获取服务历史记录成功"""
        machine = MagicMock()
        machine.id = 10
        machine.machine_no = "M-001"
        machine.machine_name = "测试机台"

        # Mock服务记录
        record1 = MagicMock()
        record1.id = 1
        record1.record_no = "SR-001"
        record1.service_type = "MAINTENANCE"
        record1.service_date = datetime(2024, 1, 1)
        record1.service_content = "日常维护"
        record1.service_result = "正常"
        record1.issues_found = None
        record1.solution_provided = None
        record1.duration_hours = Decimal("2.5")
        record1.service_engineer_name = "张三"
        record1.customer_satisfaction = 5
        record1.customer_feedback = "很好"
        record1.location = "车间A"
        record1.created_at = datetime(2024, 1, 1)

        mock_query = self.db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1

        with patch("app.services.machine_custom.service.apply_pagination") as mock_pagination:
            mock_pagination.return_value.all.return_value = [record1]
            
            result = self.service.get_service_history(machine, page=1, page_size=20)
            
            self.assertEqual(result["machine_id"], 10)
            self.assertEqual(result["summary"]["total_records"], 1)
            self.assertEqual(result["summary"]["total_service_hours"], 2.5)
            self.assertEqual(result["summary"]["avg_satisfaction"], 5.0)
            self.assertEqual(len(result["items"]), 1)
            self.assertEqual(result["items"][0]["record_no"], "SR-001")


if __name__ == "__main__":
    unittest.main()
