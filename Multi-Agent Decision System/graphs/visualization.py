from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import ast
import inspect
import subprocess
import textwrap

from graphs.graph import builder


Edge = Tuple[str, str]


def _display_label(node_id: str) -> str:
    if node_id == "__start__":
        return "START"
    if node_id == "__end__":
        return "END"
    return node_id


def _node_role(node_id: str, branch_sources: Set[str], branch_targets: Set[str]) -> str:
    if node_id == "__start__":
        return "start"
    if node_id == "__end__":
        return "end"
    if node_id in branch_sources:
        return "source"
    if node_id in branch_targets:
        return "target"
    return "regular"


def _infer_branch_targets(path_func, node_ids: Set[str]) -> Set[str]:
    try:
        source = inspect.getsource(path_func)
    except (OSError, TypeError):
        return set()

    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return set()

    targets: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in node_ids:
            targets.add(node.value)
    return targets


def _collect_edges() -> Tuple[List[Edge], Set[str], Set[str]]:
    node_ids = set(builder.nodes.keys())
    hard_edges = sorted(set(builder.edges))
    branch_edges: Set[Edge] = set()
    branch_sources: Set[str] = set()
    branch_targets: Set[str] = set()

    for source, branches in builder.branches.items():
        branch_sources.add(source)
        for branch in branches.values():
            if branch.ends:
                inferred = set(branch.ends.values())
            else:
                inferred = _infer_branch_targets(branch.path.func, node_ids)

            for target in inferred:
                if target in node_ids:
                    branch_edges.add((source, target))
                    branch_targets.add(target)

    combined_edges = list(hard_edges)
    for edge in sorted(branch_edges):
        if edge not in hard_edges:
            combined_edges.append(edge)

    return combined_edges, branch_sources, branch_targets


def _compute_levels(edges: Sequence[Edge], start_node: str = "__start__") -> Dict[str, int]:
    adjacency: Dict[str, List[str]] = defaultdict(list)
    for source, target in edges:
        adjacency[source].append(target)

    levels: Dict[str, int] = {start_node: 0}
    queue: deque = deque([start_node])

    while queue:
        node = queue.popleft()
        current_level = levels[node]
        for neighbor in adjacency.get(node, []):
            next_level = current_level + 1
            if neighbor not in levels or next_level < levels[neighbor]:
                levels[neighbor] = next_level
                queue.append(neighbor)

    return levels


def build_workflow_dot() -> str:
    edges, branch_sources, branch_targets = _collect_edges()
    node_ids = list(builder.nodes.keys())
    levels = _compute_levels(edges)

    nodes_by_level: Dict[int, List[str]] = defaultdict(list)
    for node_id in node_ids:
        nodes_by_level[levels.get(node_id, 0)].append(node_id)

    lines: List[str] = [
        "digraph MultiAgentDecisionSystem {",
        '    graph [',
        '        rankdir=TB,',
        '        bgcolor="white",',
        '        pad="0.35",',
        '        nodesep="0.45",',
        '        ranksep="0.8",',
        '        splines=polyline,',
        '        fontname="Helvetica",',
        '        concentrate=true',
        '    ];',
        "",
        '    node [',
        '        shape=box,',
        '        style="rounded,filled",',
        '        fontname="Helvetica",',
        '        color="#3b82f6",',
        '        fillcolor="#dbeafe",',
        '        penwidth=1.3,',
        '        margin="0.18,0.12"',
        '    ];',
        "",
        '    edge [',
        '        color="#6b7280",',
        '        penwidth=1.15,',
        '        arrowsize=0.8,',
        '        fontname="Helvetica"',
        '    ];',
        "",
    ]

    for level in sorted(nodes_by_level):
        group = sorted(nodes_by_level[level], key=lambda nid: (nid not in branch_sources, nid not in branch_targets, nid))
        lines.append(f"    subgraph cluster_level_{level} {{")
        lines.append('        style="invis";')
        lines.append("        rank=same;")
        for node_id in group:
            role = _node_role(node_id, branch_sources, branch_targets)
            label = _display_label(node_id)
            if role == "start":
                lines.extend(
                    [
                        f'        "{node_id}" [',
                        f'            label="{label}",',
                        '            shape=circle,',
                        '            style="filled",',
                        '            fillcolor="#111827",',
                        '            fontcolor="white",',
                        '            color="#111827",',
                        '            width=0.75,',
                        '            fixedsize=true',
                        "        ];",
                    ]
                )
            elif role == "end":
                lines.extend(
                    [
                        f'        "{node_id}" [',
                        f'            label="{label}",',
                        '            shape=doublecircle,',
                        '            style="filled",',
                        '            fillcolor="#111827",',
                        '            fontcolor="white",',
                        '            color="#111827",',
                        '            width=0.7,',
                        '            fixedsize=true',
                        "        ];",
                    ]
                )
            elif role == "source":
                lines.extend(
                    [
                        f'        "{node_id}" [',
                        f'            label="{label}",',
                        '            shape=diamond,',
                        '            fillcolor="#fef3c7",',
                        '            color="#f59e0b",',
                        '            fontcolor="#111827"',
                        "        ];",
                    ]
                )
            elif role == "target":
                lines.extend(
                    [
                        f'        "{node_id}" [',
                        f'            label="{label}",',
                        '            shape=box,',
                        '            style="rounded,filled",',
                        '            fillcolor="#dcfce7",',
                        '            color="#22c55e",',
                        '            fontcolor="#111827"',
                        "        ];",
                    ]
                )
            else:
                lines.extend(
                    [
                        f'        "{node_id}" [',
                        f'            label="{label}",',
                        '            shape=box,',
                        '            style="rounded,filled",',
                        '            fillcolor="#dbeafe",',
                        '            color="#3b82f6",',
                        '            fontcolor="#111827"',
                        "        ];",
                    ]
                )
        lines.append("    }")
        lines.append("")

    hard_edges = set(builder.edges)
    for source, target in edges:
        attrs: List[str] = []
        is_branch_edge = (source, target) not in hard_edges

        if is_branch_edge:
            attrs.append('style="dashed"')
            attrs.append('color="#dc2626"')
            if levels.get(target, 0) <= levels.get(source, 0):
                attrs.append("constraint=false")
        elif source == "__start__":
            attrs.append('color="#111827"')
        elif target == "__end__":
            attrs.append('color="#16a34a"')

        attr_text = ""
        if attrs:
            attr_text = " [" + ", ".join(attrs) + "]"

        lines.append(f'    "{source}" -> "{target}"{attr_text};')

    lines.append("}")
    return "\n".join(lines)


def render_workflow_graph(
    output_png: Path,
    output_dot: Optional[Path] = None,
    output_svg: Optional[Path] = None,
) -> None:
    dot_source = build_workflow_dot()
    dot_path = output_dot or output_png.with_suffix(".dot")
    dot_path.write_text(dot_source, encoding="utf-8")

    subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(output_png)], check=True)

    if output_svg is not None:
        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(output_svg)], check=True)
