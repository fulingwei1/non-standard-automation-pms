import app.schemas.business_support as business_support_compat


def test_business_support_compat_exports_expected_symbols():
    assert business_support_compat.BiddingProjectCreate is not None
    assert business_support_compat.SupplierRegistrationReviewRequest is not None
    assert "BiddingProjectCreate" in business_support_compat.__all__
    assert "SupplierRegistrationReviewRequest" in business_support_compat.__all__
