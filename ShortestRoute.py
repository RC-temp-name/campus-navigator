import networkx as nx
def shortest_route(graph, start, end):
    try:
        return nx.shortest_path(graph, source=start, target=end)
    except nx.NetworkXNoPath:
        return None