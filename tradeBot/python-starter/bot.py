#!/usr/local/bin/python3

import sys
from classes import World

text = sys.stdin.read().split("\n")[:-1]
if not text:
    # ADD YOUR BOT NAME HERE
    # This is displayed only in multiplayer games
    print("Starter bot")
    exit(0)

world = World(text)
me = world.me

# # # # # YOUR CODE GOES HERE # # # #
if me.can_buy_here():
    action = "Buy 10"
elif me.can_sell_here():
    action = "Sell 10"
else:
    action = "Move 1"
# # # # # # # # # # # # # # # # # # #

print(action)
