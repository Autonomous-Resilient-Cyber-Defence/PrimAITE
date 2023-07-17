# Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.
import csv
from logging import Logger
from typing import Final, List, Tuple, TYPE_CHECKING, Union

from primaite import getLogger
from primaite.transactions.transaction import Transaction

if TYPE_CHECKING:
    from primaite.environment.primaite_env import Primaite

_LOGGER: Logger = getLogger(__name__)


class SessionOutputWriter:
    """
    A session output writer class.

    Is used to write session outputs to csv file.
    """

    _AV_REWARD_PER_EPISODE_HEADER: Final[List[str]] = [
        "Episode",
        "Average Reward",
    ]

    def __init__(
        self,
        env: "Primaite",
        transaction_writer: bool = False,
        learning_session: bool = True,
    ):
        """
        Initialise the Session Output Writer.

        :param env: PrimAITE gym environment.
        :type env: Primaite
        :param transaction_writer: If `true`, this will output a full account of every transaction taken by the agent.
            If `false` it will output the average reward per episode, defaults to False
        :type transaction_writer: bool, optional
        :param learning_session: Set to `true` to indicate that the current session is a training session. This
            determines the name of the folder which contains the final output csv. Defaults to True
        :type learning_session: bool, optional
        """
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
        self._csv_file = open(self._csv_file_path, "w", encoding="UTF8", newline="")

        self._csv_writer = csv.writer(self._csv_file)

    def __del__(self):
        self.close()

    def close(self):
        """Close the cvs file."""
        if self._csv_file:
            self._csv_file.close()
            _LOGGER.debug(f"Finished writing file: {self._csv_file_path}")

    def write(self, data: Union[Tuple, Transaction]):
        """
        Write a row of session data.

        :param data: The row of data to write. Can be a Tuple or an instance of Transaction.
        """
        if isinstance(data, Transaction):
            header, data = data.as_csv_data()
        else:
            header = self._AV_REWARD_PER_EPISODE_HEADER

        if self._first_write:
            self._init_csv_writer()
            self._csv_writer.writerow(header)
            self._first_write = False
        self._csv_writer.writerow(data)
