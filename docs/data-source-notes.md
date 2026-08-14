# Spoonacular Menu Data Notes

**Status:** Historical exploration notes; verify limits and pricing before relying on them

This document records observations that informed the first TasteIQ dataset. It is not an authoritative description of the current Spoonacular API. Quotas, prices, fields, and endpoint behavior can change and must be verified before running a new ingestion job.

## Endpoint used

The original ingestion used the menu-item search endpoint:

```http
GET /food/menuItems/search
```

Pagination used `offset` and `number`. The observed records included fields such as:

- ID
- Title
- Restaurant chain
- Image and image type
- Servings
- Optional nutrition and macronutrient data

Requesting expanded menu-item information changed the response depth and increased API usage. Ingestion therefore needs to handle multiple response shapes and make enrichment explicit and cost-aware.

## Data-quality observations

### Nutrition

Nutrition records can contain a nutrient name, amount, unit, and percentage of daily need. Nutrition is not guaranteed to be present or complete for every menu item.

The most useful observed fields were:

- Calories
- Protein
- Fat
- Carbohydrates

These fields were more consistently available and relevant than vitamins, minerals, micronutrients, or percentages of daily need. Even macros must retain source provenance and should not be represented as known when missing.

### Serving information

Serving quantities and units were inconsistent across records. Cross-item nutrition comparisons should not assume equivalent serving sizes without a normalization strategy.

### Generated text

Generated descriptions were frequently absent and should not be treated as a dependable retrieval field.

### Cuisine labels

The observed menu items did not provide dependable cuisine labels. Cuisine classification would therefore require derived labels from restaurant metadata and item text. Any derived cuisine must be marked as inferred rather than source ground truth.

### Low-value fields

The initial exploration did not find the following fields reliable enough for core recommendation logic:

- Likes
- Platform-specific scores
- Inferred micronutrients
- Percentages of daily need

Some may still be useful for display or experiments, but they should not silently influence hard constraints.

## Ingestion implications

The production ingestion path should:

1. Store raw source payloads with fetch timestamps.
2. Record the request mode that produced each payload.
3. Validate multiple possible response shapes.
4. Track API consumption and rate-limit responses.
5. Use bounded concurrency and retry only transient failures.
6. Preserve missing values as unknown.
7. Store source and confidence for inferred fields.
8. Measure field coverage after every ingestion run.

The current repository contains an incomplete historical snapshot. These observations should inform a new reproducible ingestion pipeline, not substitute for validating the present API and dataset.
