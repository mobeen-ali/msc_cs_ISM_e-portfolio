"""Visualization utilities for the attack tree analyzer.

This module uses `networkx` and `matplotlib` (with the Agg backend)
to render an attack tree as a PNG image.  Nodes of different types
(AND, OR, LEAF) are drawn with different marker shapes to assist
interpretation.  The resulting image is saved into the
``static/outputs`` directory of the Flask application with a
timestamped filename.
"""

from __future__ import annotations

import os
import time
from typing import Dict, Any, Tuple

import matplotlib

# Use a non‑interactive backend suitable for headless environments
matplotlib.use("Agg")  # noqa: E402  # must be set before pyplot import

import matplotlib.pyplot as plt
try:
    import networkx as nx  # type: ignore
except Exception:
    nx = None  # networkx may be unavailable


def render_tree(root_id: str, nodes: Dict[str, Dict[str, Any]]) -> str:
    """Render the attack tree to a PNG file and return its relative path."""
    import math
    import textwrap
    import matplotlib.pyplot as plt

    # --- helpers -------------------------------------------------------------
    def wrap_label(s: str, width: int = 16, max_lines: int = 3) -> str:
        lines = textwrap.wrap(s, width=width)
        if len(lines) > max_lines:
            lines = lines[:max_lines - 1] + [lines[max_lines - 1] + "…"]
        return "\n".join(lines) if lines else s

    def node_depths(root: str) -> Dict[str, int]:
        """Compute depth from root (for fallback tree layout & rank separation)."""
        from collections import deque
        depth = {root: 0}
        q = deque([root])
        while q:
            u = q.popleft()
            for v in nodes.get(u, {}).get("children", []):
                if v not in depth:
                    depth[v] = depth[u] + 1
                    q.append(v)
        return depth

    # --- figure sizing based on graph size ----------------------------------
    N = max(1, len(nodes))
    # Wider/taller for larger trees
    fig_w = min(28, max(10, 0.6 * math.sqrt(N) * 6))
    fig_h = min(18, max(7,  0.6 * math.sqrt(N) * 4))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.clear()
    ax.axis("off")
    ax.margins(0.15)

    # --- Build graph ---------------------------------------------------------
    if nx is not None:
        G = nx.DiGraph()
        for nid, node in nodes.items():
            G.add_node(nid, type=node["type"], raw_label=node["label"])
            if node["type"] != "LEAF":
                for child in node.get("children", []):
                    G.add_edge(nid, child)
    else:
        G = None  # fallback later

    # --- Choose layout: Graphviz -> Spring -> Fallback -----------------------
    pos = None
    used_graphviz = False
    if G is not None:
        try:
            # Try Graphviz (best for layered trees)
            # You need pygraphviz (preferred) or pydot installed; Graphviz must be on PATH.
            try:
                from networkx.drawing.nx_agraph import graphviz_layout
            except Exception:
                graphviz_layout = None
            if graphviz_layout is None:
                from networkx.drawing.nx_pydot import graphviz_layout  # type: ignore
            # Increase ranksep/nodesep a bit to avoid overlaps
            pos = graphviz_layout(G, prog="dot")
            used_graphviz = True
        except Exception:
            pos = None

        if pos is None:
            # Tuned spring layout: spread increases as N grows
            # k ~ ideal distance between nodes
            k = 1.1 / math.sqrt(N) if N > 1 else 0.5
            pos = nx.spring_layout(G, k=k * 3, iterations=300, seed=42)
    else:
        # original simple recursive fallback
        def layout(node_id: str, depth: int = 0) -> Tuple[Dict[str, Tuple[float, float]], float]:
            node = nodes[node_id]
            if node["type"] == "LEAF" or not node.get("children"):
                return {node_id: (0.0, -depth)}, 1.0
            positions: Dict[str, Tuple[float, float]] = {}
            total_width = 0.0
            x_offset = 0.0
            for child in node["children"]:
                pos_dict, width = layout(child, depth + 1)
                for nid2, (x, y) in pos_dict.items():
                    positions[nid2] = (x + x_offset, y)
                x_offset += width
                total_width += width
            centre = total_width / 2.0 - 0.5
            positions[node_id] = (centre, -depth)
            return positions, total_width
        positions, _ = layout(root_id)
        pos = positions

    # --- Draw ----------------------------------------------------------------
    type_to_shape = {"AND": "s", "OR": "o", "LEAF": "v"}

    if G is not None:
        # Draw nodes by type with larger sizes for readability
        for typ, shape in type_to_shape.items():
            nodelist = [n for n, d in G.nodes(data=True) if d.get("type") == typ]
            if not nodelist:
                continue
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=nodelist,
                node_shape=shape,
                node_size=450,  # bigger nodes reduce label crowding on top
                node_color="#94c3f3" if typ == "LEAF" else "#f9d793",
                edgecolors="black",
                linewidths=1.0,
                ax=ax,
            )
        nx.draw_networkx_edges(G, pos, arrows=False, ax=ax)

        # Labels: wrap + offset + bbox for readability
        depths = node_depths(root_id)
        # Font scales slightly with figure size; clamp to reasonable range
        base_font = max(7, min(12, int(8 + 0.2 * math.sqrt(N))))
        for n in G.nodes():
            x, y = pos[n]
            raw = G.nodes[n].get("raw_label", str(n))
            lbl = wrap_label(raw, width=18 if used_graphviz else 14, max_lines=3)
            # Offset label above node; a bit more offset if dense levels
            offset_pts = 8
            ax.annotate(
                lbl, xy=(x, y), xytext=(0, offset_pts),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=base_font,
                linespacing=0.95,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, boxstyle="round,pad=0.2"),
                clip_on=False,
            )
    else:
        # Fallback drawing (no networkx)
        # Draw edges
        for nid, node in nodes.items():
            if node["type"] != "LEAF":
                for child in node.get("children", []):
                    x1, y1 = pos[nid]
                    x2, y2 = pos[child]
                    ax.plot([x1, x2], [y1, y2], color="black")
        # Draw nodes + labels
        for nid, (x, y) in pos.items():
            typ = nodes[nid]["type"]
            raw = nodes[nid]["label"]
            lbl = wrap_label(raw, width=18, max_lines=3)
            marker = "s" if typ == "AND" else ("o" if typ == "OR" else "v")
            colour = "#edc064" if typ in ("AND", "OR") else "#63adf7"
            ax.scatter(x, y, marker=marker, s=450, color=colour, edgecolors="black", linewidths=1.0)
            ax.annotate(
                lbl, xy=(x, y), xytext=(0, 12),
                textcoords="offset points",
                ha="center", va="bottom",
                fontsize=9,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, boxstyle="round,pad=0.2"),
                clip_on=False,
            )
    # --- Legend at top ----------------------------------------------------------
    import matplotlib.lines as mlines

    legend_handles = [
        mlines.Line2D([], [], color='black', marker='s', linestyle='None',
                    markerfacecolor='#f9d793', markersize=10, label='AND Node (square)'),
        mlines.Line2D([], [], color='black', marker='o', linestyle='None',
                    markerfacecolor='#f9d793', markersize=10, label='OR Node (circle)'),
        mlines.Line2D([], [], color='black', marker='v', linestyle='None',
                    markerfacecolor='#94c3f3', markersize=10, label='LEAF Node (triangle)'),
    ]

    # Create legend above the plot
    ax.legend(
        handles=legend_handles,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.12),
        ncol=3,
        frameon=True,
        fontsize=10
    )

    # --- Save higher DPI, extra tight bbox -----------------------------------
    import os, time
    timestamp = int(time.time() * 1000)
    filename = f"tree_{timestamp}.png"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_dir = os.path.join(current_dir, ".", "static", "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    file_path = os.path.join(outputs_dir, filename)

    plt.tight_layout(pad=1.0)
    fig.savefig(file_path, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return os.path.join("outputs", filename)
