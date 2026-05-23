"""Agent definitions for the Schelling segregation model."""

from __future__ import annotations

import math
from dataclasses import dataclass


# Valid group labels used throughout the model and CSV output.
GROUPS = ("blue", "orange")


@dataclass
class Agent:
    """Represents one resident in the segregation model."""

    # Unique integer identifier assigned when the agent is created.
    ident: int
    # Group membership. The baseline model uses only blue and orange.
    group: str
    # Continuous x coordinate. The occupied patch is derived from this value.
    x: float
    # Continuous y coordinate. The occupied patch is derived from this value.
    y: float
    # NetLogo-style heading in degrees, where 0 means north.
    heading: float
    # Income used by the extension. Baseline agents keep this as None.
    income: float | None = None
    # Cached count of nearby agents of the same group.
    similar_nearby: int = 0
    # Cached count of nearby agents of the other group.
    other_nearby: int = 0
    # Cached total number of occupied neighbouring patches.
    total_nearby: int = 0
    # Whether the agent currently satisfies the model's happiness rule.
    happy: bool = False
    # Whether the agent currently satisfies only the neighbourhood preference.
    preference_satisfied: bool = False
    # Whether the agent can afford the rent on its current patch.
    affordability_satisfied: bool = True

    def patch(self, size: int) -> tuple[int, int]:
        """Return the toroidal patch containing this agent's continuous position."""
        return (math.floor(self.x + 0.5) % size, math.floor(self.y + 0.5) % size)

    def can_afford(self, rent: float) -> bool:
        """Return whether the agent can pay a rent value.

        Baseline agents have no income constraint and are treated as able to afford
        every patch.
        """
        if self.income is None:
            return True
        return rent <= self.income
