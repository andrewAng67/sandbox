#   Written by Zac Partridge
#   This file outlines the basics of the world
#   There is no need to modify this file, but feel free to to change it however you like


class World():
    '''
        Object: WORLD

        The World hosts everything concerning the world, and the objects that are located on it.

        The functionality is as follows:
            -> A user-made bot makes calls to the world to see if their current location is a buyer, seller or petrol station.
                (This is done by check whether the merchant held within self.sellers, self.buyers and self.petrol_stations has the same
                    location (index) as the users location index).
            -> A user-made bot utilises the world restrictions to make choices and movement within a round.
                (i.e. takes into account fuel_capacity restrictions, bag_capacity restrictions, maximum_move and also turns_left).
    '''
    def __init__(self, text):
        self.fuel_capacity = int(text[0].split("=")[-1])
        self.bag_capacity = int(text[1].split("=")[-1])
        self.maximum_move = int(text[2].split("=")[-1])
        self.turns_left = 0
        self.locations = []
        self.sellers = []
        self.buyers = []
        self.petrol_stations = []
        self.bots = {}
        self.me = None

        text = text[3:]
        self.parse_locations(text)
        self.locs_by_name = {l.name: l for l in self.locations}
        self.parse_bots(text)
        if not self.me:
            self.me = list(self.bots.values())[0]

    def parse_bots(self, text):
        '''
            This method parses all bots that were passed from referee.py to the world, so that the World can keep a list of all bots currently active within the world
                within the self.bots method.

            Remember each bot has a seperate world generated for them, as we can only assign a singular bot to the 'self.me' attribute.
        '''
        for line in text:
            if line.startswith("*** Turn "):
                line = line.split()
                self.turns_left = int(line[4]) - int(line[2])
            elif line.startswith("*** You are"):
                self.me = self.bots[line.split('"')[1]]
            elif line.startswith('"'):
                line = line.split('"')
                name = line[1]
                loc = self.locs_by_name[line[3]]
                line = line[4].split()
                cash = int(line[1][1:-1])
                fuel_level = int(line[4].strip(","))
                b = Bot(name, loc, cash, fuel_level, self)
                line = " ".join(line[5:]).split(",")
                for item in line:
                    if not item:
                        break
                    item = item.split()
                    b.add_to_bag(item[3], int(item[0]))
                self.bots[name] = b

    def parse_locations(self, text):
        '''
            Parses and assigns locations within the world.

            Essentially this method sets up the buyers, sellers and petrol_stations that were generated randomly from
                the seed given to the world by referee.py. The referee generates the locations and parses them as text
                to this method as the attribute 'text'.
        '''
        for i, line in enumerate(text):
            if line.startswith('"'):
                break
            line = line.split(":")
            name = line[0]
            if line[1] == " other":
                self.locations.append(Location(i, name))
                continue
            line = line[1].split()
            rock = line[5]
            price = int(line[7].split("/")[0][1:])
            quantity = int(line[2])
            if quantity == 0:
                self.locations.append(Location(i, name))
            elif "Petrol" in line:
                l = Location(i, name, rock, price, quantity, petrol=True)
                self.locations.append(l)
                self.petrol_stations.append(l)
            elif "buy" in line:
                l = Location(i, name, rock, price, quantity, buyer=True)
                self.locations.append(l)
                self.buyers.append(l)
            elif "sell" in line:
                l = Location(i, name, rock, price, quantity, seller=True)
                self.locations.append(l)
                self.sellers.append(l)

class Location():
    '''
        Object: Location

        The location is an object that stores all the information pertaining to a certain spot within the world. For example, we might have a merchant at position X within the world,
            and another at position Y.

        The location is used to keep data and information pertaining to the current location. It holds data such as the merchant that occupies the location, the rock they are selling,
            the price that they are selling at, the quantity they hold/will-buy and a boolean value to say whether they are a buyer, seller or petrol_station.
    '''
    def __init__(self, index, name, rock=None, price=0, quantity=0, bots=None, seller=False, buyer=False, petrol=False):
        self.index = index
        self.name = name
        self.rock = rock
        self.price = price
        self.quantity = quantity
        if bots != None:
            self.bots = bots
        else:
            self.bots = []
        self.seller = seller
        self.buyer = buyer
        self.petrol = petrol

    def print(self):
        if self.buyer:
            print(f"{self.name}: will buy {self.quantity} kg of {self.rock} for ${self.price}/kg")
        elif self.seller:
            print(f"{self.name}: will sell {self.quantity} kg of {self.rock} for ${self.price}/kg")
        elif self.petrol:
            print(f"{self.name}: will sell {self.quantity} L of Petrol for ${self.price}/L")
        else:
            print(f"{self.name}: other")


class Bot():
    '''
        Remember, to run execution you type: python3 referee starter/bot.py -W <size>

        From this command, you're passing rockBot as a bot to the World which stores it as 'self.me'. When specifying your own bot, when you use this variable,
            it is pointing to this Bot() instance, to which you can use these base methods.

        You DO NOT need to overwrite these methods, but utilise them to communicate with the current location and other variables within the world.

        All logic for what the bot should buy and sell, should be written in the user-implemented file. The logic is pretty much all the user has to worry about.
    '''
    def __init__(self, name, location, cash, fuel_level, world):
        self.name = name
        self.location = location
        self.cash = cash
        self.fuel_level = fuel_level
        self.world = world
        self.bag = {}

    def add_to_bag(self, rock, num):
        '''
            When we buy a rock from a merchant we want to add that rock to our inventory.
            This method aims to add the rock to the bots inventory, as well as reducing our cash value.

            You need to use this function if you ONLY if you are simulating future rounds. For your
            first bot it is NOT recommended to use this function
        '''
        if rock in self.bag:
            self.bag[rock] += num
        else:
            self.bag[rock] = num
        self.cash -= num*self.location.price


    def remove_from_bag(self, rock, num):
        '''
            When we sell a rock to a merchant, we want to remove that rock from our inventory.
            This method aims to remove the rock from our inventory, and also increase our cash value.

            You need to use this function if you ONLY if you are simulating future rounds. For your
            first bot it is NOT recommended to use this function
        '''
        self.cash += num*self.location.price
        self.bag[rock] -= num
        assert(self.bag[rock] >= 0)
        if self.bag[rock] == 0:
            del self.bag[rock]

    def get_bag_weight(self):
        return sum(w for w in self.bag.values())

    def can_sell_at(self, location):
        return location.buyer and location.quantity > 0 and location.rock in self.bag

    def can_buy_at(self, location):
        return location.seller and location.quantity > 0 and self.cash > location.price and self.get_bag_weight() < self.world.bag_capacity

    def can_refuel_at(self, location):
        return location.petrol and location.quantity > 0 and self.cash > location.price and self.fuel_level < self.world.fuel_capacity

    def can_sell_here(self):
        return self.can_sell_at(self.location)

    def can_buy_here(self):
        return self.can_buy_at(self.location)

    def can_refuel_here(self):
        return self.can_refuel_at(self.location)

    def print(self):
        s = '"{}" is at "{}" with ${}, fuel level: {}'.format(
            self.name, self.location.name, self.cash, self.fuel_level)
        for rock in self.bag:
            s += ", {} kg of {}".format(self.bag[rock], rock)
        print(s)
