#include <stdio.h>
#include <stdlib.h>
#include "rock_bot.h"

#define ACTION_MOVE 0
#define ACTION_BUY  1
#define ACTION_SELL 2

void print_player_name(void);
void print_move(struct bot *b);
void get_action(struct bot *b, int *action, int *n);

// YOU SHOULD NOT NEED TO CHANGE THIS MAIN FUNCTION

int main(int argc, char *argv[]) {
    struct bot *me = rock_bot_input(stdin);
    if (me == NULL) {
        print_player_name();
    } else {
        print_move(me);
    }
    return 0;
}

void print_player_name(void) {
    // TODO: ADD YOUR BOT NAME HERE
    // This is displayed only in multiplayer games
    printf("Starter bot\n");
}

void print_move(struct bot *b) {
    int action;
    int n;
    get_action(b, &action, &n);
    if (action == ACTION_MOVE) {
        printf("Move ");
    } else if (action == ACTION_BUY) {
        printf("Buy ");
    } else if (action == ACTION_SELL) {
        printf("Sell ");
    } else {
        printf("Error\n");
    }
    printf("%d\n", n);
}

// TODO: Edit this function and add more
void get_action(struct bot *b, int *action, int *n) {
    *action = ACTION_MOVE;
    *n = 1;
}
