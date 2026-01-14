from app.api.v1.endpoints.business_support_orders.utils import (
    _serialize_attachments,
    _deserialize_attachments,
)


def test_serialize_and_deserialize_attachments_round_trip():
    attachments = ["invoice.pdf", "evidence.docx"]
    serialized = _serialize_attachments(attachments)

    assert isinstance(serialized, str)
    assert _deserialize_attachments(serialized) == attachments


def test_serialize_none_returns_none():
    assert _serialize_attachments(None) is None
    assert _deserialize_attachments(None) is None


def test_deserialize_invalid_payload_wraps_value():
    payload = "plain-text"
    assert _deserialize_attachments(payload) == [payload]
