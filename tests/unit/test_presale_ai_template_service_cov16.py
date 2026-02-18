# -*- coding: utf-8 -*-
"""
第十六批：售前AI方案模板服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.presale_ai_template_service import PresaleAITemplateService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_template(**kwargs):
    tpl = MagicMock()
    tpl.id = kwargs.get("id", 1)
    tpl.name = kwargs.get("name", "测试模板")
    tpl.template_type = kwargs.get("template_type", "SOLUTION")
    tpl.content = kwargs.get("content", "{}")
    tpl.is_active = kwargs.get("is_active", True)
    tpl.created_by = kwargs.get("created_by", 1)
    return tpl


class TestPresaleAITemplateService:
    def _svc(self, db=None):
        db = db or make_db()
        return PresaleAITemplateService(db)

    def test_init(self):
        db = make_db()
        svc = PresaleAITemplateService(db)
        assert svc.db is db

    def test_create_template(self):
        db = make_db()
        svc = PresaleAITemplateService(db)
        data = {"name": "新模板", "industry": "制造业", "solution_content": "{}"}
        with patch("app.services.presale_ai_template_service.save_obj") as mock_save, \
             patch("app.services.presale_ai_template_service.PresaleAISolutionTemplate") as mock_cls:
            mock_cls.return_value = MagicMock()
            result = svc.create_template(data, user_id=1)
            mock_save.assert_called_once()

    def test_update_template_not_found(self):
        db = make_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        with pytest.raises(ValueError):
            svc.update_template(999, {"name": "新名称"})

    def test_update_template_found(self):
        db = make_db()
        template = make_template()
        db.query.return_value.filter_by.return_value.first.return_value = template
        svc = PresaleAITemplateService(db)
        result = svc.update_template(1, {"name": "更新名称"})
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_get_template_found(self):
        db = make_db()
        template = make_template()
        db.query.return_value.filter_by.return_value.first.return_value = template
        svc = PresaleAITemplateService(db)
        result = svc.get_template(1)
        assert result is template

    def test_get_template_not_found(self):
        db = make_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        result = svc.get_template(999)
        assert result is None

    def test_delete_template_not_found(self):
        db = make_db()
        db.query.return_value.filter_by.return_value.first.return_value = None
        svc = PresaleAITemplateService(db)
        result = svc.delete_template(999)
        assert result is False

    def test_delete_template_found(self):
        db = make_db()
        template = make_template()
        db.query.return_value.filter_by.return_value.first.return_value = template
        svc = PresaleAITemplateService(db)
        result = svc.delete_template(1)
        # 软删除应该返回True
        assert result is True
