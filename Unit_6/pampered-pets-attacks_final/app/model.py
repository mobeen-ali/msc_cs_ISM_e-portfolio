"""Core data model and computations for the attack tree analyzer.

This module is responsible for parsing attack tree specifications
expressed in YAML, JSON or XML; normalising them to a common internal
representation; validating their structure; and performing the
aggregations required by the application such as computing the
probability of the top event, expected loss and top contributors.  The
internal representation is a dictionary mapping node identifiers to
their attributes.  Each node dictionary contains the keys ``id``,
``label``, ``type`` (``AND``, ``OR`` or ``LEAF``), ``children`` (list
of child identifiers for internal nodes), ``prob`` and ``impact``.

Functions in this module are pure and do not depend on any Flask
context, making them easy to unit test.
"""

from __future__ import annotations

import json
from typing import Any

import yaml  # type: ignore

try:
    import xmltodict  # type: ignore
except Exception:
    xmltodict = None  # xmltodict may not be available in the environment


class SpecError(Exception):
    """Exception raised for errors in the attack tree specification."""


def _normalise_node(node: dict[str, Any]) -> dict[str, Any]:
    """Ensure a node dictionary has all required keys with default values.

    Parameters
    ----------
    node
        The node dictionary from the input specification.

    Returns
    -------
    dict
        A new dictionary containing ``id``, ``label``, ``type``,
        ``children``, ``prob`` and ``impact``.  Missing fields are
        initialised to sensible defaults: ``children`` becomes an empty
        list for leaf nodes and ``prob``/``impact`` become ``None`` if
        absent.
    """
    # Copy to avoid mutating the caller's object
    n: dict[str, Any] = {
        "id": node.get("id"),
        "label": node.get("label"),
        "type": node.get("type"),
    }
    typ = (n["type"] or "").upper()
    n["type"] = typ
    if typ == "LEAF":
        # Leaves don't have children, but prob/impact may be present
        n["children"] = []
        n["prob"] = node.get("prob")
        n["impact"] = node.get("impact")
    else:
        # Internal node: ensure children is a list
        children = node.get("children", [])
        if isinstance(children, dict):
            # In XML input a single child may come through as a dict; wrap it
            children = [children]
        # Normalise to list of strings
        n["children"] = [c if isinstance(c, str) else c.get("id") for c in children]
        n["prob"] = None
        n["impact"] = None
    return n


