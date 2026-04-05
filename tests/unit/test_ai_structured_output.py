# -*- coding: utf-8 -*-
"""Tests for AI structured output helpers."""

from app.services.ai_structured_output import extract_json_payload


def test_extract_json_payload_from_code_block():
    content = """```json
    {"answer": "ok", "score": 95}
    ```"""

    payload = extract_json_payload(content)

    assert payload == {"answer": "ok", "score": 95}


def test_extract_json_payload_from_embedded_object():
    content = '模型输出如下：{"items":[{"name":"机器人"}]} 请查收'

    payload = extract_json_payload(content)

    assert payload == {"items": [{"name": "机器人"}]}


def test_extract_json_payload_invalid_returns_none():
    assert extract_json_payload("not json") is None
