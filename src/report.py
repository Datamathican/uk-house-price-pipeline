"""Export the mart to CSV and render a chart for the README."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (must follow matplotlib.use)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("WAREHOUSE_PATH", ROOT / "data" / "warehouse.duckdb"))
SUMMARY_CSV = ROOT / "data" / "summary.csv"
CHART_PNG = ROOT / "docs" / "chart.png"


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    monthly = con.execute(
        """
        SELECT sale_month, sales, median_price
        FROM main.monthly_prices_uk
        ORDER BY sale_month
        """
    ).df()
    con.close()

    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    CHART_PNG.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(SUMMARY_CSV, index=False)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(monthly["sale_month"], monthly["median_price"] / 1000, marker="o")
    ax.set_title("UK median house sale price by month")
    ax.set_ylabel("Median price (£k)")
    ax.set_xlabel("")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(CHART_PNG, dpi=150)


if __name__ == "__main__":
    main()
