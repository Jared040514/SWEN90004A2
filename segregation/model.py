"""Simulation engine for the baseline and extended segregation models."""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from segregation.agent import Agent, GROUPS
from segregation import stats
from segregation.world import DEFAULT_WORLD_SIZE, RentConfig, World


# Default maximum number of random-walk relocation attempts per unhappy agent.
DEFAULT_RELOCATION_ATTEMPTS = 10_000

# Default extension stop condition after repeated ticks with no successful movement.
DEFAULT_STALL_LIMIT = 50

# Income levels used by the extension's three-tier distribution.
INCOME_TIERS = (35.0, 65.0, 95.0)


@dataclass
class SegregationConfig:
    """Configuration values for a segregation simulation run."""

    # Either "baseline" or "extension".
    mode: str = "baseline"
    # Width and height of the square toroidal world.
    size: int = DEFAULT_WORLD_SIZE
    # Probability, as a percentage, that an initial patch contains an agent.
    density: float = 80.0
    # Required same-group neighbour percentage for preference satisfaction.
    similar_wanted: float = 30.0
    # Seed for the standard-library random number generator.
    seed: int | None = None
    # Maximum number of ticks to run.
    max_ticks: int = 10_000
    # Maximum random-walk attempts per unhappy agent.
    max_relocation_attempts: int = DEFAULT_RELOCATION_ATTEMPTS
    # Extension income distribution gap between blue and orange agents.
    income_gap: float = 0.0
    # Whether rent affordability affects happiness and relocation.
    use_affordability: bool = True
    # Maximum centre rent for the extension.
    rent_max: float = 100.0
    # Exponential distance scale for the extension rent surface.
    rent_scale: float = 14.0
    # Stop extension runs after this many no-movement ticks.
    stall_limit: int = DEFAULT_STALL_LIMIT


