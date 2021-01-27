
#include <stdio.h>
#include <stdlib.h>

#include "Graph.h"

static int doNumReachable(Graph g, int v, int *visited);

int numReachable(Graph g, int src) {
	int *visited = calloc(GraphNumVertices(g), sizeof(int));
	int result = doNumReachable(g, src, visited);
	free(visited);
	return result;
}

static int doNumReachable(Graph g, int v, int *visited) {
	visited[v] = 1;
	int result = 1;
	for (int w = 0; w < GraphNumVertices(g); w++) {
		if (GraphIsAdjacent(g, v, w) && !visited[w]) {
			result += doNumReachable(g, w, visited);
		}
	}
	return result;
}

