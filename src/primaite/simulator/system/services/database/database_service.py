from datetime import datetime
from ipaddress import IPv4Address
from typing import Any, Dict, List, Literal, Optional, Union

from primaite import getLogger
from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.ftp.ftp_client import FTPClient
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState

_LOGGER = getLogger(__name__)


class DatabaseService(Service):
    """
    A class for simulating a generic SQL Server service.

    This class inherits from the `Service` class and provides methods to simulate a SQL database.
    """

    password: Optional[str] = None
    connections: Dict[str, datetime] = {}

    backup_server: IPv4Address = None
    """IP address of the backup server."""

    latest_backup_directory: str = None
    """Directory of latest backup."""

    latest_backup_file_name: str = None
    """File name of latest backup."""

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseService"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self._db_file: File
        self._create_db_file()

    def set_original_state(self):
        """Sets the original state."""
        _LOGGER.debug(f"Setting DatabaseService original state on node {self.software_manager.node.hostname}")
        super().set_original_state()
        vals_to_include = {
            "password",
            "connections",
            "backup_server",
            "latest_backup_directory",
            "latest_backup_file_name",
        }
        self._original_state.update(self.model_dump(include=vals_to_include))

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        _LOGGER.debug("Resetting DatabaseService original state on node {self.software_manager.node.hostname}")
        self.connections.clear()
        super().reset_component_for_episode(episode)

    def configure_backup(self, backup_server: IPv4Address):
        """
        Set up the database backup.

        :param: backup_server_ip: The IP address of the backup server
        """
        self.backup_server = backup_server

    def backup_database(self) -> bool:
        """Create a backup of the database to the configured backup server."""
        # check if this action can be performed
        if not self._can_perform_action():
            return False

        # check if the backup server was configured
        if self.backup_server is None:
            self.sys_log.error(f"{self.name} - {self.sys_log.hostname}: not configured.")
            return False

        software_manager: SoftwareManager = self.software_manager
        ftp_client_service: FTPClient = software_manager.software["FTPClient"]

        # send backup copy of database file to FTP server
        response = ftp_client_service.send_file(
            dest_ip_address=self.backup_server,
            src_file_name=self._db_file.name,
            src_folder_name=self.folder.name,
            dest_folder_name=str(self.uuid),
            dest_file_name="database.db",
        )

        if response:
            return True

        self.sys_log.error("Unable to create database backup.")
        return False

    def restore_backup(self) -> bool:
        """Restore a backup from backup server."""
        # check if this action can be performed
        if not self._can_perform_action():
            return False

        software_manager: SoftwareManager = self.software_manager
        ftp_client_service: FTPClient = software_manager.software["FTPClient"]

        # retrieve backup file from backup server
        response = ftp_client_service.request_file(
            src_folder_name=str(self.uuid),
            src_file_name="database.db",
            dest_folder_name="downloads",
            dest_file_name="database.db",
            dest_ip_address=self.backup_server,
        )

        if not response:
            self.sys_log.error("Unable to restore database backup.")
            return False

        # replace db file
        self.file_system.delete_file(folder_name=self.folder.name, file_name="downloads.db")
        self.file_system.copy_file(
            src_folder_name="downloads", src_file_name="database.db", dst_folder_name=self.folder.name
        )
        self._db_file = self.file_system.get_file(folder_name=self.folder.name, file_name="database.db")

        if self._db_file is None:
            self.sys_log.error("Copying database backup failed.")
            return False

        self.set_health_state(SoftwareHealthState.GOOD)

        return True

    def _create_db_file(self):
        """Creates the Simulation File and sqlite file in the file system."""
        self._db_file: File = self.file_system.create_file(folder_name="database", file_name="database.db")
        self.folder = self.file_system.get_folder_by_id(self._db_file.folder_id)

    def _process_connect(
        self, session_id: str, password: Optional[str] = None
    ) -> Dict[str, Union[int, Dict[str, bool]]]:
        status_code = 500  # Default internal server error
        if self.operating_state == ServiceOperatingState.RUNNING:
            status_code = 503  # service unavailable
            if self.health_state_actual == SoftwareHealthState.GOOD:
                if self.password == password:
                    status_code = 200  # ok
                    self.connections[session_id] = datetime.now()
                    self.sys_log.info(f"{self.name}: Connect request for {session_id=} authorised")
                else:
                    status_code = 401  # Unauthorised
                    self.sys_log.info(f"{self.name}: Connect request for {session_id=} declined")
        else:
            status_code = 404  # service not found
        return {"status_code": status_code, "type": "connect_response", "response": status_code == 200}

    def _process_sql(self, query: Literal["SELECT", "DELETE"], query_id: str) -> Dict[str, Union[int, List[Any]]]:
        """
        Executes the given SQL query and returns the result.

        Possible queries:
        - SELECT : returns the data
        - DELETE : deletes the data

        :param query: The SQL query to be executed.
        :return: Dictionary containing status code and data fetched.
        """
        self.sys_log.info(f"{self.name}: Running {query}")
        if query == "SELECT":
            if self.health_state_actual == SoftwareHealthState.GOOD:
                return {"status_code": 200, "type": "sql", "data": True, "uuid": query_id}
            else:
                return {"status_code": 404, "data": False}
        elif query == "DELETE":
            if self.health_state_actual == SoftwareHealthState.GOOD:
                self.health_state_actual = SoftwareHealthState.COMPROMISED
                return {"status_code": 200, "type": "sql", "data": False, "uuid": query_id}
            else:
                return {"status_code": 404, "data": False}
        else:
            # Invalid query
            return {"status_code": 500, "data": False}

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        return super().describe_state()

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Processes the incoming SQL payload and sends the result back.

        :param payload: The SQL query to be executed.
        :param session_id: The session identifier.
        :return: True if the Status Code is 200, otherwise False.
        """
        if not super().receive(payload=payload, session_id=session_id, **kwargs):
            return False

        result = {"status_code": 500, "data": []}
        if isinstance(payload, dict) and payload.get("type"):
            if payload["type"] == "connect_request":
                result = self._process_connect(session_id=session_id, password=payload.get("password"))
            elif payload["type"] == "disconnect":
                if session_id in self.connections:
                    self.connections.pop(session_id)
            elif payload["type"] == "sql":
                if session_id in self.connections:
                    result = self._process_sql(query=payload["sql"], query_id=payload["uuid"])
                else:
                    result = {"status_code": 401, "type": "sql"}
        self.send(payload=result, session_id=session_id)
        return True

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        """
        Send a SQL response back down to the SessionManager.

        :param payload: The SQL query results.
        :param session_id: The session identifier.
        :return: True if the Status Code is 200, otherwise False.
        """
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(payload=payload, session_id=session_id)

        return payload["status_code"] == 200
