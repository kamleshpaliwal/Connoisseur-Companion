# Restaurant data

The raw JSON files in `raw/` are copies of the course capstone source files. Keep these source copies unchanged; parsing and normalization belong in application code so the original data stays inspectable.

## Files

- `raw/structured_restaurant_data.json` — 210 restaurant records. Each record contains `name`, `location`, `type`, `food_style`, `rating`, `price_range`, `signatures`, `vibe`, `environment`, `shortcomings`, and `itemId`.
- `raw/augmented_user_review.json` — 10 review records. Each record contains `reviewId`, `userId`, `itemId`, `title`, `text`, `date`, `rating`, `language`, `images`, and `image_captions`.

## Data notes

- Reviews refer to restaurants through `itemId`; the current review IDs all match a restaurant in the restaurant file.
- The review `images` field is a string containing a serialized list of URLs, while `image_captions` is already a JSON list. A future loader should handle this mismatch explicitly.
- The course folder also named a `California-Culinary-Map.txt` file, but it was not present when the source directory was inspected.
