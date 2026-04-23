# Open Dataset Support

NestGPT can now read local open datasets from this folder and use them alongside live web sources.

## How it works

- Add one or more manifest files ending in `.dataset.json`.
- Each manifest can either include `records` inline or point to a JSON file with `data_file`.
- The agent will only use datasets whose `countries`, `cities`, `dataset_type`/`market_type`, and optional `keywords` match the user's question.
- When a dataset is used, the answer pipeline includes:
  - dataset origin
  - source URL
  - license
  - dataset type and market type
  - preprocessing notes

## Recommended manifest shape

```json
{
  "name": "Lisbon Rent Samples 2025",
  "source": "Kaggle",
  "source_url": "https://www.kaggle.com/datasets/example/lisbon-rents",
  "license": "CC BY 4.0",
  "description": "Sample long-term rental rows for Lisbon neighborhoods.",
  "dataset_type": "rental",
  "market_type": "rent",
  "countries": ["Portugal"],
  "cities": ["Lisbon"],
  "keywords": ["rent", "housing", "budget"],
  "preprocessing": [
    "Filtered rows to Lisbon only",
    "Dropped records with missing monthly_rent_eur",
    "Kept the first 6 rows as lightweight evidence for prompting"
  ],
  "data_file": "lisbon_rent_samples.json"
}
```

## Data file shape

```json
[
  {
    "neighborhood": "Arroios",
    "monthly_rent_eur": 1450,
    "bedrooms": 1,
    "listing_type": "apartment"
  }
]
```

## Notes

- Keep only small, relevant slices here. This MVP injects dataset excerpts into the model prompt, so oversized files are not helpful.
- Verify each dataset's license and terms before adding it.
- Document any filtering, cleaning, deduplication, or sampling in `preprocessing`.
- Prefer explicit intent metadata: use `dataset_type` such as `rental` or `purchase`, and `market_type` such as `rent`, `sale`, or `transaction`.
