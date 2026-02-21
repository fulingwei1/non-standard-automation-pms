# -*- coding: utf-8 -*-
"""
数据库辅助函数全面测试

测试 app/utils/db_helpers.py 中的所有函数
"""
import pytest
from unittest.mock import Mock, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils.db_helpers import (
    get_or_404,
    save_obj,
    delete_obj,
    update_obj,
    safe_commit,
)


class TestGetOr404:
    """测试get_or_404函数"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.__name__ = "TestModel"
        model.id = Mock()
        return model
    
    def test_find_existing_object(self, mock_db, mock_model):
        """测试查找存在的对象"""
        mock_obj = Mock()
        mock_query = Mock()
        mock_query.filter().first.return_value = mock_obj
        mock_db.query.return_value = mock_query
        
        result = get_or_404(mock_db, mock_model, 123)
        
        assert result == mock_obj
        mock_db.query.assert_called_once_with(mock_model)
    
    def test_object_not_found_raises_404(self, mock_db, mock_model):
        """测试对象不存在时抛出404"""
        mock_query = Mock()
        mock_query.filter().first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(mock_db, mock_model, 123)
        
        assert exc_info.value.status_code == 404
        assert "TestModel" in exc_info.value.detail
        assert "123" in exc_info.value.detail
    
    def test_custom_detail_message(self, mock_db, mock_model):
        """测试自定义错误消息"""
        mock_query = Mock()
        mock_query.filter().first.return_value = None
        mock_db.query.return_value = mock_query
        
        custom_message = "自定义的未找到消息"
        
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(mock_db, mock_model, 123, detail=custom_message)
        
        assert exc_info.value.detail == custom_message
    
    def test_custom_id_field(self, mock_db, mock_model):
        """测试自定义ID字段"""
        mock_obj = Mock()
        mock_model.uuid = Mock()
        mock_query = Mock()
        mock_query.filter().first.return_value = mock_obj
        mock_db.query.return_value = mock_query
        
        result = get_or_404(mock_db, mock_model, "abc-123", id_field="uuid")
        
        assert result == mock_obj
    
    def test_custom_id_field_not_found(self, mock_db, mock_model):
        """测试自定义ID字段未找到"""
        mock_model.uuid = Mock()
        mock_query = Mock()
        mock_query.filter().first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(mock_db, mock_model, "abc-123", id_field="uuid")
        
        assert "uuid=abc-123" in exc_info.value.detail


class TestSaveObj:
    """测试save_obj函数"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    def test_save_with_refresh(self, mock_db):
        """测试保存并刷新"""
        mock_obj = Mock()
        
        result = save_obj(mock_db, mock_obj)
        
        mock_db.add.assert_called_once_with(mock_obj)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_obj)
        assert result == mock_obj
    
    def test_save_without_refresh(self, mock_db):
        """测试保存不刷新"""
        mock_obj = Mock()
        
        result = save_obj(mock_db, mock_obj, refresh=False)
        
        mock_db.add.assert_called_once_with(mock_obj)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_not_called()
        assert result == mock_obj
    
    def test_save_raises_exception_on_commit(self, mock_db):
        """测试提交时抛出异常"""
        mock_obj = Mock()
        mock_db.commit.side_effect = Exception("数据库错误")
        
        with pytest.raises(Exception, match="数据库错误"):
            save_obj(mock_db, mock_obj)
        
        mock_db.add.assert_called_once()


