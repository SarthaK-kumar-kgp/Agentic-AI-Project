import json


def dispatch_agents(
    router_output,
    cost_agent,
    engineering_agent,
    security_agent,
    performance_agent,
):
    if isinstance(router_output, str):
        router_output = json.loads(router_output)

    routes = router_output.get("routes", [])
    selected_agents = set()

    for route in routes:
        selected_agents.add(route.get("primary_agent"))
        selected_agents.update(route.get("secondary_agents", []))

    results = {}

    if "cost_agent" in selected_agents:
        results["cost"] = cost_agent(router_output)

    if "engineering_agent" in selected_agents:
        results["engineering"] = engineering_agent(router_output)

    if "security_agent" in selected_agents:
        results["security"] = security_agent(router_output)

    if "performance_agent" in selected_agents:
        results["performance"] = performance_agent(router_output)

    return results
