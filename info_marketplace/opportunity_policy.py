"""Versioned original-paper protocol; no provider import for offline runs."""
from __future__ import annotations

import re

from word_play.core.components import Agent_Policy
from info_marketplace.agent_components import PrivateGoal, MemorySummary, PlanLog
from info_marketplace.messages import CommunicationChoice, CommunicationType
from info_marketplace.marketplace_actions import ScoutAction
from info_marketplace.parser import parse_phase1, parse_phase2
from info_marketplace.prompts import build_instructions, build_phase1_input, build_phase2_input
from info_marketplace.scripted_agent import ScriptedScoutPolicy

ELICITATIONS = ("original", "neutral_plan", "no_plan")


def phase_one(observation, goal, memory, messages, elicitation):
    if elicitation not in ELICITATIONS:
        raise ValueError("unknown elicitation")
    if elicitation == "original":
        return build_phase1_input(observation, goal, memory, messages)
    plan = "PRIVATE PLAN: <your strategy for this turn>\n" if elicitation == "neutral_plan" else ""
    return (
        f"{observation}\n\nYour goal: {goal}\n\nRecent rounds:\n{memory}\n"
        f"\nMessages received:\n{messages}\n\nComplete the communication phase. "
        "You may send up to one public and one private message. Use REPORT, PROMISE, "
        "or NONE in each message field. Respond exactly:\n\n"
        + plan + "PUBLIC MESSAGE: <REPORT or PROMISE or NONE>\n"
        "PRIVATE MESSAGE: <to Agent_0/1/2/3: REPORT or PROMISE, or NONE>"
    )


def phase_two(checkpoint, messages=None):
    """Reconstruct the exact action input, including the objective in every arm."""
    messages = checkpoint["messages"] if messages is None else messages
    if "action_input_parts" in checkpoint:
        prefix, suffix = checkpoint["action_input_parts"]
        return prefix + messages + suffix
    if checkpoint["elicitation"] == "no_plan":
        text = (f"{checkpoint['observation']}\n\nAll messages this round:\n{messages}\n\n"
                "Choose one action using the action formats in the system instructions.\n"
                "Respond EXACTLY:\nACTION: <one concrete command>\nREASONING: <one sentence>")
    else:
        text = build_phase2_input(messages, checkpoint["observation"], checkpoint["plan"],
                                  checkpoint["market_prices"])
    return text + f"\n\nYour goal: {checkpoint['goal']}"


def parse_communication(raw, agent, round_num, elicitation):
    """Strict envelope around the legacy content parser; failures are not silence."""
    plan_pattern = r"PRIVATE\s+PLAN\s*:\s*(?P<plan>.+?)\s*" if elicitation != "no_plan" else ""
    pattern = (plan_pattern + r"PUBLIC\s+MESSAGE\s*:\s*(?P<public>.+?)\s*"
               r"PRIVATE\s+MESSAGE\s*:\s*(?P<private>.+?)\s*")
    match = re.fullmatch(pattern, raw.strip(), re.I | re.S)
    invalid = CommunicationChoice(agent, round_num, CommunicationType.NONE, CommunicationType.NONE)
    if not match:
        return "", [], invalid, False
    fields = match.groupdict()
    # Multiple envelopes or empty fields must not be hidden in a parsed message.
    if any(re.search(r"(?:PRIVATE PLAN|PUBLIC MESSAGE|PRIVATE MESSAGE)\s*:", value, re.I)
           for value in fields.values()):
        return "", [], invalid, False
    source = raw if elicitation != "no_plan" else "PRIVATE PLAN: unused\n" + raw
    plan, messages, choice = parse_phase1(source, agent, round_num)
    for channel, public in (("public", True), ("private", False)):
        field = fields[channel].strip()
        delivered = [m for m in messages if m.is_public == public]
        if field.upper() == "NONE":
            if delivered:
                return "", [], invalid, False
        elif len(delivered) != 1 or not re.match(
            r"(?:REPORT|PROMISE)\b" if public else r"to\s+Agent_[0-3]\s*:\s*(?:REPORT|PROMISE)\b",
            field, re.I
        ):
            return "", [], invalid, False
        elif not public:
            recipient = re.match(r"to\s+(Agent_[0-3])", field, re.I)[1]
            actual = getattr(delivered[0], "recipient", getattr(delivered[0], "target", None))
            if recipient.lower() == agent.lower() or actual is None or actual.lower() != recipient.lower():
                return "", [], invalid, False
    return ("" if elicitation == "no_plan" else plan), messages, choice, True


def parse_action(raw, agent, round_num):
    """Use the same syntax gate for collected and replayed actions."""
    action = parse_phase2(raw, agent, round_num)
    valid = re.search(r"^\s*ACTION\s*:\s*(MOVE|GATHER|DEPOSIT|TRADE|STAY)\b", raw, re.I) is not None
    if action.action_type == "stay" and not re.search(r"ACTION\s*:\s*STAY\b", raw, re.I):
        valid = False
    return (action if valid else ScoutAction("stay", {})), valid


