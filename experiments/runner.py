"""Batch experiment runner for replication and extension experiments."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Repository root inserted so this script works by path and by module name.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from segregation.model import SegregationConfig, SegregationModel


# Baseline replication sweep from the proposal.
REPLICATION_SIMILAR_WANTED = tuple(range(15, 71, 5))

# Baseline density values from the proposal.
REPLICATION_DENSITIES = (70, 80, 90, 95)

# Extension income-gap sweep. Values are proportions in [0, 1].
EXTENSION_GAPS = (0.0, 0.25, 0.5, 0.75, 1.0)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for batch experiments."""
    parser = argparse.ArgumentParser(description="Run SWEN90004 segregation experiments.")
    parser.add_argument(
        "--experiment",
        choices=("replication", "extension", "all"),
        default="replication",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--max-ticks", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=10_000)
    parser.add_argument("--final-only", action="store_true")
    parser.add_argument("--density", type=float, default=80.0)
    parser.add_argument("--rent-max", type=float, default=100.0)
    parser.add_argument("--rent-scale", type=float, default=14.0)
    return parser.parse_args()


def run_replication(args: argparse.Namespace) -> Path:
    """Run the baseline parameter sweep and write one CSV file."""
    output_path = args.out_dir / "replication.csv"
    writer = CsvAppendWriter(output_path)
    for density in REPLICATION_DENSITIES:
        for similar_wanted in REPLICATION_SIMILAR_WANTED:
            for repetition in range(args.repetitions):
                seed = args.seed + density * 100_000 + similar_wanted * 1_000 + repetition
                config = SegregationConfig(
                    mode="baseline",
                    density=float(density),
                    similar_wanted=float(similar_wanted),
                    seed=seed,
                    max_ticks=args.max_ticks,
                )
                run_id = f"rep_d{density}_s{similar_wanted}_r{repetition}"
                append_model_rows(
                    writer,
                    config,
                    run_id,
                    repetition,
                    "replication",
                    args.final_only,
                )
    writer.close()
    return output_path


def run_extension(args: argparse.Namespace) -> Path:
    """Run the three extension treatments from the proposal."""
    output_path = args.out_dir / "extension.csv"
    writer = CsvAppendWriter(output_path)
    treatments = build_extension_treatments(args)
    for treatment, similar_wanted, income_gap, use_affordability in treatments:
        for repetition in range(args.repetitions):
            seed = args.seed + int(similar_wanted) * 10_000 + int(income_gap * 1_000) + repetition
            config = SegregationConfig(
                mode="extension",
                density=args.density,
                similar_wanted=similar_wanted,
                seed=seed,
                max_ticks=args.max_ticks,
                income_gap=income_gap,
                use_affordability=use_affordability,
                rent_max=args.rent_max,
                rent_scale=args.rent_scale,
            )
            gap_label = str(income_gap).replace(".", "p")
            run_id = f"{treatment}_s{int(similar_wanted)}_g{gap_label}_r{repetition}"
            append_model_rows(writer, config, run_id, repetition, treatment, args.final_only)
    writer.close()
    return output_path


def build_extension_treatments(args: argparse.Namespace) -> list[tuple[str, float, float, bool]]:
    """Return treatment tuples of name, threshold, income gap, and affordability use."""
    treatments: list[tuple[str, float, float, bool]] = []
    for similar_wanted in REPLICATION_SIMILAR_WANTED:
        treatments.append(("T1_preference_only", float(similar_wanted), 0.0, False))
    for gap in EXTENSION_GAPS:
        treatments.append(("T2_income_only", 0.0, gap, True))
    for gap in EXTENSION_GAPS:
        treatments.append(("T3_combined", 30.0, gap, True))
    return treatments


def append_model_rows(
    writer: "CsvAppendWriter",
    config: SegregationConfig,
    run_id: str,
    repetition: int,
    treatment: str,
    final_only: bool,
) -> None:
    """Run one model and append its rows to a CSV writer."""
    model = SegregationModel(config)
    if not final_only:
        writer.writerow(model.metrics_row(run_id, repetition, treatment))
    while model.step():
        if not final_only:
            writer.writerow(model.metrics_row(run_id, repetition, treatment))
    if final_only:
        writer.writerow(model.metrics_row(run_id, repetition, treatment))


class CsvAppendWriter:
    """Small helper that writes a single header while appending many model rows."""

    def __init__(self, output_path: Path):
        """Open an output file and prepare to write rows lazily."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = output_path.open("w", newline="", encoding="utf-8")
        self.writer: csv.DictWriter[str] | None = None

    def writerow(self, row: dict[str, str | int | float]) -> None:
        """Write a row, creating the DictWriter from the first row's fields."""
        if self.writer is None:
            self.writer = csv.DictWriter(self.handle, fieldnames=list(row.keys()))
            self.writer.writeheader()
        self.writer.writerow(row)

    def close(self) -> None:
        """Close the underlying CSV file handle."""
        self.handle.close()


def main() -> None:
    """Run the requested experiment suite."""
    args = parse_args()
    outputs: list[Path] = []
    if args.experiment in ("replication", "all"):
        outputs.append(run_replication(args))
    if args.experiment in ("extension", "all"):
        outputs.append(run_extension(args))
    for output in outputs:
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
