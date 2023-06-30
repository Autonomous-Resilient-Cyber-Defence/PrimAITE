import tempfile
from datetime import datetime
from pathlib import Path

from primaite import getLogger

_LOGGER = getLogger(__name__)


def get_temp_session_path(session_timestamp: datetime) -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    session_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    session_path = (
        Path(tempfile.gettempdir()) / "primaite" / date_dir / session_path
    )
    session_path.mkdir(exist_ok=True, parents=True)
    _LOGGER.debug(f"Created temp session directory: {session_path}")
    return session_path
