
import csv
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FILE = Path("data/source_orders.csv")
TARGET_FILE = Path("data/target_orders.csv")
OUTPUT_FOLDER = Path("output")

REQUIRED_COLUMNS = {"order_id", "amount"}
ALLOWED_COLUMNS = {"order_id", "amount"}


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def read_orders(file_path):
    rows = []

    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)

        if not reader.fieldnames:
            raise ValueError(f"CSV file is empty or has no header: {file_path}")

        columns = [name.strip().lower() for name in reader.fieldnames]

        if len(columns) != len(set(columns)):
            raise ValueError(f"Duplicate column names found in {file_path}")

        missing_columns = REQUIRED_COLUMNS - set(columns)
        unexpected_columns = set(columns) - ALLOWED_COLUMNS

        if missing_columns:
            raise ValueError(
                f"Missing required columns in {file_path}: "
                f"{sorted(missing_columns)}"
            )

        if unexpected_columns:
            raise ValueError(
                f"Unexpected columns in {file_path}: "
                f"{sorted(unexpected_columns)}"
            )

        reader.fieldnames = columns

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(
                    f"Malformed CSV row {row_number} in {file_path}: "
                    "too many fields"
                )

            if not row or all(
                value is None or not str(value).strip()
                for value in row.values()
            ):
                continue

            cleaned_row = {
                key.strip().lower(): (
                    value.strip() if value is not None else ""
                )
                for key, value in row.items()
            }

            rows.append(cleaned_row)

    return rows


def validate_orders(rows, file_name):
    valid_rows = []
    rejected_rows = []
    seen_ids = set()

    for row_number, row in enumerate(rows, start=2):
        order_id = row.get("order_id", "").strip()
        amount_value = row.get("amount")
        amount = "" if amount_value is None else str(amount_value).strip()
        reason = ""

        if not order_id:
            reason = "missing_order_id"

        elif not amount:
            reason = "missing_amount"

        else:
            try:
                numeric_amount = int(amount)

                if numeric_amount < 0:
                    reason = "invalid_amount"

            except ValueError:
                reason = "invalid_amount"

        if not reason and order_id in seen_ids:
            reason = "duplicate_order_id"

        if reason:
            rejected_rows.append({
                "source_file": file_name,
                "source_row_number": row_number,
                "order_id": order_id,
                "amount": amount,
                "reject_reason": reason
            })

        else:
            seen_ids.add(order_id)

            valid_rows.append({
                "order_id": order_id,
                "amount": str(int(amount))
            })

    return valid_rows, rejected_rows


def reconcile(source_orders, target_orders):
    source_by_id = {
        row["order_id"]: row for row in source_orders
    }

    target_by_id = {
        row["order_id"]: row for row in target_orders
    }

    matched_count = 0
    amount_mismatch_count = 0
    missing_from_source_count = 0
    missing_from_target_count = 0
    mismatches = []

    all_order_ids = sorted(
        set(source_by_id) | set(target_by_id)
    )

    for order_id in all_order_ids:
        source = source_by_id.get(order_id)
        target = target_by_id.get(order_id)

        if source is None:
            issue = "missing_from_source"
            missing_from_source_count += 1
            source_amount = ""
            target_amount = target["amount"]

        elif target is None:
            issue = "missing_from_target"
            missing_from_target_count += 1
            source_amount = source["amount"]
            target_amount = ""

        elif int(source["amount"]) != int(target["amount"]):
            issue = "amount_mismatch"
            amount_mismatch_count += 1
            source_amount = source["amount"]
            target_amount = target["amount"]

        else:
            matched_count += 1
            continue

        mismatches.append({
            "order_id": order_id,
            "issue": issue,
            "source_amount": source_amount,
            "target_amount": target_amount
        })

    return {
        "matched_records": matched_count,
        "amount_mismatches": amount_mismatch_count,
        "missing_from_source": missing_from_source_count,
        "missing_from_target": missing_from_target_count,
        "mismatches": mismatches
    }