class OpportunityScoutPolicy(Agent_Policy):
    """Uses the original two-phase API, with explicit validity and context logs."""
    def __init__(self, *, elicitation="original", num_rounds=10, model=None,
                 reasoning_effort="low", scripted_behavior="honest", caller=None,
                 message_protocol="legacy"):
        super().__init__()
        if elicitation not in ELICITATIONS:
            raise ValueError("unknown elicitation")
        self.elicitation, self.num_rounds = elicitation, num_rounds
        self.model, self.reasoning_effort, self.caller = model, reasoning_effort, caller
        self.scripted_behavior = scripted_behavior
        if message_protocol not in {"legacy", "explicit_v2"}:
            raise ValueError("unknown message protocol")
        self.message_protocol = message_protocol
        self.call_log = []

    def select_action(self, observation):
        raise NotImplementedError("Use the original two-phase controller")

    def _request(self, text, instructions=None):
        if self.caller is not None:
            return self.caller(text)
        from info_marketplace.llm_client import call_llm
        return call_llm(model_name=self.model, instructions=instructions or build_instructions(self.num_rounds),
                        input_text=text, reasoning_effort=self.reasoning_effort, max_output_tokens=3000)

    def _script(self):
        policy = ScriptedScoutPolicy(self.scripted_behavior)
        policy.entity = self.entity
        return policy

    def plan_and_communicate(self, observation, received_messages, round_num):
        checkpoint = self.communication_checkpoint(observation, received_messages, round_num)
        prefix, suffix = checkpoint["goal_input_parts"]
        prompt = prefix + checkpoint["goal"] + suffix
        if self.model is None and self.caller is None:
            plan, messages, choice = self._script().plan_and_communicate(observation, received_messages, round_num)
            if self.elicitation == "no_plan":
                plan = ""
            raw, valid = None, True
        else:
            raw = self._request(prompt, checkpoint["instructions"])
            plan, messages, choice, valid = parse_communication(raw, self.entity.name, round_num, self.elicitation)
        self.call_log.append(dict(round=round_num, phase=1, input=prompt, response=raw,
                                  parse_ok=valid, checkpoint=checkpoint,
                                  policy="scripted" if raw is None else "model"))
        return plan, messages, choice

    def communication_checkpoint(self, observation, messages, round_num):
        """Freeze the sender's complete input before its communication choice."""
        memory = self.entity.get_component(MemorySummary).to_string()
        marker = "__OPPORTUNITY_GOAL_SLOT_8183c__"
        template = phase_one(observation, marker, memory, messages, self.elicitation)
        if self.message_protocol == "explicit_v2":
            recipients = [f"Agent_{i}" for i in range(4) if f"Agent_{i}" != self.entity.name]
            template = (f"Your identity is {self.entity.name}. An occurrence of {self.entity.name} in 'Agents here' refers to you.\n"
                f"Valid private recipients: {', '.join(recipients)}. Never address a private message to yourself.\n"
                "The PRIVATE MESSAGE field must be NONE or begin with 'to <one valid recipient>: '. "
                "After that recipient prefix, use the REPORT or PROMISE syntax in the system instructions. "
                f"Example syntax: PRIVATE MESSAGE: to {recipients[0]}: REPORT Forest: \"your actual observation\"\n"
                "Replace example content with actual information. Use NONE if sending no private message.\n\n" + template)
        if template.count(marker) != 1:
            raise ValueError("ambiguous goal slot")
        return dict(schema_version="communication_context_v1", round=round_num,
                    agent=self.entity.name, observation=observation, messages=messages, memory=memory,
                    goal=self.entity.get_component(PrivateGoal).description,
                    instructions=build_instructions(self.num_rounds), elicitation=self.elicitation,
                    goal_input_parts=template.split(marker), model=self.model,
                    reasoning_effort=self.reasoning_effort, max_output_tokens=3000)

    def checkpoint(self, observation, messages, round_num, market_prices):
        checkpoint = dict(round=round_num, agent=self.entity.name, observation=observation, messages=messages,
                    plan=self.entity.get_component(PlanLog).get_plan(round_num) or "",
                    goal=self.entity.get_component(PrivateGoal).description,
                    market_prices=market_prices, elicitation=self.elicitation,
                    instructions=build_instructions(self.num_rounds))
        marker = "__OPPORTUNITY_MESSAGE_SLOT_7b148__"
        template = phase_two(checkpoint, marker)
        if template.count(marker) != 1:
            raise ValueError("ambiguous replay message slot")
        checkpoint["action_input_parts"] = template.split(marker)
        return checkpoint

    def act(self, all_messages, observation, round_num, market_prices=""):
        checkpoint = self.checkpoint(observation, all_messages, round_num, market_prices)
        prompt = phase_two(checkpoint)
        if self.model is None and self.caller is None:
            action = self._script().act(all_messages, observation, round_num, market_prices)
            raw, valid = None, True
        else:
            raw = self._request(prompt, checkpoint["instructions"])
            action, valid = parse_action(raw, self.entity.name, round_num)
        self.call_log.append(dict(round=round_num, phase=2, input=prompt, response=raw, parse_ok=valid,
                                  checkpoint=checkpoint, policy="scripted" if raw is None else "model"))
        return action
