# Data Reconciliation Pipeline

## 1. Project Overview

The Data Reconciliation Pipeline is a Python-based project that compares source and target order datasets to identify data quality issues and inconsistencies.

It validates order records, detects duplicate IDs, compares order amounts, identifies missing records, calculates aggregate totals, and generates machine-readable reconciliation reports.

## 2. Features

- CSV source and target data processing
- Required-field and data-type validation
- Detection of missing order IDs and amounts
- Detection of invalid and negative amounts
- Duplicate order ID detection
- Record-level reconciliation using order IDs
- Detection of amount mismatches and missing records
- Source and target aggregate amount comparison
- JSON reconciliation report
- CSV mismatch and rejected-record reports
- Logging of pipeline activity and errors
- Execution-time measurement
- Automated unit tests
- Synthetic data generation with a fixed random seed
- Support for generating 100,000 records

## 3. Technology Stack

- Python
- CSV and JSON
- `pathlib`
- `logging`
- `unittest`
- `uv`

The project uses Python's standard library for its current pipeline implementation.

## 4. Project Structure

```text
data-reconciliation-pipeline/
├── main.py
├── generate_data.py
├── pyproject.toml
├── uv.lock
├── .gitignore
├── tests/
│   └── test_pipeline.py
├── data/
│   ├── source_orders.csv
│   └── target_orders.csv
└── README.md
```

The `output/` directory contains generated reports and logs created when the pipeline runs.

## 5. Requirements

- Python installed
- `uv` installed
- Visual Studio Code or another code editor

## 6. Setup

Open the project folder in your terminal:

```powershell
cd C:\Users\MAIDA\OneDrive\Desktop\data-reconciliation-pipeline
```

If the synthetic datasets need to be regenerated, run:

```powershell
uv run python generate_data.py
```

## 7. Run the Pipeline

Run the following command:

```powershell
uv run python main.py
```

The pipeline reads the source and target CSV files, validates records, performs reconciliation, and generates output reports.

## 8. Run Automated Tests

Execute the unit tests with:

```powershell
uv run python -m unittest discover -s tests -v
```

The test suite covers valid records, missing values, invalid amounts, duplicate IDs, empty inputs, amount mismatches, missing records, negative amounts, and successful reconciliation.

## 9. Input Data Dictionary

| Field | Type | Description |
|---|---|---|
| `order_id` | String | Unique identifier for an order |
| `amount` | Integer | Order amount used for reconciliation |

Both source and target datasets are expected to contain `order_id` and `amount` columns.

## 10. Output Files

### `reconciliation_report.json`

Contains row counts, valid and rejected record counts, matched records, mismatch counts, missing-record counts, aggregate amounts, reconciliation status, and execution duration.

### `mismatches.csv`

Contains records with reconciliation differences, including the order ID, issue type, source amount, and target amount.

### `rejects.csv`

Contains invalid records with their source file, row number, order ID, amount, and rejection reason.

### `pipeline.log`

Records pipeline start, data loading, validation, reconciliation results, completion, and errors.

## 11. Reconciliation Logic

Records are compared using `order_id` as the business key.

- Matching IDs and amounts are counted as matched records.
- Matching IDs with different amounts are reported as amount mismatches.
- Records present only in the source or only in the target are reported separately.
- Invalid records and duplicate IDs are rejected during validation.

The pipeline reports `PASSED` when there are no rejected records, amount mismatches, or missing records. Otherwise, it reports `FAILED`.

## 12. Synthetic Dataset

The data generator uses a fixed random seed to produce reproducible test data.

The current sample contains 100,000 source records and 100,000 target records. It intentionally changes every 100th target amount to test the pipeline's mismatch detection.

Expected results for this dataset:

- Source records: 100,000
- Target records: 100,000
- Matching records: 99,000
- Amount mismatches: 1,000
- Rejected records: 0

The reconciliation status is expected to be `FAILED` because the generated target data deliberately contains amount differences.

## 13. Idempotency and Repeatability

The pipeline writes the JSON and CSV reports in write mode, replacing previous report contents on each run rather than appending duplicate report rows.

