"""Data quality checks that run after `dbt build` (see CI and refresh workflows)."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("WAREHOUSE_PATH", ROOT / "data" / "warehouse.duckdb"))


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip(f"Warehouse not found at {DB_PATH}; run ingest + dbt first")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


def test_raw_not_empty(con):
    assert con.execute("select count(*) from raw.price_paid").fetchone()[0] > 0


def test_prices_are_positive(con):
    bad = con.execute("select count(*) from main.stg_price_paid where price <= 0").fetchone()[0]
    assert bad == 0


def test_no_future_sales(con):
    bad = con.execute(
        "select count(*) from main.stg_price_paid where sale_date > current_date"
    ).fetchone()[0]
    assert bad == 0


def test_staging_excludes_category_b(con):
    raw_b = con.execute(
        "select count(*) from raw.price_paid where ppd_category = 'B'"
    ).fetchone()[0]
    raw_total = con.execute("select count(*) from raw.price_paid").fetchone()[0]
    stg = con.execute("select count(*) from main.stg_price_paid").fetchone()[0]
    assert stg <= raw_total - raw_b


def test_data_is_recent(con):
    """Skip on the tiny CI fixture; enforce freshness on real data."""
    if os.environ.get("CI_FIXTURE"):
        pytest.skip("fixture data")
    latest = con.execute("select max(sale_date) from main.stg_price_paid").fetchone()[0]
    age_days = (con.execute("select current_date").fetchone()[0] - latest).days
    assert age_days < 120, f"Latest sale is {age_days} days old"
