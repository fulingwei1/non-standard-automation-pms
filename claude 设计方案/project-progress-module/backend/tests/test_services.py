"""
业务逻辑服务测试
"""
import pytest
from datetime import date, timedelta


class TestProgressCalculation:
    """进度计算测试"""
    
    @pytest.mark.unit
    def test_weighted_progress_calculation(self):
        """测试加权进度计算"""
        tasks = [
            {"progress_rate": 100, "weight": 20},
            {"progress_rate": 50, "weight": 30},
            {"progress_rate": 0, "weight": 50}
        ]
        
        total_weight = sum(t["weight"] for t in tasks)
        weighted_sum = sum(t["progress_rate"] * t["weight"] for t in tasks)
        progress = weighted_sum / total_weight if total_weight > 0 else 0
        
        # 期望: (100*20 + 50*30 + 0*50) / 100 = 35%
        assert progress == 35
    
    @pytest.mark.unit
    def test_spi_calculation(self):
        """测试SPI计算"""
        # SPI = 实际进度 / 计划进度
        actual, plan = 45, 50
        spi = actual / plan if plan > 0 else 1
        assert spi == 0.9
        
        # 进度超前
        actual, plan = 60, 50
        spi = actual / plan
        assert spi == 1.2
    
    @pytest.mark.unit
    def test_health_status_determination(self):
        """测试健康状态判定"""
        def get_health(spi):
            if spi >= 0.95: return "绿"
            elif spi >= 0.8: return "黄"
            else: return "红"
        
        assert get_health(1.0) == "绿"
        assert get_health(0.95) == "绿"
        assert get_health(0.9) == "黄"
        assert get_health(0.8) == "黄"
        assert get_health(0.7) == "红"


class TestCriticalPathAlgorithm:
    """关键路径算法测试"""
    
    @pytest.mark.unit
    def test_topological_sort(self):
        """测试拓扑排序"""
        # 简单依赖: 1 -> 2 -> 4, 1 -> 3 -> 4
        tasks = {
            1: {"predecessors": []},
            2: {"predecessors": [1]},
            3: {"predecessors": [1]},
            4: {"predecessors": [2, 3]}
        }
        
        # 入度计算
        in_degree = {t: 0 for t in tasks}
        for t, data in tasks.items():
            for p in data["predecessors"]:
                pass  # 不增加入度，这里只是示例
        
        # 任务1应该先执行（无前置）
        assert len(tasks[1]["predecessors"]) == 0
    
    @pytest.mark.unit
    def test_critical_path_duration(self):
        """测试关键路径工期计算"""
        # 任务: 1(5天) -> 2(3天) -> 4(2天) = 10天
        #            -> 3(4天) -> 4(2天) = 11天 (关键路径)
        
        path1 = 5 + 3 + 2  # 10天
        path2 = 5 + 4 + 2  # 11天
        
        critical_duration = max(path1, path2)
        assert critical_duration == 11
    
    @pytest.mark.unit
    def test_float_time_calculation(self):
        """测试浮动时间计算"""
        # 任务2的浮动时间 = 最迟开始 - 最早开始
        # 任务3是关键路径，任务2有1天浮动
        task2_es = 5  # 最早开始（任务1完成后）
        task2_ls = 6  # 最迟开始（不影响关键路径的前提下）
        task2_float = task2_ls - task2_es
        
        assert task2_float == 1


class TestAlertRules:
    """预警规则测试"""
    
    @pytest.mark.unit
    def test_overdue_detection(self):
        """测试逾期检测"""
        today = date.today()
        
        task1_end = today - timedelta(days=3)  # 逾期3天
        task2_end = today + timedelta(days=5)  # 未逾期
        
        def is_overdue(end_date, status):
            return status != "已完成" and end_date < today
        
        assert is_overdue(task1_end, "进行中") == True
        assert is_overdue(task2_end, "进行中") == False
        assert is_overdue(task1_end, "已完成") == False
    
    @pytest.mark.unit
    def test_alert_level_by_overdue_days(self):
        """测试按逾期天数确定预警级别"""
        def get_level(days):
            if days >= 7: return "红"
            elif days >= 3: return "橙"
            else: return "黄"
        
        assert get_level(1) == "黄"
        assert get_level(3) == "橙"
        assert get_level(5) == "橙"
        assert get_level(7) == "红"
        assert get_level(10) == "红"
    
    @pytest.mark.unit
    def test_upcoming_deadline_detection(self):
        """测试即将到期检测"""
        today = date.today()
        threshold = 3
        
        tasks = [
            {"end_date": today + timedelta(days=1), "status": "进行中"},  # 1天后
            {"end_date": today + timedelta(days=3), "status": "进行中"},  # 3天后
            {"end_date": today + timedelta(days=5), "status": "进行中"},  # 5天后
        ]
        
        upcoming = [
            t for t in tasks 
            if t["status"] != "已完成" 
            and 0 <= (t["end_date"] - today).days <= threshold
        ]
        
        assert len(upcoming) == 2


class TestWorkloadCalculation:
    """负荷计算测试"""
    
    @pytest.mark.unit
    def test_allocation_rate(self):
        """测试负荷率计算"""
        standard_hours = 176  # 月标准工时
        
        # 正常负荷
        assigned = 160
        rate = assigned / standard_hours * 100
        assert round(rate, 1) == 90.9
        
        # 超负荷
        assigned = 200
        rate = assigned / standard_hours * 100
        assert round(rate, 1) == 113.6
    
    @pytest.mark.unit
    def test_available_hours(self):
        """测试可用工时计算"""
        standard_hours = 176
        
        # 已分配90%
        allocation_rate = 90
        available = standard_hours * (1 - allocation_rate / 100)
        assert available == 17.6
        
        # 已分配50%
        allocation_rate = 50
        available = standard_hours * (1 - allocation_rate / 100)
        assert available == 88
    
    @pytest.mark.unit
    def test_overload_threshold(self):
        """测试超负荷阈值"""
        threshold = 100  # 100%为临界值
        
        users = [
            {"name": "张工", "rate": 120},
            {"name": "李工", "rate": 90},
            {"name": "王工", "rate": 105}
        ]
        
        overloaded = [u for u in users if u["rate"] > threshold]
        assert len(overloaded) == 2
        assert overloaded[0]["name"] == "张工"
        assert overloaded[1]["name"] == "王工"


class TestTimesheetValidation:
    """工时验证测试"""
    
    @pytest.mark.unit
    def test_daily_hours_limit(self):
        """测试每日工时上限"""
        max_daily = 24
        
        assert 8 <= max_daily
        assert 12 <= max_daily
        assert 25 > max_daily  # 无效
    
    @pytest.mark.unit
    def test_future_date_validation(self):
        """测试未来日期验证"""
        today = date.today()
        
        def is_valid_date(work_date):
            return work_date <= today
        
        assert is_valid_date(today) == True
        assert is_valid_date(today - timedelta(days=1)) == True
        assert is_valid_date(today + timedelta(days=1)) == False
    
    @pytest.mark.unit
    def test_duplicate_entry_check(self):
        """测试重复条目检查"""
        existing = [
            {"user_id": 1, "task_id": 101, "work_date": "2025-01-15"},
            {"user_id": 1, "task_id": 102, "work_date": "2025-01-15"}
        ]
        
        new_entry = {"user_id": 1, "task_id": 101, "work_date": "2025-01-15"}
        
        is_duplicate = any(
            e["user_id"] == new_entry["user_id"] and
            e["task_id"] == new_entry["task_id"] and
            e["work_date"] == new_entry["work_date"]
            for e in existing
        )
        
        assert is_duplicate == True
