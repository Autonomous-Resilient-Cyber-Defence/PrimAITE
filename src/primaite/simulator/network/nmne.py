from typing import Dict, Final, List

CAPTURE_NMNE: bool = True
"""Indicates whether Malicious Network Events (MNEs) should be captured. Default is True."""

NMNE_CAPTURE_KEYWORDS: List[str] = []
"""List of keywords to identify malicious network events."""

# TODO: Remove final and make configurable after example layout when the NicObservation creates nmne structure dynamically
CAPTURE_BY_DIRECTION: Final[bool] = True
"""Flag to determine if captures should be organized by traffic direction (inbound/outbound)."""
CAPTURE_BY_IP_ADDRESS: Final[bool] = False
"""Flag to determine if captures should be organized by source or destination IP address."""
CAPTURE_BY_PROTOCOL: Final[bool] = False
"""Flag to determine if captures should be organized by network protocol (e.g., TCP, UDP)."""
CAPTURE_BY_PORT: Final[bool] = False
"""Flag to determine if captures should be organized by source or destination port."""
CAPTURE_BY_KEYWORD: Final[bool] = False
"""Flag to determine if captures should be filtered and categorised based on specific keywords."""


def set_nmne_config(nmne_config: Dict):
    """
    Sets the configuration for capturing Malicious Network Events (MNEs) based on a provided dictionary.

    This function updates global settings related to NMNE capture, including whether to capture NMNEs and what
    keywords to use for identifying NMNEs.

    The function ensures that the settings are updated only if they are provided in the `nmne_config` dictionary,
    and maintains type integrity by checking the types of the provided values.

    :param nmne_config: A dictionary containing the NMNE configuration settings. Possible keys include:
        "capture_nmne" (bool) to indicate whether NMNEs should be captured, "nmne_capture_keywords" (list of strings)
        to specify keywords for NMNE identification.
    """
    global NMNE_CAPTURE_KEYWORDS
    global CAPTURE_NMNE

    # Update the NMNE capture flag, defaulting to False if not specified or if the type is incorrect
    CAPTURE_NMNE = nmne_config.get("capture_nmne", False)
    if not isinstance(CAPTURE_NMNE, bool):
        CAPTURE_NMNE = True  # Revert to default True if the provided value is not a boolean

    # Update the NMNE capture keywords, appending new keywords if provided
    NMNE_CAPTURE_KEYWORDS += nmne_config.get("nmne_capture_keywords", [])
    if not isinstance(NMNE_CAPTURE_KEYWORDS, list):
        NMNE_CAPTURE_KEYWORDS = []  # Reset to empty list if the provided value is not a list
