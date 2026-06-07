from app.schemas.presale_technical_parameter import CostEstimateRequest


def test_cost_estimate_request_keeps_sales_presale_project_context():
    request = CostEstimateRequest(
        template_id=1,
        lead_id=2026,
        opportunity_id=2,
        ticket_id=501,
        project_id=42,
        parameters={"test_station_count": 4},
    )

    assert request.lead_id == 2026
    assert request.opportunity_id == 2
    assert request.ticket_id == 501
    assert request.project_id == 42
