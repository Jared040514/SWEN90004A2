"""Convert NetLogo BehaviorSpace table output into a simple CSV file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


# Number of metadata rows before the BehaviorSpace table header.
BEHAVIORSPACE_METADATA_ROWS = 6


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for NetLogo table conversion."""
    parser = argparse.ArgumentParser(description="Convert NetLogo BehaviorSpace table CSV.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/netlogo/reference_clean.csv"))
    return parser.parse_args()


def convert_table(input_path: Path, output_path: Path) -> None:
    """Read a BehaviorSpace table CSV and write normalised final-run rows."""
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    header = rows[BEHAVIORSPACE_METADATA_ROWS]
    records = rows[BEHAVIORSPACE_METADATA_ROWS + 1:]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source",
        "run_number",
        "density",
        "similar_wanted",
        "ticks",
        "population",
        "percent_similar",
        "percent_unhappy",
        "unhappy_count",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(zip(header, record))
            writer.writerow(
                {
                    "source": "netlogo",
                    "run_number": row["[run number]"],
                    "density": row["density"],
                    "similar_wanted": row["%-similar-wanted"],
                    "ticks": row["ticks"],
                    "population": row["count turtles"],
                    "percent_similar": row["percent-similar"],
                    "percent_unhappy": row["percent-unhappy"],
                    "unhappy_count": row["count turtles with [not happy?]"],
                }
            )


def main() -> None:
    """Convert the requested table and print the output path."""
    args = parse_args()
    convert_table(args.input, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
