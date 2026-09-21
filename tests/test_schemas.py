from app.main import app


EXPECTED_RESPONSE_MODELS = {
    "/profiles/{dataset_id}": "ProfileResponse",
    "/analytics/quality/{dataset_id}": "QualityResponse",
    "/analytics/statistics/{dataset_id}": "StatisticsResponse",
    "/analytics/kpis/{dataset_id}": "KPIResponse",
    "/analytics/trends/{dataset_id}": "TrendResponse",
    "/analytics/insights/{dataset_id}": "InsightsResponse",
    "/analytics/recommendations/{dataset_id}": (
        "RecommendationsResponse"
    ),
}


def test_analytics_routes_have_response_models():
    routes = {
        route.path: route
        for route in app.routes
    }

    for path, expected_model in EXPECTED_RESPONSE_MODELS.items():
        assert path in routes

        route = routes[path]

        assert route.response_model is not None
        assert route.response_model.__name__ == expected_model


def test_openapi_contains_analytics_routes():
    openapi = app.openapi()

    for path in EXPECTED_RESPONSE_MODELS:
        assert path in openapi["paths"]


def test_openapi_contains_response_schemas():
    openapi = app.openapi()
    schemas = openapi["components"]["schemas"]

    expected_schemas = [
        "ProfileResponse",
        "QualityResponse",
        "StatisticsResponse",
        "KPIResponse",
        "TrendResponse",
        "InsightsResponse",
        "RecommendationsResponse",
    ]

    for schema_name in expected_schemas:
        assert schema_name in schemas