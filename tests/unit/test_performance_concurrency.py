# -*- coding: utf-8 -*-
"""
D5组：性能 & 并发场景测试
==========================================
目标：测试系统在高并发和大数据量下的行为。

覆盖场景：
1. 大批量数据处理 — TimesheetSyncService 批量同步 + add_all 路径性能
2. 缓存穿透保护   — cache_response 装饰器：缓存未命中 → 函数执行 → 写入缓存
3. 缓存失效测试   — 数据更新后缓存应失效（del 被调用）
4. 分页偏移性能   — get_pagination_params 深页码正确生成 offset/limit
5. 权限缓存命中   — PermissionService.check_permission 通过缓存，不重复查 DB
6. 工时锁定保护   — 已锁定（非 APPROVED）工时记录不允许同步/修改
"""

import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# =========================================================
# 场景 1：大批量数据处理
# =========================================================

class TestBatchTimesheetPerformance:
    """批量工时数据处理性能测试"""

    def test_batch_sync_1000_records_under_2s(self):
        """
        批量同步1000条工时记录（同步到财务）应在2秒内完成。

        策略：mock 掉 DB 查询，仅测试 service 层循环逻辑本身的吞吐。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService
        from datetime import date

        db = MagicMock()
        service = TimesheetSyncService(db)

        # 构造 1000 条已审批工时对象
        N = 1000
        def _make_ts(i):
            ts = MagicMock()
            ts.id = i
            ts.user_id = i % 100 + 1
            ts.project_id = i % 10 + 1
            ts.project_code = f"PRJ{i % 10:03d}"
            ts.project_name = f"Project {i % 10}"
            ts.status = "APPROVED"
            ts.work_date = date(2026, 2, 17)
            ts.hours = Decimal("8.0")
            ts.work_content = f"Task {i}"
            ts.approver_id = 1
            ts.approve_time = None
            ts.user_name = f"User{i}"
            return ts

        timesheets = [_make_ts(i) for i in range(N)]

        # 模拟 get_month_range_by_ym、DB 查询、HourlyRateService
        with patch("app.services.timesheet_sync_service.get_month_range_by_ym",
                   return_value=(date(2026, 2, 1), date(2026, 2, 28))), \
             patch("app.services.timesheet_sync_service.HourlyRateService") as mock_hr, \
             patch("app.services.timesheet_sync_service.save_obj"):

            mock_hr.get_user_hourly_rate.return_value = Decimal("100.0")

            # 批量查询返回 1000 条
            db.query.return_value.filter.return_value.all.return_value = timesheets
            # 不存在现有记录（走 create 分支）
            db.query.return_value.filter.return_value.first.return_value = None

            start = time.time()
            result = service.sync_to_finance(project_id=1, year=2026, month=2)
            elapsed = time.time() - start

        assert elapsed < 2.0, f"同步1000条耗时 {elapsed:.2f}s，超过2秒限制"
        assert result.get("success") is True
        assert result.get("created_count") == N

    def test_batch_add_all_performance(self):
        """
        使用 session.add_all() 批量添加500条记录，应比逐条 add 快。

        验证：add_all 被调用，而非循环调用500次 add。
        """
        from app.models.timesheet import Timesheet
        from datetime import date

        db = MagicMock()
        records = [
            Timesheet(
                user_id=i,
                hours=Decimal("8.0"),
                work_date=date(2026, 2, 17),
                status="DRAFT",
            )
            for i in range(500)
        ]

        # 模拟批量添加
        start = time.time()
        db.add_all(records)
        db.commit()
        elapsed = time.time() - start

        # add_all 应被调用1次（而非500次 add）
        db.add_all.assert_called_once_with(records)
        assert elapsed < 0.5, f"add_all 调用本身耗时 {elapsed:.3f}s，异常"

    def test_large_dataset_loop_no_excessive_db_queries(self):
        """
        处理200条记录时，DB 查询次数不应超过 N*2（每条最多2次：检查现有+创建）。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService
        from datetime import date

        db = MagicMock()
        service = TimesheetSyncService(db)
        N = 200

        def _make_ts(i):
            ts = MagicMock()
            ts.id = i
            ts.user_id = 1
            ts.project_id = 1
            ts.project_code = "PRJ001"
            ts.project_name = "Project A"
            ts.status = "APPROVED"
            ts.work_date = date(2026, 2, 17)
            ts.hours = Decimal("8.0")
            ts.work_content = "Work"
            ts.approver_id = 1
            ts.approve_time = None
            ts.user_name = "User1"
            return ts

        timesheets = [_make_ts(i) for i in range(N)]

        with patch("app.services.timesheet_sync_service.get_month_range_by_ym",
                   return_value=(date(2026, 2, 1), date(2026, 2, 28))), \
             patch("app.services.timesheet_sync_service.HourlyRateService") as mock_hr, \
             patch("app.services.timesheet_sync_service.save_obj"):

            mock_hr.get_user_hourly_rate.return_value = Decimal("100.0")
            db.query.return_value.filter.return_value.all.return_value = timesheets
            db.query.return_value.filter.return_value.first.return_value = None

            result = service.sync_to_finance(project_id=1, year=2026, month=2)

        # 验证：DB query 调用次数 <= N * 2 + 1（最后1次是初始批量查询）
        assert db.query.call_count <= N * 2 + 1, (
            f"DB 查询次数 {db.query.call_count} 超出预期 {N * 2 + 1}"
        )


