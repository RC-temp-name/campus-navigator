import json
import networkx as nx

# Distance + Weight Computation

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def compute_weight(edge_type, src_coords, tgt_coords, preference):
    base = manhattan(src_coords, tgt_coords)

    # Hallways distance
    if edge_type == "hallway":
        return base

    # Stairs vs elevator preference logic
    if edge_type == "stairs":
        return base if preference == "stairs" else base + 500

    if edge_type == "elevator":
        return base if preference == "elevator" else base + 500

    # Default fallback
    return base


# Graph Loader

def load_building_graph(nodes_file, edges_file, preference="elevator"):
    """
   loads a building graph from JSON files, 
   computing edge weights based on type and 
   user preference
    """

    # Load nodes
    with open(nodes_file) as f:
        nodes = json.load(f)

    # Load edges
    with open(edges_file) as f:
        edges = json.load(f)

    # Create graph
    G = nx.MultiDiGraph()

    # Add nodes
    for node in nodes:
        G.add_node(node["id"], **node)

    # Add edges with computed weights
    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        src_coords = G.nodes[src]["coords"]
        tgt_coords = G.nodes[tgt]["coords"]

        edge_type = edge.get("type", "hallway")
        weight = compute_weight(edge_type, src_coords, tgt_coords, preference)

        G.add_edge(src, tgt, weight=weight, **edge)

    return G

def main():
    # Example usage
    graph = load_building_graph("data/nodes.json", "data/edges.json", preference="elevator")
    print("Graph loaded with {} nodes and {} edges".format(graph.number_of_nodes(), graph.number_of_edges()))

if __name__ == "__main__":
    main()