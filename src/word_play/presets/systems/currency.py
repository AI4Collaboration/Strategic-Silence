from __future__ import annotations

from word_play.core import Action_Validation, Component, Entity, Environment, Action_Arg


class Currency_Amount_Arg(Action_Arg):
    def parse(self, input: str) -> int:
        return int(input)

    def is_valid(self, value: int | float, actor: Entity, target_entity: Entity, env: Environment) -> bool:
        try:
            return value > 0
        except TypeError:
            return False

    def arg_description(self, actor: Entity, target_entity: Entity, env: Environment) -> str:
        money = actor.get_component(Money)
        if money:
            return f"Amount (you have {money.amount} {money.currency_name})"
        return "Amount"


class Money(Component):
    def __init__(self, currency_name: str = "gold", amount: float = 0.0):
        super().__init__()
        self.currency_name = currency_name
        self.amount: float = amount

    def __str__(self) -> str:
        return f"{self.amount:g} {self.currency_name}"

    def add(self, amount: float) -> float:
        if amount <= 0:
            return 0.0
        self.amount += amount
        return amount

    def subtract(self, amount: float) -> float:
        actual = min(amount, self.amount)
        self.amount -= actual
        return actual

    def transfer_to(self, recipient: Money, amount: float) -> float:
        moved = self.subtract(amount)
        recipient.add(moved)
        return moved


class Has_Money(Action_Validation):
    def is_valid(self, actor: Entity, target_entity: Entity, env: Environment) -> bool:
        return actor.get_component(Money) is not None


class Has_Currency(Action_Validation):
    def is_valid(self, actor: Entity, target_entity: Entity, env: Environment) -> bool:
        money = actor.get_component(Money)
        return money is not None and money.amount > 0


def money_amount(entity: Entity) -> float:
    money = entity.get_component(Money)
    return 0 if money is None else money.amount


def amount_within_balance(amount: int | float, actor: Entity, target_entity: Entity, env: Environment) -> bool:
    return isinstance(amount, (int, float)) and not isinstance(amount, bool) and 0 <= amount <= money_amount(actor)
