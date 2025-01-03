# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from ipaddress import IPv4Address
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import Field

from primaite.interface.request import RequestFormat, RequestResponse
from primaite.simulator.core import RequestManager, RequestType
from primaite.simulator.system.applications.application import Application
from primaite.simulator.system.applications.database_client import DatabaseClient, DatabaseClientConnection
from primaite.utils.validation.ip_protocol import PROTOCOL_LOOKUP
from primaite.utils.validation.port import PORT_LOOKUP


class RansomwareScript(Application, identifier="RansomwareScript"):
    """Ransomware Kill Chain - Designed to be used by the TAP001 Agent on the example layout Network.

    :ivar payload: The attack stage query payload. (Default ENCRYPT)
    """

    class ConfigSchema(Application.ConfigSchema):
        """ConfigSchema for RansomwareScript."""

        type: str = "RansomwareScript"

    config: "RansomwareScript.ConfigSchema" = Field(default_factory=lambda: RansomwareScript.ConfigSchema())

    server_ip_address: Optional[IPv4Address] = None
    """IP address of node which hosts the database."""
    server_password: Optional[str] = None
    """Password required to access the database."""
    payload: Optional[str] = "ENCRYPT"
    "Payload String for the payload stage"

    def __init__(self, **kwargs):
        kwargs["name"] = "RansomwareScript"
        kwargs["port"] = PORT_LOOKUP["NONE"]
        kwargs["protocol"] = PROTOCOL_LOOKUP["NONE"]

        super().__init__(**kwargs)
        self._db_connection: Optional[DatabaseClientConnection] = None

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        return state

    @property
    def _host_db_client(self) -> DatabaseClient:
        """Return the database client that is installed on the same machine as the Ransomware Script."""
        db_client: DatabaseClient = self.software_manager.software.get("DatabaseClient")
        if db_client is None:
            self.sys_log.warning(f"{self.__class__.__name__} cannot find a database client on its host.")
        return db_client

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        rm.add_request(
            name="execute",
            request_type=RequestType(func=lambda request, context: RequestResponse.from_bool(self.attack())),
        )

        def _configure(request: RequestFormat, context: Dict) -> RequestResponse:
            """
            Request for configuring the target database and payload.

            :param request: Request with one element contianing a dict of parameters for the configure method.
            :type request: RequestFormat
            :param context: additional context for resolving this action, currently unused
            :type context: dict
            :return: RequestResponse object with a success code reflecting whether the configuration could be applied.
            :rtype: RequestResponse
            """
            ip = request[-1].get("server_ip_address")
            ip = None if ip is None else IPv4Address(ip)
            pw = request[-1].get("server_password")
            payload = request[-1].get("payload")
            return RequestResponse.from_bool(self.configure(ip, pw, payload))

        rm.add_request("configure", request_type=RequestType(func=_configure))
        return rm

    def run(self) -> bool:
        """Calls the parent classes execute method before starting the application loop."""
        super().run()
        return True

    def _application_loop(self) -> bool:
        """
        The main application loop of the script, handling the attack process.

        This is the core loop where the bot sequentially goes through the stages of the attack.
        """
        if not self._can_perform_action():
            return False
        if self.server_ip_address and self.payload:
            self.sys_log.info(f"{self.name}: Running")
            if self._perform_ransomware_encrypt():
                return True
            return False
        else:
            self.sys_log.warning(f"{self.name}: Failed to start as it requires both a target_ip_address and payload.")
            return False

    def configure(
        self,
        server_ip_address: Optional[IPv4Address] = None,
        server_password: Optional[str] = None,
        payload: Optional[str] = None,
    ) -> bool:
        """
        Configure the Ransomware Script to communicate with a DatabaseService.

        :param server_ip_address: The IP address of the Node the DatabaseService is on.
        :param server_password: The password on the DatabaseService.
        :param payload: The attack stage query (Encrypt / Delete)
        """
        if server_ip_address:
            self.server_ip_address = server_ip_address
        if server_password:
            self.server_password = server_password
        if payload:
            self.payload = payload
        self.sys_log.info(
            f"{self.name}: Configured the {self.name} with {server_ip_address=}, {payload=}, {server_password=}."
        )
        return True

    def attack(self) -> bool:
        """Perform the attack steps after opening the application."""
        self.run()
        if not self._can_perform_action():
            self.sys_log.warning("Ransomware application is unable to perform it's actions.")
        self.num_executions += 1
        return self._application_loop()

    def _establish_db_connection(self) -> bool:
        """Establish a db connection to the Database Server."""
        self._db_connection = self._host_db_client.get_new_connection()
        return True if self._db_connection else False

    def _perform_ransomware_encrypt(self) -> bool:
        """
        Execute the Ransomware Encrypt payload on the target.

        Advances the attack stage to `COMPLETE` if successful, or 'FAILED' if unsuccessful.
        """
        if self._host_db_client is None:
            self.sys_log.info(f"{self.name}: Failed to connect to db_client - Ransomware Script")
            return False

        self._host_db_client.server_ip_address = self.server_ip_address
        self._host_db_client.server_password = self.server_password
        self.sys_log.info(f"{self.name}: Attempting to launch payload")
        if not self._db_connection:
            self._establish_db_connection()
        if self._db_connection:
            attack_successful = self._db_connection.query(self.payload)
            self.sys_log.info(f"{self.name} Payload delivered: {self.payload}")
            if attack_successful:
                self.sys_log.info(f"{self.name}: Payload Successful")
                return True
            else:
                self.sys_log.info(f"{self.name}: Payload failed")
            return False
        else:
            self.sys_log.warning("Attack Attempted to launch too quickly")
            return False

    def show(self, markdown: bool = False):
        """
        Prints a table of the current status of the Ransomware Script.

        Displays the current values of the following Ransomware Attributes:

        ``server_ip_address`:
        The IP of the target database.

        ``payload``:
        The payload (type of attack) to be sent to the database.

        :param markdown: If True, outputs the table in markdown format. Default is False.
        """
        table = PrettyTable(["Target Server IP Address", "Payload"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.name} Running Status"
        table.add_row([self.server_ip_address, self.payload])
        print(table)
