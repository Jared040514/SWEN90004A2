"""Build the data-driven SVG figures embedded in the final report.

Reads:
    results/python/full/replication_summary.csv
    results/netlogo/full/replication_summary.csv
    results/python/full/extension_summary.csv

Writes (one SVG per figure):
    results/python/figures/fig2_replication_overlay_d80.svg
    results/python/figures/fig2b_replication_overlay_all_densities.svg
    results/python/figures/fig4_t2_rent_gap.svg

The script is intentionally tiny: it filters the summary CSVs to the rows
relevant to each figure, packs the (x, y) series into the dict shape that
``experiments.plotting.write_svg_line_chart`` expects, and lets that helper
render the SVG.  No third-party dependencies, no CLI flags - just run it once
from the repository root to refresh every report figure in place.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Repository root inserted so this script works by path and by module name.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.plotting import write_svg_line_chart


# Default input paths anchored to the post-restructure symmetric layout.
PYTHON_REPLICATION_SUMMARY = Path("results/python/full/replication_summary.csv")
NETLOGO_REPLICATION_SUMMARY = Path("results/netlogo/full/replication_summary.csv")
PYTHON_EXTENSION_SUMMARY = Path("results/python/full/extension_summary.csv")

# All figures are written under one directory for easy report assembly.
FIGURES_DIR = Path("results/python/figures")

# Density used for the report's primary replication-comparison figure.
PRIMARY_DENSITY = 80.0

# All densities present in the parameter sweep, for the multi-panel variant.
ALL_DENSITIES = (70.0, 80.0, 90.0, 95.0)


def filter_replication_series(
    summary_path: Path,
    density: float,
    label: str,
) -> list[tuple[float, float]]:
    """Return sorted (similar_wanted, percent_similar_mean) tuples for one density."""
    points: list[tuple[float, float]] = []
    with summary_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_density = float(row["density"])
            if abs(row_density - density) > 1e-9:
                continue
            x_value = float(row["similar_wanted"])
            y_value = float(row["percent_similar_mean"])
            points.append((x_value, y_value))
    points.sort()
    if not points:
        raise ValueError(
            f"No rows matched density={density} in {summary_path} for series '{label}'"
        )
    return points


def build_replication_overlay_single_density(
    python_csv: Path,
    netlogo_csv: Path,
    output_path: Path,
    density: float,
) -> None:
    """Plot Python vs NetLogo mean percent_similar curves at one density."""
    series = {
        "Python": filter_replication_series(python_csv, density, "Python"),
        "NetLogo": filter_replication_series(netlogo_csv, density, "NetLogo"),
    }
    write_svg_line_chart(
        series,
        output_path,
        x_label=f"%-similar-wanted  (density={density:g}, n=30 per cell)",
        y_label="percent_similar mean  (Python vs NetLogo)",
    )


def build_replication_overlay_all_densities(
    python_csv: Path,
    netlogo_csv: Path,
    output_path: Path,
) -> None:
    """Overlay every density curve from both implementations on a single chart.

    Series labels are prefixed so the legend separates Python and NetLogo runs.
    """
    series: dict[str, list[tuple[float, float]]] = {}
    for density in ALL_DENSITIES:
        py_label = f"Py d={int(density)}"
        nl_label = f"NL d={int(density)}"
        series[py_label] = filter_replication_series(python_csv, density, py_label)
        series[nl_label] = filter_replication_series(netlogo_csv, density, nl_label)
    write_svg_line_chart(
        series,
        output_path,
        x_label="%-similar-wanted  (n=30 per cell)",
        y_label="percent_similar mean  (Python vs NetLogo)",
    )


def build_t2_rent_chart(
    extension_csv: Path,
    output_path: Path,
) -> None:
    """Plot T2 income-only mean_rent_blue and mean_rent_orange vs income_gap.

    The two lines diverging from a shared baseline at income_gap = 0 is the
    visual proof that economic inequality alone produces spatial sorting.
    """
    blue: list[tuple[float, float]] = []
    orange: list[tuple[float, float]] = []
    with extension_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["treatment"] != "T2_income_only":
                continue
            gap_value = float(row["income_gap"])
            blue.append((gap_value, float(row["mean_rent_blue_mean"])))
            orange.append((gap_value, float(row["mean_rent_orange_mean"])))
    blue.sort()
    orange.sort()
    if not blue or not orange:
        raise ValueError(f"No T2_income_only rows found in {extension_csv}")
    series = {
        "blue group mean rent": blue,
        "orange group mean rent": orange,
    }
    write_svg_line_chart(
        series,
        output_path,
        x_label="inter-group income gap  (0 = identical distributions, 1 = max divergence)",
        y_label="mean rent paid per agent  (T2: %-similar-wanted = 0)",
    )


def main() -> None:
    """Build every report figure into FIGURES_DIR."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig2_path = FIGURES_DIR / "fig2_replication_overlay_d80.svg"
    build_replication_overlay_single_density(
        PYTHON_REPLICATION_SUMMARY,
        NETLOGO_REPLICATION_SUMMARY,
        fig2_path,
        PRIMARY_DENSITY,
    )
    print(f"Wrote {fig2_path}")

    fig2b_path = FIGURES_DIR / "fig2b_replication_overlay_all_densities.svg"
    build_replication_overlay_all_densities(
        PYTHON_REPLICATION_SUMMARY,
        NETLOGO_REPLICATION_SUMMARY,
        fig2b_path,
    )
    print(f"Wrote {fig2b_path}")

    fig4_path = FIGURES_DIR / "fig4_t2_rent_gap.svg"
    build_t2_rent_chart(PYTHON_EXTENSION_SUMMARY, fig4_path)
    print(f"Wrote {fig4_path}")


if __name__ == "__main__":
    main()
