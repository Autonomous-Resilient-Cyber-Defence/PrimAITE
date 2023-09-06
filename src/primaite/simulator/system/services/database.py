import sqlite3
from ipaddress import IPv4Address
from sqlite3 import OperationalError
from typing import Dict, Optional, Any, List, Union

from prettytable import PrettyTable, MARKDOWN

from primaite.simulator.file_system.file_system import File
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.core.software_manager import SoftwareManager
from primaite.simulator.system.services.service import Service


class DatabaseService(Service):
    """A generic SQL Server Service."""
    backup_server: Optional[IPv4Address] = None
    "The IP Address of the server the "

    def __init__(self, **kwargs):
        kwargs["name"] = "Database"
        kwargs["port"] = Port.POSTGRES_SERVER
        kwargs["protocol"] = IPProtocol.TCP
        super().__init__(**kwargs)
        self._db_file: File
        self._create_db_file()
        self._conn = sqlite3.connect(self._db_file.sim_path)
        self._cursor = self._conn.cursor()

    def tables(self) -> List[str]:
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';"
        results = self._process_sql(sql)
        return [row[0] for row in results["data"]]

    def show(self, markdown: bool = False):
        """Prints a Table names in the Database."""
        table = PrettyTable(["Table"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.file_system.sys_log.hostname} Database"
        for row in self.tables():
            table.add_row([row])
        print(table)

    def _create_db_file(self):
        self._db_file: File = self.file_system.create_file(folder_name="database", file_name="database.db", real=True)
        self.folder = self._db_file.folder

    def _process_sql(self, query: str) -> Dict[str, Union[int, List[Any]]]:
        try:
            self._cursor.execute(query)
            self._conn.commit()
        except OperationalError:
            # Handle the case where the table does not exist.
            return {"status_code": 404, "data": []}

        return {"status_code": 200, "data": self._cursor.fetchall()}

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        return super().describe_state()

    def receive(self, payload: Any, session_id: str, **kwargs) -> bool:
        result = self._process_sql(payload)
        software_manager: SoftwareManager = self.software_manager
        software_manager.send_payload_to_session_manager(payload=result, session_id=session_id)

        return result["status_code"]

    def send(self, payload: Any, session_id: str, **kwargs) -> bool:
        pass