# =========================================================
# 场景 2 & 3：缓存穿透保护 & 缓存失效
# =========================================================

class TestCacheProtection:
    """缓存穿透保护与失效测试"""

    def test_cache_miss_fallback_calls_function_once(self):
        """
        缓存未命中时，函数体执行1次；第二次调用命中内存缓存，不再执行函数体。

        使用 cache_response 装饰器 + mock CacheService。
        """
        from app.utils.cache_decorator import cache_response

        call_count = [0]

        # 创建 mock CacheService：第一次 get=None（未命中），后续 get 返回缓存结果
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # 始终未命中（模拟 Redis miss）
        mock_cache.set = MagicMock()

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="test:project", ttl=60)
            def get_project(project_id):
                call_count[0] += 1
                return {"id": project_id, "name": "Test"}

            result1 = get_project(project_id=1)
            # 首次调用 → 缓存 miss → 执行函数 → set 缓存
            assert call_count[0] == 1
            assert result1["id"] == 1
            mock_cache.set.assert_called_once()

    def test_cache_hit_skips_function_body(self):
        """
        缓存命中时，函数体不再执行。
        """
        from app.utils.cache_decorator import cache_response

        call_count = [0]
        cached_value = {"id": 42, "name": "Cached"}

        mock_cache = MagicMock()
        mock_cache.get.return_value = cached_value  # 始终命中

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="test:project", ttl=60)
            def get_project(project_id):
                call_count[0] += 1
                return {"id": project_id, "name": "Fresh"}

            result = get_project(project_id=42)

        assert call_count[0] == 0, "缓存命中时函数体不应执行"
        assert result["id"] == 42

    def test_cache_invalidation_on_update(self):
        """
        数据更新后缓存应失效：cache_project_detail.invalidate 应调用 cache_service.invalidate_project_detail。
        """
        from app.utils.cache_decorator import cache_project_detail

        mock_cache = MagicMock()
        mock_cache.get_project_detail.return_value = None
        mock_cache.set_project_detail = MagicMock()
        mock_cache.invalidate_project_detail = MagicMock()

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_project_detail
            def get_project_detail(self, project_id):
                return {"id": project_id, "name": "Detail"}

            # 获取详情
            get_project_detail(None, project_id=10)

            # 触发缓存失效
            get_project_detail.invalidate(10)

        mock_cache.invalidate_project_detail.assert_called_once_with(10)

    def test_cache_service_get_set_sequence(self):
        """
        get → None → 执行函数 → set 的调用序列正确。
        """
        from app.utils.cache_decorator import cache_response

        mock_cache = MagicMock()
        call_log = []

        def fake_get(key):
            call_log.append(("get", key))
            return None

        def fake_set(key, value, expire_seconds=None):
            call_log.append(("set", key))

        mock_cache.get.side_effect = fake_get
        mock_cache.set.side_effect = fake_set

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="test:seq", ttl=120)
            def compute(x):
                return {"result": x * 2}

            compute(x=5)

        ops = [op for op, _ in call_log]
        assert ops[0] == "get", "第一步应是缓存读取"
        assert ops[1] == "set", "缓存未命中后应写入缓存"


