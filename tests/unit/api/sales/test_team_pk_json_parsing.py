# -*- coding: utf-8 -*-
"""团队 PK JSON 兼容解析测试"""

from app.api.v1.endpoints.sales.team.pk import _safe_parse_id_list, _safe_parse_json


class TestTeamPKJsonParsing:
    def test_safe_parse_id_list_handles_json_array(self):
        assert _safe_parse_id_list("[1, 2, 3]") == [1, 2, 3]

    def test_safe_parse_id_list_handles_legacy_delimiters(self):
        assert _safe_parse_id_list("1;2|3 4") == [1, 2, 3, 4]

    def test_safe_parse_id_list_handles_invalid_json_without_crash(self):
        assert _safe_parse_id_list("{broken") == []

    def test_safe_parse_id_list_accepts_scalar_json(self):
        assert _safe_parse_id_list("5") == [5]

    def test_safe_parse_json_returns_object_for_valid_json(self):
        assert _safe_parse_json('{"winner": 1, "score": 99}') == {"winner": 1, "score": 99}

    def test_safe_parse_json_returns_none_for_invalid_json(self):
        assert _safe_parse_json("{broken") is None
