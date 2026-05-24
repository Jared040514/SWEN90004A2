"""Summarise cleaned NetLogo reference rows by parameter setting."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# Repository root inserted so this script works by path and by module name.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from segregation.stats import confidence_interval_95


# NetLogo metrics summarised for each parameter cell.
SUMMARY_METRICS = (
    "ticks",
    "population",
    "percent_similar",
    "percent_unhappy",
    "unhappy_count",
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for NetLogo summary generation."""
    parser = argparse.ArgumentParser(description="Summarise cleaned NetLogo reference CSV.")
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("results/netlogo/full/replication_summary.csv")
    )
    return parser.parse_args()


def summarise(input_path: Path, output_path: Path) -> None:
    """Write group means and 95 percent confidence intervals."""
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            groups[(row["density"], row["similar_wanted"])].append(row)

    fieldnames = ["source", "density", "similar_wanted", "n"]
    for metric in SUMMARY_METRICS:
        fieldnames.extend([f"{metric}_mean", f"{metric}_ci95"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for key, rows in sorted(groups.items(), key=lambda item: numeric_key(item[0])):
            density, similar_wanted = key
            output_row: dict[str, str | int] = {
                "source": "netlogo",
                "density": density,
                "similar_wanted": similar_wanted,
                "n": len(rows),
            }
            for metric in SUMMARY_METRICS:
                values = [float(row[metric]) for row in rows if row.get(metric)]
                centre, interval = confidence_interval_95(values)
                output_row[f"{metric}_mean"] = f"{centre:.6f}"
                output_row[f"{metric}_ci95"] = f"{interval:.6f}"
            writer.writerow(output_row)


def numeric_key(key: tuple[str, str]) -> tuple[float, float]:
    """Return a numeric sort key for density and threshold strings."""
    return (float(key[0]), float(key[1]))


def main() -> None:
    """Summarise the requested NetLogo CSV and print the output path."""
    args = parse_args()
    summarise(args.input, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
