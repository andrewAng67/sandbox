
#include "list.h"

// More concise
int listDeleteLargest(List l) {
	// Find max
	Node max = l->head;
	for (Node curr = l->head; curr != NULL; curr = curr->next) {
		if (curr->value > max->value) {
			max = curr;
		}
	}
	int largest = max->value;
	
	// Delete it
	if (max == l->head) {
		l->head = l->head->next;
	} else {
		Node prev = l->head;
		while (prev->next != max) {
			prev = prev->next;
		}
		prev->next = prev->next->next;
	}
	free(max);
	
	return largest;
}