class SegregationModel:
    """Runs one stochastic Schelling segregation simulation."""

    def __init__(self, config: SegregationConfig):
        """Initialise the world, random generator, and starting population."""
        self.config = config
        self.rng = random.Random(config.seed)
        rent_config = None
        if config.mode == "extension":
            rent_config = RentConfig(config.rent_max, config.rent_scale)
        self.world = World(config.size, rent_config)
        self.agents: dict[int, Agent] = {}
        self.tick = 0
        self.last_moved_count = 0
        self.last_stuck_unhappy = 0
        self.no_movement_ticks = 0
        self._setup()

    def _setup(self) -> None:
        """Populate patches independently according to the density setting."""
        next_ident = 0
        for x in range(self.config.size):
            for y in range(self.config.size):
                if self.rng.random() * 100.0 >= self.config.density:
                    continue
                group = GROUPS[0] if self.rng.random() < 0.5 else GROUPS[1]
                income = self._draw_income(group) if self.config.mode == "extension" else None
                agent = Agent(
                    ident=next_ident,
                    group=group,
                    x=float(x),
                    y=float(y),
                    heading=self.rng.random() * 360.0,
                    income=income,
                )
                self.agents[next_ident] = agent
                self.world.place_agent(agent)
                next_ident += 1
        self.update_agent_states()

    def _draw_income(self, group: str) -> float:
        """Draw an extension income from a group-conditional three-tier distribution."""
        gap = max(0.0, min(1.0, self.config.income_gap))
        low_base = 1.0 / 3.0
        high_base = 1.0 / 3.0
        shift = 0.22 * gap
        if group == "blue":
            low_probability = low_base - shift
            high_probability = high_base + shift
        else:
            low_probability = low_base + shift
            high_probability = high_base - shift
        mid_probability = 1.0 - low_probability - high_probability

        draw = self.rng.random()
        if draw < low_probability:
            return INCOME_TIERS[0]
        if draw < low_probability + mid_probability:
            return INCOME_TIERS[1]
        return INCOME_TIERS[2]

    def update_agent_states(self) -> None:
        """Recount neighbours and update happiness for every agent."""
        for agent in self.agents.values():
            patch = agent.patch(self.world.size)
            similar = 0
            other = 0
            for neighbour in self.world.neighbours(patch):
                ident = self.world.occupancy.get(neighbour)
                if ident is None:
                    continue
                if self.agents[ident].group == agent.group:
                    similar += 1
                else:
                    other += 1

            total = similar + other
            agent.similar_nearby = similar
            agent.other_nearby = other
            agent.total_nearby = total
            threshold_count = self.config.similar_wanted * total / 100.0
            agent.preference_satisfied = total == 0 or similar >= threshold_count

            rent = self.world.rent_at(patch)
            if self.config.mode == "extension" and self.config.use_affordability:
                agent.affordability_satisfied = agent.can_afford(rent)
            else:
                agent.affordability_satisfied = True
            agent.happy = agent.preference_satisfied and agent.affordability_satisfied

    def unhappy_agents(self) -> list[Agent]:
        """Return agents that are currently unhappy."""
        return [agent for agent in self.agents.values() if not agent.happy]

    def is_finished(self) -> bool:
        """Return whether the run should stop before another movement tick."""
        return self.termination_reason() != "running"

    def termination_reason(self) -> str:
        """Return the current stopping state for reporting and control flow."""
        if not self.unhappy_agents():
            return "converged"
        if self.tick >= self.config.max_ticks:
            return "max_ticks"
        if self.config.mode == "extension" and self.no_movement_ticks >= self.config.stall_limit:
            return "stalled"
        return "running"

    def step(self) -> bool:
        """Advance the simulation by one tick.

        The unhappy set is chosen before movement, then shuffled to mimic NetLogo's
        randomised ask order.
        """
        if self.is_finished():
            return False

        unhappy = self.unhappy_agents()
        self.rng.shuffle(unhappy)
        moved_count = 0
        stuck_count = 0

        for agent in unhappy:
            moved = self._relocate_unhappy_agent(agent)
            if moved:
                moved_count += 1
            elif self.config.mode == "extension":
                stuck_count += 1

        self.last_moved_count = moved_count
        self.last_stuck_unhappy = stuck_count
        self.tick += 1
        if moved_count == 0:
            self.no_movement_ticks += 1
        else:
            self.no_movement_ticks = 0
        self.update_agent_states()
        return True

    def _relocate_unhappy_agent(self, agent: Agent) -> bool:
        """Move one unhappy agent to a valid random-walk target if possible."""
        if (
            self.config.mode == "extension"
            and self.config.use_affordability
            and not self._has_admissible_extension_patch(agent)
        ):
            return False

        search_x = agent.x
        search_y = agent.y
        search_heading = agent.heading
        for _ in range(self.config.max_relocation_attempts):
            new_x, new_y, search_heading, patch = self.world.random_walk_from(
                search_x,
                search_y,
                search_heading,
                self.rng,
            )
            search_x = new_x
            search_y = new_y
            if self.world.is_occupied(patch, excluding=agent.ident):
                continue
            if (
                self.config.mode == "extension"
                and self.config.use_affordability
                and not agent.can_afford(self.world.rent_at(patch))
            ):
                continue
            agent.heading = search_heading
            return self.world.move_agent(agent, new_x, new_y)
        agent.heading = search_heading
        return False

    def _has_admissible_extension_patch(self, agent: Agent) -> bool:
        """Return whether any vacant affordable patch exists for an extension agent."""
        for x in range(self.world.size):
            for y in range(self.world.size):
                patch = (x, y)
                if self.world.is_occupied(patch, excluding=agent.ident):
                    continue
                if agent.can_afford(self.world.rent_at(patch)):
                    return True
        return False

    def metrics_row(
        self,
        run_id: str = "single",
        repetition: int = 0,
        treatment: str = "",
    ) -> dict[str, str | int | float]:
        """Return a CSV-ready row with the current simulation metrics."""
        agent_list = list(self.agents.values())
        isolation = stats.isolation_by_group(agent_list)
        mean_rent = stats.mean_rent_by_group(self.world, agent_list)
        dissimilarity = stats.dissimilarity_index(self.world, self.agents)
        unhappy_count = sum(1 for agent in agent_list if not agent.happy)
        stuck_fraction = 0.0
        if agent_list:
            stuck_fraction = self.last_stuck_unhappy / len(agent_list)

        return {
            "run_id": run_id,
            "repetition": repetition,
            "treatment": treatment,
            "mode": self.config.mode,
            "seed": "" if self.config.seed is None else self.config.seed,
            "tick": self.tick,
            "size": self.config.size,
            "density": self.config.density,
            "similar_wanted": self.config.similar_wanted,
            "income_gap": self.config.income_gap,
            "use_affordability": str(self.config.use_affordability).lower(),
            "population": len(agent_list),
            "unhappy_count": unhappy_count,
            "percent_similar": _csv_number(stats.percent_similar(agent_list)),
            "percent_unhappy": _csv_number(stats.percent_unhappy(agent_list)),
            "moved_count": self.last_moved_count,
            "stuck_unhappy": self.last_stuck_unhappy,
            "stuck_unhappy_fraction": _csv_number(stuck_fraction),
            "no_movement_ticks": self.no_movement_ticks,
            "converged": str(unhappy_count == 0).lower(),
            "termination_reason": self.termination_reason(),
            "isolation_blue": _csv_number(isolation.get("blue")),
            "isolation_orange": _csv_number(isolation.get("orange")),
            "dissimilarity": _csv_number(dissimilarity),
            "mean_rent_blue": _csv_number(mean_rent.get("blue")),
            "mean_rent_orange": _csv_number(mean_rent.get("orange")),
        }

    def run_to_csv(
        self,
        output_path: Path,
        run_id: str = "single",
        repetition: int = 0,
        treatment: str = "",
        final_only: bool = False,
    ) -> None:
        """Run the simulation and write metric rows to a CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, str | int | float]] = []
        if not final_only:
            rows.append(self.metrics_row(run_id, repetition, treatment))
        while self.step():
            if not final_only:
                rows.append(self.metrics_row(run_id, repetition, treatment))
        if final_only:
            rows.append(self.metrics_row(run_id, repetition, treatment))
        write_rows(output_path, rows)


def _csv_number(value: float | None) -> str:
    """Format optional floating-point values for stable CSV output."""
    if value is None:
        return ""
    return f"{value:.6f}"


def write_rows(output_path: Path, rows: list[dict[str, str | int | float]]) -> None:
    """Write CSV rows using the field order from the first row."""
    if not rows:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
