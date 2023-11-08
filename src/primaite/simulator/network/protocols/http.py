from enum import Enum

from src.primaite.simulator.network.protocols.packet import DataPacket


class HttpRequestMethod(Enum):
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


class HttpStatusCode(Enum):
    """List of available HTTP Statuses."""

    OK = 200
    """request has succeeded."""

    BAD_REQUEST = 400
    """Payload cannot be parsed."""

    UNAUTHORIZED = 401
    """Auth required."""

    NOT_FOUND = 404
    """Item not found in server."""

    METHOD_NOT_ALLOWED = 405
    """Method is not supported by server."""

    INTERNAL_SERVER_ERROR = 500
    """Error on the server side."""


class HttpRequestPacket(DataPacket):
    """Class that represents an HTTP Request Packet."""

    request_method: HttpRequestMethod
    """The HTTP Request method."""

    request_url: str
    """URL of request."""


class HttpResponsePacket(DataPacket):
    """Class that reprensents an HTTP Response Packet."""

    status_code: HttpStatusCode = None
    """Status code of the HTTP response."""
