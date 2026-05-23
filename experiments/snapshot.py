"""Render world-state snapshots of the segregation model as standalone SVGs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repository root inserted so this script works by path and by module name.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from segregation.model import SegregationConfig, SegregationModel


# Pixel size of one patch in the SVG output. 12 keeps a 51x51 grid at 612x612.
PATCH_PX = 12

# Fill colours used for each agent group, matching the NetLogo blue and orange.
GROUP_COLOURS = {
    "blue": "#2563eb",
    "orange": "#f59e0b",
}

# Fill colour for vacant patches when rent shading is disabled.
EMPTY_COLOUR = "#f5f5f5"

# Stroke colour for the optional grid overlay.
GRID_COLOUR = "#e5e7eb"

# Lightest and darkest grey used for the optional rent background gradient.
RENT_LIGHT_GREY = 245
RENT_DARK_GREY = 185


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the snapshot renderer."""
    parser = argparse.ArgumentParser(description="Render segregation world snapshots as SVG.")
    parser.add_argument("--mode", choices=("baseline", "extension"), default="baseline")
    parser.add_argument("--size", type=int, default=51)
    parser.add_argument("--density", type=float, default=80.0)
    parser.add_argument("--similar-wanted", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=10_000)
    parser.add_argument("--income-gap", type=float, default=0.0)
    parser.add_argument("--disable-affordability", action="store_true")
    parser.add_argument("--rent-max", type=float, default=100.0)
    parser.add_argument("--rent-scale", type=float, default=14.0)
    parser.add_argument(
        "--snap-at",
        default="0,5,15,50,200,1000",
        help="Comma-separated tick numbers at which to render snapshots.",
    )
    parser.add_argument(
        "--also-final",
        action="store_true",
        help="Render an extra snapshot when the run halts, even if not in --snap-at.",
    )
    parser.add_argument(
        "--show-rent",
        action="store_true",
        help="Shade each patch background by its rent value (extension mode only).",
    )
    parser.add_argument(
        "--show-grid",
        action="store_true",
        help="Overlay thin patch borders for readability.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/snapshots"),
        help="Directory where snap_t####.svg files are written.",
    )
    parser.add_argument(
        "--prefix",
        default="snap",
        help="Filename prefix; final files are <prefix>_t####.svg or <prefix>_final.svg.",
    )
    return parser.parse_args()


def render_world_svg(
    model: SegregationModel,
    output_path: Path,
    show_rent: bool = False,
    show_grid: bool = False,
) -> None:
    """Write the current world state as a standalone SVG file.

    The SVG flips the y axis so that y = 0 is at the bottom of the image,
    matching NetLogo's display orientation.
    """
    size = model.world.size
    px = PATCH_PX
    width = size * px
    height = size * px

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{EMPTY_COLOUR}"/>',
    ]

    if show_rent and model.world.rent:
        rent_max = max(model.world.rent.values())
        if rent_max > 0:
            parts.extend(_rent_background_rects(model, size, px, rent_max))

    parts.extend(_agent_rects(model, size, px))

    if show_grid:
        parts.extend(_grid_overlay(size, px))

    parts.append(_caption(model, width, height))
    parts.append("</svg>")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _rent_background_rects(
    model: SegregationModel,
    size: int,
    px: int,
    rent_max: float,
) -> list[str]:
    """Return SVG rects shading each patch by its rent value."""
    rects: list[str] = []
    span = RENT_LIGHT_GREY - RENT_DARK_GREY
    for (x, y), rent in model.world.rent.items():
        intensity = rent / rent_max
        grey = int(RENT_LIGHT_GREY - intensity * span)
        rects.append(
            f'<rect x="{x * px}" y="{(size - 1 - y) * px}" width="{px}" height="{px}" '
            f'fill="rgb({grey},{grey},{grey})"/>'
        )
    return rects


def _agent_rects(model: SegregationModel, size: int, px: int) -> list[str]:
    """Return SVG rects for every occupied patch coloured by agent group."""
    rects: list[str] = []
    for (x, y), ident in model.world.occupancy.items():
        agent = model.agents[ident]
        colour = GROUP_COLOURS.get(agent.group, "#000000")
        rects.append(
            f'<rect x="{x * px}" y="{(size - 1 - y) * px}" width="{px}" height="{px}" '
            f'fill="{colour}"/>'
        )
    return rects


def _grid_overlay(size: int, px: int) -> list[str]:
    """Return SVG lines drawing thin patch borders across the world."""
    lines: list[str] = []
    extent = size * px
    for index in range(size + 1):
        offset = index * px
        lines.append(
            f'<line x1="0" y1="{offset}" x2="{extent}" y2="{offset}" '
            f'stroke="{GRID_COLOUR}" stroke-width="0.5"/>'
        )
        lines.append(
            f'<line x1="{offset}" y1="0" x2="{offset}" y2="{extent}" '
            f'stroke="{GRID_COLOUR}" stroke-width="0.5"/>'
        )
    return lines


def _caption(model: SegregationModel, width: int, height: int) -> str:
    """Return an SVG text node summarising the snapshot parameters."""
    config = model.config
    text = (
        f"tick={model.tick} | mode={config.mode} | density={config.density:g} "
        f"| similar_wanted={config.similar_wanted:g}"
    )
    if config.mode == "extension":
        text += f" | income_gap={config.income_gap:g} | affordable={config.use_affordability}"
    return (
        f'<text x="6" y="{height - 6}" font-family="Arial" font-size="11" '
        f'fill="#374151">{text}</text>'
    )


def main() -> None:
    """Run a single simulation and emit SVGs at the requested ticks."""
    args = parse_args()
    snap_ticks = sorted({int(value) for value in args.snap_at.split(",") if value.strip()})

    config = SegregationConfig(
        mode=args.mode,
        size=args.size,
        density=args.density,
        similar_wanted=args.similar_wanted,
        seed=args.seed,
        max_ticks=args.max_ticks,
        income_gap=args.income_gap,
        use_affordability=not args.disable_affordability,
        rent_max=args.rent_max,
        rent_scale=args.rent_scale,
    )
    model = SegregationModel(config)
    output_dir: Path = args.output_dir

    pending = set(snap_ticks)
    if 0 in pending:
        target = output_dir / f"{args.prefix}_t0000.svg"
        render_world_svg(model, target, show_rent=args.show_rent, show_grid=args.show_grid)
        pending.discard(0)
        print(f"Wrote {target}")

    while model.step():
        if model.tick in pending:
            target = output_dir / f"{args.prefix}_t{model.tick:04d}.svg"
            render_world_svg(model, target, show_rent=args.show_rent, show_grid=args.show_grid)
            pending.discard(model.tick)
            print(f"Wrote {target}")
        if not pending and not args.also_final:
            break

    if args.also_final or pending:
        target = output_dir / f"{args.prefix}_final_t{model.tick:04d}.svg"
        render_world_svg(model, target, show_rent=args.show_rent, show_grid=args.show_grid)
        print(f"Wrote {target}")


if __name__ == "__main__":
    main()
