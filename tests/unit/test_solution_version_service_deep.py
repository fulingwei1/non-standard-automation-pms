# -*- coding: utf-8 -*-
"""solution_version_service 深度测试"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.solution_version_service import SolutionVersionService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, get_map=None):
        self._first_value = first_value
        self._all_value = all_value or []
        self._get_map = get_map or {}

    def get(self, key):
        return self._get_map.get(key)

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value


class TestSolutionVersionServiceDeep:
    @pytest.mark.asyncio
    async def test_create_version_success(self):
        db = MagicMock()
        service = SolutionVersionService(db)
        solution = SimpleNamespace(id=1)
        latest = SimpleNamespace(id=9, version_no="V1.2", status="approved")
        db.query.return_value = FakeQuery(get_map={1: solution})
        service._get_latest_version = MagicMock(return_value=latest)

        class FakeVersion:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)
                self.id = 18

        with patch("app.services.sales.solution_version_service.SolutionVersion", FakeVersion):
            version = await service.create_version(
                1,
                {
                    "generated_solution": "方案A",
                    "change_summary": "升级版本",
                    "quality_score": 0.95,
                },
                created_by=7,
                change_reason="客户要求",
            )

        assert version.solution_id == 1
        assert version.version_no == "V2.0"
        assert version.parent_version_id == 9
        assert version.change_reason == "客户要求"
        assert version.change_summary == "升级版本"
        assert version.generated_solution == "方案A"
        assert version.quality_score == 0.95
        assert version.created_by == 7
        assert version.status == "draft"
        db.add.assert_called_once_with(version)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(version)

    @pytest.mark.asyncio
    async def test_create_version_raises_when_solution_missing(self):
        db = MagicMock()
        db.query.return_value = FakeQuery(get_map={})
        service = SolutionVersionService(db)

        with pytest.raises(ValueError, match="方案不存在: 99"):
            await service.create_version(99, {}, created_by=1)

    @pytest.mark.asyncio
    async def test_submit_for_review_success_and_invalid_status(self):
        draft = SimpleNamespace(id=5, status="draft")
        pending = SimpleNamespace(id=6, status="approved")
        db = MagicMock()
        service = SolutionVersionService(db)

        db.query.return_value = FakeQuery(get_map={5: draft})
        version = await service.submit_for_review(5)
        assert version.status == "pending_review"
        db.commit.assert_called_once()

        db.commit.reset_mock()
        db.query.return_value = FakeQuery(get_map={6: pending})
        with pytest.raises(ValueError, match="只能提交 draft 状态的版本"):
            await service.submit_for_review(6)
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_approve_and_reject_version(self):
        version = SimpleNamespace(id=8, solution_id=3, status="pending_review")
        solution = SimpleNamespace(id=3, current_version_id=None)
        rejected = SimpleNamespace(id=9, solution_id=3, status="pending_review")
        db = MagicMock()
        service = SolutionVersionService(db)
        db.query.side_effect = [
            FakeQuery(get_map={8: version}),
            FakeQuery(get_map={3: solution}),
            FakeQuery(get_map={9: rejected}),
        ]

        approved = await service.approve_version(8, approved_by=11, comments="通过")
        denied = await service.reject_version(9, rejected_by=12, comments="重做")

        assert approved.status == "approved"
        assert approved.approved_by == 11
        assert isinstance(approved.approved_at, datetime)
        assert approved.approval_comments == "通过"
        assert solution.current_version_id == 8
        assert denied.status == "rejected"
        assert denied.approved_by == 12
        assert denied.approval_comments == "重做"
        assert db.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_reject_version_requires_comments(self):
        service = SolutionVersionService(MagicMock())

        with pytest.raises(ValueError, match="驳回必须填写原因"):
            await service.reject_version(1, rejected_by=2, comments="")

    @pytest.mark.asyncio
    async def test_get_version_history_compare_and_latest(self):
        db = MagicMock()
        service = SolutionVersionService(db)
        history = [SimpleNamespace(id=2), SimpleNamespace(id=1)]
        v1 = SimpleNamespace(
            id=1,
            version_no="V1.0",
            status="draft",
            created_at=datetime(2026, 4, 1, 8, 0, 0),
            generated_solution="A",
            architecture_diagram="arch1",
            bom_list=[1],
            technical_parameters={"x": 1},
        )
        v2 = SimpleNamespace(
            id=2,
            version_no="V1.1",
            status="approved",
            created_at=datetime(2026, 4, 2, 9, 0, 0),
            generated_solution="B",
            architecture_diagram="arch1",
            bom_list=[1, 2],
            technical_parameters={"x": 2},
        )
        latest = SimpleNamespace(id=2, version_no="V1.1")
        db.query.side_effect = [
            FakeQuery(all_value=history),
            FakeQuery(get_map={1: v1}),
            FakeQuery(get_map={2: v2}),
            FakeQuery(first_value=latest),
        ]

        result_history = await service.get_version_history(1)
        compared = await service.compare_versions(1, 2)
        result_latest = service._get_latest_version(1)

        assert result_history == history
        assert compared["has_differences"] is True
        assert compared["differences"]["generated_solution"] == {"version_1": "A", "version_2": "B"}
        assert compared["differences"]["bom_list"] == {"version_1": [1], "version_2": [1, 2]}
        assert compared["version_1"]["created_at"] == "2026-04-01T08:00:00"
        assert compared["version_2"]["status"] == "approved"
        assert result_latest is latest

    @pytest.mark.asyncio
    async def test_compare_versions_raises_when_missing(self):
        db = MagicMock()
        db.query.side_effect = [FakeQuery(get_map={1: None}), FakeQuery(get_map={2: SimpleNamespace(id=2)})]
        service = SolutionVersionService(db)

        with pytest.raises(ValueError, match="版本不存在"):
            await service.compare_versions(1, 2)
