from enum import Enum

from primaite.simulator.network.protocols.packet import DataPacket


class HTTPRequestMethod(Enum):
    """Enum list of HTTP Request methods that can be handled by the simulation."""

    GET = "GET"
    """HTTP GET Method. Requests using GET should only retrieve data."""

    HEAD = "HEAD"
    """Asks for a response identical to a GET request, but without the response body."""

    POST = "POST"
    """Submit an entity to the specified resource, often causing a change in state or side effects on the server."""

    PUT = "PUT"
    """Replace all current representations of the target resource with the request payload."""

    DELETE = "DELETE"
    """Delete the specified resource."""

    PATCH = "PATCH"
    """Apply partial modifications to a resource."""


class HTTPStatusCode(Enum):
    """List of available HTTP Statuses."""

    OK = 200
    """request has succeeded."""

    BAD_REQUEST = 400
    """Payload cannot be parsed."""

    UNAUTHORIZED = 401
    """Auth required."""

    METHOD_NOT_ALLOWED = 405
    """Method is not supported by server."""

    INTERNAL_SERVER_ERROR = 500
    """Error on the server side."""


class HTTPRequestPacket(DataPacket):
    """Class that represents an HTTP Request Packet."""

    request_method: HTTPRequestMethod
    """The HTTP Request method."""

    request_url: str
    """URL of request."""


class HTTPResponsePacket(DataPacket):
    """Class that reprensents an HTTP Response Packet."""

    status_code: HTTPStatusCode = None
    """Status code of the HTTP response."""
