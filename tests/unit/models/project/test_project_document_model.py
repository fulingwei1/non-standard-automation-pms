# -*- coding: utf-8 -*-
"""
ProjectDocument Model 测试
"""

import pytest
from datetime import datetime
from app.models.project.document import ProjectDocument


class TestProjectDocumentModel:
    """ProjectDocument 模型测试"""

    def test_create_document(self, db_session, sample_project, sample_user):
        """测试创建项目文档"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="需求规格说明书.docx",
            doc_type="需求文档",
            file_path="/uploads/docs/req_spec.docx",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.id is not None
        assert doc.document_name == "需求规格说明书.docx"
        assert doc.document_type == "需求文档"
        assert doc.file_path == "/uploads/docs/req_spec.docx"

    def test_document_project_relationship(self, db_session, sample_project, sample_user):
        """测试文档-项目关系"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="设计文档.pdf",
            doc_type="设计",
            file_path="/uploads/design.pdf",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        db_session.refresh(doc)
        assert doc.project is not None
        assert doc.project.project_code == "PRJ001"

    def test_document_uploader_relationship(self, db_session, sample_project, sample_user):
        """测试文档-上传者关系"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="测试报告.xlsx",
            doc_type="测试",
            file_path="/uploads/test_report.xlsx",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        db_session.refresh(doc)
        assert doc.uploader is not None
        assert doc.uploader.username == "testuser"

    def test_document_file_size(self, db_session, sample_project, sample_user):
        """测试文档文件大小"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="架构图.png",
            doc_type="设计",
            file_path="/uploads/arch.png",
            file_size=2048576,  # 2MB
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.file_size == 2048576
        # 转换为MB
        size_mb = doc.file_size / (1024 * 1024)
        assert size_mb == 2.0

    def test_document_version(self, db_session, sample_project, sample_user):
        """测试文档版本"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="接口文档",
            doc_type="技术文档",
            file_path="/uploads/api_v1.md",
            version="1.0",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.version == "1.0"
        
        doc.version = "1.1"
        db_session.commit()
        
        db_session.refresh(doc)
        assert doc.version == "1.1"

    def test_document_description(self, db_session, sample_project, sample_user):
        """测试文档描述"""
        desc = "项目初期需求分析文档，包含业务流程和功能清单"
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="需求分析",
            doc_type="需求",
            file_path="/uploads/req.docx",
            description=desc,
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.description == desc

    def test_document_category(self, db_session, sample_project, sample_user):
        """测试文档分类"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="会议纪要",
            doc_type="会议记录",
            file_path="/uploads/meeting_20260221.docx",
            category="管理",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.category == "管理"

    def test_document_update(self, db_session, sample_project, sample_user):
        """测试更新文档"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="初稿",
            doc_type="草稿",
            file_path="/uploads/draft.docx",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        doc.document_name = "最终版"
        doc.document_type = "正式文档"
        doc.file_path = "/uploads/final.docx"
        db_session.commit()
        
        db_session.refresh(doc)
        assert doc.document_name == "最终版"
        assert doc.document_type == "正式文档"

    def test_document_delete(self, db_session, sample_project, sample_user):
        """测试删除文档"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="临时文档",
            doc_type="临时",
            file_path="/uploads/temp.txt",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        doc_id = doc.id
        
        db_session.delete(doc)
        db_session.commit()
        
        deleted = db_session.query(ProjectDocument).filter_by(id=doc_id).first()
        assert deleted is None

    def test_multiple_documents_same_project(self, db_session, sample_project, sample_user):
        """测试同一项目多个文档"""
        docs = [
            ProjectDocument(
                project_id=sample_project.id,
                doc_name=f"文档{i}.pdf",
                doc_type="技术",
                file_path=f"/uploads/doc{i}.pdf",
                uploaded_by=sample_user.id
            ) for i in range(1, 6)
        ]
        db_session.add_all(docs)
        db_session.commit()
        
        result = db_session.query(ProjectDocument).filter_by(
            project_id=sample_project.id
        ).all()
        assert len(result) == 5

    def test_document_timestamp(self, db_session, sample_project, sample_user):
        """测试文档时间戳"""
        doc = ProjectDocument(
            project_id=sample_project.id,
            doc_name="时间戳测试",
            doc_type="测试",
            file_path="/uploads/ts.txt",
            uploaded_by=sample_user.id
        )
        db_session.add(doc)
        db_session.commit()
        
        assert doc.created_at is not None
        assert isinstance(doc.created_at, datetime)
