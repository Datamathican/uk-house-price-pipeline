"""Ingest HM Land Registry Price Paid Data into a local DuckDB warehouse.

Usage:
    python src/ingest.py                      # download current-year file
    python src/ingest.py --year 2025          # download a specific year
    python src/ingest.py --file path/to.csv   # load a local file (used in CI)
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import urllib.request
from pathlib import Path

import duckdb

BASE_URL = (
    "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1."
    "amazonaws.com/pp-{year}.csv"
)
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = Path(os.environ.get("WAREHOUSE_PATH", ROOT / "data" / "warehouse.duckdb"))

# The Price Paid CSV has no header row; these are the documented columns.
COLUMNS = {
    "transaction_id": "VARCHAR",
    "price": "BIGINT",
    "date_of_transfer": "TIMESTAMP",
    "postcode": "VARCHAR",
    "property_type": "VARCHAR",  # D, S, T, F, O
    "new_build": "VARCHAR",  # Y / N
    "tenure": "VARCHAR",  # F / L
    "paon": "VARCHAR",
    "saon": "VARCHAR",
    "street": "VARCHAR",
    "locality": "VARCHAR",
    "town_city": "VARCHAR",
    "district": "VARCHAR",
    "county": "VARCHAR",
    "ppd_category": "VARCHAR",
    "record_status": "VARCHAR",
}

log = logging.getLogger("ingest")


def download(year: int) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = os.environ.get("DATA_URL") or BASE_URL.format(year=year)
    target = RAW_DIR / f"pp-{year}.csv"
    log.info("Downloading %s", url)
    urllib.request.urlretrieve(url, target)
    log.info("Saved %s (%.1f MB)", target, target.stat().st_size / 1e6)
    return target


def load(csv_path: Path, db_path: Path = DB_PATH) -> int:
    """Load a Price Paid CSV into raw.price_paid, replacing existing rows."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cols = ", ".join(f"'{k}': '{v}'" for k, v in COLUMNS.items())
    con = duckdb.connect(str(db_path))
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw.price_paid AS
            SELECT *, current_timestamp AS _loaded_at
            FROM read_csv(
                '{csv_path}',
                header = false,
                columns = {{{cols}}},
                dateformat = '%Y-%m-%d %H:%M'
            )
            """
        )
        n = con.execute("SELECT count(*) FROM raw.price_paid").fetchone()[0]
    finally:
        con.close()
    log.info("Loaded %s rows into raw.price_paid", f"{n:,}")
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=dt.date.today().year)
    parser.add_argument("--file", type=Path, help="Load a local CSV instead of downloading")
    args = parser.parse_args()

    csv_path = args.file if args.file else download(args.year)
    load(csv_path)


if __name__ == "__main__":
    main()
