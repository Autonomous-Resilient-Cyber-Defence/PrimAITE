# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict

from primaite.interface.request import RequestFormat


class AbstractAction(BaseModel, ABC):
    """Base class for actions."""

    config: "AbstractAction.ConfigSchema"

    class ConfigSchema(BaseModel, ABC):
        """Base configuration schema for Actions."""

        model_config = ConfigDict(extra="forbid")
        type: str = ""

    _registry: ClassVar[Dict[str, Type[AbstractAction]]] = {}

    def __init_subclass__(cls, identifier: Optional[str] = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if identifier is None:
            return
        if identifier in cls._registry:
            raise ValueError(f"Cannot create new action under reserved name {identifier}")
        cls._registry[identifier] = cls

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        pass
