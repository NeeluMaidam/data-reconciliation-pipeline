
# Data Reconciliation Pipeline

## 1. Project Overview

The Data Reconciliation Pipeline is a Python-based application that compares source and target order datasets to identify data quality issues and inconsistencies.

It validates order records, detects duplicate IDs, compares order amounts, identifies missing records, calculates aggregate totals, and generates machine-readable reconciliation reports.

The project demonstrates a repeatable data validation and reconciliation workflow using CSV files and Python's standard library.

## 2. Key Features

- CSV source and target data ingestion
- Required-field and schema validation
- Data type and amount validation
- Detection of missing order IDs and amounts
- Detection of invalid and negative amounts
- Duplicate order ID detection
- Record-level reconciliation using order IDs
- Detection of amount mismatches
- Identification of records missing from either dataset
- Source and target aggregate amount comparison
- JSON reconciliation summary report
- CSV mismatch and rejected-record reports
- Run ID and UTC timestamp tracking
- Logging and execution-time measurement
- Deterministic synthetic data generation
- Automated unit tests
- Support for testing with 100,000 records

## 3. Technology Stack

- Python 3.11+
- CSV and JSON
- pathlib
- logging
- unittest
- uv

The current implementation uses Python's standard library and does not require external data-processing libraries.

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

The `output/` directory is created when the pipeline runs. It contains generated reconciliation reports and log files.

## 5. Requirements

- Python 3.11 or later
- uv package manager
- Visual Studio Code or another code editor

## 6. Setup and Installation

Clone or download the repository and open the project folder in the terminal.

```bash
cd data-reconciliation-pipeline
```

Install the project dependencies and prepare the environment:

```bash
uv sync
```

The project currently uses Python's standard library, so there are no additional runtime dependencies.

## 7. Generate Synthetic Data

To generate the source and target datasets, run:

```bash
uv run python generate_data.py
```

The generator:

- Uses a fixed random seed (42) for reproducibility.
- Creates 100,000 source order records.
- Generates corresponding target records.
- Intentionally increases the amount of every 100th target record by 50.
- Produces predictable reconciliation differences for testing.

The generated files are saved in the `data/` directory.

## 8. Run the Pipeline

Execute:

```bash
uv run python main.py
```

The pipeline performs the following operations:

1. Reads the source and target CSV files.
2. Validates the input schemas and records.
3. Identifies invalid records and duplicate order IDs.
4. Compares valid records using `order_id`.
5. Detects amount mismatches and missing records.
6. Calculates aggregate totals.
7. Generates JSON and CSV reports.
8. Displays the reconciliation summary and execution time.

## 9. Run Automated Tests

Execute the test suite:

```bash
uv run python -m unittest discover -s tests -v
```

The current test suite contains 16 tests covering:

- Valid order records
- Successful reconciliation
- Matching records
- Amount mismatches
- Missing source records
- Missing target records
- Missing order IDs
- Missing amounts
- Null amounts
- Invalid amounts
- Negative amounts
- Duplicate order IDs
- Empty input
- Whitespace in order IDs
- Malformed amounts
- Aggregate differences

**Latest test result: All 16 tests passed.**

## 10. Input Data Dictionary

Both input datasets are CSV files.

| Field | Data Type | Description |
|---|---|---|
| order_id | String | Unique identifier used to identify an order |
| amount | Integer | Order amount used for reconciliation |

### Business Key

`order_id` is the business key used to compare source and target records.

Duplicate order IDs are rejected during validation to avoid ambiguous comparisons.

## 11. Output Files

The pipeline generates the following files inside the `output/` directory.

### reconciliation_report.json

Contains the reconciliation summary, including:

- Unique run ID
- Pipeline start and finish timestamps in UTC
- Source and target row counts
- Valid source and target record counts
- Rejected record count
- Matched record count
- Amount mismatch count
- Missing source and target record counts
- Source and target aggregate totals
- Aggregate difference
- Aggregate comparison result
- Reconciliation status
- Execution duration

### mismatches.csv

Contains record-level reconciliation differences, including:

- `run_id`
- `order_id`
- Issue type
- Source amount
- Target amount

### rejects.csv

Contains invalid records and validation details, including:

- `run_id`
- Source file
- Source row number
- Order ID
- Amount
- Rejection reason

### pipeline.log

Contains execution logs and error information to help monitor pipeline activity and investigate failures.

The JSON report provides a summary, while the CSV files provide details for investigating individual records.

## 12. Reconciliation Logic

The pipeline compares valid source and target records using `order_id`.

The reconciliation process identifies:

- **Matched records:** Order IDs and amounts match in both datasets.
- **Amount mismatches:** Order IDs exist in both datasets, but their amounts differ.
- **Missing from target:** Records exist in the source but not in the target.
- **Missing from source:** Records exist in the target but not in the source.
- **Rejected records:** Records that fail input validation.

### Reconciliation Status

The pipeline reports **PASSED** when there are no rejected records, amount mismatches, missing records, or aggregate differences.

It reports **FAILED** when any reconciliation difference or rejected record is detected.

The aggregate difference is calculated by comparing the total source amount with the total target amount. This provides an additional check to identify inconsistencies between the datasets.

## 13. Synthetic Dataset and Expected Results

The generator creates a reproducible dataset using a fixed random seed.

### Current Dataset Configuration

| Metric | Expected Value |
|---|---:|
| Source records | 100,000 |
| Target records | 100,000 |
| Matching records | 99,000 |
| Amount mismatches | 1,000 |
| Rejected records | 0 |
| Missing records | 0 |
| Aggregate difference | 50,000 |

Every 100th target record has its amount increased by 50.