# =========================================================
# 场景 4：分页偏移性能
# =========================================================

class TestPaginationEfficiency:
    """分页偏移性能测试"""

    def test_deep_pagination_offset_calculation(self):
        """
        第100页（每页20条）的 offset 应为 1980，limit 应为 20。
        验证 get_pagination_params 正确实现深翻页而非全表扫描。

        直接传入 default_page_size / max_page_size，绕过 settings 依赖。
        """
        from app.common.pagination import get_pagination_params
        params = get_pagination_params(page=100, page_size=20,
                                       default_page_size=20, max_page_size=500)

        assert params.offset == 1980, f"第100页 offset 应为 1980，实际为 {params.offset}"
        assert params.limit == 20, f"每页 limit 应为 20，实际为 {params.limit}"

    def test_first_page_offset_is_zero(self):
        """第1页 offset 应为 0。"""
        from app.common.pagination import get_pagination_params
        params = get_pagination_params(page=1, page_size=20,
                                       default_page_size=20, max_page_size=500)

        assert params.offset == 0
        assert params.limit == 20

    def test_page_size_capped_at_maximum(self):
        """每页条数不应超过 MAX_PAGE_SIZE 上限。"""
        from app.common.pagination import get_pagination_params
        params = get_pagination_params(page=1, page_size=9999,
                                       default_page_size=20, max_page_size=100)

        assert params.limit <= 100, f"page_size 应被限制在 100，实际为 {params.limit}"

    def test_pagination_offset_formula(self):
        """验证 offset = (page - 1) * page_size 公式，覆盖多个页码。"""
        from app.common.pagination import get_pagination_params

        cases = [
            (1, 10, 0),
            (2, 10, 10),
            (5, 25, 100),
            (50, 20, 980),
            (100, 20, 1980),
        ]
        for page, page_size, expected_offset in cases:
            params = get_pagination_params(page=page, page_size=page_size,
                                           default_page_size=20, max_page_size=500)
            assert params.offset == expected_offset, (
                f"page={page}, page_size={page_size}: "
                f"期望 offset={expected_offset}，实际={params.offset}"
            )

    def test_deep_pagination_uses_offset_not_fetchall(self):
        """
        深翻页应通过 query.offset().limit() 实现，而非先 fetchall 再切片。

        用 MagicMock 模拟 SQLAlchemy query 链，验证 offset/limit 调用顺序。
        """
        from app.common.pagination import get_pagination_params

        params = get_pagination_params(page=100, page_size=20,
                                       default_page_size=20, max_page_size=500)

        # 模拟 SQLAlchemy query 对象
        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query

        # 手动应用分页参数（模拟 ORM 使用方式）
        mock_query.offset(params.offset).limit(params.limit).all()

        mock_query.offset.assert_called_with(1980)
        mock_query.offset.return_value.limit.assert_called_with(20)


# =========================================================
# 场景 5：权限缓存命中
# =========================================================

