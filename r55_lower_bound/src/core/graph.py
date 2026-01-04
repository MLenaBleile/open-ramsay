"""
Graph representation for Ramsey coloring problems.

Design decisions:
- Use numpy boolean arrays for efficiency (edge color: False=red, True=blue)
- Symmetric matrix representation (upper triangular stored)
- Support both dense (small n) and sparse representations

For K_n, we store n(n-1)/2 edge colors in a flat boolean array.
Edge (i,j) with i < j is at position: i * n - i * (i + 1) // 2 + j - i - 1
"""

from __future__ import annotations
import numpy as np
from typing import Optional
import csv
import json

from .utils import edge_index, vertex_pair, num_edges


class RamseyGraph:
    """
    A 2-colored complete graph for Ramsey number problems.

    Edges are colored either red (False) or blue (True).
    The coloring is stored as a flat boolean array for efficiency.

    Attributes:
        n: Number of vertices
        edges: Boolean array of edge colors (False=red, True=blue)
    """

    def __init__(self, n: int, edges: Optional[np.ndarray] = None):
        """
        Initialize a Ramsey graph.

        Args:
            n: Number of vertices (must be >= 2)
            edges: Optional edge colors. If None, all edges are red (False).
        """
        if n < 2:
            raise ValueError(f"Graph must have at least 2 vertices, got {n}")

        self.n = n
        self._num_edges = num_edges(n)

        if edges is None:
            self.edges = np.zeros(self._num_edges, dtype=bool)
        else:
            if len(edges) != self._num_edges:
                raise ValueError(
                    f"Expected {self._num_edges} edges for K_{n}, got {len(edges)}"
                )
            self.edges = np.asarray(edges, dtype=bool).copy()

    def _edge_idx(self, i: int, j: int) -> int:
        """Get the index for edge (i, j) in the flat array."""
        if i == j:
            raise ValueError(f"No self-loops: i={i}, j={j}")
        if i < 0 or j < 0 or i >= self.n or j >= self.n:
            raise ValueError(f"Vertices out of range: i={i}, j={j}, n={self.n}")
        return edge_index(i, j, self.n)

    def get_edge(self, i: int, j: int) -> bool:
        """
        Get the color of edge (i, j).

        Args:
            i: First vertex
            j: Second vertex

        Returns:
            False for red, True for blue
        """
        return bool(self.edges[self._edge_idx(i, j)])

    def set_edge(self, i: int, j: int, color: bool) -> None:
        """
        Set the color of edge (i, j).

        Args:
            i: First vertex
            j: Second vertex
            color: False for red, True for blue
        """
        self.edges[self._edge_idx(i, j)] = color

    def flip_edge(self, i: int, j: int) -> None:
        """Flip the color of edge (i, j)."""
        idx = self._edge_idx(i, j)
        self.edges[idx] = not self.edges[idx]

    def to_matrix(self) -> np.ndarray:
        """
        Convert to full symmetric adjacency matrix.

        Returns:
            n x n boolean matrix where M[i,j] = edge color (False=red, True=blue)
        """
        matrix = np.zeros((self.n, self.n), dtype=bool)
        for idx in range(self._num_edges):
            i, j = vertex_pair(idx, self.n)
            color = self.edges[idx]
            matrix[i, j] = color
            matrix[j, i] = color
        return matrix

    @classmethod
    def from_matrix(cls, matrix: np.ndarray) -> RamseyGraph:
        """
        Create a RamseyGraph from a symmetric adjacency matrix.

        Args:
            matrix: n x n boolean matrix (should be symmetric)

        Returns:
            RamseyGraph with the corresponding coloring
        """
        n = matrix.shape[0]
        if matrix.shape != (n, n):
            raise ValueError(f"Matrix must be square, got shape {matrix.shape}")

        graph = cls(n)
        for i in range(n):
            for j in range(i + 1, n):
                graph.set_edge(i, j, bool(matrix[i, j]))
        return graph

    def to_csv(self, filepath: str) -> None:
        """
        Export coloring to CSV file.

        Format: Each row is "i,j,color" where color is 0 (red) or 1 (blue).
        Only upper triangular entries (i < j) are stored.

        Args:
            filepath: Path to output CSV file
        """
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['i', 'j', 'color'])
            for idx in range(self._num_edges):
                i, j = vertex_pair(idx, self.n)
                color = int(self.edges[idx])
                writer.writerow([i, j, color])

    @classmethod
    def from_csv(cls, filepath: str) -> RamseyGraph:
        """
        Import coloring from CSV file.

        Args:
            filepath: Path to input CSV file

        Returns:
            RamseyGraph with the loaded coloring
        """
        edges_dict = {}
        max_vertex = 0

        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                i, j = int(row['i']), int(row['j'])
                color = bool(int(row['color']))
                if i > j:
                    i, j = j, i
                edges_dict[(i, j)] = color
                max_vertex = max(max_vertex, i, j)

        n = max_vertex + 1
        graph = cls(n)
        for (i, j), color in edges_dict.items():
            graph.set_edge(i, j, color)
        return graph

    def to_json(self, filepath: str) -> None:
        """
        Export coloring to JSON file.

        Args:
            filepath: Path to output JSON file
        """
        data = {
            'n': self.n,
            'edges': self.edges.tolist()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

    @classmethod
    def from_json(cls, filepath: str) -> RamseyGraph:
        """
        Import coloring from JSON file.

        Args:
            filepath: Path to input JSON file

        Returns:
            RamseyGraph with the loaded coloring
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data['n'], np.array(data['edges'], dtype=bool))

    def copy(self) -> RamseyGraph:
        """Create a deep copy of this graph."""
        return RamseyGraph(self.n, self.edges.copy())

    def red_degree(self, v: int) -> int:
        """Count the number of red edges incident to vertex v."""
        count = 0
        for u in range(self.n):
            if u != v and not self.get_edge(v, u):
                count += 1
        return count

    def blue_degree(self, v: int) -> int:
        """Count the number of blue edges incident to vertex v."""
        count = 0
        for u in range(self.n):
            if u != v and self.get_edge(v, u):
                count += 1
        return count

    def count_red_edges(self) -> int:
        """Return the total number of red edges."""
        return int(np.sum(~self.edges))

    def count_blue_edges(self) -> int:
        """Return the total number of blue edges."""
        return int(np.sum(self.edges))

    def complement(self) -> RamseyGraph:
        """Return a new graph with all edge colors flipped."""
        return RamseyGraph(self.n, ~self.edges)

    def __eq__(self, other: object) -> bool:
        """Check if two graphs have the same coloring."""
        if not isinstance(other, RamseyGraph):
            return NotImplemented
        return self.n == other.n and np.array_equal(self.edges, other.edges)

    def __repr__(self) -> str:
        red = self.count_red_edges()
        blue = self.count_blue_edges()
        return f"RamseyGraph(n={self.n}, red={red}, blue={blue})"
