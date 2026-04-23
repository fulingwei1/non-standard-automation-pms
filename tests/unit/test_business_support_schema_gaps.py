import app.schemas.business_support as business_support


def test_business_support_compat_module_exports_expected_names():
    assert "BiddingProjectCreate" in business_support.__all__
    assert "SupplierRegistrationReviewRequest" in business_support.__all__
    assert business_support.BiddingProjectCreate is not None
    assert business_support.SupplierRegistrationReviewRequest is not None
