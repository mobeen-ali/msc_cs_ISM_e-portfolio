"""Flask routes and view logic for the attack tree analyzer.

This blueprint defines all HTTP endpoints for uploading specifications,
loading demo scenarios, editing leaf parameters, running sensitivity
analysis and downloading artefacts.  It interacts with the core
functions in ``model.py`` for parsing and computation and with
``viz.py`` for image rendering.  Session storage is used to persist
the current specification and generated images between requests.
"""

from __future__ import annotations

import copy
import io
import os
from typing import Any, Dict, Optional, List

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from .model import (
    parse_spec,
    compute_probabilities,
    expected_loss,
    top_contributors,
    SpecError,
)
from .viz import render_tree

# YAML is used for exporting specifications
import yaml  # type: ignore


bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET"])
def index() -> str:
    """Render the home page where users can upload or load a demo spec."""
    return render_template("index.html")


@bp.route("/load_demo/<string:scenario>", methods=["GET"])
def load_demo(scenario: str) -> Any:
    """Load one of the predefined demo scenarios from disk and analyse it.

    Parameters
    ----------
    scenario
        Either ``"pre"`` or ``"post"`` selecting which demo file to load.

    Returns
    -------
    Response
        A redirect to the analysis page or back to the index on error.
    """
    filename = None
    if scenario.lower() == "pre":
        filename = "pre_digital.yaml"
    elif scenario.lower() == "post":
        filename = "post_digital.yaml"
    else:
        flash(f"Unknown demo scenario '{scenario}'.")
        return redirect(url_for("main.index"))
    # Compute the absolute path relative to the package root
    data_dir = os.path.join(current_app.root_path, "..", "data")
    file_path = os.path.join(data_dir, filename)
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        spec = parse_spec(content, "yaml")
    except Exception as exc:
        flash(f"Failed to load demo: {exc}")
        return redirect(url_for("main.index"))
    # Store spec in session
    session["spec"] = spec
    # Remove any previous sensitivity data
    session.pop("sensitivity", None)
    return redirect(url_for("main.analyze_get"))


@bp.route("/analyze", methods=["POST"])
def analyze_post() -> Any:
    """Handle file uploads and parse the specification."""
    uploaded = request.files.get("spec_file")
    if not uploaded or uploaded.filename == "":
        flash("Please select a YAML, JSON or XML file to upload.")
        return redirect(url_for("main.index"))
    filename = uploaded.filename
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    try:
        content = uploaded.read()
        spec = parse_spec(content, ext)
    except SpecError as exc:
        flash(f"Specification error: {exc}")
        return redirect(url_for("main.index"))
    except Exception as exc:
        flash(f"Failed to parse file: {exc}")
        return redirect(url_for("main.index"))
    # Persist the spec and clear any previous sensitivity results
    session["spec"] = spec
    session.pop("sensitivity", None)
    return redirect(url_for("main.analyze_get"))


@bp.route("/analyze", methods=["GET"])
def analyze_get() -> Any:
    """Render the analysis page for the current specification."""
    spec: Optional[Dict[str, Any]] = session.get("spec")
    if not spec:
        flash("No specification is loaded. Please upload or load a demo.")
        return redirect(url_for("main.index"))
    nodes = spec["nodes"]
    # Build list of leaves (ordered for consistency)
    leaves = [n for n in nodes.values() if n["type"] == "LEAF"]
    leaves.sort(key=lambda n: n["id"])
    # Attempt to compute results; if missing values then we suppress errors
    p_top = None
    e_loss = None
    top3 = []
    results_available = True
    try:
        p_top = compute_probabilities(spec["root"], nodes)
        e_loss = expected_loss(nodes)
        top3 = top_contributors(nodes, k=3)
    except Exception:
        results_available = False
    # Render (or fetch existing) PNG for current spec
    png_path = session.get("png_path")
    # Always re-render to reflect any updated values
    try:
        png_path = render_tree(spec["root"], nodes)
        session["png_path"] = png_path
    except Exception as exc:
        flash(f"Failed to render tree: {exc}")
        png_path = None
    # Retrieve sensitivity results if present
    sensitivity = session.get("sensitivity")
    return render_template(
        "analyze.html",
        leaves=leaves,
        results_available=results_available,
        p_top=p_top,
        e_loss=e_loss,
        top3=top3,
        png_path=png_path.replace("\\", "/") if png_path else None,
        sensitivity=sensitivity,
    )


@bp.route("/recalculate", methods=["POST"])
def recalculate() -> Any:
    """Update leaf probabilities and impacts from form inputs and redirect back."""
    spec: Optional[Dict[str, Any]] = session.get("spec")
    if not spec:
        flash("No specification is loaded.")
        return redirect(url_for("main.index"))
    nodes = spec["nodes"]
    errors: List[str] = []
    # Update each leaf from the submitted form
    for node in nodes.values():
        if node["type"] == "LEAF":
            prob_key = f"prob_{node['id']}"
            impact_key = f"impact_{node['id']}"
            prob_str = request.form.get(prob_key, "").strip()
            impact_str = request.form.get(impact_key, "").strip()
            # Convert to floats if provided; allow empty to represent None
            prob_val: Optional[float]
            impact_val: Optional[float]
            try:
                prob_val = float(prob_str) if prob_str != "" else None
            except ValueError:
                errors.append(f"Invalid probability for {node['id']}")
                prob_val = None
            try:
                impact_val = float(impact_str) if impact_str != "" else None
            except ValueError:
                errors.append(f"Invalid impact for {node['id']}")
                impact_val = None
            # Validate ranges
            if prob_val is not None and not (0.0 <= prob_val <= 1.0):
                errors.append(f"Probability for {node['id']} must be between 0 and 1")
            if impact_val is not None and impact_val < 0.0:
                errors.append(f"Impact for {node['id']} must be non‑negative")
            node["prob"] = prob_val
            node["impact"] = impact_val
    # Save updated spec
    session["spec"] = spec
    # Clear any prior sensitivity results since base values changed
    session.pop("sensitivity", None)
    # Report any validation errors
    for err in errors:
        flash(err)
    return redirect(url_for("main.analyze_get"))


