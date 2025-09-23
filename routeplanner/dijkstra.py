import heapq

def dijkstra(graph, start, end, pollution, green_cover):
    """
    graph        : dictionary -> { 'A': {'B': distance, 'C': distance}, ... }
    start, end   : source & destination city names
    pollution    : dictionary -> { 'A': 10, 'B': 20, ... }
    green_cover  : dictionary -> { 'A': 5, 'B': 8, ... }
    """

    # Priority Queue → (-eco_cost, current_node, path)
    pq = [(0, start, [start])]
    visited = set()

    while pq:
        neg_eco_cost, node, path = heapq.heappop(pq)
        eco_cost = -neg_eco_cost  # convert back to positive

        if node in visited:
            continue
        visited.add(node)

        # ✅ If destination reached → return result
        if node == end:
            return {
                "path": path,
                "eco_cost": round(eco_cost, 2)
            }

        # Traverse neighbours
        for neighbor in graph.get(node, {}):
            if neighbor not in visited:
                # ✅ Eco-cost formula
                cost = (
                    green_cover.get(neighbor, 0) * 0.4   # benefit
                    - pollution.get(neighbor, 0) * 0.3   # penalty
                )

                # Push with negative cost for max-heap behavior
                heapq.heappush(
                    pq, (-(eco_cost + cost), neighbor, path + [neighbor])
                )

    # ❌ No path found
    return {
        "path": [],
        "eco_cost": float("-inf")
    }