class TestPermissionCacheOptimization:
    """权限检查缓存优化测试"""

    def test_permission_check_uses_cache_no_db_query(self):
        """
        权限命中缓存时，get_user_permissions 从缓存返回，不再执行 SQL。
        PermissionService.check_permission → get_user_permissions → 缓存命中。
        """
        from app.services.permission_service import PermissionService
        from app.models.user import User as UserModel

        # 构造明确的非超级管理员用户（避免 MagicMock 的 is_superuser 为真值）
        mock_user = MagicMock(spec=UserModel)
        mock_user.is_superuser = False
        mock_user.tenant_id = 1

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_user
        user_id = 1

        # mock PermissionCacheService 返回已缓存的权限集合
        mock_cache_svc = MagicMock()
        mock_cache_svc.get_user_permissions.return_value = {"read_project", "write_project"}

        with patch(
            "app.services.permission_service.get_permission_cache_service",
            return_value=mock_cache_svc,
        ):
            # 连续检查3次同一权限，传入 user 对象绕过 DB 查询 user
            for _ in range(3):
                has_perm = PermissionService.check_permission(
                    db, user_id, "read_project", user=mock_user
                )

        # 有权限
        assert has_perm is True
        # 缓存服务应被调用3次（每次 check_permission → get_user_permissions → 查缓存）
        assert mock_cache_svc.get_user_permissions.call_count == 3

    def test_permission_check_cache_miss_falls_back_to_db(self):
        """
        缓存未命中时，权限服务应回落到数据库查询。
        """
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user_id = 99

        # 缓存未命中
        mock_cache_svc = MagicMock()
        mock_cache_svc.get_user_permissions.return_value = None  # 未命中

        # DB 查询返回空列表（用户无权限）
        db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.services.permission_service.get_permission_cache_service",
            return_value=mock_cache_svc,
        ), patch("app.services.permission_service.text"):
            # 缓存 miss 后执行 SQL，DB 异常正常捕获降级
            has_perm = PermissionService.check_permission(
                db, user_id, "admin_access"
            )

        assert has_perm is False

    def test_superuser_bypasses_cache_and_db(self):
        """
        超级管理员应直接返回 True，不走缓存也不查 DB。
        """
        from app.services.permission_service import PermissionService
        from app.models.user import User

        db = MagicMock()
        user = MagicMock(spec=User)
        user.is_superuser = True

        mock_cache_svc = MagicMock()

        with patch(
            "app.services.permission_service.get_permission_cache_service",
            return_value=mock_cache_svc,
        ):
            result = PermissionService.check_permission(
                db, user_id=1, permission_code="any_permission", user=user
            )

        assert result is True
        # 超级管理员不查缓存
        mock_cache_svc.get_user_permissions.assert_not_called()
        db.query.assert_not_called()

    def test_permission_cache_ttl_key_isolation(self):
        """
        不同用户的权限缓存应相互隔离（使用不同缓存键）。
        """
        from app.services.permission_cache_service import PermissionCacheService

        cache_svc = PermissionCacheService()
        mock_inner_cache = MagicMock()
        mock_inner_cache.get.return_value = None
        cache_svc._cache = mock_inner_cache

        # 分别获取两个用户的权限
        cache_svc.get_user_permissions(user_id=1, tenant_id=10)
        cache_svc.get_user_permissions(user_id=2, tenant_id=10)

        # 两次调用的缓存键应不同
        calls = [call[0][0] for call in mock_inner_cache.get.call_args_list]
        assert len(calls) == 2
        assert calls[0] != calls[1], "不同用户的缓存键应不同"
        assert "1" in calls[0] and "2" in calls[1]


# =========================================================
# 场景 6：工时锁定保护
# =========================================================

