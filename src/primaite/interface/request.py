from typing import Dict, Literal

from pydantic import BaseModel, ConfigDict


class RequestResponse(BaseModel):
    """Schema for generic request responses."""

    model_config = ConfigDict(extra="forbid")
    """Cannot have extra fields in the response. Anything custom goes into the data field."""

    status: Literal["pending", "success", "failure"] = "pending"
    """
    What is the current status of the request:
        - pending - the request has not been received yet, or it has been received but it's still being processed.
        - success - the request has successfully been received and processed.
        - failure - the request could not reach it's intended target or it was rejected.

        Note that the failure status should only be used when the request cannot be processed, for instance when the
        target SimComponent doesn't exist, or is in an OFF state that prevents it from accepting requests. If the
        request is received by the target and the associated action is executed, but couldn't be completed due to
        downstream factors, the request was still successfully received, it's just that the result wasn't what was
        intended.
    """

    data: Dict = {}
    """Catch-all place to provide any additional data that was generated as a response to the request."""
    # TODO: currently, status and data have default values, because I don't want to interrupt existing functionality too
    # much. However, in the future we might consider making them mandatory.
