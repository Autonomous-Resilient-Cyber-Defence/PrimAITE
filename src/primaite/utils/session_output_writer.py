import csv
from logging import Logger
from typing import List, Final, IO, Union, Tuple
from typing import TYPE_CHECKING

from primaite import getLogger
from primaite.transactions.transaction import Transaction

if TYPE_CHECKING:
    from primaite.environment.primaite_env import Primaite

_LOGGER: Logger = getLogger(__name__)


class SessionOutputWriter:
    _AV_REWARD_PER_EPISODE_HEADER: Final[List[str]] = [
        "Episode", "Average Reward"
    ]

    def __init__(
            self,
            env: "Primaite",
            transaction_writer: bool = False,
            learning_session: bool = True
    ):
        self._env = env
        self.transaction_writer = transaction_writer
        self.learning_session = learning_session

        if self.transaction_writer:
            fn = f"all_transactions_{self._env.timestamp_str}.csv"
        else:
            fn = f"average_reward_per_episode_{self._env.timestamp_str}.csv"

        if self.learning_session:
            self._csv_file_path = self._env.session_path / "learning" / fn
        else:
            self._csv_file_path = self._env.session_path / "evaluation" / fn

        self._csv_file_path.parent.mkdir(exist_ok=True, parents=True)

        self._csv_file = None
        self._csv_writer = None

        self._first_write: bool = True

    def _init_csv_writer(self):
        self._csv_file = open(
            self._csv_file_path, "w", encoding="UTF8", newline=""
        )

        self._csv_writer = csv.writer(self._csv_file)

    def __del__(self):
        if self._csv_file:
            self._csv_file.close()
            _LOGGER.info(f"Finished writing file: {self._csv_file_path}")

    def write(
            self,
            data: Union[Tuple, Transaction]
    ):
        if isinstance(data, Transaction):
            header, data = data.as_csv_data()
        else:
            header = self._AV_REWARD_PER_EPISODE_HEADER

        if self._first_write:
            self._init_csv_writer()
            self._csv_writer.writerow(header)
            self._first_write = False

        self._csv_writer.writerow(data)
