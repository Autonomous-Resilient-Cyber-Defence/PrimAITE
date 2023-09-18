import sqlite3
from datetime import datetime
from sqlite3 import OperationalError
from typing import Any, Dict, List, Optional, Union

from prettytable import MARKDOWN, PrettyTable

from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service, ServiceOperatingState
from primaite.simulator.system.software import SoftwareHealthState


class DatabaseService(Service):
    """
    A class for simulating a generic SQL Server service.

    This class inherits from the `Service` class and provides methods to manage and query a SQLite database.
    """

    password: Optional[str] = None
    connections: Dict[str, datetime] = {}

    def __init__(self, **kwargs):
        kwargs["name"] = "DatabaseService"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self._db_file: File
        self._create_db_file()
        self._conn = sqlite3.connect(self._db_file.sim_path)
        self._cursor = self._conn.cursor()

    def tables(self) -> List[str]:
        """
        Get a list of table names present in the database.

        :return: List of table names.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';"
        results = self._process_sql(sql)
        return [row[0] for row in results["data"]]

    def show(self, markdown: bool = False):
        """
        Prints a list of table names in the database using PrettyTable.

        :param markdown: Whether to output the table in Markdown format.
        """
        table = PrettyTable(["Table"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.file_system.sys_log.hostname} Database"
        for row in self.tables():
            table.add_row([row])
        print(table)

    def _create_db_file(self):
        """Creates the Simulation File and sqlite file in the file system."""
        self._db_file: File = self.file_system.create_file(folder_name="database", file_name="database.db", real=True)
        self.folder = self._db_file.folder

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
                    self.sys_log.info(f"Connect request for {session_id=} authorised")
                else:
                    status_code = 401  # Unauthorised
                    self.sys_log.info(f"Connect request for {session_id=} declined")
        else:
            status_code = 404  # service not found
        return {"status_code": status_code, "type": "connect_response", "response": status_code == 200}

    def _process_sql(self, query: str, query_id: str) -> Dict[str, Union[int, List[Any]]]:
        """
        Executes the given SQL query and returns the result.

        :param query: The SQL query to be executed.
        :return: Dictionary containing status code and data fetched.
        """
        self.sys_log.info(f"{self.name}: Running {query}")
        try:
            self._cursor.execute(query)
            self._conn.commit()
        except OperationalError:
            # Handle the case where the table does not exist.
            self.sys_log.error(f"{self.name}: Error, query failed")
            return {"status_code": 404, "data": {}}
        data = []
        description = self._cursor.description
        if description:
            headers = []
            for header in description:
                headers.append(header[0])
            data = self._cursor.fetchall()
            if data and headers:
                data = {row[0]: {header: value for header, value in zip(headers, row)} for row in data}
        return {"status_code": 200, "type": "sql", "data": data, "uuid": query_id}

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
