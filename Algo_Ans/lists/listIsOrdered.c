
#include "list.h"

static bool listIsAscending(Node n);
static bool listIsDescending(Node n);

bool listIsOrdered(List l) {
	return listIsAscending(l->head) ||
	       listIsDescending(l->head);
}

static bool listIsAscending(Node n) {
	if (n == NULL || n->next == NULL) {
		return true;
	} else {
		return n->value <= n->next->value &&
			listIsAscending(n->next);
	}
}

static bool listIsDescending(Node n) {
	if (n == NULL || n->next == NULL) {
		return true;
	} else {
		return n->value >= n->next->value &&
			listIsDescending(n->next);
	}
}

