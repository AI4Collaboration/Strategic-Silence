"""Action definitions for the Information Marketplace simulation."""

from dataclasses import dataclass


@dataclass
class ScoutAction:
    """Simple action dataclass (NOT a Word_Play Action subclass)."""

from __future__ import annotations

    action_type: str  # "move", "gather", "deposit", "stay"
    details: dict  # {"destination": "River"}, {"resource": "food"}, {"resource": "food", "amount": 2}, {}

    def describe(self) -> str:
        """Returns human-readable description of the action."""
        if self.action_type == "move":
            return f"Move to {self.details['destination']}"
        elif self.action_type == "gather":
            return f"Gather {self.details['resource']}"
        elif self.action_type == "deposit":
            amount = self.details.get('amount', 1)
            return f"Deposit {amount} {self.details['resource']} to settlement"
        return "Stay"
