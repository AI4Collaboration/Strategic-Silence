"""Shared constants for the Information Marketplace simulation."""
from __future__ import annotations


REGION_NAMES = ["Forest", "River", "Plains", "Mines"]

ADJACENCY = {
    "Forest": ["River", "Plains"],
    "River": ["Forest", "Mines"],
    "Mines": ["River", "Plains"],
    "Plains": ["Forest", "Mines"],
}

# Ring topology:
# Forest -- River
#   |          |
# Plains -- Mines

EVENT_TYPES = ["RESOURCE_FOUND", "GOLD_FOUND", "THREAT", "DEPLETION"]

STARTING_RESOURCES = {
    "Forest": {"food": 1},
    "River": {"food": 1, "water": 4},
    "Plains": {"food": 0, "water": 0},
    "Mines": {"gold": 3},
}

NUM_AGENTS = 4
NUM_ROUNDS = 10
STARTING_REGIONS = ["Forest", "River", "Plains", "Mines"]
