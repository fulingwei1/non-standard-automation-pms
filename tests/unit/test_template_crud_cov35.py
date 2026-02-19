# -*- coding: utf-8 -*-
"""
第三十五批 - stage_template/template_crud.py (TemplateCrudMixin) 单元测试
"""
import pytest

try:
    from unittest.mock import MagicMock, call, patch
    from app.services.stage_template.template_crud import TemplateCrudMixin
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


class ConcreteCrud(TemplateCrudMixin):
    def __init__(self, db):
        self.db = db
        self._clear_default_template = MagicMock()
        self.add_stage = MagicMock(return_value=MagicMock(id=99, nodes=[]))
        self.add_node = MagicMock(return_value=MagicMock(id=88))


def _make_db(first_result=None, all_result=None, count_result=0):
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.options.return_value = q
    q.order_by.return_value = q
    q.first.return_value = first_result
    q.all.return_value = all_result or []
    q.count.return_value = count_result
    db.query.return_value = q
    return db


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestTemplateCrudMixin:

    def test_create_template_duplicate_code_raises(self):
        """模板编码重复时抛出 ValueError"""
        existing = MagicMock()
        db = _make_db(first_result=existing)
        svc = ConcreteCrud(db)
        with pytest.raises(ValueError, match="已存在"):
            svc.create_template("DUP001", "重复模板")

    def test_create_template_success(self):
        """正常创建模板（mock StageTemplate）"""
        db = _make_db(first_result=None)
        svc = ConcreteCrud(db)
        with patch("app.services.stage_template.template_crud.StageTemplate") as MockTemplate:
            mock_instance = MagicMock()
            MockTemplate.return_value = mock_instance
            result = svc.create_template("NEW001", "新模板")
        db.add.assert_called_once_with(mock_instance)
        db.flush.assert_called_once()

    def test_get_template_not_found(self):
        """模板不存在时返回 None"""
        db = _make_db(first_result=None)
        svc = ConcreteCrud(db)
        result = svc.get_template(9999)
        assert result is None

    def test_get_template_found(self):
        """模板存在时返回模板"""
        mock_tmpl = MagicMock()
        db = _make_db(first_result=mock_tmpl)
        svc = ConcreteCrud(db)
        result = svc.get_template(1)
        assert result is mock_tmpl

    def test_list_templates_all(self):
        """列出所有模板"""
        templates = [MagicMock(), MagicMock()]
        db = _make_db(all_result=templates)
        svc = ConcreteCrud(db)
        result = svc.list_templates()
        assert len(result) == 2

    def test_delete_template_not_found(self):
        """删除不存在的模板返回 False"""
        db = _make_db(first_result=None)
        svc = ConcreteCrud(db)
        result = svc.delete_template(99)
        assert result is False

    def test_delete_template_in_use_raises(self):
        """模板被项目使用时抛出 ValueError"""
        mock_tmpl = MagicMock()
        db = _make_db(first_result=mock_tmpl, count_result=3)
        svc = ConcreteCrud(db)
        with pytest.raises(ValueError, match="使用"):
            svc.delete_template(1)

    def test_delete_template_success(self):
        """模板未被使用时成功删除"""
        mock_tmpl = MagicMock()
        db = _make_db(first_result=mock_tmpl, count_result=0)
        svc = ConcreteCrud(db)
        result = svc.delete_template(1)
        assert result is True
        db.delete.assert_called_once_with(mock_tmpl)

    def test_update_template_not_found(self):
        """更新不存在的模板返回 None"""
        db = _make_db(first_result=None)
        svc = ConcreteCrud(db)
        result = svc.update_template(99, template_name="新名称")
        assert result is None

    def test_update_template_success(self):
        """更新模板字段"""
        mock_tmpl = MagicMock()
        mock_tmpl.is_default = False
        mock_tmpl.project_type = "CUSTOM"
        mock_tmpl.template_name = "旧名称"
        db = _make_db(first_result=mock_tmpl)
        svc = ConcreteCrud(db)
        result = svc.update_template(1, template_name="新名称")
        assert result is mock_tmpl
        db.flush.assert_called()
