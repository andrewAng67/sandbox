
#include <stdio.h>
#include <stdlib.h>

#include "Graph.h"
#include "Queue.h"

void breadthFirstSearch(Graph g, int src) {
	int *visited = calloc(GraphNumVertices(g), sizeof(int));
	visited[src] = 1;
	
	Queue q = QueueNew();
	QueueEnqueue(q, src);
	
	while (!QueueIsEmpty(q)) {
		Vertex v = QueueDequeue(q);
		printf("%d ", v);
		for (Vertex w = 0; w < GraphNumVertices(g); w++) {
			if (GraphIsAdjacent(g, v, w) && !visited[w]) {
				QueueEnqueue(q, w);
				visited[w] = 1;
			}
		}
	}
	
	QueueFree(q);
	free(visited);
}