The synthetic data generator uses a fixed seed to make generated data reproducible.

## 14. Current Limitations

- The current input format is CSV.
- The reconciliation business key is `order_id`.
- Amounts are represented as integers.
- The current implementation processes data in memory.
- The pipeline has been tested with a synthetic dataset of 100,000 records.

## 15. Future Improvements

- Add configurable validation rules.
- Add more domain-specific edge-case tests.
- Add performance testing with larger datasets.
- Improve structured logging and run metadata.
- Add schema configuration and more detailed aggregate checks.
- Add continuous integration for automated testing.

## 16. Architecture

The Data Reconciliation Pipeline follows a modular workflow:

1. **Data Ingestion:** Read source and target order records from CSV files.
2. **Data Validation:** Validate required fields, amount formats, negative values, and duplicate order IDs. Invalid records are written to the rejects report.
3. **Reconciliation:** Compare valid source and target records using `order_id` as the business key.
4. **Aggregate Validation:** Calculate source and target amount totals and identify aggregate differences.
5. **Reporting:** Generate a JSON summary, a CSV file containing mismatches, and a CSV file containing rejected records.
6. **Logging and Metrics:** Record pipeline activity, errors, and execution duration.

### Data Flow

`Source CSV + Target CSV` → `Validation` → `Reconciliation` → `Aggregate Comparison` → `JSON Report + Mismatch CSV + Rejects CSV`

The pipeline uses Python's standard library and processes the datasets in memory. Output reports are overwritten on each run, while the pipeline log records execution history.

## 17. Design Decisions and Trade-offs

### Python Standard Library

The pipeline uses Python's built-in modules, including `csv`, `json`, `pathlib`, and `logging`. This keeps the implementation lightweight and reduces external dependencies.

**Trade-off:** The implementation is simple to set up, but advanced data processing features would require additional libraries or custom code.

### CSV as the Input Format

CSV files provide a simple, portable format for source and target datasets.

**Trade-off:** CSV is easy to inspect and process, but it does not enforce a schema as strictly as a database.

### Order ID as the Business Key

The pipeline uses `order_id` to identify and compare records between the source and target datasets.

**Trade-off:** This works when order IDs are unique. Duplicate IDs are rejected during validation to avoid ambiguous comparisons.

### In-Memory Processing

The pipeline loads records into memory before validation and reconciliation.

**Trade-off:** This approach is straightforward and performs well for the current 100,000-record dataset, but much larger datasets may require chunked or streaming processing.

### Deterministic Synthetic Data

The generator uses a fixed random seed and deliberately modifies every 100th target amount to create predictable test scenarios.

**Trade-off:** This makes testing reproducible, although synthetic data does not cover every real-world data quality issue.

### Separate Reports for Mismatches and Rejected Records

Reconciliation mismatches and invalid input records are written to separate CSV files so that data quality problems can be investigated independently.

**Trade-off:** This improves traceability but requires users to inspect multiple output files alongside the JSON summary.

### Repeatable Report Generation

JSON and CSV reports are written in overwrite mode so that rerunning the pipeline does not append duplicate report rows.

**Trade-off:** Previous report contents are replaced, so historical report versions must be archived separately if they are needed.

## 18. Performance

The pipeline was tested using a synthetic dataset containing 100,000 source records and 100,000 target records.

### Observed Results

| Metric | Result |
|---|---:|
| Source records processed | 100,000 |
| Target records processed | 100,000 |
| Matched records | 99,000 |
| Amount mismatches | 1,000 |
| Rejected records | 0 |
| Observed execution time | Approximately 0.5 seconds |

The execution time is taken from a local run and may vary depending on hardware, system load, and the environment.

### Performance Considerations

- The pipeline uses in-memory processing and dictionaries keyed by `order_id` for record comparison.
- The current implementation is suitable for experimenting with datasets of 100,000 records.
- Memory usage grows with the size of the input datasets because records are loaded into memory.
- Larger datasets should be tested separately before making scalability claims.
- Future optimization could include chunked processing, memory profiling, and repeatable benchmarks across different dataset sizes.
