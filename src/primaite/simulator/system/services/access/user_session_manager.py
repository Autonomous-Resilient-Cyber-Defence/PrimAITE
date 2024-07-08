# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.access.user_manager import User, UserManager
from primaite.simulator.system.services.service import Service
from primaite.utils.validators import IPV4Address


class UserSession(SimComponent):
    user: User
    start_step: int
    last_active_step: int
    end_step: Optional[int] = None
    local: bool = True

    @classmethod
    def create(cls, user: User, timestep: int) -> UserSession:
        return UserSession(user=user, start_step=timestep, last_active_step=timestep)
    def describe_state(self) -> Dict:
        return self.model_dump()


class RemoteUserSession(UserSession):
    remote_ip_address: IPV4Address
    local: bool = False

    def describe_state(self) -> Dict:
        state = super().describe_state()
        state["remote_ip_address"] = str(self.remote_ip_address)
        return state


class UserSessionManager(BaseModel):
    node:
    local_session: Optional[UserSession] = None
    remote_sessions: Dict[str, RemoteUserSession] = Field(default_factory=dict)
    historic_sessions: List[UserSession] = Field(default_factory=list)

    local_session_timeout_steps: int = 30
    remote_session_timeout_steps: int = 5
    max_remote_sessions: int = 3

    current_timestep: int = 0

    @property
    def _user_manager(self) -> UserManager:
        return self.software_manager.software["UserManager"]  # noqa

    def pre_timestep(self, timestep: int) -> None:
        """Apply any pre-timestep logic that helps make sure we have the correct observations."""
        self.current_timestep = timestep
        if self.local_session:
            if self.local_session.last_active_step + self.local_session_timeout_steps <= timestep:
                self._timeout_session(self.local_session)

    def _timeout_session(self, session: UserSession) -> None:
        session.end_step = self.current_timestep
        session_identity = session.user.username
        if session.local:
            self.local_session = None
            session_type = "Local"
        else:
            self.remote_sessions.pop(session.uuid)
            session_type = "Remote"
            session_identity = f"{session_identity} {session.remote_ip_address}"

        self.sys_log.info(f"{self.name}: {session_type} {session_identity} session timeout due to inactivity")

    def login(self, username: str, password: str) -> Optional[str]:
        if not self._can_perform_action():
            return None
        user = self._user_manager.authenticate_user(username=username, password=password)
        if user:
            self.logout()
            self.local_session = UserSession.create(user=user, timestep=self.current_timestep)
            self.sys_log.info(f"{self.name}: User {user.username} logged in")
            return self.local_session.uuid
        else:
            self.sys_log.info(f"{self.name}: Incorrect username or password")

    def logout(self):
        if not self._can_perform_action():
            return False
        if self.local_session:
            session = self.local_session
            session.end_step = self.current_timestep
            self.historic_sessions.append(session)
            self.local_session = None
            self.sys_log.info(f"{self.name}: User {session.user.username} logged out")
