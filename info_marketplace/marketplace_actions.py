"""Action definitions for the Information Marketplace simulation."""

from dataclasses import dataclass


@dataclass
class ScoutAction:
    """Simple action dataclass (NOT a Word_Play Action subclass)."""

    action_type: str  # "move", "gather", "deposit", "stay", "trade"
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
        elif self.action_type == "trade":
            give_res = self.details.get('give_resource', '?')
            give_amt = self.details.get('give_amount', 0)
            recv_res = self.details.get('receive_resource', '?')
            recv_amt = self.details.get('receive_amount', 0)
            partner = self.details.get('partner', '?')
            return f"Trade {give_amt} {give_res} for {recv_amt} {recv_res} with {partner}"
        return "Stay"
