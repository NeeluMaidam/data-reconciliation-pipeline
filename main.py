import csv
import json
import logging
import time
from pathlib import Path

source_file = Path("data/source_orders.csv")
target_file = Path("data/target_orders.csv")
output_folder = Path("output")


def read_orders(file_path):
    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, skipinitialspace=True)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file is empty: {file_path}")

        reader.fieldnames = [
            name.strip().lower() for name in reader.fieldnames
        ]

        required_columns = {"order_id", "amount"}
        if not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{file_path} must contain order_id and amount columns"
            )

        print(f"Columns in {file_path}: {reader.fieldnames}")

        rows = []
        for row in reader:
            if not row or all(
                value is None or not str(value).strip()
                for value in row.values()
            ):
                continue

            cleaned_row = {
                key.strip().lower(): value.strip() if value else ""
                for key, value in row.items()
                if key is not None
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
                amount_value = int(amount)

                if amount_value < 0:
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
            valid_rows.append(row)

    return valid_rows, rejected_rows


def reconcile(source_orders, target_orders):
    source_by_id = {row["order_id"]: row for row in source_orders}
    target_by_id = {row["order_id"]: row for row in target_orders}

    matched_count = 0
    amount_mismatch_count = 0
    missing_from_source_count = 0
    missing_from_target_count = 0
    mismatches = []

    for order_id in sorted(set(source_by_id) | set(target_by_id)):
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

        elif source["amount"] != target["amount"]:
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
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    output_folder.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=str(output_folder / "pipeline.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True
    )

    start_time = time.time()
    logging.info("Data reconciliation pipeline started.")

    try:
        source_raw = read_orders(source_file)
        target_raw = read_orders(target_file)

        logging.info("Source and target data loaded successfully.")

        source_row_count = len(source_raw)
        target_row_count = len(target_raw)

        source_orders, source_rejects = validate_orders(
            source_raw, "source_orders.csv"
        )
        target_orders, target_rejects = validate_orders(
            target_raw, "target_orders.csv"
        )

        all_rejects = source_rejects + target_rejects

        logging.info(
            "Validation completed. Source rows: %d, target rows: %d, "
            "valid source: %d, valid target: %d, rejected: %d",
            source_row_count,
            target_row_count,
            len(source_orders),
            len(target_orders),
            len(all_rejects)
        )

        print("\nData quality validation:")
        print("Original source rows:", source_row_count)
        print("Original target rows:", target_row_count)
        print("Valid source rows:", len(source_orders))
        print("Valid target rows:", len(target_orders))
        print("Rejected rows:", len(all_rejects))

        results = reconcile(source_orders, target_orders)

        report = {
            "source_row_count": source_row_count,
            "target_row_count": target_row_count,
            "valid_source_rows": len(source_orders),
            "valid_target_rows": len(target_orders),
            "rejected_rows": len(all_rejects),
            "matched_records": results["matched_records"],
            "amount_mismatches": results["amount_mismatches"],
            "missing_from_source": results["missing_from_source"],
            "missing_from_target": results["missing_from_target"],
            "source_total_amount": sum(
                int(row["amount"]) for row in source_orders
            ),
            "target_total_amount": sum(
                int(row["amount"]) for row in target_orders
            ),
            "aggregate_difference": sum(
                int(row["amount"]) for row in target_orders
            ) - sum(
                int(row["amount"]) for row in source_orders
            ),
            "aggregates_match": sum(
                int(row["amount"]) for row in source_orders
            ) == sum(
            int(row["amount"]) for row in target_orders
            ),
            "reconciliation_status": (
                "PASSED"
                if not all_rejects
                and results["amount_mismatches"] == 0
                and results["missing_from_source"] == 0
                and results["missing_from_target"] == 0
                and report["aggregates_match"]
                else "FAILED"
            ),

        }

        report_file = output_folder / "reconciliation_report.json"
        with open(report_file, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        mismatch_file = output_folder / "mismatches.csv"
        write_csv(
            mismatch_file,
            ["order_id", "issue", "source_amount", "target_amount"],
            results["mismatches"]
        )

        rejects_file = output_folder / "rejects.csv"
        write_csv(
            rejects_file,
            [
                "source_file",
                "source_row_number",
                "order_id",
                "amount",
                "reject_reason"
            ],
            all_rejects
        )

        duration = round(time.time() - start_time, 3)

        report["duration_seconds"] = duration

        with open(report_file, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        logging.info(
            "Reconciliation completed. Status: %s, matched: %d, "
            "amount mismatches: %d, missing from source: %d, "
            "missing from target: %d, rejected: %d, duration: %.3f seconds",
            report["reconciliation_status"],
            results["matched_records"],
            results["amount_mismatches"],
            results["missing_from_source"],
            results["missing_from_target"],
            len(all_rejects),
            duration
        )

        print("\nJSON report created:", report_file)
        print(json.dumps(report, indent=4))
        print("\nMismatch file created:", mismatch_file)
        print("Total mismatched records:", len(results["mismatches"]))
        print("Rejects file created:", rejects_file)
        print("Total rejected rows:", len(all_rejects))
        print("Execution time:", duration, "seconds")

        logging.info("Data reconciliation pipeline finished.")

    except Exception:
        logging.exception("Data reconciliation pipeline failed.")
        raise


if __name__ == "__main__":
    main()
