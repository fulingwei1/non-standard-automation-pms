# -*- coding: utf-8 -*-
"""solution_extraction 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.ecn.knowledge.solution_extraction import (
    _auto_extract_solution,
    _build_solution_description,
    _extract_keywords,
    _extract_solution_steps,
    extract_solution,
)


class FakeQuery:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value or []

    def filter(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value


class TestSolutionExtractionDeep:
    def test_auto_extract_solution_priority(self):
        ecn = SimpleNamespace(
            solution="直接方案",
            execution_note="执行说明",
            change_description="解决方案 调整流程",
        )

        assert _auto_extract_solution(ecn) == "直接方案"

    def test_auto_extract_solution_from_change_description(self):
        ecn = SimpleNamespace(
            solution=None,
            execution_note=None,
            change_description="问题描述。解决方案 更换物料并重新校准",
        )

        assert _auto_extract_solution(ecn) == "更换物料并重新校准"

    def test_build_solution_description_with_fallback_parts(self):
        ecn = SimpleNamespace(
            change_description="改线",
            root_cause_analysis="设计错误",
            execution_note="重新加工",
        )

        result = _build_solution_description(ecn, "")

        assert "变更内容：改线" in result
        assert "根本原因：设计错误" in result
        assert "执行说明：重新加工" in result

    def test_build_solution_description_default_text(self):
        ecn = SimpleNamespace(change_description=None, root_cause_analysis=None, execution_note=None)

        assert _build_solution_description(ecn, "") == "暂无解决方案描述"

    def test_extract_keywords_includes_material_and_common_keywords(self):
        ecn = SimpleNamespace(
            id=1,
            ecn_type="DESIGN",
            root_cause_category="质量",
            change_description="物料设计变更，需要控制成本和交期",
        )
        materials = [
            SimpleNamespace(material_name="Motor Assembly"),
            SimpleNamespace(material_name="Cable Harness"),
        ]
        service = SimpleNamespace(db=Mock())
        service.db.query.return_value = FakeQuery(all_value=materials)

        result = _extract_keywords(service, ecn)

        assert "DESIGN" in result
        assert "质量" in result
        assert "物料" in result
        assert "成本" in result
        assert "交期" in result
        assert "Motor" in result
        assert "Assembly" in result
        assert len(result) <= 10

    def test_extract_solution_steps_from_solution_text(self):
        service = SimpleNamespace(db=Mock())
        ecn = SimpleNamespace(id=1)
        solution = "1. 拆除旧件\n2. 安装新件\n- 校准参数\n普通说明"

        result = _extract_solution_steps(service, ecn, solution)

        assert result == ["1. 拆除旧件", "2. 安装新件", "- 校准参数"]

    def test_extract_solution_steps_fallback_to_tasks(self):
        tasks = [
            SimpleNamespace(task_name="备料", task_description="准备新物料"),
            SimpleNamespace(task_name="调试", task_description=None),
        ]
        service = SimpleNamespace(db=Mock())
        service.db.query.return_value = FakeQuery(all_value=tasks)
        ecn = SimpleNamespace(id=2)

        result = _extract_solution_steps(service, ecn, "无序文本")

        assert result == ["备料: 准备新物料", "调试: "]

    def test_extract_solution_raises_when_ecn_missing(self):
        service = SimpleNamespace(db=Mock())
        service.db.query.return_value = FakeQuery(first_value=None)

        with pytest.raises(ValueError):
            extract_solution(service, 99)

    def test_extract_solution_end_to_end_manual_mode(self):
        ecn = SimpleNamespace(
            id=3,
            solution="1. 替换零件\n2. 回归测试",
            execution_note="备用说明",
            change_description="变更描述",
            cost_impact=1234.5,
            schedule_impact_days=3,
            ecn_type="PROCESS",
            root_cause_category="工艺",
            root_cause_analysis="工装偏差",
        )
        materials = [SimpleNamespace(material_name="Fixture Plate")]
        service = SimpleNamespace(db=Mock())
        service.db.query.side_effect = [
            FakeQuery(first_value=ecn),
            FakeQuery(all_value=materials),
        ]

        result = extract_solution(service, 3, auto_extract=False)

        assert result["ecn_id"] == 3
        assert result["solution"] == "1. 替换零件\n2. 回归测试"
        assert result["solution_steps"] == ["1. 替换零件", "2. 回归测试"]
        assert result["estimated_cost"] == 1234.5
        assert result["estimated_days"] == 3
        assert result["ecn_type"] == "PROCESS"
        assert result["root_cause_category"] == "工艺"
        assert "Fixture" in result["keywords"]
        assert isinstance(result["extracted_at"], str)
