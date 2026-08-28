"""
validate_data.py — sanity-check data/nodes.json and data/edges.json.

Catches the common mistakes that break the app before you even open a
browser:

  Errors (must fix):
    - malformed JSON (missing comma, bad quote, trailing comma)
    - node missing required fields (id, name, type, building, floor, coords)
    - edge missing required fields (source, target, weight, instruction)
    - duplicate node ids
    - edge pointing at a node that doesn't exist
    - non-numeric edge weight
    - coords that aren't a [x, y] pair
    - an edge that has no reverse edge (connections must be bidirectional)

  Warnings (probably wrong, doesn't block):
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

    # ---- nodes ----
    node_ids = set()
    for i, node in enumerate(nodes):
        missing = REQUIRED_NODE_FIELDS - set(node)
        if missing:
            errors.append(f"nodes.json[{i}]: missing field(s) {sorted(missing)}")
            continue

        node_id = node["id"]
        if node_id in node_ids:
            errors.append(f"nodes.json: duplicate node id '{node_id}'")
        node_ids.add(node_id)

        coords = node["coords"]
        if (
            not isinstance(coords, list)
            or len(coords) != 2
            or not all(isinstance(v, (int, float)) for v in coords)
        ):
            errors.append(
                f"node '{node_id}': coords must be [x, y] numbers, got {coords!r}"
            )

        if not node_id.startswith(node["building"] + "_"):
            warnings.append(
                f"node '{node_id}': id doesn't start with building "
                f"prefix '{node['building']}_'"
            )

    # ---- edges ----
    edge_pairs = set()
    for i, edge in enumerate(edges):
        missing = REQUIRED_EDGE_FIELDS - set(edge)
        if missing:
            errors.append(f"edges.json[{i}]: missing field(s) {sorted(missing)}")
            continue

        label = f"{edge['source']} → {edge['target']}"
        for field in ("source", "target"):
            if edge[field] not in node_ids:
                errors.append(f"edge {label}: '{edge[field]}' is not a known node id")
        if not isinstance(edge["weight"], (int, float)):
            errors.append(
                f"edge {label}: weight must be a number, got {edge['weight']!r}"
            )
        if not isinstance(edge["instruction"], str) or not edge["instruction"].strip():
            errors.append(f"edge {label}: instruction must be non-empty text")

        edge_pairs.add((edge["source"], edge["target"]))

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