@bp.route("/sensitivity", methods=["POST"])
def run_sensitivity() -> Any:
    """Run a sensitivity analysis on a selected leaf and multiplier."""
    spec: Optional[Dict[str, Any]] = session.get("spec")
    if not spec:
        flash("No specification is loaded.")
        return redirect(url_for("main.index"))
    leaf_id = request.form.get("leaf_id")
    multiplier_str = request.form.get("multiplier", "1").strip()
    try:
        multiplier = float(multiplier_str)
    except ValueError:
        flash("Multiplier must be a number.")
        return redirect(url_for("main.analyze_get"))
    if not leaf_id:
        flash("Please select a leaf for sensitivity analysis.")
        return redirect(url_for("main.analyze_get"))
    nodes = spec["nodes"]
    if leaf_id not in nodes or nodes[leaf_id]["type"] != "LEAF":
        flash("Selected node is not a valid leaf.")
        return redirect(url_for("main.analyze_get"))
    base_prob = nodes[leaf_id].get("prob")
    if base_prob is None:
        flash("The selected leaf is missing a probability value.")
        return redirect(url_for("main.analyze_get"))
    # Clone the nodes and apply the multiplier to the chosen leaf
    cloned_nodes = copy.deepcopy(nodes)
    new_prob = min(float(base_prob) * multiplier, 1.0)
    cloned_nodes[leaf_id]["prob"] = new_prob
    try:
        p_top = compute_probabilities(spec["root"], cloned_nodes)
        e_loss = expected_loss(cloned_nodes)
    except Exception as exc:
        flash(f"Cannot compute sensitivity results: {exc}")
        return redirect(url_for("main.analyze_get"))
    # Store the sensitivity results in session
    session["sensitivity"] = {
        "leaf_id": leaf_id,
        "multiplier": multiplier,
        "p_top": p_top,
        "e_loss": e_loss,
    }
    return redirect(url_for("main.analyze_get"))


@bp.route("/apply_sensitivity", methods=["POST"])
def apply_sensitivity() -> Any:
    """Apply the most recent sensitivity run to the stored specification."""
    spec: Optional[Dict[str, Any]] = session.get("spec")
    sensitivity: Optional[Dict[str, Any]] = session.get("sensitivity")
    if not spec or not sensitivity:
        flash("No sensitivity run to apply.")
        return redirect(url_for("main.analyze_get"))
    leaf_id = sensitivity.get("leaf_id")
    multiplier = sensitivity.get("multiplier")
    if not leaf_id or multiplier is None:
        flash("Incomplete sensitivity data.")
        return redirect(url_for("main.analyze_get"))
    nodes = spec["nodes"]
    # Ensure the leaf is still valid
    if leaf_id in nodes and nodes[leaf_id]["type"] == "LEAF":
        base_prob = nodes[leaf_id].get("prob")
        if base_prob is not None:
            nodes[leaf_id]["prob"] = min(float(base_prob) * float(multiplier), 1.0)
    # Save updated spec and clear sensitivity
    session["spec"] = spec
    session.pop("sensitivity", None)
    return redirect(url_for("main.analyze_get"))


@bp.route("/download/spec")
def download_spec() -> Any:
    """Serve the currently loaded specification as a YAML file for download."""
    spec: Optional[Dict[str, Any]] = session.get("spec")
    if not spec:
        flash("No specification to download.")
        return redirect(url_for("main.index"))
    # Convert internal representation back to the external YAML structure
    nodes = spec["nodes"]
    root_id = spec["root"]
    # Build the output dictionary
    out_spec = {
        "id": root_id,
        "label": nodes[root_id]["label"],
        "type": nodes[root_id]["type"],
        "children": nodes[root_id]["children"],
        "nodes": [],
    }
    for nid, node in nodes.items():
        if nid == root_id:
            continue
        entry = {
            "id": nid,
            "label": node["label"],
            "type": node["type"],
        }
        if node["type"] == "LEAF":
            entry["prob"] = node.get("prob")
            entry["impact"] = node.get("impact")
        else:
            entry["children"] = node["children"]
        out_spec["nodes"].append(entry)
    # Serialise to YAML in memory
    text_buf = io.StringIO()
    yaml.safe_dump(out_spec, text_buf, sort_keys=False, allow_unicode=True)
    data = text_buf.getvalue().encode("utf-8")
    buffer = io.BytesIO(data)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="updated_spec.yaml",
        mimetype="text/yaml",
    )


@bp.route("/download/png")
def download_png() -> Any:
    """Serve the most recently rendered attack tree PNG for download."""
    png_path = session.get("png_path")
    if not png_path:
        flash("No image available to download.")
        return redirect(url_for("main.analyze_get"))
    # The png_path is relative to the static folder; compute absolute path
    abs_path = os.path.join(current_app.root_path, "static", png_path)
    if not os.path.exists(abs_path):
        flash("The requested image file does not exist.")
        return redirect(url_for("main.analyze_get"))
    return send_file(
        abs_path,
        as_attachment=True,
        download_name=os.path.basename(abs_path),
        mimetype="image/png",
    )