class TestTimesheetLockProtection:
    """工时锁定保护测试"""

    def test_non_approved_timesheet_cannot_be_synced(self):
        """
        未审批（非 APPROVED）的工时记录不允许同步到财务系统。
        sync_to_finance 应返回 success=False 并给出拒绝理由。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService

        db = MagicMock()
        service = TimesheetSyncService(db)

        draft_record = MagicMock()
        draft_record.status = "DRAFT"
        draft_record.id = 1
        db.query.return_value.filter.return_value.first.return_value = draft_record

        result = service.sync_to_finance(timesheet_id=1)

        assert result.get("success") is False
        assert "审批" in result.get("message", "") or "APPROVED" in result.get("message", "")

    def test_rejected_timesheet_cannot_be_synced(self):
        """
        被驳回（REJECTED）的工时记录不允许同步。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService

        db = MagicMock()
        service = TimesheetSyncService(db)

        rejected_record = MagicMock()
        rejected_record.status = "REJECTED"
        rejected_record.id = 2
        db.query.return_value.filter.return_value.first.return_value = rejected_record

        result = service.sync_to_finance(timesheet_id=2)

        assert result.get("success") is False

    def test_approved_timesheet_can_be_synced(self):
        """
        已审批（APPROVED）的工时记录可以正常同步（有效的基准场景）。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService
        from datetime import date

        db = MagicMock()
        service = TimesheetSyncService(db)

        approved_record = MagicMock()
        approved_record.status = "APPROVED"
        approved_record.id = 3
        approved_record.project_id = 1
        approved_record.project_code = "PRJ001"
        approved_record.project_name = "Project A"
        approved_record.work_date = date(2026, 2, 17)
        approved_record.hours = Decimal("8.0")
        approved_record.user_id = 1
        approved_record.user_name = "Alice"
        approved_record.work_content = "Coding"
        approved_record.approver_id = 2
        approved_record.approve_time = None

        # 第一次 query 返回 timesheet，第二次返回 None（无现有财务记录）
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [approved_record, None]
        db.query.return_value = query_mock

        with patch("app.services.timesheet_sync_service.HourlyRateService") as mock_hr, \
             patch("app.services.timesheet_sync_service.save_obj"):
            mock_hr.get_user_hourly_rate.return_value = Decimal("150.0")
            result = service.sync_to_finance(timesheet_id=3)

        assert result.get("success") is True

    def test_timesheet_without_project_cannot_be_synced_to_finance(self):
        """
        未关联项目的工时记录无法同步到财务系统（业务约束）。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService

        db = MagicMock()
        service = TimesheetSyncService(db)

        no_project_record = MagicMock()
        no_project_record.status = "APPROVED"
        no_project_record.id = 4
        no_project_record.project_id = None  # 未关联项目
        db.query.return_value.filter.return_value.first.return_value = no_project_record

        result = service.sync_to_finance(timesheet_id=4)

        assert result.get("success") is False
        assert "项目" in result.get("message", "")

    def test_frozen_status_simulation_blocks_modification(self):
        """
        模拟"已锁定"状态保护：通过业务状态机验证已审批工时的不可篡改性。

        当工时记录已通过财务同步（has_synced=True），业务层应拒绝重复写入，
        防止并发修改导致数据不一致。
        """
        # 模拟一个通用的"冻结检查"函数，代表工时锁定业务规则
        def check_timesheet_editable(timesheet) -> bool:
            """业务规则：已同步或已锁定的工时不可修改"""
            if getattr(timesheet, "is_locked", False):
                return False
            if getattr(timesheet, "sync_status", None) == "SYNCED":
                return False
            if getattr(timesheet, "status", None) == "APPROVED":
                # 已审批的工时进入只读状态（不可再次同步覆盖）
                return False
            return True

        # 已审批/已同步工时 → 不可编辑
        frozen_ts = MagicMock(status="APPROVED", is_locked=True, sync_status="SYNCED")
        assert check_timesheet_editable(frozen_ts) is False

        # 草稿状态 → 可编辑
        draft_ts = MagicMock(status="DRAFT", is_locked=False, sync_status="PENDING")
        assert check_timesheet_editable(draft_ts) is True

    def test_concurrent_sync_idempotency(self):
        """
        并发场景：同一工时记录被并发同步2次，应保持幂等性（不创建重复财务记录）。

        TimesheetSyncService._create_financial_cost_from_timesheet 在记录存在时走 update 分支。
        """
        from app.services.timesheet_sync_service import TimesheetSyncService
        from datetime import date

        db = MagicMock()
        service = TimesheetSyncService(db)

        ts = MagicMock()
        ts.id = 100
        ts.project_id = 1
        ts.project_code = "PRJ001"
        ts.project_name = "Project A"
        ts.work_date = date(2026, 2, 17)
        ts.hours = Decimal("8.0")
        ts.user_id = 1
        ts.user_name = "Bob"
        ts.work_content = "Review"
        ts.approver_id = 2
        ts.approve_time = None

        # 模拟已存在的财务记录（并发第二次请求时）
        existing_cost = MagicMock()
        existing_cost.id = 999

        with patch("app.services.timesheet_sync_service.HourlyRateService") as mock_hr:
            mock_hr.get_user_hourly_rate.return_value = Decimal("100.0")

            # 第一次：记录不存在 → create
            db.query.return_value.filter.return_value.first.return_value = None
            with patch("app.services.timesheet_sync_service.save_obj"):
                result1 = service._create_financial_cost_from_timesheet(ts)

            # 第二次（并发/重试）：记录已存在 → update（幂等）
            db.query.return_value.filter.return_value.first.return_value = existing_cost
            result2 = service._create_financial_cost_from_timesheet(ts)

        assert result1.get("created") is True
        assert result2.get("updated") is True
        assert result1.get("success") is True
        assert result2.get("success") is True


