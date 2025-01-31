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

    def __init_subclass__(cls, discriminator: Optional[str] = None, **kwargs: Any) -> None:
        """
        Register an action type.

        :param discriminator: discriminator used to uniquely specify action types.
        :type discriminator: str
        :raises ValueError: When attempting to create an action with a name that is already in use.
        """
        super().__init_subclass__(**kwargs)
        if discriminator is None:
            return
        if discriminator in cls._registry:
            raise ValueError(f"Cannot create new action under reserved name {discriminator}")
        cls._registry[discriminator] = cls

    @classmethod
    def form_request(cls, config: ConfigSchema) -> RequestFormat:
        """Return the action formatted as a request which can be ingested by the PrimAITE simulation."""
        pass
