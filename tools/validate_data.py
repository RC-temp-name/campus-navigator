"""
validate_data.py — sanity-check data/nodes.json and data/edges.json.

Catches the common mistakes that break the app before you even open a
browser:

  Errors (must fix):
    - malformed JSON (missing comma, bad quote, trailing comma)
    - nodes.json or edges.json has the wrong top-level shape
    - node or edge entries that aren't objects
    - node missing required fields (id, name, type, building, floor, coords)
    - edge missing required fields (source, target, weight, instruction)
    - duplicate node ids
    - edge pointing at a node that doesn't exist
    - non-numeric edge weight
    - coords that aren't a [x, y] pair

  Warnings (probably wrong, doesn't block):
    - an edge has no reverse edge (connections should be bidirectional)
    - node id doesn't start with the building prefix (e.g. NPB_5_102)

Usage:
    uv run tools/validate_data.py
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

REQUIRED_NODE_FIELDS = {"id", "name", "type", "building", "floor", "coords"}
REQUIRED_EDGE_FIELDS = {"source", "target", "weight", "instruction"}


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load(name):
    path = DATA_DIR / name
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ Missing file: {path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"✗ {name} is not valid JSON — line {exc.lineno}: {exc.msg}")
        print("  Look near that line for a missing comma or quote.")
        sys.exit(1)


def main():
    nodes = load("nodes.json")
    edges = load("edges.json")

    errors = []
    warnings = []

    if not isinstance(nodes, list):
        errors.append(
            f"nodes.json: top-level value must be a list, got {type(nodes).__name__}"
        )
        nodes = []
    if not isinstance(edges, list):
        errors.append(
            f"edges.json: top-level value must be a list, got {type(edges).__name__}"
        )
        edges = []

    # ---- nodes ----
    node_ids = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(
                f"nodes.json[{i}]: entry must be an object, got {type(node).__name__}"
            )
            continue

        missing = REQUIRED_NODE_FIELDS - set(node)
        if missing:
            errors.append(f"nodes.json[{i}]: missing field(s) {sorted(missing)}")
            continue

        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id.strip():
            errors.append(f"nodes.json[{i}]: id must be non-empty text")
            continue
        if node_id in node_ids:
            errors.append(f"nodes.json: duplicate node id '{node_id}'")
        node_ids.add(node_id)

        coords = node["coords"]
        if (
            not isinstance(coords, list)
            or len(coords) != 2
            or not all(is_number(value) for value in coords)
        ):
            errors.append(
                f"node '{node_id}': coords must be [x, y] numbers, got {coords!r}"
            )

        for field in ("name", "type"):
            if not isinstance(node[field], str) or not node[field].strip():
                errors.append(f"node '{node_id}': {field} must be non-empty text")

        if not isinstance(node["floor"], int) or isinstance(node["floor"], bool):
            errors.append(f"node '{node_id}': floor must be an integer")

        building = node["building"]
        if not isinstance(building, str) or not building.strip():
            errors.append(f"node '{node_id}': building must be non-empty text")
        elif not node_id.startswith(building + "_"):
            warnings.append(
                f"node '{node_id}': id doesn't start with building prefix '{building}_'"
            )

    # ---- edges ----
    edge_pairs = set()
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(
                f"edges.json[{i}]: entry must be an object, got {type(edge).__name__}"
            )
            continue

        missing = REQUIRED_EDGE_FIELDS - set(edge)
        if missing:
            errors.append(f"edges.json[{i}]: missing field(s) {sorted(missing)}")
            continue

        source = edge["source"]
        target = edge["target"]
        label = f"{source} → {target}"
        for field, node_ref in (("source", source), ("target", target)):
            if not isinstance(node_ref, str) or node_ref not in node_ids:
                errors.append(f"edge {label}: '{node_ref}' is not a known node id")
        if not is_number(edge["weight"]):
            errors.append(
                f"edge {label}: weight must be a number, got {edge['weight']!r}"
            )
        if not isinstance(edge["instruction"], str) or not edge["instruction"].strip():
            errors.append(f"edge {label}: instruction must be non-empty text")

        if isinstance(source, str) and isinstance(target, str):
            edge_pairs.add((source, target))

    for source, target in sorted(edge_pairs):
        if (target, source) not in edge_pairs:
            warnings.append(
                f"edge {source} → {target}: no reverse edge exists "
                "(connections must be bidirectional)"
            )

    # ---- report ----
    for warning in warnings:
        print(f"  ⚠ {warning}")
    for error in errors:
        print(f"  ✗ {error}")

    if errors:
        print(
            f"\n✗ {len(errors)} problem(s) found in data/ — fix them, then re-run `uv run tools/validate_data.py`."
        )
        sys.exit(1)

    print(
        f"✓ Data OK — {len(nodes)} nodes, {len(edges)} edges ({len(edge_pairs)} connections)"
    )
    if warnings:
        print(f"  ({len(warnings)} warning(s) above — worth a look, not blocking)")
    else:
        print(
            "  No duplicate ids, no dangling edges, every connection is bidirectional."
        )


if __name__ == "__main__":
    main()
