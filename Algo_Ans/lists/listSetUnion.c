
#include "list.h"

static void listPrepend(List l, int val);
static bool inList(List l, int val);

List listSetUnion(List s1, List s2) {
	List s3 = newList();
	
	for (Node curr = s1->head; curr != NULL; curr = curr->next) {
		listPrepend(s3, curr->value);
	}
	for (Node curr = s2->head; curr != NULL; curr = curr->next) {
		if (!inList(s3, curr->value)) {
			listPrepend(s3, curr->value);
		}
	}
	
	return s3;
}

static void listPrepend(List l, int val) {
	Node n = newNode(val);
	n->next = l->head;
	l->head = n;
}

static bool inList(List l, int val) {
	for (Node curr = l->head; curr != NULL; curr = curr->next) {
		if (curr->value == val) {
			return true;
		}
	}
	return false;
}

