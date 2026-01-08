from app.api.v1.endpoints import business_support_orders as bs_orders


def test_serialize_and_deserialize_attachments_round_trip():
    attachments = ["invoice.pdf", "evidence.docx"]
    serialized = bs_orders._serialize_attachments(attachments)

    assert isinstance(serialized, str)
    assert bs_orders._deserialize_attachments(serialized) == attachments


def test_serialize_none_returns_none():
    assert bs_orders._serialize_attachments(None) is None
    assert bs_orders._deserialize_attachments(None) is None


def test_deserialize_invalid_payload_wraps_value():
    payload = "plain-text"
    assert bs_orders._deserialize_attachments(payload) == [payload]
