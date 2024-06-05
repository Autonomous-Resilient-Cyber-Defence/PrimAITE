# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict, ForwardRef, List, Literal, Union

from pydantic import BaseModel, ConfigDict, StrictBool, validate_call

RequestFormat = List[Union[str, int, float]]

RequestResponse = ForwardRef("RequestResponse")
"""This makes it possible to type-hint RequestResponse.from_bool return type."""


class RequestResponse(BaseModel):
    """Schema for generic request responses."""

    model_config = ConfigDict(extra="forbid", strict=True)
    """Cannot have extra fields in the response. Anything custom goes into the data field."""

    status: Literal["pending", "success", "failure", "unreachable"] = "pending"
    """
    What is the current status of the request:
        - pending - the request has not been received yet, or it has been received but it's still being processed.
        - success - the request has been received and executed successfully.
        - failure - the request has been received and attempted, but execution failed.
        - unreachable - the request could not reach it's intended target, either because it doesn't exist or the target
                        is off.
    """

    data: Dict = {}
    """Catch-all place to provide any additional data that was generated as a response to the request."""
    # TODO: currently, status and data have default values, because I don't want to interrupt existing functionality too
    # much. However, in the future we might consider making them mandatory.

    @classmethod
    @validate_call
    def from_bool(cls, status_bool: StrictBool) -> RequestResponse:
        """
        Construct a basic request response from a boolean.

        True maps to a success status. False maps to a failure status.

        :param status_bool: Whether to create a successful response
        :type status_bool: bool
        """
        if status_bool is True:
            return cls(status="success", data={})
        elif status_bool is False:
            return cls(status="failure", data={})
