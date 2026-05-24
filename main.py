"""Command-line entry point for running one segregation model simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

from segregation.model import SegregationConfig, SegregationModel


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for a single simulation run."""
    parser = argparse.ArgumentParser(description="Run the SWEN90004 segregation model.")
    parser.add_argument("--mode", choices=("baseline", "extension"), default="baseline")
    parser.add_argument("--size", type=int, default=51)
    parser.add_argument("--density", type=float, default=80.0)
    parser.add_argument("--similar-wanted", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=10_000)
    parser.add_argument("--output", type=Path, default=Path("results/python/single_run.csv"))
    parser.add_argument("--final-only", action="store_true")
    parser.add_argument("--income-gap", type=float, default=0.0)
    parser.add_argument("--disable-affordability", action="store_true")
    parser.add_argument("--rent-max", type=float, default=100.0)
    parser.add_argument("--rent-scale", type=float, default=14.0)
    parser.add_argument("--max-relocation-attempts", type=int, default=10_000)
    parser.add_argument("--stall-limit", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    """Run one simulation and write the requested CSV output."""
    args = parse_args()
    config = SegregationConfig(
        mode=args.mode,
        size=args.size,
        density=args.density,
        similar_wanted=args.similar_wanted,
        seed=args.seed,
        max_ticks=args.max_ticks,
        max_relocation_attempts=args.max_relocation_attempts,
        income_gap=args.income_gap,
        use_affordability=not args.disable_affordability,
        rent_max=args.rent_max,
        rent_scale=args.rent_scale,
        stall_limit=args.stall_limit,
    )
    model = SegregationModel(config)
    model.run_to_csv(args.output, final_only=args.final_only)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