class TestDeleteObj:
    """测试delete_obj函数"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    def test_delete_object(self, mock_db):
        """测试删除对象"""
        mock_obj = Mock()
        
        delete_obj(mock_db, mock_obj)
        
        mock_db.delete.assert_called_once_with(mock_obj)
        mock_db.commit.assert_called_once()
    
    def test_delete_raises_exception_on_commit(self, mock_db):
        """测试提交时抛出异常"""
        mock_obj = Mock()
        mock_db.commit.side_effect = Exception("删除失败")
        
        with pytest.raises(Exception, match="删除失败"):
            delete_obj(mock_db, mock_obj)
        
        mock_db.delete.assert_called_once()


class TestUpdateObj:
    """测试update_obj函数"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    def test_update_single_field(self, mock_db):
        """测试更新单个字段"""
        mock_obj = Mock()
        mock_obj.name = "Old Name"
        
        data = {"name": "New Name"}
        result = update_obj(mock_db, mock_obj, data)
        
        assert mock_obj.name == "New Name"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_multiple_fields(self, mock_db):
        """测试更新多个字段"""
        mock_obj = Mock()
        mock_obj.name = "Old Name"
        mock_obj.status = "OLD"
        mock_obj.value = 100
        
        data = {
            "name": "New Name",
            "status": "NEW",
            "value": 200
        }
        result = update_obj(mock_db, mock_obj, data)
        
        assert mock_obj.name == "New Name"
        assert mock_obj.status == "NEW"
        assert mock_obj.value == 200
    
    def test_update_ignore_non_existent_fields(self, mock_db):
        """测试忽略不存在的字段"""
        mock_obj = Mock(spec=["name", "status"])
        mock_obj.name = "Old Name"
        mock_obj.status = "OLD"
        
        data = {
            "name": "New Name",
            "non_existent_field": "Should be ignored"
        }
        result = update_obj(mock_db, mock_obj, data)
        
        assert mock_obj.name == "New Name"
        assert not hasattr(mock_obj, "non_existent_field")
    
    def test_update_without_refresh(self, mock_db):
        """测试更新不刷新"""
        mock_obj = Mock()
        mock_obj.name = "Old Name"
        
        data = {"name": "New Name"}
        result = update_obj(mock_db, mock_obj, data, refresh=False)
        
        mock_db.refresh.assert_not_called()
    
    def test_update_empty_data(self, mock_db):
        """测试空数据更新"""
        mock_obj = Mock()
        
        data = {}
        result = update_obj(mock_db, mock_obj, data)
        
        # 应该仍然调用add和commit
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestSafeCommit:
    """测试safe_commit函数"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    def test_successful_commit(self, mock_db):
        """测试成功提交"""
        result = safe_commit(mock_db)
        
        assert result is True
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()
    
    def test_failed_commit(self, mock_db):
        """测试提交失败"""
        mock_db.commit.side_effect = Exception("提交失败")
        
        result = safe_commit(mock_db)
        
        assert result is False
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_called_once()
    
    def test_rollback_on_integrity_error(self, mock_db):
        """测试完整性错误时回滚"""
        from sqlalchemy.exc import IntegrityError
        mock_db.commit.side_effect = IntegrityError("", "", "")
        
        result = safe_commit(mock_db)
        
        assert result is False
        mock_db.rollback.assert_called_once()


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_create_update_delete_workflow(self):
        """测试创建-更新-删除工作流"""
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.__name__ = "User"
        mock_model.id = Mock()
        
        # 1. 创建对象
        new_obj = Mock()
        new_obj.id = 1
        new_obj.name = "Test User"
        saved_obj = save_obj(mock_db, new_obj)
        
        assert saved_obj == new_obj
        
        # 2. 查找对象
        mock_query = Mock()
        mock_query.filter().first.return_value = saved_obj
        mock_db.query.return_value = mock_query
        
        found_obj = get_or_404(mock_db, mock_model, 1)
        assert found_obj == saved_obj
        
        # 3. 更新对象
        update_data = {"name": "Updated User"}
        updated_obj = update_obj(mock_db, found_obj, update_data)
        assert updated_obj.name == "Updated User"
        
        # 4. 删除对象
        delete_obj(mock_db, updated_obj)
        mock_db.delete.assert_called_with(updated_obj)
    
    def test_safe_batch_operations(self):
        """测试安全的批量操作"""
        mock_db = Mock(spec=Session)
        
        # 创建多个对象
        objects = [Mock(id=i, name=f"Object {i}") for i in range(3)]
        
        for obj in objects:
            save_obj(mock_db, obj)
        
        assert mock_db.add.call_count == 3
        assert mock_db.commit.call_count == 3
        
        # 使用safe_commit批量提交
        mock_db.commit.side_effect = None
        result = safe_commit(mock_db)
        assert result is True
    
    def test_error_handling_scenario(self):
        """测试错误处理场景"""
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.__name__ = "Project"
        mock_model.id = Mock()
        
        # 查找不存在的对象
        mock_query = Mock()
        mock_query.filter().first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            get_or_404(mock_db, mock_model, 999)
        
        assert exc_info.value.status_code == 404
        assert "999" in exc_info.value.detail
        
        # 保存失败
        mock_obj = Mock()
        mock_db.commit.side_effect = Exception("保存失败")
        
        with pytest.raises(Exception, match="保存失败"):
            save_obj(mock_db, mock_obj)
        
        # 使用safe_commit处理
        result = safe_commit(mock_db)
        assert result is False
        mock_db.rollback.assert_called()


class TestEdgeCases:
    """边界情况测试"""

    def test_get_or_404_with_none_id(self):
        """测试None作为ID"""
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.__name__ = "Model"
        mock_model.id = Mock()
        
        mock_query = Mock()
        mock_query.filter().first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException):
            get_or_404(mock_db, mock_model, None)
    
    def test_update_obj_with_none_values(self):
        """测试None值更新"""
        mock_db = Mock(spec=Session)
        mock_obj = Mock()
        mock_obj.name = "Old"
        mock_obj.value = 100
        
        data = {"name": None, "value": 0}
        update_obj(mock_db, mock_obj, data)
        
        assert mock_obj.name is None
        assert mock_obj.value == 0
    
    def test_save_obj_already_in_session(self):
        """测试保存已在session中的对象"""
        mock_db = Mock(spec=Session)
        mock_obj = Mock()
        
        # 不会报错，add是幂等的
        save_obj(mock_db, mock_obj)
        save_obj(mock_db, mock_obj)
        
        assert mock_db.add.call_count == 2
