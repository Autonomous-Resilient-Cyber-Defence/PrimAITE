# flake8: noqa
"""Core of the PrimAITE Simulator."""
from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from primaite import getLogger

_LOGGER = getLogger(__name__)


class RequestPermissionValidator(BaseModel):
    """
    Base class for request validators.

    The permissions manager is designed to be generic. So, although in the first instance the permissions
    are evaluated purely on membership to AccountGroup, this class can support validating permissions based on any
    arbitrary criteria.
    """

    @abstractmethod
    def __call__(self, request: List[str], context: Dict) -> bool:
        """Use the request and context paramters to decide whether the request should be permitted."""
        pass


class AllowAllValidator(RequestPermissionValidator):
    """Always allows the request."""

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Always allow the request."""
        return True


class RequestType(BaseModel):
    """
    This object stores data related to a single request type.

    This includes the callable that can execute the request, and the validator that will decide whether
    the request can be performed or not.
    """

    func: Callable[[List[str], Dict], None]
    """
    ``func`` is a function that accepts a request and a context dict. Typically this would be a lambda function
    that invokes a class method of your SimComponent. For example if the component is a node and the request type is for
    turning it off, then the SimComponent should have a turn_off(self) method that does not need to accept any args.
    Then, this request will be given something like ``func = lambda request, context: self.turn_off()``.

    ``func`` can also be another request manager, since RequestManager is a callable with a signature that matches what is
    expected by ``func``.
    """
    validator: RequestPermissionValidator = AllowAllValidator()
    """
    ``validator`` is an instance of ``RequestPermissionValidator``. This is essentially a callable that
    accepts `request` and `context` and returns a boolean to represent whether the permission is granted to perform
    the request. The default validator will allow
    """


class RequestManager(BaseModel):
    """
    RequestManager is used by `SimComponent` instances to keep track of requests.

    Its main purpose is to be a lookup from request name to request function and corresponding validation function. This
    class is responsible for providing a consistent API for processing requests as well as helpful error messages.
    """

    request_types: Dict[str, RequestType] = {}
    """maps request name to an RequestType object."""

    def __call__(self, request: Callable[[List[str], Dict], None], context: Dict) -> None:
        """
        Process an request request.

        :param request: A list of strings describing the request. The first string must be one of the allowed
            request names, i.e. it must be a key of self.request_types. The subsequent strings in the list are passed as
            parameters to the request function.
        :type request: List[str]
        :param context: Dictionary of additional information necessary to process or validate the request.
        :type context: Dict
        :raises RuntimeError: If the request parameter does not have a valid request name as the first item.
        """
        request_key = request[0]

        if request_key not in self.request_types:
            msg = (
                f"Request {request} could not be processed because {request_key} is not a valid request name",
                "within this RequestManager",
            )
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        request_type = self.request_types[request_key]
        request_options = request[1:]

        if not request_type.validator(request_options, context):
            _LOGGER.debug(f"Request {request} was denied due to insufficient permissions")
            return

        request_type.func(request_options, context)

    def add_request(self, name: str, request_type: RequestType) -> None:
        """
        Add a request type to this request manager.

        :param name: The string associated to this request.
        :type name: str
        :param request_type: Request type object which contains information about how to resolve request.
        :type request_type: RequestType
        """
        if name in self.request_types:
            msg = f"Attempted to register a request but the request name {name} is already taken."
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        self.request_types[name] = request_type

    def remove_request(self, name: str) -> None:
        """
        Remove a request from this manager.

        :param name: name identifier of the request
        :type name: str
        """
        if name not in self.request_types:
            msg = f"Attempted to remove request {name} from request manager, but it was not registered."
            _LOGGER.error(msg)
            raise RuntimeError(msg)

        self.request_types.pop(name)

    def get_request_types_recursively(self) -> List[List[str]]:
        """Recursively generate request tree for this component."""
        requests = []
        for req_name, req in self.request_types.items():
            if isinstance(req.func, RequestManager):
                sub_requests = req.func.get_request_types_recursively()
                sub_requests = [[req_name] + a for a in sub_requests]
                requests.extend(sub_requests)
            else:
                requests.append([req_name])
        return requests


class SimComponent(BaseModel):
    """Extension of pydantic BaseModel with additional methods that must be defined by all classes in the simulator."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
    """Configure pydantic to allow arbitrary types and to let the instance have attributes not present in model."""

    uuid: str
    """The component UUID."""

    def __init__(self, **kwargs):
        if not kwargs.get("uuid"):
            kwargs["uuid"] = str(uuid4())
        super().__init__(**kwargs)
        self._request_manager: RequestManager = self._init_request_manager()
        self._parent: Optional["SimComponent"] = None

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager for this component.

        When using a hierarchy of components, the child classes should call the parent class's _init_request_manager and
        add additional requests on top of the existing generic ones.

        Example usage for inherited classes:

        ..code::python

            class WebBrowser(Application):
            def _init_request_manager(self) -> RequestManager:
                am = super()._init_request_manager() # all requests generic to any Application get initialised
                am.add_request(...) # initialise any requests specific to the web browser
                return am

        :return: Request manager object belonging to this sim component.
        :rtype: RequestManager
        """
        return RequestManager()

    @abstractmethod
    def describe_state(self) -> Dict:
        """
        Return a dictionary describing the state of this object and any objects managed by it.

        This is similar to pydantic ``model_dump()``, but it only outputs information about the objects owned by this
        object. If there are objects referenced by this object that are owned by something else, it is not included in
        this output.
        """
        state = {
            "uuid": self.uuid,
        }
        return state

    def scan(self) -> None:
        """Update the visible statuses of the SimComponent."""
        pass

    def apply_request(self, request: List[str], context: Dict = {}) -> None:
        """
        Apply a request to a simulation component. Request data is passed in as a 'namespaced' list of strings.

        If the list only has one element, the request is intended to be applied directly to this object. If the list has
        multiple entries, the request is passed to the child of this object specified by the first one or two entries.
        This is essentially a namespace.

        For example, ["turn_on",] is meant to apply a request of 'turn on' to this component.

        However, ["services", "email_client", "turn_on"] is meant to 'turn on' this component's email client service.

        :param request: List describing the request to apply to this object.
        :type request: List[str]

        :param: context: Dict containing context for requests
        :type context: Dict
        """
        if self._request_manager is None:
            return
        self._request_manager(request, context)

    def apply_timestep(self, timestep: int) -> None:
        """
        Apply a timestep evolution to this component.

        Override this method with anything that happens automatically in the component such as scheduled restarts or
        sending data.
        """
        pass

    def reset_component_for_episode(self, episode: int):
        """
        Reset this component to its original state for a new episode.

        Override this method with anything that needs to happen within the component for it to be reset.
        """
        pass

    @property
    def parent(self) -> "SimComponent":
        """Reference to the parent object which manages this object.

        :return: Parent object.
        :rtype: SimComponent
        """
        return self._parent

    @parent.setter
    def parent(self, new_parent: Union["SimComponent", None]) -> None:
        if self._parent and new_parent:
            msg = f"Overwriting parent of {self.uuid}. Old parent: {self._parent.uuid}, New parent: {new_parent.uuid}"
            _LOGGER.warn(msg)
            raise RuntimeWarning(msg)
        self._parent = new_parent
