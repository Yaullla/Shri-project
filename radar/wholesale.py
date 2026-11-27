"""Private operator-supplied Moscow CSV quotes; never treated as public offers."""
import argparse
import csv
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

from radar.offers import connect, moment, number


def import_csv(db, path, supplier):
    supplier = supplier.strip()
    if not supplier or len(supplier) > 120:
        raise ValueError("Invalid supplier label")
    path = Path(path)
    if path.stat().st_size > 5_000_000:
        raise ValueError("CSV exceeds 5 MB")
    db.execute("""CREATE TABLE IF NOT EXISTS wholesale_quotes (
        supplier TEXT NOT NULL, product_key TEXT NOT NULL, observed_at TEXT NOT NULL,
        price_rub TEXT NOT NULL, PRIMARY KEY(supplier,product_key,observed_at))""")
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as stream, db:
        reader = csv.DictReader(stream)
        if not {"product_key", "observed_at", "price_rub"}.issubset(reader.fieldnames or []):
            raise ValueError("Required columns: product_key,observed_at,price_rub")
        for row in reader:
            key = row["product_key"].strip().casefold()
            if len(key.split("|")) != 4 or not all(key.split("|")) or len(key) > 200:
                raise ValueError("Require exact brand|mpn|variant|condition")
            timestamp = moment(row["observed_at"])
            if timestamp > datetime.now(UTC) + timedelta(minutes=5):
                raise ValueError("Future quote")
            result = db.execute("""INSERT OR IGNORE INTO wholesale_quotes VALUES (?,?,?,?)""",
                (supplier, key, timestamp.isoformat(timespec="microseconds"),
                 str(number(row["price_rub"], positive=True))))
            count += result.rowcount
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--supplier", required=True)
    args = parser.parse_args()
    with closing(connect()) as db:
        print(f"Imported private quotes: {import_csv(db, args.csv, args.supplier)}")


if __name__ == "__main__":
    main()
