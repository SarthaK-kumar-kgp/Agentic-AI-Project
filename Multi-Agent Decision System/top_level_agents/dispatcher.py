import json
from typing import Any, Dict, List


def dispatch_agents(router_output, *_, **__):
    if isinstance(router_output, str):
        router_output = json.loads(router_output)

    routes = router_output.get("routes", [])
    agent_routes: Dict[str, List[Dict[str, Any]]] = {
        "cost_agent": [],
        "engineering_agent": [],
        "security_agent": [],
        "performance_agent": [],
    }

    selected_agents = set()

    for route in routes:
        primary_agent = route.get("primary_agent")
        secondary_agents = route.get("secondary_agents", []) or []
        route_agents = {primary_agent, *secondary_agents}

        for agent_name in route_agents:
            if agent_name in agent_routes:
                selected_agents.add(agent_name)
                agent_routes[agent_name].append(route)

    return {
        "selected_agents": sorted(selected_agents),
        "agent_routes": agent_routes,
        "routes": routes,
    }
