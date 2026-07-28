from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from word_play.core import Environment


@dataclass
class Human_Text_Request:
    observation_text: str
    initial_text: str = ""
    prompt: str = "> "

    def prompt_text(self) -> str:
        return self.prompt


class Human_IO(ABC):
    @abstractmethod
    def notify(self, text: str, *, env: "Environment" | None = None) -> None:
        pass

    @abstractmethod
    def request_text(
        self,
        request: Human_Text_Request,
        *,
        env: "Environment" | None = None,
    ) -> str:
        pass


class Terminal_Human_IO(Human_IO):
    def notify(self, text: str, *, env: "Environment" | None = None) -> None:
        del env
        if text:
            print(text)

    def request_text(
        self,
        request: Human_Text_Request,
        *,
        env: "Environment" | None = None,
    ) -> str:
        del env
        observation_text = request.observation_text.strip()
        if observation_text:
            print(observation_text)
        return input(request.prompt_text())