def _build_internal_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw spec dictionary into the internal representation.

    The top level of an attack tree specification contains the root
    node's ``id``, ``label``, ``type`` and ``children``, as well as a
    ``nodes`` sequence containing all other nodes.  This function
    constructs a mapping of node identifiers to fully normalised node
    dictionaries and validates that all referenced children exist.

    Parameters
    ----------
    spec
        The parsed specification object.

    Returns
    -------
    dict
        A dictionary with keys ``root`` and ``nodes``.  ``root`` is the
        identifier of the top event.  ``nodes`` maps each node
        identifier to its normalised dictionary.

    Raises
    ------
    SpecError
        If there are structural issues such as missing nodes or
        duplicate identifiers.
    """
    if not isinstance(spec, dict):
        raise SpecError("Spec must be a mapping at the top level")
    root_id = spec.get("id")
    if root_id is None:
        raise SpecError("Missing 'id' for root node")
    # Start building nodes mapping with an entry for the root
    nodes_map: dict[str, dict[str, Any]] = {}
    # Add root from top level
    root_node = {
        "id": root_id,
        "label": spec.get("label"),
        "type": spec.get("type"),
        "children": spec.get("children", []),
    }
    nodes_map[root_id] = _normalise_node(root_node)
    # Populate the rest of the nodes
    nodes_list = spec.get("nodes", [])
    if isinstance(nodes_list, dict):
        # xmltodict may convert a single element sequence into a dict
        nodes_list = [nodes_list]
    for raw_node in nodes_list:
        node = _normalise_node(raw_node)
        nid = node.get("id")
        if nid is None:
            raise SpecError("Each node must have an 'id'")
        if nid in nodes_map:
            # Merge with existing definition but preserve children defined at top level
            existing = nodes_map[nid]
            # If this appears to redefine the node type we treat it as an error
            if existing["type"] != node["type"]:
                raise SpecError(f"Duplicate node id '{nid}' with conflicting types")
            # For leaf nodes we propagate prob/impact values if provided in nodes list
            if node["prob"] is not None:
                existing["prob"] = node["prob"]
            if node["impact"] is not None:
                existing["impact"] = node["impact"]
            # For internal nodes we update the children list
            if node["children"]:
                existing["children"] = node["children"]
            continue
        nodes_map[nid] = node
    # Validate that all children references exist
    for nid, node in nodes_map.items():
        if node["type"] != "LEAF":
            for child_id in node["children"]:
                if child_id not in nodes_map:
                    raise SpecError(f"Node '{nid}' references unknown child '{child_id}'")
    return {"root": root_id, "nodes": nodes_map}


def parse_spec(data: bytes | str, extension: str) -> dict[str, Any]:
    """Parse an attack tree specification from YAML, JSON or XML.

    Parameters
    ----------
    data
        The raw file contents as bytes or text.
    extension
        The file extension (lowercase) used to determine the parser.

    Returns
    -------
    dict
        The internal representation of the specification with keys
        ``root`` and ``nodes``.

    Raises
    ------
    SpecError
        If the input is malformed or fails validation.
    """
    if isinstance(data, bytes):
        text = data.decode("utf-8")
    else:
        text = data
    ext = extension.lower()
    try:
        if ext in {"yaml", "yml"}:
            spec_obj = yaml.safe_load(text)
        elif ext == "json":
            spec_obj = json.loads(text)
        elif ext == "xml":
            # Parse XML.  Use xmltodict if available, otherwise fall back
            # to xml.etree.ElementTree.  The expected XML schema has a
            # top element wrapping the spec contents.
            if xmltodict is not None:
                xml_dict = xmltodict.parse(text)  # type: ignore[operator]
                if len(xml_dict) != 1:
                    raise SpecError("Unexpected XML format")
                spec_obj = next(iter(xml_dict.values()))
            else:
                import xml.etree.ElementTree as ET

                root_el = ET.fromstring(text)
                spec_obj = {}
                # Extract simple scalar fields
                for tag in ("id", "label", "type"):
                    el = root_el.find(tag)
                    if el is not None and el.text is not None:
                        spec_obj[tag] = el.text.strip()
                # Extract children
                children_el = root_el.find("children")
                if children_el is not None:
                    spec_obj["children"] = [c.text.strip() for c in children_el if c.text]
                # Extract nodes
                nodes_el = root_el.find("nodes")
                nodes_list = []
                if nodes_el is not None:
                    for node_el in nodes_el.findall("node"):
                        node_dict: dict[str, Any] = {}
                        for tag in ("id", "label", "type"):
                            el2 = node_el.find(tag)
                            if el2 is not None and el2.text is not None:
                                node_dict[tag] = el2.text.strip()
                        # Children of internal nodes
                        children2_el = node_el.find("children")
                        if children2_el is not None:
                            node_dict["children"] = [c.text.strip() for c in children2_el if c.text]
                        # Probability and impact values for leaves
                        prob_el = node_el.find("prob")
                        if prob_el is not None and prob_el.text not in (None, ""):
                            try:
                                node_dict["prob"] = float(prob_el.text)
                            except ValueError:
                                node_dict["prob"] = prob_el.text
                        impact_el = node_el.find("impact")
                        if impact_el is not None and impact_el.text not in (None, ""):
                            try:
                                node_dict["impact"] = float(impact_el.text)
                            except ValueError:
                                node_dict["impact"] = impact_el.text
                        nodes_list.append(node_dict)
                spec_obj["nodes"] = nodes_list
        else:
            raise SpecError(f"Unsupported file extension '{extension}'")
    except Exception as exc:
        raise SpecError(f"Failed to parse spec: {exc}") from exc
    # Build internal representation and validate
    return _build_internal_spec(spec_obj)


def compute_probabilities(root_id: str, nodes: dict[str, dict[str, Any]]) -> float:
    """Recursively compute the probability of the top event.

    Parameters
    ----------
    root_id
        Identifier of the top node.
    nodes
        Mapping of node identifiers to node dictionaries.

    Returns
    -------
    float
        The computed probability of the root event.

    Raises
    ------
    ValueError
        If a leaf node is missing its probability.
    """

    def _prob(node_id: str) -> float:
        node = nodes[node_id]
        typ = node["type"]
        if typ == "LEAF":
            p = node.get("prob")
            if p is None:
                raise ValueError(f"Missing probability for leaf '{node_id}'")
            return float(p)
        # Compute child probabilities recursively
        child_probs = [_prob(cid) for cid in node["children"]]
        if typ == "AND":
            result = 1.0
            for cp in child_probs:
                result *= cp
            return result
        if typ == "OR":
            p_not = 1.0
            for cp in child_probs:
                p_not *= 1.0 - cp
            return 1.0 - p_not
        raise ValueError(f"Unknown node type '{typ}' for node '{node_id}'")

    return _prob(root_id)


def expected_loss(nodes: dict[str, dict[str, Any]]) -> float:
    """Compute the expected loss across all leaves.

    The expected loss is the sum over all leaf nodes of
    ``probability * impact``.  A missing probability or impact will
    trigger a ValueError so the caller can prompt the user to fill in
    missing values.

    Parameters
    ----------
    nodes
        Mapping of node identifiers to node dictionaries.

    Returns
    -------
    float
        The expected loss.

    Raises
    ------
    ValueError
        If any leaf node lacks a probability or impact.
    """
    total = 0.0
    for node in nodes.values():
        if node["type"] == "LEAF":
            prob = node.get("prob")
            impact = node.get("impact")
            if prob is None:
                raise ValueError(f"Missing probability for leaf '{node['id']}'")
            if impact is None:
                raise ValueError(f"Missing impact for leaf '{node['id']}'")
            total += float(prob) * float(impact)
    return total


def top_contributors(nodes: dict[str, dict[str, Any]], k: int = 3) -> list[dict[str, Any]]:
    """Return the top ``k`` leaves by contribution (probability × impact).

    Parameters
    ----------
    nodes
        Mapping of node identifiers to node dictionaries.
    k
        Number of top contributors to return.  Defaults to 3.

    Returns
    -------
    list of dict
        A list of dictionaries each containing ``id``, ``label`` and
        ``value`` for the top contributors sorted in descending order.
    """
    contributions: list[tuple[str, str, float]] = []
    for node in nodes.values():
        if node["type"] == "LEAF":
            prob = node.get("prob")
            impact = node.get("impact")
            if prob is None or impact is None:
                continue
            contributions.append((node["id"], node["label"], float(prob) * float(impact)))
    # Sort by contribution descending
    contributions.sort(key=lambda x: x[2], reverse=True)
    top = contributions[:k]
    return [{"id": nid, "label": lbl, "value": val} for nid, lbl, val in top]