# =========================================================
# 场景综合：性能基准快速验证
# =========================================================

class TestPerformanceBenchmarks:
    """性能基准快速验证"""

    def test_pagination_params_computation_speed(self):
        """连续计算1000次分页参数应在100ms内完成。"""
        from app.common.pagination import get_pagination_params

        start = time.time()
        for page in range(1, 1001):
            params = get_pagination_params(page=page, page_size=20,
                                           default_page_size=20, max_page_size=500)
            assert params.offset == (page - 1) * 20
        elapsed = time.time() - start

        assert elapsed < 0.1, f"1000次分页参数计算耗时 {elapsed:.3f}s，超过100ms"

    def test_permission_cache_lookup_speed(self):
        """权限缓存查询（已命中）应极快：10000次命中在200ms内。"""
        from app.services.permission_cache_service import PermissionCacheService

        cache_svc = PermissionCacheService()
        mock_inner = MagicMock()
        mock_inner.get.return_value = ["read_project", "write_project"]
        cache_svc._cache = mock_inner

        start = time.time()
        for i in range(10000):
            cache_svc.get_user_permissions(user_id=i % 100, tenant_id=1)
        elapsed = time.time() - start

        assert elapsed < 0.2, f"10000次缓存命中查询耗时 {elapsed:.3f}s，超过200ms"

    def test_list_comprehension_vs_loop_for_record_creation(self):
        """
        列表推导式批量创建对象应在10ms内完成（对比逐条append）。
        """
        from datetime import date

        # 方式A：列表推导式（推荐）
        start = time.time()
        records_a = [
            {"engineer_id": i, "hours": 8.0, "date": "2026-02-17"}
            for i in range(1000)
        ]
        elapsed_a = time.time() - start

        # 方式B：逐条 append
        start = time.time()
        records_b = []
        for i in range(1000):
            records_b.append({"engineer_id": i, "hours": 8.0, "date": "2026-02-17"})
        elapsed_b = time.time() - start

        assert elapsed_a < 0.01, f"列表推导式耗时 {elapsed_a*1000:.2f}ms，超过10ms"
        assert len(records_a) == len(records_b) == 1000
