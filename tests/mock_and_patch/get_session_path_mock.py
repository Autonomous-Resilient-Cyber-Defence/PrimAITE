# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from primaite import getLogger

_LOGGER = getLogger(__name__)


def temp_user_sessions_path() -> Path:
    """
    Get a temp directory session path the test session will output to.

    :param session_timestamp: This is the datetime that the session started.
    :return: The session directory path.
    """
    session_path = Path(tempfile.gettempdir()) / "primaite" / str(uuid4())
    session_path.mkdir(exist_ok=True, parents=True)
    _LOGGER.debug(f"Created temp session directory: {session_path}")
    return session_path
