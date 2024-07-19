# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from pydantic import BaseModel
from typing import Dict, List


class NMNEConfig(BaseModel):
    """Store all the information to perform NMNE operations."""

    capture_nmne: bool = False
    """Indicates whether Malicious Network Events (MNEs) should be captured."""
    nmne_capture_keywords: List[str] = []
    """List of keywords to identify malicious network events."""
    capture_by_direction: bool = True
    """Captures should be organized by traffic direction (inbound/outbound)."""
    capture_by_ip_address: bool = False
    """Captures should be organized by source or destination IP address."""
    capture_by_protocol: bool = False
    """Captures should be organized by network protocol (e.g., TCP, UDP)."""
    capture_by_port: bool = False
    """Captures should be organized by source or destination port."""
    capture_by_keyword: bool = False
    """Captures should be filtered and categorised based on specific keywords."""


def store_nmne_config(nmne_config: Dict) -> NMNEConfig:
    """
    Store configuration for capturing Malicious Network Events (MNEs).

    This function updates global settings related to NMNE capture, including whether to capture
    NMNEs and what keywords to use for identifying NMNEs.

    The function ensures that the settings are updated only if they are provided in the
    `nmne_config` dictionary, and maintains type integrity by checking the types of the provided
    values.

    :param nmne_config: A dictionary containing the NMNE configuration settings. Possible keys
    include:
        "capture_nmne" (bool) to indicate whether NMNEs should be captured;
        "nmne_capture_keywords" (list of strings) to specify keywords for NMNE identification.
    :rvar dataclass with data read from config file.
    """
    nmne_capture_keywords: List[str] = []
    # Update the NMNE capture flag, defaulting to False if not specified or if the type is incorrect
    capture_nmne = nmne_config.get("capture_nmne", False)

    # Update the NMNE capture keywords, appending new keywords if provided
    nmne_capture_keywords += nmne_config.get("nmne_capture_keywords", [])

    return NMNEConfig(capture_nmne=capture_nmne, nmne_capture_keywords=nmne_capture_keywords)
