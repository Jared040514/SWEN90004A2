"""Metric calculations for baseline and extended segregation runs."""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean

from segregation.agent import Agent, GROUPS
from segregation.world import World


# Spatial block size used for the dissimilarity index in the extension.
DISSIMILARITY_BLOCK_SIZE = 5


def percent_similar(agents: list[Agent]) -> float | None:
    """Return the neighbour-count-weighted percent-similar metric.

    The result is None when no agent has any occupied neighbour, matching the
    undefined edge case in the NetLogo model.
    """
    total_neighbours = sum(agent.total_nearby for agent in agents)
    if total_neighbours == 0:
        return None
    similar = sum(agent.similar_nearby for agent in agents)
    return 100.0 * similar / total_neighbours


def percent_unhappy(agents: list[Agent]) -> float:
    """Return the percentage of agents that are currently unhappy."""
    if not agents:
        return 0.0
    unhappy = sum(1 for agent in agents if not agent.happy)
    return 100.0 * unhappy / len(agents)


def isolation_by_group(agents: list[Agent]) -> dict[str, float | None]:
    """Return neighbour-count-weighted same-group exposure for each group."""
    result: dict[str, float | None] = {}
    for group in GROUPS:
        group_agents = [agent for agent in agents if agent.group == group]
        total = sum(agent.total_nearby for agent in group_agents)
        if total == 0:
            result[group] = None
        else:
            similar = sum(agent.similar_nearby for agent in group_agents)
            result[group] = 100.0 * similar / total
    return result


def mean_rent_by_group(world: World, agents: list[Agent]) -> dict[str, float | None]:
    """Return the mean current rent paid by each group."""
    rents: dict[str, list[float]] = {group: [] for group in GROUPS}
    for agent in agents:
        rents[agent.group].append(world.rent_at(agent.patch(world.size)))
    return {
        group: mean(values) if values else None
        for group, values in rents.items()
    }


def dissimilarity_index(world: World, agents: dict[int, Agent]) -> float | None:
    """Return a block-level two-group dissimilarity index.

    Single-occupancy patches make patch-level dissimilarity trivially equal to
    one, so the metric is computed over fixed 5x5 patch blocks.
    """
    totals = world.count_by_group(agents)
    blue_total = totals.get("blue", 0)
    orange_total = totals.get("orange", 0)
    if blue_total == 0 or orange_total == 0:
        return None

    regions: dict[tuple[int, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for patch, ident in world.occupancy.items():
        region = (patch[0] // DISSIMILARITY_BLOCK_SIZE, patch[1] // DISSIMILARITY_BLOCK_SIZE)
        regions[region][agents[ident].group] += 1

    total_difference = 0.0
    for counts in regions.values():
        blue_share = counts.get("blue", 0) / blue_total
        orange_share = counts.get("orange", 0) / orange_total
        total_difference += abs(blue_share - orange_share)
    return 0.5 * total_difference


def confidence_interval_95(values: list[float]) -> tuple[float, float]:
    """Return mean and normal-approximation 95 percent half-width."""
    if not values:
        return (math.nan, math.nan)
    centre = mean(values)
    if len(values) == 1:
        return (centre, 0.0)
    variance = sum((value - centre) ** 2 for value in values) / (len(values) - 1)
    return (centre, 1.96 * math.sqrt(variance) / math.sqrt(len(values)))
