
#include <stdlib.h>

#include "tree.h"

static int treeSize(Tree t);

bool TreeIsPerfectlyBalanced(Tree t) {
	if (t == NULL) {
		return true;
	}
	
	int l = treeSize(t->left);
	int r = treeSize(t->right);
	if (l - r > 1 || r - l > 1) {
		return false;
	} else {
		return TreeIsPerfectlyBalanced(t->left) &&
		       TreeIsPerfectlyBalanced(t->right);
	}
}

static int treeSize(Tree t) {
	if (t == NULL) {
		return 0;
	} else {
		return 1 + treeSize(t->left) + treeSize(t->right);
	}
}

