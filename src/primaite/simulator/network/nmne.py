# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from typing import List

from pydantic import BaseModel, ConfigDict


class NMNEConfig(BaseModel):
    """Store all the information to perform NMNE operations."""

    model_config = ConfigDict(extra="forbid")

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
