
#include "list.h"

static int listGetLargest(List l);
static void listDelete(List l, int val);

int listDeleteLargest(List l) {
	// find the maximum
	int max = listGetLargest(l);
	
	// then delete it
	listDelete(l, max);
	
	return max;
}

static int listGetLargest(List l) {
	int max = l->head->value;
	for (Node curr = l->head; curr != NULL; curr = curr->next) {
		if (curr->value > max) {
			max = curr->value;
		}
	}
	return max;
}

// deletes a value that is assumed to be in the list
static void listDelete(List l, int val) {
	Node prev = NULL;
	Node curr = l->head;
	while (curr->value != val) {
		prev = curr;
		curr = curr->next;
	}
	
	if (curr == l->head) {
		l->head = curr->next;
	} else {
		prev->next = curr->next;
	}
	free(curr);
}

