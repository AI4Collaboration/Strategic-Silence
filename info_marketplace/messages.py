"""Message and communication components for the Information Marketplace simulation."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class CommunicationType(Enum):
    REPORT = "REPORT"
    PROMISE = "PROMISE"
    NONE = "NONE"


@dataclass
class CommunicationChoice:
    """Records an agent's communication decision for a round — including silence.

    This captures the *choice* of whether to communicate, not just the content
    of messages that were sent. Silence (NONE) is a first-class signal here.
    """

    agent_name: str
    round_num: int
    public_type: CommunicationType
    private_type: CommunicationType
    private_recipient: str | None = None

    @property
    def sent_any(self) -> bool:
        return self.public_type != CommunicationType.NONE or self.private_type != CommunicationType.NONE

    @property
    def fully_silent(self) -> bool:
        return self.public_type == CommunicationType.NONE and self.private_type == CommunicationType.NONE

    @property
    def silent_in_public(self) -> bool:
        return self.public_type == CommunicationType.NONE

    @property
    def only_whispered(self) -> bool:
        return self.public_type == CommunicationType.NONE and self.private_type != CommunicationType.NONE

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "round": self.round_num,
            "public_type": self.public_type.value,
            "private_type": self.private_type.value,
            "private_recipient": self.private_recipient,
            "sent_any": self.sent_any,
            "fully_silent": self.fully_silent,
            "silent_in_public": self.silent_in_public,
            "only_whispered": self.only_whispered,
        }


@dataclass
class Report:
    """A report about a region sent by an agent."""

    sender: str
    region_claimed: str
    claim: str
    is_public: bool
    recipient: str | None
    round_sent: int
    message_id: str = ""


@dataclass
class Promise:
    """A promise made by an agent to another agent."""

    sender: str
    target: str
    commitment: str
    by_round: int
    round_sent: int
    is_public: bool
    message_id: str = ""
    fulfilled: bool | None = None


class MessageLog:
    """Standalone object (NOT a Component) owned by the environment."""

    def __init__(self):
        self.messages: list[Report | Promise] = []
        self.counter = 0

    def next_id(self) -> str:
        """Returns sequential message IDs: msg_001, msg_002, etc."""
        self.counter += 1
        return f"msg_{self.counter:03d}"

    def add(self, message: Report | Promise):
        """Stores message, auto-assigns message_id if empty."""
        if not message.message_id:
            message.message_id = self.next_id()
        self.messages.append(message)

    def get_messages_for(self, agent_name: str, round_num: int) -> list[Report | Promise]:
        """Returns public messages + private messages addressed to agent, from this round."""
        result = []
        for msg in self.messages:
            if msg.round_sent != round_num:
                continue
            if msg.is_public:
                result.append(msg)
            elif isinstance(msg, Report) and msg.recipient == agent_name:
                result.append(msg)
            elif isinstance(msg, Promise) and msg.target == agent_name:
                result.append(msg)
        return result

    def get_sent_by(self, agent_name: str) -> list[Report | Promise]:
        """Returns all messages sent by agent."""
        return [msg for msg in self.messages if msg.sender == agent_name]

    def get_promises_by(self, agent_name: str) -> list[Promise]:
        """Returns all promises made by agent."""
        return [msg for msg in self.messages if isinstance(msg, Promise) and msg.sender == agent_name]

    def format_for_agent(self, agent_name: str, round_num: int) -> str:
        """Human-readable format, <100 tokens."""
        messages = self.get_messages_for(agent_name, round_num)
        if not messages:
            return "No messages received."

        lines = []
        for msg in messages:
            if isinstance(msg, Report):
                visibility = "PUBLIC" if msg.is_public else f"PRIVATE to {'you' if msg.recipient == agent_name else msg.recipient}"
                lines.append(f'[{visibility}] {msg.sender} reports about {msg.region_claimed}: "{msg.claim}"')
            elif isinstance(msg, Promise):
                visibility = "PUBLIC" if msg.is_public else f"PRIVATE to {'you' if msg.target == agent_name else msg.target}"
                lines.append(
                    f"[{visibility}] {msg.sender} promises {msg.target}: \"{msg.commitment}\" (by round {msg.by_round})"
                )

        return "\n".join(lines)


if __name__ == "__main__":
    print("=== Testing MessageLog ===")
    log = MessageLog()

    print("\n--- Adding Reports ---")
    # Public report
    report1 = Report(
        sender="Agent_0",
        region_claimed="River",
        claim="Found 3 food, area safe.",
        is_public=True,
        recipient=None,
        round_sent=1,
    )
    log.add(report1)
    print(f"Added public report: {report1.message_id}")

    # Private report
    report2 = Report(
        sender="Agent_2",
        region_claimed="Mines",
        claim="Gold deposit, 2 units.",
        is_public=False,
        recipient="Agent_0",
        round_sent=1,
    )
    log.add(report2)
    print(f"Added private report: {report2.message_id}")

    # Another public report
    report3 = Report(
        sender="Agent_1",
        region_claimed="Forest",
        claim="Low on resources, moving out.",
        is_public=True,
        recipient=None,
        round_sent=2,
    )
    log.add(report3)
    print(f"Added public report: {report3.message_id}")

    print("\n--- Adding Promises ---")
    promise1 = Promise(
        sender="Agent_1",
        target="Agent_3",
        commitment="I will scout Forest.",
        by_round=5,
        round_sent=1,
        is_public=True,
    )
    log.add(promise1)
    print(f"Added public promise: {promise1.message_id}")

    promise2 = Promise(
        sender="Agent_2",
        target="Agent_0",
        commitment="I will bring back gold.",
        by_round=3,
        round_sent=2,
        is_public=False,
    )
    log.add(promise2)
    print(f"Added private promise: {promise2.message_id}")

    print("\n--- Testing get_messages_for (Agent_0, round 1) ---")
    messages_agent0_r1 = log.get_messages_for("Agent_0", 1)
    print(f"Found {len(messages_agent0_r1)} messages")
    for msg in messages_agent0_r1:
        print(f"  - {msg.message_id}: {type(msg).__name__}")

    print("\n--- Testing format_for_agent (Agent_0, round 1) ---")
    formatted = log.format_for_agent("Agent_0", 1)
    print(formatted)

    print("\n--- Testing format_for_agent (Agent_1, round 1) ---")
    formatted = log.format_for_agent("Agent_1", 1)
    print(formatted)

    print("\n--- Testing format_for_agent (Agent_3, round 1) ---")
    formatted = log.format_for_agent("Agent_3", 1)
    print(formatted)

    print("\n--- Testing format_for_agent (Agent_0, round 2) ---")
    formatted = log.format_for_agent("Agent_0", 2)
    print(formatted)

    print("\n--- Testing get_sent_by (Agent_2) ---")
    sent_by_agent2 = log.get_sent_by("Agent_2")
    print(f"Agent_2 sent {len(sent_by_agent2)} messages:")
    for msg in sent_by_agent2:
        print(f"  - {msg.message_id}: {type(msg).__name__}")

    print("\n--- Testing get_promises_by (Agent_1) ---")
    promises_by_agent1 = log.get_promises_by("Agent_1")
    print(f"Agent_1 made {len(promises_by_agent1)} promises:")
    for promise in promises_by_agent1:
        print(f"  - {promise.message_id}: {promise.commitment}")

    print("\n--- Testing empty messages ---")
    formatted_empty = log.format_for_agent("Agent_99", 10)
    print(formatted_empty)
