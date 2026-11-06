import json
from pathlib import Path

import pytest

from connoisseur_companion.services import RestaurantService


@pytest.fixture(scope="module")
def service() -> RestaurantService:
    return RestaurantService()


def test_partial_name_search_returns_all_matching_dataset_records(
    service: RestaurantService,
) -> None:
    data_path = Path(__file__).resolve().parents[2] / "data" / "raw"
    restaurants = json.loads(
        (data_path / "structured_restaurant_data.json").read_text(encoding="utf-8")
    )
    expected_ids = {
        restaurant["itemId"]
        for restaurant in restaurants
        if "iron" in restaurant["name"].casefold()
    }

    results = service.search_restaurants("Iron", limit=len(expected_ids))

    assert {restaurant["itemId"] for restaurant in results} == expected_ids
    assert all("iron" in restaurant["name"].casefold() for restaurant in results)


def test_partial_name_search_is_case_insensitive(service: RestaurantService) -> None:
    assert service.search_restaurants("iRoN", limit=12) == service.search_restaurants(
        "Iron", limit=12
    )


def test_partial_name_search_orders_exact_match_first(
    service: RestaurantService,
) -> None:
    results = service.search_restaurants("Iron & Embers")

    assert results[0]["name"] == "Iron & Embers"


def test_partial_name_search_returns_empty_for_unknown_name(
    service: RestaurantService,
) -> None:
    assert service.search_restaurants("No Such Restaurant") == []


@pytest.mark.parametrize("query", ["", "   "])
def test_partial_name_search_rejects_empty_query(
    service: RestaurantService, query: str
) -> None:
    with pytest.raises(ValueError, match="query must be a non-empty phrase"):
        service.search_restaurants(query)


@pytest.mark.parametrize("limit", [0, -1])
def test_partial_name_search_rejects_non_positive_limit(
    service: RestaurantService, limit: int
) -> None:
    with pytest.raises(ValueError, match="limit must be at least 1"):
        service.search_restaurants("Iron", limit=limit)
