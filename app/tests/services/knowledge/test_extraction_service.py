# -*- coding: utf-8 -*-
"""
KnowledgeExtractionService 测试
经验教训自动提取服务
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock, patch

from app.services.knowledge.extraction_service import KnowledgeExtractionService
from app.models.knowledge_base import KnowledgeEntry, KnowledgeTypeEnum, KnowledgeStatusEnum


class TestKnowledgeExtractionService:
    """知识提取服务测试"""

    def test_extract_all_project_not_found(self, db_session):
        """
        测试项目不存在时的错误处理
        """
        # 模拟查询返回 None（项目不存在）
        mock_project_query = MagicMock()
        mock_project_query.filter.return_value.first.return_value = None
        
        with patch.object(db_session, 'query', return_value=mock_project_query):
            service = KnowledgeExtractionService(db_session)
            
            with pytest.raises(ValueError, match="项目 999 不存在"):
                service.extract_all(project_id=999)

    def test_generate_code_format(self, db_session):
        """
        测试知识编号生成格式
        """
        # 模拟没有已有编号的情况
        mock_ke_query = MagicMock()
        mock_ke_query.filter.return_value.order_by.return_value.first.return_value = None
        
        with patch.object(db_session, 'query', return_value=mock_ke_query):
            service = KnowledgeExtractionService(db_session)
            code = service._generate_code()
            
            # 验证格式 KE-YYYYMMDD-NNN (如 KE-20260406-001)
            assert code.startswith("KE-")
            assert len(code) == 15  # KE-YYYYMMDD-NNN (3+8+3=14, 实际是15)

    def test_generate_code_increments(self, db_session):
        """
        测试知识编号自动递增
        """
        # 模拟已有编号 - 使用当前日期
        today = datetime.now().strftime("%Y%m%d")
        
        mock_old_entry = MagicMock()
        mock_old_entry.entry_code = f"KE-{today}-001"
        
        mock_ke_query = MagicMock()
        mock_ke_query.filter.return_value.order_by.return_value.first.return_value = mock_old_entry
        
        with patch.object(db_session, 'query', return_value=mock_ke_query):
            service = KnowledgeExtractionService(db_session)
            code = service._generate_code()
            
            # 验证递增
            assert code == f"KE-{today}-002"

    def test_build_risk_tags(self, db_session):
        """
        测试风险标签构建
        """
        service = KnowledgeExtractionService(db_session)
        
        # 创建模拟的风险对象
        mock_risk = MagicMock()
        mock_risk.risk_type = "SUPPLY"
        mock_risk.risk_level = "HIGH"
        
        mock_project = MagicMock()
        mock_project.project_type = "非标设备"
        mock_project.product_category = "ICT"
        
        tags = service._build_risk_tags(mock_risk, mock_project)
        
        assert "风险经验" in tags
        assert "SUPPLY" in tags
        assert "HIGH" in tags
        assert "非标设备" in tags
        assert "ICT" in tags

    def test_build_issue_tags(self, db_session):
        """
        测试问题标签构建
        """
        service = KnowledgeExtractionService(db_session)
        
        # 创建模拟的问题对象
        mock_issue = MagicMock()
        mock_issue.category = "技术问题"
        mock_issue.severity = "HIGH"
        
        mock_project = MagicMock()
        mock_project.project_type = "非标设备"
        mock_project.product_category = "ICT"
        
        tags = service._build_issue_tags(mock_issue, mock_project)
        
        assert "问题方案" in tags
        assert "技术问题" in tags
        assert "HIGH" in tags

    def test_build_ecn_tags(self, db_session):
        """
        测试变更单标签构建
        """
        service = KnowledgeExtractionService(db_session)
        
        mock_project = MagicMock()
        mock_project.project_type = "非标设备"
        mock_project.product_category = "ICT"
        
        # 测试高频变更（>=3次）
        mock_group = [MagicMock(), MagicMock(), MagicMock()]
        tags = service._build_ecn_tags("设计变更", mock_group, mock_project)
        
        assert "变更分析" in tags
        assert "设计变更" in tags
        assert "高频变更" in tags