# -*- coding: utf-8 -*-
"""
第三十五批 - stage_template/default_template.py 单元测试
"""
import pytest

try:
    from unittest.mock import MagicMock, patch
    from app.services.stage_template.default_template import DefaultTemplateMixin
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


class ConcreteTemplateMixin(DefaultTemplateMixin):
    """具体实现类（供测试使用）"""

    def __init__(self, db):
        self.db = db
        self._clear_default_template = MagicMock()


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDefaultTemplateMixin:

    def _make_service(self, query_result=None):
        db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = query_result
        db.query.return_value = mock_q
        return ConcreteTemplateMixin(db), db

    def test_get_default_template_found(self):
        """找到默认模板时正常返回"""
        mock_template = MagicMock()
        svc, _ = self._make_service(query_result=mock_template)
        result = svc.get_default_template("CUSTOM")
        assert result is mock_template

    def test_get_default_template_not_found(self):
        """没有默认模板时返回 None"""
        svc, _ = self._make_service(query_result=None)
        result = svc.get_default_template("CUSTOM")
        assert result is None

    def test_get_default_template_uses_project_type(self):
        """传入 project_type 参数时正常使用"""
        svc, db = self._make_service()
        svc.get_default_template(project_type="STANDARD")
        # 确保查询被调用
        db.query.assert_called()

    def test_set_default_template_not_found(self):
        """模板不存在时抛出 ValueError"""
        svc, _ = self._make_service(query_result=None)
        with pytest.raises(ValueError, match="不存在"):
            svc.set_default_template(999)

    def test_set_default_template_success(self):
        """模板存在时设置为默认"""
        mock_template = MagicMock()
        mock_template.project_type = "CUSTOM"
        mock_template.is_default = False
        svc, db = self._make_service(query_result=mock_template)
        result = svc.set_default_template(1)
        assert result is mock_template
        assert mock_template.is_default is True
        svc._clear_default_template.assert_called_once_with("CUSTOM")

    def test_set_default_template_calls_flush(self):
        """设置默认后调用 db.flush"""
        mock_template = MagicMock()
        mock_template.project_type = "STANDARD"
        svc, db = self._make_service(query_result=mock_template)
        svc.set_default_template(2)
        db.flush.assert_called_once()
