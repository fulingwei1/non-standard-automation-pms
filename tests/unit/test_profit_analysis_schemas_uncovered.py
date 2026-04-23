from app.schemas.project.profit_analysis import (
    HighProfitPatternsResponse,
    LowProfitRootCauseResponse,
    MarginAnalysisResponse,
    OptimizationSuggestion,
    ProfitAnalysisResponse,
    QuoteVarianceSummary,
)


def test_profit_analysis_nested_models():
    suggestion = OptimizationSuggestion(
        type="cost_overrun",
        cost_type="labor",
        suggestion="控制加班",
        priority="high",
        current_amount=12000.0,
        potential_saving=3000.0,
    )
    variance = QuoteVarianceSummary(
        has_quote=True,
        overall_variance=5000.0,
        overall_variance_pct=12.5,
        top_variances=[{"type": "labor", "variance": 2000.0}],
    )
    response = ProfitAnalysisResponse(
        project_id=1,
        current_margin=100000.0,
        current_margin_rate=22.5,
        forecast_margin=80000.0,
        forecast_margin_rate=18.0,
        target_margin_rate=25.0,
        margin_gap=2.5,
        health="warning",
        contract_amount=500000.0,
        actual_cost=300000.0,
        remaining_cost=120000.0,
        forecast_total_cost=420000.0,
        optimization_suggestions=[suggestion],
        quote_variance=variance,
    )

    assert response.optimization_suggestions[0].priority == "high"
    assert response.quote_variance.has_quote is True
    assert response.quote_variance.top_variances[0]["type"] == "labor"


def test_profit_analysis_summary_models_defaults():
    margin = MarginAnalysisResponse(project_id=1)
    high_profit = HighProfitPatternsResponse()
    low_profit = LowProfitRootCauseResponse()

    assert margin.target_margin_rate == 25.0
    assert margin.health == "healthy"
    assert high_profit.high_profit_threshold == 30.0
    assert high_profit.high_profit_projects == []
    assert high_profit.patterns == {}
    assert low_profit.low_profit_threshold == 10.0
    assert low_profit.low_profit_projects == []
    assert low_profit.warning_signals == []
    assert low_profit.improvements == []
