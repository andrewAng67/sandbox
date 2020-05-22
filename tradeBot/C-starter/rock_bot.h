// header guard: https://en.wikipedia.org/wiki/Include_guard
// This avoids errors if this file is included multiple times
// in a complex source file setup

#ifndef ROCK_BOT_H
#define ROCK_BOT_H

// These constants are upper bounds on various features of the Rock Bot world
// You may not need to use any of these constants in your program.

#define MAX_TURNS                         999
#define MAX_LOCATIONS                     2048
#define MAX_BOTS                          2048
#define MAX_ROCK_TYPES                    128
#define MAX_NAME_CHARS                    64
#define MAX_SUPPLIED_BOT_NAME_CHARS       32


// Description of the state of a single bot
//
//  name - unique string of between 1 and MAX_NAME_CHARS (does not change during simulation)
//
//  location - pointer to struct representing bot's current location, never NULL
//
//  cash - how much cash the bot has
//
//  fuel_level - how many L in the bot's fuel tank - reduces by 1 L for every location bot moves
//
//  rock - name of the rock bot is carrying (between 1 and MAX_NAME_CHARS)
//          note bots may only carry one type of rock at a time
//          NULL if the bot is not carrying rock
//
//  num_rocks - how many kg of rock the bot is carrying
//
//  turns_left - turns left in simulation, always > 0 (reduces by 1 every turn)
//
//  fuel_capacity - maximum L bot's fuel tank can hold
//
//  maximum_move - maximum number of location bot can move
//
//  bag_capacity - maximum kg of rock bot can carry
//
//  fuel_capacity, bag_capacity, maximum_move are the same for all bots
//  and do not change during the simulation.
//
//  name is different for every bot and does not change during the simulation

struct bot {
    char            *name;
    struct location *location;
    int             cash;
    int             fuel_level;
    struct bag      *bag;
    int             num_rocks;
    int             turns_left;
    int             fuel_capacity;
    int             maximum_move;
    int             bag_capacity;
};


struct bag {
    int             num_rocks;
    char            *rock;
    struct bag      *next;
};


// Description of a location in the rock bot world
//
//  name - unique string of between 1 and MAX_NAME_CHARS (never NULL)
//
//  rock - name of the rock this location buys/sells
//          string of between 1 and MAX_NAME_CHARS (never NULL)
//          if rock == "Anything" location buys any rock
//          rock == "Petrol" is a special case, bots can refuel by buying petrol
//          note some locations have rock == "Nothing" and price == 0 & quantity  == 0
//
//  price -  price at which this location sells/buys a kg of rock or, L of petrol
//           a positive price indicates this location only buys rock
//           a negative price indicates this location only sells rock or petrol
//           a price of zero indicates location does not buy or sell anything
//           price does not change during the simulation
//
//  quantity - a non-negative number indicating how many units of rock/petrol
//             this location currently has available to buy or sell
//             quantity never increases during the simulation
//             it reduces by n kg/L when a bot buy/sells n kg/L at this location
//
//  bots - pointer to a linked list of bots currently at this location (NULL if no bots at this location)
//
//
//  left - pointer to struct representing next location left, never NULL
//         The left fields of locations link them in a circular list
//
//  right - pointer to struct representing next location right, never NULL
//         The right fields of locations link them in a circular list
//         but in the reverse direction to left fields.
//

struct location {
    char                *name;
    char                *rock;
    int                 price;
    int                 quantity;
    struct location     *left;
    struct location     *right;
    struct bot_list     *bots;
};



// linked list of bots
//
// bot - pointer to a struct representing a bot
//
// next - points to remainder of list
//        next is NULL if there are no more bots in list

struct bot_list {
    struct bot      *bot;
    struct bot_list *next;
};


struct bot *rock_bot_input(FILE *stream);

#endif
