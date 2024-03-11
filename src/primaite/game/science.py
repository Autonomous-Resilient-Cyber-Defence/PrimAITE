from random import random
from typing import Any, Iterable, Mapping


def simulate_trial(p_of_success: float) -> bool:
    """
    Simulates the outcome of a single trial in a Bernoulli process.

    This function returns True with a probability 'p_of_success', simulating a success outcome in a single
    trial of a Bernoulli process. When this function is executed multiple times, the set of outcomes follows
    a binomial distribution. This is useful in scenarios where one needs to model or simulate events that
    have two possible outcomes (success or failure) with a fixed probability of success.

    :param p_of_success: The probability of success in a single trial, ranging from 0 to 1.
    :returns: True if the trial is successful (with probability 'p_of_success'); otherwise, False.
    """
    return random() < p_of_success


def graph_has_cycle(graph: Mapping[Any, Iterable[Any]]) -> bool:
    """Detect cycles in a directed graph.

    Provide the graph as a dictionary that describes which nodes are linked. For example:
    {0: {1,2}, 1:{2,3}, 3:{0}}    here there's a cycle 0 -> 1 -> 3 -> 0
    {'a': ('b','c'), c:('b')}     here there is no cycle

    :param graph: a mapping from node to a set of nodes to which it is connected.
    :type graph: Mapping[Any, Iterable[Any]]
    :return: Whether the graph has any cycles
    :rtype: bool
    """
    visited = set()
    currently_visiting = set()

    def depth_first_search(node: Any) -> bool:
        """Perform depth-first search (DFS) traversal to detect cycles starting from a given node."""
        if node in currently_visiting:
            return True  # Cycle detected
        if node in visited:
            return False  # Already visited, no need to explore further

        visited.add(node)
        currently_visiting.add(node)

        for neighbour in graph.get(node, []):
            if depth_first_search(neighbour):
                return True  # Cycle detected

        currently_visiting.remove(node)
        return False

    # Start DFS traversal from each node
    for node in graph:
        if depth_first_search(node):
            return True  # Cycle detected

    return False  # No cycles found


def topological_sort(graph: Mapping[Any, Iterable[Any]]) -> Iterable[Any]:
    """
    Perform topological sorting on a directed graph.

    This guarantees that if there's a directed edge from node A to node B, then A appears before B.

    :param graph: A dictionary representing the directed graph, where keys are node identifiers
                  and values are lists of outgoing edges from each node.
    :type graph: dict[int, list[Any]]

    :return: A topologically sorted list of node identifiers.
    :rtype: list[Any]
    """
    visited: set[Any] = set()
    stack: list[Any] = []

    def dfs(node: Any) -> None:
        """
        Depth-first search traversal to visit nodes and their neighbors.

        :param node: The current node to visit.
        :type node: Any
        """
        if node in visited:
            return
        visited.add(node)
        for neighbour in graph.get(node, []):
            dfs(neighbour)
        stack.append(node)

    # Perform DFS traversal from each node
    for node in graph:
        dfs(node)

    # Reverse the stack and return it.
    return stack[::-1]
