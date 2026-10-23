"""Deterministic services for querying the restaurant and review data."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class DataLoadError(ValueError):
    """Raised when the source data is missing or does not match its expected shape."""


class RestaurantService:
    """Load the JSON data once and provide deterministic restaurant lookups."""

    RESTAURANT_FIELDS = {
        "name",
        "location",
        "type",
        "food_style",
        "rating",
        "price_range",
        "signatures",
        "vibe",
        "environment",
        "shortcomings",
        "itemId",
    }
    REVIEW_FIELDS = {
        "reviewId",
        "userId",
        "itemId",
        "title",
        "text",
        "date",
        "rating",
        "language",
        "images",
        "image_captions",
    }

    def __init__(self, raw_data_dir: Path | str | None = None) -> None:
        if raw_data_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            raw_data_dir = project_root / "data" / "raw"

        raw_data_dir = Path(raw_data_dir)
        restaurants = self._read_records(
            raw_data_dir / "structured_restaurant_data.json",
            self.RESTAURANT_FIELDS,
        )
        reviews = self._read_records(
            raw_data_dir / "augmented_user_review.json",
            self.REVIEW_FIELDS,
        )

        restaurant_ids = [restaurant["itemId"] for restaurant in restaurants]
        review_ids = [review["reviewId"] for review in reviews]
        if len(restaurant_ids) != len(set(restaurant_ids)):
            raise DataLoadError("Restaurant data contains duplicate itemId values.")
        if len(review_ids) != len(set(review_ids)):
            raise DataLoadError("Review data contains duplicate reviewId values.")

        known_restaurant_ids = set(restaurant_ids)
        orphan_review_ids = sorted(
            {review["itemId"] for review in reviews} - known_restaurant_ids
        )
        if orphan_review_ids:
            raise DataLoadError(
                "Reviews refer to unknown restaurant itemId values: "
                f"{orphan_review_ids}"
            )

        self._restaurants = restaurants
        self._restaurants_by_id = {
            restaurant["itemId"]: restaurant for restaurant in restaurants
        }
        self._reviews = reviews

    @staticmethod
    def _read_records(path: Path, required_fields: set[str]) -> list[dict[str, Any]]:
        try:
            with path.open(encoding="utf-8") as data_file:
                records = json.load(data_file)
        except OSError as exc:
            raise DataLoadError(f"Could not read data file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataLoadError(f"Invalid JSON in data file: {path}") from exc

        if not isinstance(records, list):
            raise DataLoadError(f"Expected a JSON list in data file: {path}")

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise DataLoadError(
                    f"Expected an object at record {index} in data file: {path}"
                )
            missing_fields = required_fields - record.keys()
            if missing_fields:
                raise DataLoadError(
                    f"Record {index} in {path.name} is missing fields: "
                    f"{sorted(missing_fields)}"
                )
        return records

    def get_restaurant_info(self, item_id: int) -> dict[str, Any] | None:
        """Return one restaurant by itemId, or None when it is not found."""
        restaurant = self._restaurants_by_id.get(item_id)
        return deepcopy(restaurant) if restaurant is not None else None

    def recommend_by_vibe(self, vibe: str, limit: int = 5) -> list[dict[str, Any]]:
        """Match an atmosphere phrase against vibe/environment, then rank by rating."""
        phrase = vibe.strip().casefold()
        if not phrase:
            raise ValueError("vibe must be a non-empty phrase")
        if limit < 1:
            raise ValueError("limit must be at least 1")

        matches = [
            restaurant
            for restaurant in self._restaurants
            if phrase
            in f"{restaurant['vibe']} {restaurant['environment']}".casefold()
        ]
        matches.sort(key=lambda restaurant: (-restaurant["rating"], restaurant["name"].casefold()))
        return deepcopy(matches[:limit])

    def get_review(self, item_id: int) -> list[dict[str, Any]]:
        """Return reviews for a restaurant, newest date first."""
        matches = [review for review in self._reviews if review["itemId"] == item_id]
        matches.sort(key=lambda review: (review["date"], review["reviewId"]), reverse=True)
        return deepcopy(matches)
