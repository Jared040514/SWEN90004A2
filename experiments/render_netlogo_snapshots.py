"""Render NetLogo final-state turtle lists as SVG spatial snapshots."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


# NetLogo world bounds for the Segregation model.
MIN_COORD = -25
MAX_COORD = 25
WORLD_SIZE = MAX_COORD - MIN_COORD + 1

# NetLogo colour numbers used by the original Segregation model.
NETLOGO_BLUE = "105"
NETLOGO_ORANGE = "27"

# Regular expression for one turtle list entry: [xcor ycor color].
TURTLE_PATTERN = re.compile(r"\[(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (\d+)\]")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for snapshot rendering."""
    parser = argparse.ArgumentParser(description="Render NetLogo snapshot SVGs.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("results/netlogo/snapshots"))
    return parser.parse_args()


def read_snapshot_rows(input_path: Path) -> list[dict[str, str]]:
    """Read BehaviorSpace rows after the metadata header block."""
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    header = rows[6]
    return [dict(zip(header, row)) for row in rows[7:]]


def parse_turtles(raw_value: str) -> list[tuple[int, int, str]]:
    """Parse a NetLogo list of turtle coordinate and colour triples."""
    turtles: list[tuple[int, int, str]] = []
    for match in TURTLE_PATTERN.finditer(raw_value):
        x_value = int(round(float(match.group(1))))
        y_value = int(round(float(match.group(2))))
        turtles.append((x_value, y_value, match.group(3)))
    return turtles


def render_snapshot(row: dict[str, str], out_dir: Path) -> Path:
    """Render one BehaviorSpace row into an SVG snapshot file."""
    turtle_field = "[(list xcor ycor color)] of turtles"
    turtles = parse_turtles(row[turtle_field])
    density = row["density"]
    similar = row["%-similar-wanted"]
    # Mirror the Python snapshot layout: results/<lang>/snapshots/baseline_d<D>_s<S>/snap_final.svg.
    output_path = out_dir / f"baseline_d{density}_s{similar}" / "snap_final.svg"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cell = 8
    plot_size = WORLD_SIZE * cell
    title_height = 42
    width = plot_size
    height = plot_size + title_height
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        (
            f'<text x="8" y="18" font-family="Arial" font-size="13">'
            f'NetLogo density={density}, similar={similar}, ticks={row["ticks"]}, '
            f'% similar={float(row["percent-similar"]):.1f}</text>'
        ),
        f'<rect x="0" y="{title_height}" width="{plot_size}" height="{plot_size}" ',
        'fill="#f9fafb" stroke="#111827" stroke-width="1"/>',
    ]

    for x_coord, y_coord, colour in turtles:
        x_pixel = (x_coord - MIN_COORD) * cell
        y_pixel = (MAX_COORD - y_coord) * cell + title_height
        fill = "#2563eb" if colour == NETLOGO_BLUE else "#f97316"
        if colour not in (NETLOGO_BLUE, NETLOGO_ORANGE):
            fill = "#374151"
        lines.append(
            f'<rect x="{x_pixel}" y="{y_pixel}" width="{cell}" height="{cell}" '
            f'fill="{fill}"/>'
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """Render all snapshot rows from a NetLogo BehaviorSpace table."""
    args = parse_args()
    rows = read_snapshot_rows(args.input)
    for row in rows:
        print(f"Wrote {render_snapshot(row, args.out_dir)}")


if __name__ == "__main__":
    main()