def write_csv(file_path, fieldnames, rows):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=str(OUTPUT_FOLDER / "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True
    )

    run_id = str(uuid.uuid4())
    started_at = get_timestamp()
    start_time = time.time()

    report_file = OUTPUT_FOLDER / "reconciliation_report.json"

    logging.info(
        "Pipeline started. run_id=%s started_at=%s",
        run_id,
        started_at
    )

    try:
        source_raw = read_orders(SOURCE_FILE)
        target_raw = read_orders(TARGET_FILE)

        source_row_count = len(source_raw)
        target_row_count = len(target_raw)

        source_orders, source_rejects = validate_orders(
            source_raw, SOURCE_FILE.name
        )

        target_orders, target_rejects = validate_orders(
            target_raw, TARGET_FILE.name
        )

        all_rejects = source_rejects + target_rejects

        logging.info(
            "Validation completed. Source=%d Target=%d "
            "Valid source=%d Valid target=%d Rejected=%d",
            source_row_count,
            target_row_count,
            len(source_orders),
            len(target_orders),
            len(all_rejects)
        )

        results = reconcile(source_orders, target_orders)

        source_total = sum(
            int(row["amount"]) for row in source_orders
        )

        target_total = sum(
            int(row["amount"]) for row in target_orders
        )

        aggregates_match = source_total == target_total

        reconciliation_passed = (
            not all_rejects
            and results["amount_mismatches"] == 0
            and results["missing_from_source"] == 0
            and results["missing_from_target"] == 0
            and aggregates_match
        )

        report = {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": None,
            "source_row_count": source_row_count,
            "target_row_count": target_row_count,
            "valid_source_rows": len(source_orders),
            "valid_target_rows": len(target_orders),
            "rejected_rows": len(all_rejects),
            "matched_records": results["matched_records"],
            "amount_mismatches": results["amount_mismatches"],
            "missing_from_source": results["missing_from_source"],
            "missing_from_target": results["missing_from_target"],
            "source_total_amount": source_total,
            "target_total_amount": target_total,
            "aggregate_difference": target_total - source_total,
            "aggregates_match": aggregates_match,
            "reconciliation_status": (
                "PASSED" if reconciliation_passed else "FAILED"
            )
        }

        mismatch_file = OUTPUT_FOLDER / "mismatches.csv"

        mismatch_rows = []

        for mismatch in results["mismatches"]:
            mismatch_rows.append({
                "run_id": run_id,
                **mismatch
            })

        write_csv(
            mismatch_file,
            [
                "run_id",
                "order_id",
                "issue",
                "source_amount",
                "target_amount"
            ],
            mismatch_rows
        )

        rejects_file = OUTPUT_FOLDER / "rejects.csv"

        reject_rows = []

        for reject in all_rejects:
            reject_rows.append({
                "run_id": run_id,
                **reject
            })

        write_csv(
            rejects_file,
            [
                "run_id",
                "source_file",
                "source_row_number",
                "order_id",
                "amount",
                "reject_reason"
            ],
            reject_rows
        )

        duration = round(time.time() - start_time, 3)

        report["finished_at"] = get_timestamp()
        report["duration_seconds"] = duration

        with open(report_file, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        logging.info(
            "Reconciliation completed. run_id=%s status=%s "
            "matched=%d mismatches=%d rejected=%d duration=%.3f",
            run_id,
            report["reconciliation_status"],
            results["matched_records"],
            results["amount_mismatches"],
            len(all_rejects),
            duration
        )

        print("\nDATA RECONCILIATION SUMMARY")
        print("---------------------------")
        print("Run ID:", run_id)
        print("Source rows:", source_row_count)
        print("Target rows:", target_row_count)
        print("Valid source rows:", len(source_orders))
        print("Valid target rows:", len(target_orders))
        print("Rejected rows:", len(all_rejects))
        print("Matched records:", results["matched_records"])
        print("Amount mismatches:", results["amount_mismatches"])
        print("Missing from source:", results["missing_from_source"])
        print("Missing from target:", results["missing_from_target"])
        print("Source total:", source_total)
        print("Target total:", target_total)
        print("Aggregate difference:", target_total - source_total)
        print("Aggregates match:", aggregates_match)
        print("Status:", report["reconciliation_status"])
        print("Execution time:", duration, "seconds")

        print("\nOutput files created:")
        print(report_file)
        print(mismatch_file)
        print(rejects_file)

        logging.info("Data reconciliation pipeline finished.")

    except Exception as error:
        logging.exception(
            "Pipeline failed. run_id=%s error=%s",
            run_id,
            error
        )
        raise


if __name__ == "__main__":
    main()
