from __future__ import annotations

from typing import Any

from word_play.presets.models.model import Model


class Model_Registry:
    def __init__(self) -> None:
        self._specs: dict[str, tuple[type[Model], dict[str, Any]]] = {}
        self._instances: dict[str, Model] = {}

    def register(self, key: str, model_class: type[Model], **kwargs: Any) -> None:
        if key in self._instances:
            raise ValueError(
                f"Model '{key}' is already loaded. Call unload('{key}') before re-registering."
            )
        self._specs[key] = (model_class, kwargs)

    def resolve(self, key: str) -> Model:
        if key not in self._instances:
            if key not in self._specs:
                raise KeyError(
                    f"No model registered under '{key}'. "
                    f"Registered keys: {list(self._specs)}"
                )
            model_class, kwargs = self._specs[key]
            self._instances[key] = model_class(**kwargs)
        return self._instances[key]

    def unload(self, key: str) -> None:
        self._instances.pop(key, None)

    def __contains__(self, key: str) -> bool:
        return key in self._specs


LLM_MODEL_REGISTRY = Model_Registry()


def register_model(key: str, model_class: type[Model], **kwargs: Any) -> None:
    LLM_MODEL_REGISTRY.register(key, model_class, **kwargs)


def resolve_registered_model(key: str) -> Model:
    return LLM_MODEL_REGISTRY.resolve(key)
