"""Toroidal grid and spatial utilities for the segregation model."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from segregation.agent import Agent


# Default NetLogo world size for the Segregation model, from -25 to 25 inclusive.
DEFAULT_WORLD_SIZE = 51


@dataclass
class RentConfig:
    """Parameters used to construct the extension rent surface."""

    # Maximum rent at the centre of the world.
    rent_max: float = 100.0
    # Distance scale in the exponential rent decay.
    rent_scale: float = 14.0


class World:
    """Stores patch occupancy and rent values for a square toroidal grid."""

    def __init__(self, size: int = DEFAULT_WORLD_SIZE, rent_config: RentConfig | None = None):
        """Create an empty world.

        If rent_config is provided, every patch receives an exponentially decaying
        rent value with the highest rent at the centre of the world.
        """
        self.size = size
        self.occupancy: dict[tuple[int, int], int] = {}
        self.rent: dict[tuple[int, int], float] = {}
        self.rent_config = rent_config
        if rent_config is not None:
            self._build_rent_surface(rent_config)

    def _build_rent_surface(self, rent_config: RentConfig) -> None:
        """Populate rent values for all patches.

        Rent is intentionally not wrapped around the torus: the rent field models
        a single expensive centre and cheaper outer areas.
        """
        centre = (self.size - 1) / 2
        for x in range(self.size):
            for y in range(self.size):
                distance = math.hypot(x - centre, y - centre)
                rent = rent_config.rent_max * math.exp(-distance / rent_config.rent_scale)
                self.rent[(x, y)] = rent

    def wrap_patch(self, x: int, y: int) -> tuple[int, int]:
        """Return a patch coordinate wrapped into the finite toroidal world."""
        return (x % self.size, y % self.size)

    def patch_from_position(self, x: float, y: float) -> tuple[int, int]:
        """Return the toroidal patch containing a continuous coordinate."""
        return (math.floor(x + 0.5) % self.size, math.floor(y + 0.5) % self.size)

    def rent_at(self, patch: tuple[int, int]) -> float:
        """Return the rent for a patch, or zero when the extension is disabled."""
        return self.rent.get(patch, 0.0)

    def is_occupied(self, patch: tuple[int, int], excluding: int | None = None) -> bool:
        """Return whether a patch is occupied by an agent other than excluding."""
        occupant = self.occupancy.get(patch)
        return occupant is not None and occupant != excluding

    def place_agent(self, agent: Agent) -> None:
        """Record an agent at the patch corresponding to its current position."""
        self.occupancy[agent.patch(self.size)] = agent.ident

    def move_agent(self, agent: Agent, new_x: float, new_y: float) -> bool:
        """Move an agent to a new continuous position and update occupancy.

        The method assumes the target patch has already been checked for validity.
        It returns True when the occupied patch changes.
        """
        old_patch = agent.patch(self.size)
        old_occupant = self.occupancy.get(old_patch)
        if old_occupant == agent.ident:
            del self.occupancy[old_patch]

        agent.x = new_x % self.size
        agent.y = new_y % self.size
        new_patch = agent.patch(self.size)
        self.occupancy[new_patch] = agent.ident
        return old_patch != new_patch

    def neighbours(self, patch: tuple[int, int]) -> list[tuple[int, int]]:
        """Return the Moore neighbourhood around a patch with toroidal wrapping."""
        x, y = patch
        result: list[tuple[int, int]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                result.append(self.wrap_patch(x + dx, y + dy))
        return result

    def random_walk_target(
        self,
        agent: Agent,
        rng: random.Random,
        max_distance: float = 10.0,
    ) -> tuple[float, float, tuple[int, int]]:
        """Generate a NetLogo-like random-walk target for an agent.

        NetLogo heading 0 points north, so sine controls x movement and cosine
        controls y movement.
        """
        agent.heading = (agent.heading + rng.random() * 360.0) % 360.0
        distance = rng.random() * max_distance
        radians = math.radians(agent.heading)
        new_x = (agent.x + math.sin(radians) * distance) % self.size
        new_y = (agent.y + math.cos(radians) * distance) % self.size
        return new_x, new_y, self.patch_from_position(new_x, new_y)

    def random_walk_from(
        self,
        x: float,
        y: float,
        heading: float,
        rng: random.Random,
        max_distance: float = 10.0,
    ) -> tuple[float, float, float, tuple[int, int]]:
        """Generate a random-walk target from temporary search state."""
        new_heading = (heading + rng.random() * 360.0) % 360.0
        distance = rng.random() * max_distance
        radians = math.radians(new_heading)
        new_x = (x + math.sin(radians) * distance) % self.size
        new_y = (y + math.cos(radians) * distance) % self.size
        return new_x, new_y, new_heading, self.patch_from_position(new_x, new_y)

    def count_by_group(self, agents: dict[int, Agent]) -> dict[str, int]:
        """Return population counts by group."""
        counts: dict[str, int] = {}
        for ident in self.occupancy.values():
            group = agents[ident].group
            counts[group] = counts.get(group, 0) + 1
        return counts
