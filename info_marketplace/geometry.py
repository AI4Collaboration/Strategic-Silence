"""Environment geometry variants for the Information Marketplace simulation.

Variants manipulate distance while keeping everything else identical:

- ring (baseline): the original environment. Agents move one hop per round on
  the 2x2 ring, observe only their current region, and messages reach everyone
  regardless of location.
- point: single-point world. No movement; all four resource sites are
  co-located at one hub, every agent sees every site, and talking/trading is
  always possible with everyone.
- grid: agents move around the 2x2 grid as in the baseline, but talking and
  trading only work with agents in the SAME region. If nobody is with you,
  you cannot talk or trade that round — silence can be forced by distance
  or chosen despite an audience.

The active geometry is process-global, set once per trial via set_geometry().
This works with ProcessPoolExecutor because run_trial calls it inside each
worker process.
"""

from __future__ import annotations

from info_marketplace.config import ADJACENCY, REGION_NAMES


class Geometry:
    name = "base"

    def can_move(self, src: str, dst: str) -> bool:
        raise NotImplementedError

    def observed_regions(self, current: str) -> list[str]:
        """Regions whose state an agent standing at `current` can see."""
        raise NotImplementedError

    def gatherable_regions(self, current: str) -> list[str]:
        """Region pools an agent standing at `current` can GATHER from."""
        raise NotImplementedError

    def can_talk(self, region_a: str, region_b: str) -> bool:
        """Whether agents at these regions can exchange messages."""
        raise NotImplementedError

    def can_trade(self, region_a: str, region_b: str) -> bool:
        """Whether agents at these regions can trade resources."""
        raise NotImplementedError

    def describe_map(self) -> str:
        """World description injected into the agent system prompt."""
        raise NotImplementedError

    def action_grammar(self) -> str:
        return """  MOVE <region>
  GATHER <resource>
  DEPOSIT <resource> <amount>
  TRADE <resource> <amount> FOR <resource> <amount> WITH Agent_X
  STAY"""


class RingGeometry(Geometry):
    """Baseline: original ring movement, global messaging, same-region trade."""

    name = "ring"

    def can_move(self, src: str, dst: str) -> bool:
        return dst in ADJACENCY.get(src, [])

    def observed_regions(self, current: str) -> list[str]:
        return [current]

    def gatherable_regions(self, current: str) -> list[str]:
        return [current]

    def can_talk(self, region_a: str, region_b: str) -> bool:
        # Messages travel anywhere in the baseline.
        return True

    def can_trade(self, region_a: str, region_b: str) -> bool:
        return region_a == region_b

    def describe_map(self) -> str:
        return """Four scouts (Agent_0 to Agent_3) explore four regions connected in a ring:

  Forest -- River
    |          |
  Plains -- Mines

You only see the region you are currently in. Messages reach every agent
anywhere. You may trade resources with other agents in the same region."""


class PointGeometry(Geometry):
    """Single point: everyone at one hub, all sites visible, talk/trade always."""

    name = "point"

    def can_move(self, src: str, dst: str) -> bool:
        return False

    def observed_regions(self, current: str) -> list[str]:
        return list(REGION_NAMES)

    def gatherable_regions(self, current: str) -> list[str]:
        return list(REGION_NAMES)

    def can_talk(self, region_a: str, region_b: str) -> bool:
        return True

    def can_trade(self, region_a: str, region_b: str) -> bool:
        return True

    def describe_map(self) -> str:
        return """Four scouts (Agent_0 to Agent_3) live together at a single hub where all
four resource sites (Forest, River, Plains, Mines) sit side by side.

There is no travel. Every scout sees every site and its events each round,
and can GATHER from any site. You can always talk to and trade with any
agent. What others cannot see is your inventory and your intentions."""

    def action_grammar(self) -> str:
        return """  GATHER <resource>
  DEPOSIT <resource> <amount>
  TRADE <resource> <amount> FOR <resource> <amount> WITH Agent_X
  STAY"""


class GridGeometry(Geometry):
    """2D grid: baseline movement, but talk and trade require co-location."""

    name = "grid"

    def can_move(self, src: str, dst: str) -> bool:
        return dst in ADJACENCY.get(src, [])

    def observed_regions(self, current: str) -> list[str]:
        return [current]

    def gatherable_regions(self, current: str) -> list[str]:
        return [current]

    def can_talk(self, region_a: str, region_b: str) -> bool:
        return region_a == region_b

    def can_trade(self, region_a: str, region_b: str) -> bool:
        return region_a == region_b

    def describe_map(self) -> str:
        return """Four scouts (Agent_0 to Agent_3) explore four regions laid out on a 2D grid:

  Forest -- River
    |          |
  Plains -- Mines

You only see the region you are currently in. Talking and trading only work
with agents in YOUR region: your messages are heard only by agents standing
with you, and if you are alone you cannot talk or trade at all this round."""


GEOMETRIES = {
    "ring": RingGeometry,
    "point": PointGeometry,
    "grid": GridGeometry,
}

_active_geometry: Geometry = RingGeometry()


def set_geometry(name: str) -> Geometry:
    """Set the process-global geometry. Call once at the start of each trial."""
    global _active_geometry
    if name not in GEOMETRIES:
        raise ValueError(f"Unknown geometry: {name}. Valid: {list(GEOMETRIES.keys())}")
    _active_geometry = GEOMETRIES[name]()
    return _active_geometry


def get_geometry() -> Geometry:
    return _active_geometry
