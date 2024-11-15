# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Dict, Type

from pydantic import BaseModel, ConfigDict

from primaite.interface.request import RequestFormat

class AbstractAction(BaseModel):
    """Base class for actions."""

    class ConfigSchema(BaseModel, ABC):
        """Base configuration schema for Actions."""

        model_config = ConfigDict(extra="forbid")
        type: str

    _registry: ClassVar[Dict[str, Type[AbstractAction]]] = {}

    def __init_subclass__(cls, identifier: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if identifier in cls._registry:
            raise ValueError(f"Cannot create new action under reserved name {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        pass

    @classmethod
    def from_config(cls, config: Dict) -> "AbstractAction":
        """Create an action component from a config dictionary."""
        for attribute, value in config.items():
            setattr(cls.ConfigSchema, attribute, value)
        return cls
