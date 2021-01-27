
#include "list.h"

bool listIsPalindromic(List l) {
	Node curr1 = l->first;
	Node curr2 = l->last;
	while (curr1 != NULL) {
		if (curr1->value != curr2->value) {
			return false;
		}
		curr1 = curr1->next;
		curr2 = curr2->prev;
	}
	return true;
}