Therefore:

- 1,000 records contain intentional amount mismatches.
- The target aggregate is 50,000 greater than the source aggregate.
- The expected reconciliation status is FAILED.

This is an intentional test scenario. A FAILED reconciliation status confirms that the pipeline detects the injected differences; it does not mean that the program failed to execute.

## 14. Idempotency and Repeatability

The pipeline uses write mode when generating its JSON and CSV reports.

When the same pipeline is executed again:

- Existing report files are overwritten.
- Duplicate report rows are not appended.
- A new unique run ID is generated.
- New execution timestamps and metrics are recorded.

The data generator uses a fixed random seed to produce reproducible datasets.

This supports repeatable testing and prevents previous report contents from being mixed with the latest run.

## 15. Logging and Monitoring

The pipeline uses Python's logging module to record execution activity and errors.

Run information includes a unique run ID, timestamps, record counts, rejection counts, and execution duration in the generated reconciliation report.

These details help identify and investigate reconciliation results.

## 16. Current Limitations

- CSV is the only supported input format.
- The reconciliation business key is `order_id`.
- Amounts are represented as integers.
- The current implementation processes records in memory.
- The generator currently uses a fixed record count of 100,000.
- Previous reconciliation reports are overwritten during subsequent runs.
- The implementation does not currently publish results to a database.
- Automated retry and recovery workflows are not implemented.
- Performance has been measured using a local synthetic dataset.

## 17. Future Improvements

Possible future enhancements include:

- Configurable input file paths and record counts.
- Support for additional input formats such as JSON and databases.
- Chunked or streaming processing for larger datasets.
- More domain-specific validation rules.
- Additional referential integrity checks.
- Historical report storage and run comparison.
- Automated retry and recovery mechanisms.
- Structured logging and improved monitoring.
- Performance and memory profiling.
- Continuous integration for automated test execution.

## 18. Architecture

The Data Reconciliation Pipeline follows a modular workflow.

### Processing Stages

1. **Data Generation:** Create reproducible source and target datasets.
2. **Data Ingestion:** Read source and target order records from CSV files.
3. **Schema Validation:** Check required columns and input structure.
4. **Data Validation:** Validate order IDs and amounts, and identify duplicates.
5. **Reconciliation:** Compare valid source and target records using `order_id`.
6. **Aggregate Validation:** Calculate source and target totals and identify differences.
7. **Reporting:** Generate the JSON summary, mismatch CSV, and rejects CSV.
8. **Logging and Metrics:** Record execution activity and performance information.

### Data Flow

```text
Synthetic Data Generation
          |
          v
Source CSV + Target CSV
          |
          v
Schema Validation
          |
          v
Record Validation
          |
          +-------> Rejected Records
          |
          v
Record-Level Reconciliation
          |
          v
Aggregate Comparison
          |
          v
JSON Reconciliation Report
Mismatch CSV
Rejects CSV
          |
          v
Execution Summary and Metrics
```

## 19. Design Decisions and Trade-offs

### Python Standard Library

The project uses built-in Python modules such as `csv`, `json`, `pathlib`, and `logging`.

**Trade-off:** This keeps the implementation lightweight and easy to set up, but advanced processing features may require additional libraries.

### CSV Input Format

CSV provides a simple and portable format for source and target datasets.

**Trade-off:** CSV is easy to inspect, but it does not enforce data types and constraints as strictly as a database.

### Order ID as the Business Key

The pipeline uses `order_id` to identify and compare records.

**Trade-off:** This works when order IDs are unique. Duplicate IDs are rejected to avoid ambiguous comparisons.

### In-Memory Processing

The current implementation processes records in memory.

**Trade-off:** This is straightforward for the current dataset size, but larger datasets may require chunked or streaming processing.

### Deterministic Synthetic Data

The generator uses a fixed random seed and intentionally introduces amount mismatches.

**Trade-off:** This makes test results predictable and reproducible, although synthetic data cannot represent every real-world data quality issue.

### Separate Mismatch and Reject Reports

Mismatches and invalid records are written to separate CSV files.

**Trade-off:** This makes investigation easier, but users need to inspect multiple reports.

### Report Overwriting

Output reports are overwritten on every run.

**Trade-off:** This prevents duplicate report entries but does not preserve historical report versions.

## 20. Performance and Execution Results

The pipeline was tested locally using 100,000 source records and 100,000 target records.

### Latest Observed Results

| Metric | Result |
|---|---:|
| Source records processed | 100,000 |
| Target records processed | 100,000 |
| Valid source records | 100,000 |
| Valid target records | 100,000 |
| Matched records | 99,000 |
| Amount mismatches | 1,000 |
| Rejected records | 0 |
| Missing source records | 0 |
| Missing target records | 0 |
| Aggregate difference | 50,000 |
| Observed execution time | 0.628 seconds |
| Reconciliation status | FAILED |

The FAILED status is expected because the synthetic target dataset intentionally contains amount differences.

The execution time is based on a local run and may vary depending on hardware, system load, and environment.

### Performance Considerations

- The pipeline uses dictionaries keyed by `order_id` for record comparison.
- The current implementation has been tested with 100,000 records in each dataset.
- Memory usage increases with input size because records are processed in memory.
- Larger datasets should be tested before making scalability claims.
- Future performance work could include chunked processing, memory profiling, and repeatable benchmarks.

## Conclusion

This project demonstrates a reproducible data reconciliation workflow that validates input records, identifies data quality issues, compares source and target datasets, checks aggregate totals, and generates machine-readable reports.

It also demonstrates automated testing, deterministic synthetic data generation, run tracking, and repeatable report generation using Python.
