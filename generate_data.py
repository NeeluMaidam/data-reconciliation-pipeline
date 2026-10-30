import csv
import random
from pathlib import Path

random.seed(42)

data_folder = Path("data")
data_folder.mkdir(exist_ok=True)

record_count = 100_000

source_file = data_folder / "source_orders.csv"
target_file = data_folder / "target_orders.csv"

with open(source_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["order_id", "amount"])

    for i in range(1, record_count + 1):
        amount = random.randint(100, 10000)
        writer.writerow([f"ORD{i:06d}", amount])

with open(source_file, "r", newline="", encoding="utf-8") as source:
    with open(target_file, "w", newline="", encoding="utf-8") as target:
        reader = csv.DictReader(source)
        writer = csv.writer(target)
        writer.writerow(["order_id", "amount"])

        for i, row in enumerate(reader, start=1):
            amount = int(row["amount"])

            if i % 100 == 0:
                amount += 50

            writer.writerow([row["order_id"], amount])

print("Generated source records:", record_count)
print("Generated target records:", record_count)
print("Expected matching records:", record_count - record_count // 100)
print("Expected amount mismatches:", record_count // 100)
print("Files saved in:", data_folder)