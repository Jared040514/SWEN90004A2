"""Minimal SVG plotting utilities for standard-library-only reports."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


# Small fixed colour set used for SVG line charts.
SERIES_COLOURS = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#f59e0b", "#0f766e")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for generating an SVG line chart."""
    parser = argparse.ArgumentParser(description="Create a simple SVG chart from summary CSV.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--x", default="similar_wanted")
    parser.add_argument("--y", default="percent_similar_mean")
    parser.add_argument("--group", default="density")
    parser.add_argument("--output", type=Path, default=Path("results/python/chart.svg"))
    return parser.parse_args()


def load_series(
    input_path: Path,
    x_field: str,
    y_field: str,
    group_field: str,
) -> dict[str, list[tuple[float, float]]]:
    """Load grouped x-y series from a summary CSV file."""
    series: dict[str, list[tuple[float, float]]] = defaultdict(list)
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get(x_field) or not row.get(y_field):
                continue
            series[row[group_field]].append((float(row[x_field]), float(row[y_field])))
    for values in series.values():
        values.sort()
    return dict(series)


def write_svg_line_chart(
    series: dict[str, list[tuple[float, float]]],
    output_path: Path,
    x_label: str,
    y_label: str,
) -> None:
    """Write a simple labelled SVG line chart."""
    width = 760
    height = 460
    margin_left = 72
    margin_bottom = 58
    margin_top = 28
    margin_right = 28

    all_points = [point for values in series.values() for point in values]
    if not all_points:
        raise ValueError("No data points available for plotting")
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    if min_x == max_x:
        max_x += 1.0
    if min_y == max_y:
        max_y += 1.0

    def sx(value: float) -> float:
        """Scale an x value into SVG coordinates."""
        span = width - margin_left - margin_right
        return margin_left + (value - min_x) / (max_x - min_x) * span

    def sy(value: float) -> float:
        """Scale a y value into SVG coordinates."""
        span = height - margin_top - margin_bottom
        return height - margin_bottom - (value - min_y) / (max_y - min_y) * span

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" ',
        f'x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#111827"/>',
        f'<line x1="{margin_left}" y1="{margin_top}" ',
        f'x2="{margin_left}" y2="{height - margin_bottom}" stroke="#111827"/>',
        f'<text x="{width / 2}" y="{height - 16}" text-anchor="middle" ',
        f'font-family="Arial" font-size="14">{x_label}</text>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" ',
        f'transform="rotate(-90 18 {height / 2})" ',
        f'font-family="Arial" font-size="14">{y_label}</text>',
    ]

    for index, (label, points) in enumerate(sorted(series.items())):
        colour = SERIES_COLOURS[index % len(SERIES_COLOURS)]
        path = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points)
        lines.append(f'<polyline points="{path}" fill="none" stroke="{colour}" stroke-width="2"/>')
        legend_y = margin_top + 18 * index
        lines.append(
            f'<text x="{width - 180}" y="{legend_y}" font-family="Arial" '
            f'font-size="13" fill="{colour}">{label}</text>'
        )
    lines.append("</svg>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Create an SVG chart from the requested summary CSV."""
    args = parse_args()
    series = load_series(args.input, args.x, args.y, args.group)
    write_svg_line_chart(series, args.output, args.x, args.y)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
