"""Summarise final experiment rows into means and 95 percent intervals."""

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


# Metrics summarised from final rows when present.
SUMMARY_METRICS = (
    "tick",
    "percent_similar",
    "percent_unhappy",
    "stuck_unhappy_fraction",
    "isolation_blue",
    "isolation_orange",
    "dissimilarity",
    "mean_rent_blue",
    "mean_rent_orange",
)

# Grouping key: treatment, density, similar_wanted, income_gap, affordability flag.
GroupKey = tuple[str, str, str, str, str]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for CSV summarisation."""
    parser = argparse.ArgumentParser(description="Summarise segregation experiment CSV output.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/python/full/summary.csv"))
    return parser.parse_args()


def read_final_rows(input_path: Path) -> list[dict[str, str]]:
    """Read only the last tick for each run_id from an experiment CSV."""
    final_rows: dict[str, dict[str, str]] = {}
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            run_id = row["run_id"]
            current = final_rows.get(run_id)
            if current is None or int(row["tick"]) >= int(current["tick"]):
                final_rows[run_id] = row
    return list(final_rows.values())


def group_rows(rows: list[dict[str, str]]) -> dict[GroupKey, list[dict[str, str]]]:
    """Group rows by treatment and parameter values."""
    grouped: dict[GroupKey, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            row["treatment"],
            row["density"],
            row["similar_wanted"],
            row["income_gap"],
            row.get("use_affordability", ""),
        )
        grouped[key].append(row)
    return grouped


def summarise(input_path: Path, output_path: Path) -> None:
    """Write summary statistics for an experiment CSV."""
    rows = read_final_rows(input_path)
    grouped = group_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "treatment",
        "density",
        "similar_wanted",
        "income_gap",
        "use_affordability",
        "n",
        "n_converged",
        "convergence_rate",
    ]
    for metric in SUMMARY_METRICS:
        fieldnames.extend([f"{metric}_mean", f"{metric}_ci95"])

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for key, group in sorted(grouped.items()):
            treatment, density, similar_wanted, income_gap, use_affordability = key
            n = len(group)
            # Count runs that reached the natural "all agents happy" halting condition,
            # excluding those capped at max_ticks or stalled.
            n_converged = sum(1 for row in group if row.get("termination_reason") == "converged")
            convergence_rate = n_converged / n if n else 0.0
            summary: dict[str, str | int] = {
                "treatment": treatment,
                "density": density,
                "similar_wanted": similar_wanted,
                "income_gap": income_gap,
                "use_affordability": use_affordability,
                "n": n,
                "n_converged": n_converged,
                "convergence_rate": f"{convergence_rate:.6f}",
            }
            for metric in SUMMARY_METRICS:
                values = [float(row[metric]) for row in group if row.get(metric)]
                centre, interval = confidence_interval_95(values)
                summary[f"{metric}_mean"] = f"{centre:.6f}"
                summary[f"{metric}_ci95"] = f"{interval:.6f}"
            writer.writerow(summary)


def main() -> None:
    """Summarise the requested CSV and print the output path."""
    args = parse_args()
    summarise(args.input, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
