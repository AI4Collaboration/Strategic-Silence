from __future__ import annotations

import json
import re
from typing import Any

from word_play.core import Agent_Policy, Entity, Environment, Observation
from word_play.core.actions import Action_Selection
from word_play.presets.models import LLM_MODEL_REGISTRY, Model
from word_play.presets.systems.communication.core import Communication_Policy


class LLM_Action_And_Communication_Policy(Agent_Policy, Communication_Policy):
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        model_key: str,
        system_prompt: str = "",
        use_chain_of_thought: bool = True,
        reasoning_effort: str | None = None,
        action_generation_config: dict[str, Any] | None = None,
        message_generation_config: dict[str, Any] | None = None,
        observation_memory_window: int = 10,
        conversation_memory_window: int = 10,
        action_max_new_tokens: int = 300,
        message_max_new_tokens: int = 500,
        chain_of_thought_max_new_tokens: int = 1000,
    ):
        Agent_Policy.__init__(self)
        Communication_Policy.__init__(self)
        self.model_key = model_key
        self.system_prompt = system_prompt
        self.use_chain_of_thought = use_chain_of_thought
        self.reasoning_effort = reasoning_effort
        self.action_generation_config = action_generation_config or {}
        self.message_generation_config = message_generation_config or {}
        self.observation_memory_window = observation_memory_window
        self.conversation_memory_window = conversation_memory_window
        self.action_max_new_tokens = action_max_new_tokens
        self.message_max_new_tokens = message_max_new_tokens
        self.chain_of_thought_max_new_tokens = chain_of_thought_max_new_tokens

        self.conversation_history: list[dict[str, str]] = []
        self.observation_history: list[str] = []
        self.action_history: list[str] = []
        self._last_info: dict[str, Any] | None = None

    @property
    def model(self) -> Model:
        return LLM_MODEL_REGISTRY.resolve(self.model_key)

    def select_action(self, observation: Observation) -> tuple[Action_Selection, dict]:
        for attempt in range(self.MAX_ATTEMPTS):
            prompt = self._build_prompt(observation)
            reasoning = ""
            raw = ""
            try:
                if self.use_chain_of_thought:
                    reasoning = self.model.generate_text(
                        prompt,
                        self.action_generation_config,
                        max_new_tokens=self.chain_of_thought_max_new_tokens,
                    )
                    raw = self.model.generate_text(
                        f"{prompt}\n\nPrevious thoughts:\n{reasoning}\n\nNow provide your final action selection.",
                        self.action_generation_config,
                        max_new_tokens=self.action_max_new_tokens,
                    )
                else:
                    raw = self.model.generate_text(
                        prompt,
                        self.action_generation_config,
                        max_new_tokens=self.action_max_new_tokens,
                    )

                action_selection = self._parse_selection(raw, observation)
                action_choice_idx = self._action_choice_idx(action_selection, observation)
                self._record_observation(observation)
                info = {
                    "raw_response": raw,
                    "reasoning": reasoning,
                    "action_choice_idx": action_choice_idx,
                    "attempt": attempt + 1,
                }
                self._last_info = info
                return action_selection, info
            except Exception as e:
                prompt = self._retry_prompt(prompt, raw, str(e))
                continue

        raise RuntimeError(f"Failed to select a valid action after {self.MAX_ATTEMPTS} attempts.")

    def _action_choice_idx(self, action_selection: Action_Selection, observation: Observation) -> int | None:
        for idx, candidate in enumerate(observation.possible_actions):
            if candidate is action_selection:
                return idx
        return None

    def _build_prompt(self, observation: Observation) -> str:
        sections = [observation.observation_text, "\nPossible actions:"]
        for idx, action_selection in enumerate(observation.possible_actions):
            sections.append(f"[{idx}] {action_selection}")
        sections.append("\nRespond with the number of the action you choose in square brackets, e.g. [0].")
        if self.use_chain_of_thought:
            sections.append("\nFirst, think step by step about what to do.")
        return "\n".join(sections)

    def _parse_selection(self, raw: str, observation: Observation) -> Action_Selection:
        match = re.search(r"\[(\d+)\]", raw)
        if not match:
            raise ValueError(f"No action selection found in: {raw}")
        idx = int(match.group(1))
        if idx < 0 or idx >= len(observation.possible_actions):
            raise ValueError(f"Action index {idx} out of range (0-{len(observation.possible_actions) - 1})")
        return observation.possible_actions[idx]

    def _extract_json(self, text: str) -> dict:
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response.")
        return json.loads(match.group(0))

    def _retry_prompt(self, prompt: str, raw: str, error: str) -> str:
        return f"{prompt}\n\nPrevious invalid response: {raw}\nError: {error}\n\nPlease provide a valid response."

    def _record_observation(self, observation: Observation) -> None:
        self.observation_history.append(observation.observation_text)
        if len(self.observation_history) > self.observation_memory_window:
            self.observation_history = self.observation_history[-self.observation_memory_window:]

    def _record_last_selection(self, selection: Action_Selection, info: dict) -> None:
        self.action_history.append(str(selection))
        if len(self.action_history) > self.observation_memory_window:
            self.action_history = self.action_history[-self.observation_memory_window:]

    def _coerce_kwarg_value(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return json.dumps(value)

    def _with_system(self, prompt: str) -> list[dict[str, str]]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _trim_history(self) -> None:
        if len(self.conversation_history) > self.conversation_memory_window:
            self.conversation_history = self.conversation_history[-self.conversation_memory_window:]

    def start_conversation(self, participants: list[Entity], env: Environment, info: str | None = None) -> None:
        if info:
            self.conversation_history.append({"role": "system", "content": info})
            self._trim_history()

    def send_message(self, recipients: list[Entity], env: Environment, info: str | None = None) -> str:
        prompt = self._build_message_prompt(recipients, env, info)
        raw = self.model.generate_text(
            self._with_system(prompt),
            self.message_generation_config,
            max_new_tokens=self.message_max_new_tokens,
        )
        self.conversation_history.append({"role": "assistant", "content": raw})
        self._trim_history()
        return raw

    def _build_message_prompt(self, recipients: list[Entity], env: Environment, info: str | None = None) -> str:
        recipient_names = ", ".join(entity.name for entity in recipients)
        history = (
            "\n".join(entry["content"] for entry in self.conversation_history[-self.conversation_memory_window:])
            or "(no prior messages)"
        )
        info_text = f"\nContext: {info}\n" if info else ""
        return (
            f"You are {self.entity.name} in a conversation with {recipient_names}.\n"
            f"{info_text}"
            f"Recent conversation:\n{history}\n\n"
            f"Send a brief message."
        )

    def receive_message(self, message: str, sender: Entity, env: Environment) -> None:
        self.conversation_history.append(
            {"role": "user", "content": f"Message from {sender.name}: {message}"}
        )
        self._trim_history()

    def end_conversation(self, participants: list[Entity], env: Environment, info: str | None = None) -> None:
        if info:
            self.conversation_history.append({"role": "system", "content": info})
            self._trim_history()

    def _parse_action_kwargs(self, action_selection: Action_Selection, raw_kwargs: str) -> dict[str, Any] | None:
        if not raw_kwargs.strip():
            return None
        try:
            parsed = self._extract_json(raw_kwargs)
        except (json.JSONDecodeError, ValueError):
            return None
        if action_selection.required_kwargs is None:
            return None
        result: dict[str, Any] = {}
        for name, arg_type in action_selection.required_kwargs.items():
            if name in parsed:
                result[name] = arg_type.parse(str(parsed[name]))
        return result
