# Rules

RockBot is a game where you must successfully buy, sell, and transport
different types of rocks within a virtual world.

Each world is generated through a varying seed, to ensure that the
worlds are random. Within each world there are varying merchants
that the user (or bot) is able to buy goods off, or sell to.

Within the world, the player has a limited number of turns.
The only goal that the player has is to have as much cash as
possible after the last turn.

Each turn, a bot is given a description of the world, and is asked to make a
single action. A bot makes money by buying a rock at one location and
selling it at another location at a higher price.

A bot must move to a location before it can buy or sell from that location.

## Differences from traderbot
Communication with the referee is done through stdin, stdout. There is no dump,
but instead there are recycling locations that will buy anything cheaply.
There are no longer location types but instead it is possible to work out if the
location is a buyer or seller based on if their price is positive or negative.
Also there have been variable name changes to fit better with
trading rocks, check rock_bot.h for more information.

## Differences from fruitbot
It is possible to hold multiple types items at once. This means that if you
are using your old C code, the structs will have changed to be able to hold
multiple types. Also there have been variable name changes to fit better with
trading rocks, check rock_bot.h for more information.


# Writing a bot

Currently bots can only be submitted in C or python3. If you played one of the
original traderbot or fruitbot games, this should be similar and you should be
able to modify your old code to get it working here (as long as your first
year code is readable). If you didn't I would recommend using the supplied
python starter bot as it does more of the basics for you already and will
probably be a lot easier. There is no need to use any of these provided
files, they just do the tedious input parsing and setup for you but if you
want to throw this away and start from scratch feel free (not recommended).
It just needs to be able to pass the submission test.

Instead of the 10 seconds that was available per bot the original assignment,
rock bots are only allowed to use up to 0.2 seconds per turn. If your bot
does not finish within that time, it will be disqualified from the rest of
the current game. But as the bots are now compiled using `gcc -O3`, instead of
`dcc --valgrind`, they should be able to perform a similar number of calculations.

For your testing purposes only, there is a modified version of
Andrew Taylors's fruitbot referee included here.

To test the starter bots:
```
python3 referee.py python-starter/bot.py
```
OR
```
cd C-starter
gcc *.c -o bot
cd ..
python3 referee.py C-starter/bot
```

Also checkout some of the flags that you can pass to the referee:
-w, -W, -s, ...:
```
python3 referee.py python-starter/bot.py -W 50 -s 1234
```

If you get an **error message** like this
```
No such file or directory: '/path/to/file/python-starter/bot.py': '/path/to/file/python-starter/bot.py'
```

This means that you probably need to change the #! line at the top of `bot.py`
to the location that python3 is installed on your computer

## Guid to using the python starter

It is recommended that you use `classes.py` as it is to parse the input and maybe
you just add a few more methods if you want. Most of your code could be written
in `bot.py`.

The files that you are to upload should stipulate the conditions on when to
buy/sell rocks within the world, and also should contain the algorithm used
to maximise the profits of the bot.

Rather than implement your own version of `classes.py`, you should
can extend this with your own functionality. The
class 'BOT' is shrouded in the world, and as such can be used to see
whether a bot can 'sell' at a particular location (i.e. method
bot.can_sell_here() and bot.can_sell_at(location)), or buy at a
particular location (i.e. method bot.can_buy_here() and
bot.can_buy_at(location)).


## What to upload
For a C bot, you need to upload all .c and .h files that you use, i.e. `input_parser.c`, `main.c`, `rock_bot.h`

For a python bot, you need to upload all your python files, i.e. `bot.py`, `classes.py`
