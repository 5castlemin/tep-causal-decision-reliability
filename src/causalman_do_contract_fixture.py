"""Independent graph fixture; not an upstream patch or CausalMan execution."""
def remove_incoming_for_fixture(graph, node):
    result = graph.copy()
    result.remove_edges_from(list(graph.in_edges(node)))
    return result
