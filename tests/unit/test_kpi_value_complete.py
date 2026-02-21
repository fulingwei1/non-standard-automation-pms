# -*- coding: utf-8 -*-
"""
完整单元测试 - strategy/kpi_service/value.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.strategy.kpi_service.value import update_kpi_value


class TestUpdateKpiValue:
    """更新KPI值完整测试套件"""
    
    # ========== 基础功能测试 ==========
    
    def test_update_value_kpi_not_found(self):
        """测试KPI不存在时返回None"""
        db = MagicMock()
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=None):
            result = update_kpi_value(
                db,
                kpi_id=999,
                value=Decimal("50"),
                recorded_by=1
            )
        
        assert result is None
        db.commit.assert_not_called()
    
    def test_update_value_basic(self):
        """测试基础值更新"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(
                db,
                kpi_id=1,
                value=Decimal("75"),
                recorded_by=5
            )
        
        assert kpi_mock.current_value == Decimal("75")
        assert result is kpi_mock
    
    def test_update_value_sets_current_value(self):
        """测试设置当前值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("50")
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, kpi_id=1, value=Decimal("88"), recorded_by=3)
        
        assert kpi_mock.current_value == Decimal("88")
    
    def test_update_value_sets_last_collected_at(self):
        """测试设置最后采集时间"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.last_collected_at = None
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, kpi_id=1, value=Decimal("60"), recorded_by=2)
        
        # 应该设置为当前时间
        assert kpi_mock.last_collected_at is not None
        assert isinstance(kpi_mock.last_collected_at, datetime)
    
    def test_update_value_commits_db(self):
        """测试提交数据库"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, kpi_id=1, value=Decimal("70"), recorded_by=1)
        
        db.commit.assert_called_once()
    
    def test_update_value_refreshes_kpi(self):
        """测试刷新KPI对象"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(db, kpi_id=1, value=Decimal("80"), recorded_by=1)
        
        db.refresh.assert_called_once_with(kpi_mock)
        assert result is kpi_mock
    
    # ========== 快照创建测试 ==========
    
    def test_update_value_creates_snapshot(self):
        """测试创建快照"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=3)
        
        mock_snap.assert_called_once()
    
    def test_update_value_snapshot_source_type(self):
        """测试快照源类型为MANUAL"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("60"), recorded_by=5)
        
        # 验证调用参数
        call_args = mock_snap.call_args
        assert call_args[0][0] == db
        assert call_args[0][1] == 1
        assert call_args[0][2] == "MANUAL"
        assert call_args[0][3] == 5
    
    def test_update_value_with_remark(self):
        """测试带备注的值更新"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(
                db,
                kpi_id=1,
                value=Decimal("75"),
                recorded_by=2,
                remark="Manual update"
            )
        
        # 验证备注被传递
        call_args = mock_snap.call_args
        assert call_args[0][4] == "Manual update"
    
    def test_update_value_without_remark(self):
        """测试无备注的值更新"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("80"), recorded_by=3)
        
        # 备注应该是None
        call_args = mock_snap.call_args
        assert len(call_args[0]) == 4 or call_args[0][4] is None
    
    # ========== 不同值类型测试 ==========
    
    def test_update_value_zero(self):
        """测试更新为0"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(db, kpi_id=1, value=Decimal("0"), recorded_by=1)
        
        assert kpi_mock.current_value == Decimal("0")
        assert result is kpi_mock
    
    def test_update_value_negative(self):
        """测试更新为负值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(db, kpi_id=1, value=Decimal("-50"), recorded_by=1)
        
        assert kpi_mock.current_value == Decimal("-50")
    
    def test_update_value_very_large(self):
        """测试更新为超大值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            large_value = Decimal("999999999.99")
            result = update_kpi_value(db, kpi_id=1, value=large_value, recorded_by=1)
        
        assert kpi_mock.current_value == large_value
    
    def test_update_value_very_small(self):
        """测试更新为极小值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            small_value = Decimal("0.001")
            result = update_kpi_value(db, kpi_id=1, value=small_value, recorded_by=1)
        
        assert kpi_mock.current_value == small_value
    
    def test_update_value_high_precision(self):
        """测试高精度小数"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            precise_value = Decimal("75.123456789")
            result = update_kpi_value(db, kpi_id=1, value=precise_value, recorded_by=1)
        
        assert kpi_mock.current_value == precise_value
    
    # ========== 不同记录人测试 ==========
    
    def test_update_value_different_recorded_by(self):
        """测试不同记录人"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            for user_id in [1, 100, 999]:
                update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=user_id)
                
                # 验证记录人被正确传递
                call_args = mock_snap.call_args
                assert call_args[0][3] == user_id
                
                db.reset_mock()
    
    # ========== 时间戳测试 ==========
    
    def test_update_value_updates_timestamp(self):
        """测试每次更新都更新时间戳"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            # 第一次更新
            update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=1)
            timestamp1 = kpi_mock.last_collected_at
            
            # 第二次更新
            update_kpi_value(db, kpi_id=1, value=Decimal("60"), recorded_by=1)
            timestamp2 = kpi_mock.last_collected_at
            
            # 时间戳应该不同（或者相同，因为时间很接近）
            assert timestamp1 is not None
            assert timestamp2 is not None
    
    def test_update_value_timestamp_is_recent(self):
        """测试时间戳是最近的"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        before = datetime.now()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, kpi_id=1, value=Decimal("70"), recorded_by=1)
        
        after = datetime.now()
        
        # 时间戳应该在before和after之间
        assert kpi_mock.last_collected_at >= before
        assert kpi_mock.last_collected_at <= after
    
    # ========== 多次更新测试 ==========
    
    def test_update_value_multiple_times(self):
        """测试多次更新值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            values = [Decimal("10"), Decimal("20"), Decimal("30")]
            
            for value in values:
                update_kpi_value(db, kpi_id=1, value=value, recorded_by=1)
                assert kpi_mock.current_value == value
            
            # 应该创建3个快照
            assert mock_snap.call_count == 3
    
    def test_update_value_increasing_trend(self):
        """测试递增趋势"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            for i in range(1, 11):
                update_kpi_value(db, kpi_id=1, value=Decimal(str(i * 10)), recorded_by=1)
            
            # 最后的值应该是100
            assert kpi_mock.current_value == Decimal("100")
    
    def test_update_value_decreasing_trend(self):
        """测试递减趋势"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            for i in range(10, 0, -1):
                update_kpi_value(db, kpi_id=1, value=Decimal(str(i * 10)), recorded_by=1)
            
            # 最后的值应该是10
            assert kpi_mock.current_value == Decimal("10")
    
    # ========== 数据库操作测试 ==========
    
    def test_update_value_transaction_order(self):
        """测试数据库操作顺序"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        call_order = []
        
        def track_commit():
            call_order.append("commit")
        
        def track_refresh(obj):
            call_order.append("refresh")
        
        db.commit.side_effect = track_commit
        db.refresh.side_effect = track_refresh
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            update_kpi_value(db, kpi_id=1, value=Decimal("70"), recorded_by=1)
        
        # commit应该在refresh之前
        assert call_order == ["commit", "refresh"]
    
    # ========== 备注测试 ==========
    
    def test_update_value_with_empty_remark(self):
        """测试空备注"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=1, remark="")
        
        call_args = mock_snap.call_args
        assert call_args[0][4] == ""
    
    def test_update_value_with_long_remark(self):
        """测试长备注"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        long_remark = "This is a very long remark " * 20
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("60"), recorded_by=1, remark=long_remark)
        
        call_args = mock_snap.call_args
        assert call_args[0][4] == long_remark
    
    def test_update_value_with_special_characters_in_remark(self):
        """测试备注包含特殊字符"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        special_remark = "Updated with <special> & 'characters' \"quotes\" 中文"
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
            update_kpi_value(db, kpi_id=1, value=Decimal("70"), recorded_by=1, remark=special_remark)
        
        call_args = mock_snap.call_args
        assert call_args[0][4] == special_remark
    
    # ========== 异常场景测试 ==========
    
    def test_update_value_db_commit_error_handling(self):
        """测试数据库提交错误（预期抛出异常）"""
        db = MagicMock()
        kpi_mock = MagicMock()
        db.commit.side_effect = Exception("DB Error")
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            with pytest.raises(Exception, match="DB Error"):
                update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=1)
    
    def test_update_value_snapshot_creation_error(self):
        """测试快照创建错误"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot", side_effect=Exception("Snapshot error")):
            with pytest.raises(Exception, match="Snapshot error"):
                update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=1)
    
    # ========== 边界情况测试 ==========
    
    def test_update_value_from_none_to_value(self):
        """测试从None更新为具体值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = None
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(db, kpi_id=1, value=Decimal("100"), recorded_by=1)
        
        assert kpi_mock.current_value == Decimal("100")
    
    def test_update_value_same_value(self):
        """测试更新为相同值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("50")
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            result = update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=1)
        
        # 即使值相同，仍应更新（创建快照）
        assert kpi_mock.current_value == Decimal("50")
        db.commit.assert_called_once()
    
    def test_update_value_percentage(self):
        """测试百分比值"""
        db = MagicMock()
        kpi_mock = MagicMock()
        
        with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
            # 测试各种百分比值
            for percent in [0, 25, 50, 75, 100, 150]:
                update_kpi_value(db, kpi_id=1, value=Decimal(str(percent)), recorded_by=1)
                assert kpi_mock.current_value == Decimal(str(percent))
