# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

from primaite.game.agent.interface import AgentHistoryItem
from primaite.game.agent.rewards import (
    GreenAdminDatabaseUnreachablePenalty,
    WebpageUnavailablePenalty,
    WebServer404Penalty,
)
from primaite.interface.request import RequestResponse


class TestWebServer404PenaltySticky:
    def test_non_sticky(self):
        reward = WebServer404Penalty("computer", "WebService", sticky=False)

        # no response codes yet, reward is 0
        codes = []
        state = {
            "network": {"nodes": {"computer": {"services": {"WebService": {"response_codes_this_timestep": codes}}}}}
        }
        last_action_response = None
        assert reward.calculate(state, last_action_response) == 0

        # update codes (by reference), 200 response code is now present
        codes.append(200)
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # update codes (by reference), to make it empty again, reward goes back to 0
        codes.pop()
        assert reward.calculate(state, last_action_response) == 0.0

        # update codes (by reference), 404 response code is now present, reward = -1.0
        codes.append(404)
        assert reward.calculate(state, last_action_response) == -1.0

        # don't update codes, it still has just a 404, check the reward is -1.0 again
        assert reward.calculate(state, last_action_response) == -1.0

    def test_sticky(self):
        reward = WebServer404Penalty("computer", "WebService", sticky=True)

        # no response codes yet, reward is 0
        codes = []
        state = {
            "network": {"nodes": {"computer": {"services": {"WebService": {"response_codes_this_timestep": codes}}}}}
        }
        last_action_response = None
        assert reward.calculate(state, last_action_response) == 0

        # update codes (by reference), 200 response code is now present
        codes.append(200)
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # update codes (by reference), to make it empty again, reward remains at 1.0 because it's sticky
        codes.pop()
        assert reward.calculate(state, last_action_response) == 1.0

        # update codes (by reference), 404 response code is now present, reward = -1.0
        codes.append(404)
        assert reward.calculate(state, last_action_response) == -1.0

        # don't update codes, it still has just a 404, check the reward is -1.0 again
        assert reward.calculate(state, last_action_response) == -1.0


class TestWebpageUnavailabilitySticky:
    def test_non_sticky(self):
        reward = WebpageUnavailablePenalty("computer", sticky=False)

        # no response codes yet, reward is 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        browser_history = []
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0

        # agent did a successful fetch
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="success", data={})
        browser_history.append({"outcome": 200})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # agent did nothing, because reward is not sticky, it goes back to 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        browser_history = []
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0.0

        # agent fails to fetch, get a -1.0 reward
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="failure", data={})
        browser_history.append({"outcome": 404})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

        # agent fails again to fetch, get a -1.0 reward again
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="failure", data={})
        browser_history.append({"outcome": 404})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

    def test_sticky(self):
        reward = WebpageUnavailablePenalty("computer", sticky=True)

        # no response codes yet, reward is 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        browser_history = []
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0

        # agent did a successful fetch
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="success", data={})
        browser_history.append({"outcome": 200})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # agent did nothing, because reward is sticky, it stays at 1.0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # agent fails to fetch, get a -1.0 reward
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="failure", data={})
        browser_history.append({"outcome": 404})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

        # agent fails again to fetch, get a -1.0 reward again
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "WebBrowser", "execute"]
        response = RequestResponse(status="failure", data={})
        browser_history.append({"outcome": 404})
        state = {"network": {"nodes": {"computer": {"applications": {"WebBrowser": {"history": browser_history}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0


class TestGreenAdminDatabaseUnreachableSticky:
    def test_non_sticky(self):
        reward = GreenAdminDatabaseUnreachablePenalty("computer", sticky=False)

        # no response codes yet, reward is 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0

        # agent did a successful fetch
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # agent did nothing, because reward is not sticky, it goes back to 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        browser_history = []
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0.0

        # agent fails to fetch, get a -1.0 reward
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="failure", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

        # agent fails again to fetch, get a -1.0 reward again
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="failure", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

    def test_sticky(self):
        reward = GreenAdminDatabaseUnreachablePenalty("computer", sticky=True)

        # no response codes yet, reward is 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 0

        # agent did a successful fetch
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # THE IMPORTANT BIT
        # agent did nothing, because reward is not sticky, it goes back to 0
        action, params, request = "DO_NOTHING", {}, ["do_nothing"]
        response = RequestResponse(status="success", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == 1.0

        # agent fails to fetch, get a -1.0 reward
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="failure", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0

        # agent fails again to fetch, get a -1.0 reward again
        action = "NODE_APPLICATION_EXECUTE"
        params = {"node_id": 0, "application_id": 0}
        request = ["network", "node", "computer", "application", "DatabaseClient", "execute"]
        response = RequestResponse(status="failure", data={})
        state = {"network": {"nodes": {"computer": {"applications": {"DatabaseClient": {}}}}}}
        last_action_response = AgentHistoryItem(
            timestep=0, action=action, parameters=params, request=request, response=response
        )
        assert reward.calculate(state, last_action_response) == -1.0
