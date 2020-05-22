# Originally by Andrew Taylor for the fruit_bot competition in comp1511 18s1
# Modified by Zac Partridge for user testing in the rockBot competition
# Version 1.2 changed name back to user suppllied bot name
# Version 1.1 - modified world size/rock generation, and added runtime resource limits
# Version 1.0

import argparse,atexit, bz2, codecs, glob, io, math, os, pickle, random, re, shutil, subprocess, sys, tempfile, time, zipfile, json, resource


def limitations():
    max_mem = 100 * 1024 * 1024 # 100 MB
    resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))

def run_with_resource_limits(*args, **kwargs):
    try:
        p = subprocess.run(*args, timeout=0.2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, preexec_fn=limitations, **kwargs)
    except subprocess.TimeoutExpired:
        return b"", b"", 1
    return (p.stdout, p.stderr, p.returncode)

try:
    from termcolor import colored as termcolor_colored
except ImportError:
    termcolor_colored = lambda x, *args, **kwargs: x


MAX_SUPPLIED_BOT_NAME_CHARS = 32
MAX_NAME_CHARS = 64
VERSION = 0.14

def main(run_in_parallel=False):
    global args
    args = args_parser()
    if run_in_parallel:
        args.tournament = True
    if args.tournament:
        args.output_html = True
        args.show_bot_stdout = False
        args.show_reproduce_command = False
        args.save_world_each_turn = True
        args.world_size = max(len(args.source_files), args.n_bots)
        args.dump_pickle_files = True
        args.bzip_files = True
    if not args.quiet:
        print('Version:', VERSION)

    global colored
    if args.colorize:
        colored = termcolor_colored
        os.environ['DCC_COLORIZE_OUTPUT'] = 'true'
    else:
        colored = lambda x, *args, **kwargs: x

    set_environment()
    print('seeding with', args.seed)
    random.seed(args.seed)
    if args.compiler == 'dcc':
        for compiler in "dcc clang gcc".split():
            if search_path(compiler):
                args.compiler = compiler
                break

    if args.compiler != 'dcc':
        args.valgrind = False

    if args.world_file:
        try:
            (parameters, locations) = read_world(args.world_file)
        except OSError as e:
            print("Can not open world file '{}': {}".format(args.world_file, e), file=sys.stderr)
            sys.exit(1)
    elif args.world_size:
        (parameters, locations) = parse_world(scaled_world(args.world_size))
    else:
        (parameters, locations) = parse_world(world_descriptions[args.world])

    if args.print_world:
        (parameters, locations) = randomize_world(parameters, locations, args.n_bots)
        print(locations2string(locations))
        return 0
    if args.print_html:
        (parameters, locations) = randomize_world(parameters, locations, args.n_bots)
        print(locations2table(locations))
        return 0

    binaries = compile_bots(args)
    if not binaries and not args.interactive_player:
        return 1

    n_bots = max(len(binaries), args.n_bots) if binaries else 0
    (parameters, locations) = randomize_world(parameters, locations, n_bots)
    for name_value in args.parameter:
        (name,value) = name_value.split('=')
        parameters[name] = int(value)
    bots = []
    for b in range(n_bots):
        binary = binaries[b % len(binaries)]
        get_action = lambda world, bot, binary=binary: run_get_action(world, bot, binary, show_bot_stdout=args.show_bot_stdout)
        bots.append(create_bot(run_get_bot_name(binary), get_action, parameters, locations, binary=binary))

    if args.interactive_player:
        bots.append(create_bot("Interactive Player", interactive_player, parameters, locations))

    sanitize_bots(bots)

    if run_in_parallel:
        return (locations, bots, parameters, binaries, args)

    run_world(locations, bots, parameters, args)
    print()
    if args.print_rerun_command:
        print('You can rerun this game with this command:')
        print(rerun_command())
        print()
    return 0

def args_parser():
    assignment_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--compiler", default="gcc", help="compiler for C source files")
    parser.add_argument("--json", action="store_true", default=False, help="print world description as json each round")
    parser.add_argument("-w", "--world", choices=sorted(world_descriptions.keys()), default='tiny', help="world to run simulation in")
    parser.add_argument("-f", "--world_file", help="world description")
    parser.add_argument("--no_valgrind", action="store_false", dest="valgrind", default=True, help="don't also run binary with valgrind to check for uninitialized variables")
    parser.add_argument("-n", "--n_bots", type=int, default=1, help="how many instance of bot to run")
    parser.add_argument("-p", "--parameter", action="append", default=[], help="set parameter (name=value)")
    parser.add_argument("-s", "--seed", type=int, default=random.getrandbits(24), help="random number generator seed")
    parser.add_argument("-S", "--source_directory", default=assignment_dir, help="directory where rock_bot.h and read_world.c live")
    parser.add_argument("-i", "--interactive_player", action="store_true", default=False, help="add an interactive_player"
    )
    parser.add_argument("-t", "--save_world_each_turn", action="store_true", default=False, help="save the world to a file named world_turn<n>.txt each turn")
    parser.add_argument("-W", "--world_size", type=int, help="generate world scaled to suit n bots")

    parser.add_argument("-d", "--debug", action="count", default=0,  help="show refere debugging information")
    parser.add_argument("--colorize", action="store_true", default=sys.stdout.isatty(), help="colorize output")
    parser.add_argument("--no_colorize", action="store_false", dest="colorize",  help="do not colorize output")

    parser.add_argument("--upload_url", default='https://cgi.cse.unsw.edu.au/~cs1511/18s1/cgi/autotest_upload.cgi', help="URL for upload of results")
    parser.add_argument("--upload_max_bytes", default=2048000, type=int, help="MAX bytes in upload of results")
    parser.add_argument("--no_print_rerun_command", action="store_false", dest="print_rerun_command", default=True, help="don't print rerun command")
    parser.add_argument("--quiet", action="store_true", default=False, help="don't print any output during simulation")
#   parser.add_argument("--print_summary", action="store_true", default=False, help="print an easily-parsable summary at the end of simulation")
    parser.add_argument("--tournament", action="store_true", default=False, help="make output suitable for a tournament")
    parser.add_argument("--dump_pickle_files", action="store_true", default=False, help="dump cash & bot names to pickle files after game")
    parser.add_argument("--bzip_files", action="store_true", default=False, help="bzip output files")
    parser.add_argument("--output_html", action="store_true", dest="output_html", default=False, help="output_html")
    parser.add_argument("--print_html", action="store_true", help="print world as HTML table")
    parser.add_argument("--no_show_bot_stdout", action="store_false", dest="show_bot_stdout", default=True, help="show test input")
    parser.add_argument("--print_world", action="store_true", help="print world")
    parser.add_argument("--no_print_changes", action="store_false", help="don't print changes")
    parser.add_argument("--no_show_reproduce_command", action="store_false", dest="show_reproduce_command", default=True, help="don't show reproduce command")
    parser.add_argument("source_files",  nargs='*', default=[], help="")
    return parser.parse_args()

def rerun_command(extra=[]):
    if '-s' in sys.argv or '--seed' in  sys.argv:
        rerun_args = sys.argv[1:]
    else:
        rerun_args = ['-s', str(args.seed)] + sys.argv[1:]
    rerun_args = sys.argv[:1] + extra + rerun_args
    return ' '.join(rerun_args)

def interactive_player(bot_world, bot):
    print(bot2string(bot))
    action = input('Enter action for ' + bot['name']+': ').strip()
    print()
    m = re.match(r'^\s*(move|buy|sell)\s*(-?\d+)\s*$', action, re.I)
    if m:
        return m.group(1).lower(), int(m.group(2))
    if action:
        print('Illegal action:',  colored(action, 'red'))
        print('Action must be move, buy or sell followed by an integer')
    return interactive_player(bot_world, bot)

def get_bot_actions(bots, world_state, turn):
    remaining_bots = []
    for bot in bots:
        if not bot['disqualified']:
            bot_world_state = world_state + '*** You are "{}"\n'.format(bot['name'])
            (bot['action'], bot['requested_n']) = bot['get_action'](bot_world_state, bot)
            if bot['action']:
                remaining_bots.append(bot)
            else:
                bot['disqualified'] = True
    return remaining_bots

def run_world(locations, bots, parameters, args, get_bot_actions=get_bot_actions):
    if args.output_html:
        print('<h3>Rock Bot Parameters</h3>\n<pre>')
    else:
        print(colored('*** Rock Bot Parameters ***', 'yellow'))
    print(parameters2string(parameters))
    for bot in bots:
        locations[0]['bots'][bot['name']] = bot
    active_bots = bots
    old_locations_description = ""
    for turn in range(parameters['turns_left']):
        if not active_bots:
            break
        if args.output_html:
            world_file = "{}.html".format(turn)
            print('<br><b>Turn {}</b>: <a href="{}">state of the world before turn</a>\n'.format(turn, world_file))
            if args.bzip_files:
                with bz2.open(world_file+'.bz2', "wt") as f:
                    print(locations2table(locations), file=f)
            else:
                with open(world_file, "w") as f:
                    print(locations2table(locations), file=f)
        else:
            print(colored('*** Turn {} of {} *** ***'.format(turn+1, parameters['turns_left']), 'yellow'))
            print()
            if args.no_print_changes:
                locations_description = locations2string(locations)
                if locations_description != old_locations_description:
                    print(locations_description)
                    old_locations_description = locations_description
        sys.stdout.flush()

        turns_left = parameters['turns_left'] - turn
        for bot in active_bots:
            bot['turns_left'] = turns_left

        world_state = parameters2string(parameters) + locations2string(locations, colorize=False) + bots2string(bots) + '*** Turn {} of {} ***\n'.format(parameters['turns_left'] - turns_left + 1, parameters['turns_left'])
        if args.save_world_each_turn:
            turn_file = "world_turn_{}".format(turn)
            if args.output_html:
                print(' <a href="reproduce/{}">instructions to rerun your bot with the input for this turn</a>\n'.format(turn_file))
            if args.bzip_files:
                with bz2.open(turn_file+'.txt.bz2',"wt") as f:
                    f.write(world_state)
            else:
                with open(turn_file+'.txt',"w") as f:
                    f.write(world_state)
        active_bots = get_bot_actions(bots, world_state, turn)

        for bot in active_bots:
            bot['n'] = sanitize_action(bot, bot['action'], bot['requested_n'])

        for location in locations:
            arbitrate_sales(location)
        if args.output_html:
            print('<table class="table table-striped table-condensed">')
            for bot in sorted(active_bots, key=lambda x:x['name'].lower().strip()):
                actual_n = '' if bot['n'] == bot['requested_n'] else '(reduced to <b>{}</b>)'.format(bot['n'])
                print("<tr><td>{}: action=<b>{}</b> {}".format(bot2string(bot), action2str(bot['action'], bot['requested_n']), actual_n))
            print('</table>')
        else:
            for bot in sorted(active_bots, key=lambda x:x['name'].lower().strip()):
                actual_n = '' if bot['n'] == bot['requested_n'] else colored('(reduced to {})'.format(bot['n']), 'red')
                print(bot2string(bot)+':', 'action =', colored(action2str(bot['action'], bot['requested_n']), 'green'), actual_n)
            print()
        for bot in active_bots:
            implement_action(bot, bot['action'], bot['n'], locations)
        if args.json:
            # will eventually be posting this, not just printing
            for b in bots:
                print(get_bot_json(locations, b))
    if args.output_html:
        print('<h3>Simulation Over - Bots in Profit Order</h3>')
        print(bots2table_postgame(sorted(bots, key=lambda x:-x['cash'])))
    else:
        print(colored('*** Simulation Over ***', 'yellow'))
        print()
        for bot in sorted(bots, key=lambda x:x['cash']):
            print(bot2string(bot), 'profit =', end=' ')
            profit = bot['cash'] - parameters['cash']
            if profit >= 0:
                print(colored('$'+str(profit), 'green'))
            else:
                print(colored('-$'+str(-profit), 'red'))
    if args.dump_pickle_files:
        cash = {}
        bot_name = {}
        for bot in bots:
            m = re.search(r'(\d{7})', bot['binary'])
            if m:
                zid = m.group(1)
                cash[zid] = bot['cash'] - parameters['cash']
                bot_name[zid] = bot['name']
        with open("cash.pkl", "wb") as f:
            pickle.dump(cash, f)
        with open("bot_name.pkl", "wb") as f:
            pickle.dump(bot_name, f)

def get_bot_json(locations, bot):
    return json.dumps({
        "fuel": bot['fuel_level'],
        "items": [
            {
                "name": name,
                "quantity": bot['bag'][name]
            } for name in bot['bag']
        ],
        "current_location": bot['location']['index'],
        "locations": [
            {
                "name": l['name'],
                "item": l['rock'],
                "quantity": l['quantity'],
                "buy_here": l['price'] < 0,
                "sell_here": l['price'] > 0,
                "num_players": len(l['bots']),
            } for l in locations
        ]
    })

def simple_get_action(locations, bots, bot):
    location = bot['location']
    if location['rock'] == 'Petrol' and location['quantity'] and bot['fuel_level'] < bot['fuel_capacity']:
        action = 'buy'
        n = bot['fuel_capacity'] - bot['fuel_level']
    elif location['rock'] == 'Anything' and bot['num_rocks']:
        action = 'sell'
        n = bot['num_rocks']
    elif location['price'] > 0 and location['rock'] and bot['bag'] and location['rock'] in bot['bag']:
        action = 'sell'
        n = bot['num_rocks']
    elif location['price'] < 0 and location['quantity'] and not bot['num_rocks']:
        action = 'buy'
        n = location['quantity']
    else:
        action = 'move'
        n = random.randrange(1, bot['maximum_move'] + 1)
    return (action, n)


def sanitize_action(bot, action, n):
    location = bot['location']
    rock = location['rock']
    if action == 'move':
        max_distance = min(bot['maximum_move'], bot['fuel_level'])
        n = max(min(max_distance, n), -max_distance)
    elif action == 'buy':
        n = max(0, n)
        price = -location['price']
        if price <= 0:
            n = 0
        elif rock == 'Petrol':
            n = min(n, location['quantity'], bot['fuel_capacity'] - bot['fuel_level'], bot['cash']/price)
        else:
            available_weight = bot['bag_capacity'] -  bot['num_rocks']
            n = min(n, location['quantity'], bot['cash']/price, available_weight)
        assert(n >= 0)
    elif action == 'sell':
        n = max(0, n)
        if location['price'] > 0 and (rock in bot['bag'] or rock == "Anything"):
            if rock == "Anything":
                n = min(n, location['quantity'], bot['num_rocks'])
            else:
                n = min(n, location['quantity'], bot['bag'][rock])
        else:
            n = 0
        assert(n >= 0)
    return int(n)

def implement_action(bot, action, n, locations):
    loc = bot['location']
    if action == 'move':
        del loc['bots'][bot['name']]
        bot['location'] = locations[(loc['index'] + n) % len(locations)]
        bot['location']['bots'][bot['name']] = bot
        bot['fuel_level'] -= abs(n)
        assert(bot['fuel_level'] >= 0)
    elif action == 'buy' and loc['rock'] == 'Petrol' and n:
        bot['location']['quantity'] -= n
        bot['cash'] += loc['price'] * n
        bot['fuel_level'] += n
        assert(bot['cash'] >= 0)
        assert(bot['fuel_level'] <= bot['fuel_capacity'] )
    elif action == 'buy' and n:
        bot['location']['quantity'] -= n
        bot['cash'] += loc['price'] * n
        assert(bot['cash'] >= 0)
        if loc['rock'] not in bot['bag']:
            bot['bag'][loc['rock']] = 0
        bot['bag'][loc['rock']] += n
        bot['num_rocks'] += n
    elif action == 'sell' and n:
        bot['location']['quantity'] -= n
        bot['cash'] += loc['price'] * n
        bot['num_rocks'] -= n
        assert(bot['num_rocks'] >= 0)
        if loc['rock'] == "Anything":
            count = n
            for rock in list(bot['bag'].keys()):
                if count == 0:
                    break
                x = min(count, bot['bag'][rock])
                count -= x
                bot['bag'][rock] -= x
                assert(bot['bag'][rock] >= 0)
                if not bot['bag'][rock]:
                    del bot['bag'][rock]
        else:
            bot['bag'][loc['rock']] -= n
            assert(bot['bag'][loc['rock']] >= 0)
            if not bot['bag'][loc['rock']]:
                del bot['bag'][loc['rock']]

def arbitrate_sales(location):
    bots_save = bots = [b for b in location['bots'].values() if b['action'] in ['buy', 'sell']]
    bots = sorted(bots, key = lambda b: b['n'])
    quantity = location['quantity']
    while bots and quantity/len(bots) >= bots[0]['n']:
        quantity -= bots[0]['n']
        bots.pop(0)
    for bot in bots:
        bot['n'] = int(quantity/len(bots))
    assert(sum(b['n'] for b in bots_save) <= location['quantity'])

# return pseudo-random random world
def randomize_world(parameters, locations, n_bots):
    for (parameter, value) in sorted(parameters.items()):
        parameters[parameter] = generate_variable(value)
    parameters['n_locations'] = len(locations)
    parameters['n_fruit_buyers'] = len([l for l in locations if l['price'] > 0])
    parameters['n_fruit_sellers'] = len([l for l in locations if l['price'] < 0 and l['rock'] not in ['Petrol', 'Anything']])
    parameters['n_bots'] = n_bots
    parameters['n_charging_stations'] = len([l for l in locations if l['rock'] == "Petrol"])
    average_price = {}
    fruits = set(l['rock'] for l in locations) - set(["Petrol", "Anything"])
    for rock in sorted(fruits):
        prices = [abs(l['price']) for l in locations if l['rock'] == rock]
        mean = sum(prices) / len(prices)
        if mean:
            average_price[rock] = generate_variable(mean)
    for location in locations:
        generate_price_quantity(location, average_price, parameters)
    start = locations.pop(0)
    random.shuffle(locations)
    locations.insert(0, start)
    for (index, l) in enumerate(locations):
        l['index'] = index
    parameters['fuel_capacity'] = max(len(locations)//2, parameters['fuel_capacity'])
    return (parameters, locations)

# return random price, quantity tuple for a location
def generate_price_quantity(location, average_price, parameters):
    if args.debug > 1:
        print('generate_price_quantity before:', location)
    if not location['price']:
        return
    rock = location['rock']
    if rock == "Petrol":
        quantity = parameters['n_bots'] * parameters['turns_left'] * parameters["maximum_move"] / (6 * parameters['n_charging_stations'])
        quantity = generate_variable(quantity)
        price = generate_variable(abs(location['price']))
    elif rock not in average_price:
        # Anything
        quantity = generate_variable(parameters['n_bots'] * location['quantity'])
        price = generate_variable(abs(location['price']))
    else:
        fruit_price = average_price[rock]
        total_fruit_kg = parameters['n_bots'] * parameters['bag_capacity'] * parameters['turns_left']  / 5.0
        n_traders = parameters['n_fruit_sellers'] if location['price'] < 0 else parameters['n_fruit_buyers']
        n_traders = max(1, n_traders)
        per_location_fruit_kg = total_fruit_kg / n_traders
        if args.debug > 1:
            print('generate_price_quantity total_fruit_kg:', rock, fruit_price, total_fruit_kg, n_traders, per_location_fruit_kg)
        quantity = generate_variable(per_location_fruit_kg)
        if location['price'] < 0:
            price = generate_variable((0.5 * fruit_price, 1.1 * fruit_price))
        elif location['price'] > 0:
            price = generate_variable((0.9 * fruit_price, 2 * fruit_price))
    price = max(1, price)
    location['quantity'] = quantity
    # location['quantity'] = max(5, quantity)
    if location['price'] < 0:
        price = -price
    location['price'] = price
    if args.debug > 1:
        print('generate_price_quantity after:', location)

# if 2 values generate a normal value truncated to be in interval
# if a single value supplied interval used is (value/2,2*value)
def generate_variable(bounds):
    if isinstance(bounds, (list,tuple)):
        (minimum, maximum) = bounds
    else:
        minimum = bounds / 2
        maximum = 2 * bounds
    if minimum == maximum:
        return int(minimum)
    mean = (float(minimum) + float(maximum))/2.0
    standard_deviation = abs(maximum - minimum)/4
    value = random.gauss(mean, standard_deviation)
#    if isinstance(minimum, int) and isinstance(maximum, int):
    # every thing is ints
    return int(max(min(value, maximum), minimum))

def create_bot(name, get_action, parameters, locations, binary=''):
    return {
        'name' : name,
        'cash' : parameters['cash'],
        'fuel_level' :  parameters['fuel_capacity'],
        'location' : locations[0],
        'bag': {},
        'num_rocks': 0,
        'turns_left' :  parameters['turns_left'],
        'fuel_capacity' :    parameters['fuel_capacity'],
        'maximum_move' :  parameters['maximum_move'],
        'bag_capacity' :  parameters['bag_capacity'],
        'get_action' : get_action,
        'moves': [],
        'binary':  binary,
        'disqualified' : False
    }

def sanitize_bots(bots):
    names = set()
    for (index,bot) in enumerate(bots):
        bot['index'] = index
        name = bot['name']
        bot['prefix'] = prefix = re.sub(r"[^a-zA-Z0-9' _-]", '', name)[:MAX_SUPPLIED_BOT_NAME_CHARS]
        i = 0
        name = prefix
        while name in names:
            name = prefix + str(i)
            i += 1
        bot['name'] = name
        names.add(name)

def parameters2string(parameters):
    string = ""
    for parameter in ['fuel_capacity', 'bag_capacity', 'maximum_move']:
        string += '{}={}\n'.format(parameter, parameters[parameter])
    return string

def bots2string(bots):
    return "\n".join(bot2string(b) for b in bots)+"\n"

def bot2string(bot):
    s = '"{}" is at "{}" with ${}, fuel level: {}'.format(bot['name'], bot['location']['name'], bot['cash'], bot['fuel_level'])
    if bot['bag'] and bot['num_rocks'] :
        for rock in bot['bag']:
            s += ", {} kg of {}".format(bot['bag'][rock], rock)
    return s

def bots2table(bots):
    s = '<table class="table table-striped table-condensed" style="width:90%;">\n'
#    s += '<tr><th style="text-align:left;">Name<th style="text-align:left;">Location<th style="text-align:right;">Cash<th style="text-align:right;">Battery<th style="text-align:right;">Action\n'
    for b in bots:
        s += '<tr><td><b>%s</b><td><i>%s</i><td style="text-align:right;">$%s<td style="text-align:right;">%s<td>%s\n' % bot2tablerow(b)
    s += '</table>\n'
    return s

def bot2tablerow(bot):
    action = action2str(bot['action'], bot['requested_n'])
    if bot['requested_n'] != bot['n']:
        action += "(reduced to {})".format(bot['n'])
    return (bot['name'], bot['location']['name'], bot['cash'], bot['fuel_level'], action)


def bots2table_postgame(bots):
    s = '<table class="table table-striped table-condensed" style="width:50%;">\n'
#    s += '<tr><th style="text-align:left;">Name<th style="text-align:left;">Location<th style="text-align:right;">Cash<th style="text-align:right;">Fuel\n'
    for bot in bots:
        s += '<tr><td><b>%s</b><td style="text-align:right;">$%s\n' % (bot['name'], bot['cash'])
    s += '</table>\n'
    return s
    return

def action2str(action, n):
    if action == 'move':
        return 'Move ' + str(n)
    elif action == 'buy':
       return 'Buy ' + str(n)
    elif action == 'sell':
       return 'Sell ' + str(n)

def locations2string(locations, colorize=True):
    return "\n".join(location2string(l, colorize=colorize) for l in locations)+"\n"

def location2string(location, colorize=True):
    if not colorize:
        colored_local = lambda x,*a,**kw: x
    else:
        colored_local = colored
    s = location['name'] + ': '
    q = location['quantity']
    price = location['price']
    f = location['rock']
    if price > 0:
        s += 'will buy %s kg of %s for $%s/kg' % (q, colored_local(f, 'red') if q else f, price)
    elif price < 0:
        if f == "Petrol":
            s += 'will sell %s L of %s for $%s/L' % (q, colored_local(f, 'green') if q  else f, -price)
        else:
            s += 'will sell %s kg of %s for $%s/kg' % (q, colored_local(f, 'green') if q  else f, -price)
    else:
        s += colored_local('other', 'yellow')
    return s

def locations2table(locations):
    s = '<table class="table table-striped table-condensed" style="width:70%;">\n'
    s += '<tr><th style="text-align:left;">Name<th style="text-align:left;">Type<th style="text-align:left;">Rock<th style="text-align:right;">Quantity (kg or L)<th style="text-align:right;">Price\n'
    for l in locations:
        s += '<tr><td><b>%s</b><td><i>%s</i><td>%s<td style="text-align:right;">%s<td style="text-align:right;">%s\n' % location2tablerow(l)
    s += '</table>\n'
    return s

def location2tablerow(location):
    s = location['name']
    q = location['quantity']
    p = location['price']
    f = location['rock']
    if p < 0:
        return (s, 'Seller', f, str(q), '$'+str(-p))
    elif p > 0:
        return (s, 'Buyer', f, str(q), '$'+str(p))
    else:
        return (s, 'Other', '', '', '')

def read_world(world_file):
    with open(world_file) as f:
        return parse_world(f.read())

def parse_world(world_string):
    locations = []
    parameters = {
        'cash' : 50,
        'fuel_level' : 50,
        'maximum_move' : 7,
        'bag_capacity' : 25,
        'fuel_capacity' : 50,
        'turns_left' : 30
    }
    for line in world_string.splitlines():
        line = re.sub(r'#.*', '', line)
        if re.match(r'^\s*$', line):
            continue
        if args.debug > 1:
            print("line: '{}'\n".format(line), file=sys.stderr)
        m = re.search(r'^(\w+)\s*=\s*(\d+)\s*$', line)
        if not locations and m:
            parameters[m.group(1)] = int(m.group(2))
            continue
        m = re.search(r'^(.*\S)\s*:\s*will\s*(sell|buy)s?\s*(\d+)\s*(Kg|L)\sof\s+(\S.*\S)\s+for\s+\$(\d+)', line, flags=re.I)
        if m:
            l = {
                'name' : m.group(1)[:MAX_NAME_CHARS],
                'rock' : m.group(5)[:MAX_NAME_CHARS],
                'quantity' : int(m.group(3)),
                'price' : int(m.group(6)),
                'bots': {},
                }
            if args.debug > 1:
                print(m.groups(), l, file=sys.stderr)
            if m.group(2).lower() == 'sell':
                l['price'] *= -1
            assert(l['price'])
            assert(l['quantity'])
            if (all(loc['name'] != l['name'] for loc in locations)):
                locations.append(l)
            else:
                print('Skipping duplicate location', l['name'], file=sys.stderr)
            continue
        m = re.search(r'^(.*\S)\s*:\s*other\s*$', line, flags=re.I)
        if m:
            l = {
                'name' : m.group(1)[:MAX_NAME_CHARS],
                'rock' : "Nothing",
                'quantity' : 0,
                'price' : 0,
                'bots': {},
                }
            if (all(loc['name'] != l['name'] for loc in locations)):
                locations.append(l)
            else:
                print('Skipping duplicate location', l['name'], file=sys.stderr)
            continue
        m = re.search(r'^\*\*\*\s+Turn\s+(\d+)\s+of\s+(\d+)', line, flags=re.I)
        if m:
            parameters['turns_left'] = int(m.group(2)) - int(m.group(1)) + 1
            if args.debug > 1:
                print("parameters['turns_left'] set to ", parameters['turns_left'], file=sys.stderr)
            continue
        if args.debug:
            print("unparsed line: '{}'\n".format(line), file=sys.stderr)
    return (parameters, locations)

def cleanup(temp_dir=None):
    if temp_dir and re.search('^/tmp/', temp_dir) and args.debug < 10:
        shutil.rmtree(temp_dir)
    if args.debug >= 10:
        print('leaving', temp_dir)


def compile_bots(args):
    def new_player_dir():
        nonlocal temp_dir, player_dirs
        if not temp_dir:
            temp_dir = tempfile.mkdtemp()
            atexit.register(cleanup, temp_dir=temp_dir)
        player_dir = os.path.join(temp_dir, str(len(player_dirs)))
        os.mkdir(player_dir)
        player_dirs.append(player_dir)
        return player_dir
    player_dirs = []
    temp_dir = None
    binaries = []
    for path in args.source_files:
        if os.path.isdir(path):
            player_dir = new_player_dir()
            for file in glob.glob(os.path.join(path, '*.[ch]')) + glob.glob(os.path.join(path, '*.txt')):
                try:
                    shutil.copy(file, player_dir)
                except IOError:
                    print(sys.argv[0], 'could not open', file, file=sys.stderr)
        elif re.search(r'\b(tar|tgz)\b', path):
            player_dir = new_player_dir()
            if subprocess.run(['tar', '-x', '-C', player_dir, '-f', path, '--exclude', 'rock_bot.h']).returncode != 0:
                print("Can not extract tar file '{}'".format(path), file=sys.stderr)
                sys.exit(1)
        elif os.path.splitext(path)[1] in ['.c']:
            dir = new_player_dir()
            try:
                shutil.copy(path, dir)
            except IOError:
                print(sys.argv[0], 'could not open', path, file=sys.stderr)
                sys.exit(1)
        elif os.path.isfile(path) and os.access(path, os.X_OK):
            binaries.append(make_portable_CSE_pathname(path))
        else:
            print('Unexpected argument:', path, file=sys.stderr)
            print(f'make sure that "{path}" is an executable file', file=sys.stderr)
            sys.exit(1)
    for player_dir in player_dirs:
        binaries.append(compile_program(args, dir=player_dir))
    return binaries

def run_get_bot_name(binary):
    (stdout, stderr, exit_status, which_binary) = run_dual(binary)
    return stdout if stdout else "The Unknown Bot"

def run_get_action(world_description, bot, binary, show_bot_stdout=True):
    (stdout, stderr, exit_status, which_binary) = run_dual(binary, input=world_description)
    if args.debug > 1:
        print('run_get_action', (stdout, stderr, exit_status, which_binary))
    if stderr and (show_bot_stdout or exit_status != 0):
        print(colored('--- stderr from '+bot['name']+' ---\n', 'magenta'))
        print(stderr) # p
    if stdout and not re.match(r'^\s*(move|buy|sell)\s*(-?\d+)\s*$', stdout, re.I) and show_bot_stdout:
        o = '--- stdout from '+bot['name']+' ---\n'
        o += hr() + '\n'
        o += stdout
        o += hr() + '\n'
        print(colored(o, 'magenta'))
    m = re.search(r'(move|buy|sell)\s*(-?\d+)\s*$', stdout, flags=re.DOTALL|re.I)
    if not m:
        print(colored(bot['name'] + ' disqualified for not printing a legal action.', 'red'))
        if args.show_reproduce_command:
            try:
                input_filename = 'rock_bot_input_' + str(args.seed) + '.txt'
                print('Creating', colored(input_filename, 'blue'))
                with open(input_filename, "w") as f:
                    f.write(world_description)
                print('To reproduce this error (assuming your executable bot is named rock_bot) run:')
                print(colored('./rock_bot < '+input_filename, 'blue'))
            except OSError:
                pass
        return (None, None)
    action = m.group(1).lower()
    n = int(m.group(2))
    if args.debug:
        print('run_get_action returning', (action, n))
    return (action, n)

def hr():
    return '-'*72 + '\n'


def run_dual(binary, arguments=[], input=''):
    output = []
    binaries = [binary]
    valgrind_binary = binary + '-valgrind'
    if os.path.exists(valgrind_binary):
        binaries += [valgrind_binary]
    for b in binaries:
        for attempt in range(3):
            if isinstance(input, str):
                input_bytes = input.encode('ascii')
            (stdout, stderr, exit_status) = run_with_resource_limits([b]+arguments, input=input_bytes)
            stdout = codecs.decode(stdout, 'ascii', errors='replace')
            stderr = codecs.decode(stderr, 'ascii', errors='replace')

            if args.debug and input:
                print("echo -e '{}'|{}".format(str(input).rstrip().replace('\n', '\\n'), ' '.join([b]+arguments)),file=sys.stderr)
            if stderr and exit_status != 0:
                return (stdout, stderr, exit_status, binary)
            if not stdout and exit_status != 0:
                # weird termination with non-zero exit status seen on some CSE servers
                # ignore this execution
                time.sleep(1)
                continue
            output.append((stdout, stderr, exit_status, binary))
            break
    return output[0] if output else ('', '', 1, binary)

def set_environment():
    for variable in list(os.environ.keys()):
        os.environ.pop(variable, None)
    os.environ['LANG'] = 'en_AU.utf8'
    os.environ['LANGUAGE'] = 'en_AU.UTF-8'
    os.environ['LC_ALL'] = 'en_AU.UTF-8'
    os.environ['LC_COLLATE'] = 'POSIX'
    os.environ['PATH'] = '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:.'

def search_path(program):
    for path in os.environ["PATH"].split(os.pathsep):
        full_path = os.path.join(path, program)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path


def make_portable_CSE_pathname(pathname):
    pathname = os.path.realpath(pathname)
    pathname = re.sub(r'/tmp_amd/\w+/\w+ort/\w+/\d+/', '/home/', pathname)
    pathname = re.sub(r'^/tmp_amd/\w+/\w+ort/\d+/', '/home/', pathname)
    pathname = re.sub(r'^/(import|export)/\w+/\d+/', '/home/', pathname)
    return pathname

world_descriptions = {
    'tiny' : """
fuel_capacity=20
bag_capacity=17
maximum_move=7

*** Turn 1 of 5 ***

Campus Recycling: will buy 1000 kg of Anything for $1
Campus Petrol: will sell 100 kg of Petrol for $4
Mathews A: will buy 100 kg of Copper for $15
CLB 7: will buy 100 kg of Copper for $15
Kensington Rocks: will sell 100 kg of Copper for $15
""",

    'medium' : """
turns_left=100
fuel_capacity=65
maximum_move=7
cash=500

UNSW Metallic Waste: will buy 1000 kg of Anything for $1

BP: will sell 100 L of Petrol for $4
Shell: will sell 100 L of Petrol for $4


Mathews C: will buy 100 kg of Copper for $14
CLB 8: will buy 100 kg of Copper for $14
Science Theatre: will buy 100 kg of Copper for $14

Eastgardens Rock: will sell 100 kg of Copper for $14
Kensington Copper: will sell 100 kg of Copper for $14
Botany Mine: will sell 100 kg of Copper for $14


J17 G03: will buy 100 kg of Silver for $32
Clancy Auditorium: will buy 100 kg of Silver  for $32

Rosebery Silver Mine: will sell 100 kg of Silver  for $32
Kingsford Silver: will sell 100 kg of Silver  for $32
Campus Rock Centre: will sell 100 kg of Silver  for $32

Physics Theatre: will buy 100 kg of Marble for $25
K17 Basement: will buy 100 kg of Marble for $25

Bondi Marble Centre: will sell 100 kg of Marble for $25
Heavy Marble: will sell 100 kg of Marble for $25

Mathews B: will buy 100 kg of Clay for $6

Wentworth Clay: will sell 100 kg of Clay for $6
Clovelly Clay: will sell 100 kg of Clay for $6
Maroubra Clay: will sell 100 kg of Clay for $6

Smelly Rocks R Us: will sell 100 kg of Diamonds for $64

Bondi Diamond Jeweler: will buy 100 kg of Diamonds for $64
Kora Lab: will buy 100 kg of Diamonds for $64
Sitar Lab: will buy 100 kg of Diamonds for $64
""",
}

def random_copy(list):
    list_copy = [x for x in list if x != '']
    random.shuffle(list_copy)
    return list_copy

def scaled_world(n_bots):
    world = []
    n_fruit = max(1, generate_variable(0.2 * n_bots))
    n_charging = max(1, generate_variable(0.07 * n_bots))
    n_anything = max(1, generate_variable(0.05 * n_bots))
    suburbs = random_copy(suburb_list)
    location_names = set()
    suburbs = random_copy(suburb_list)
    for n in range(n_anything):
        while True:
            suburb = random.choice(suburbs)
            template = random.choice(anything_location_templates)
            name = template.format(suburb=suburb)
            if name  in location_names:
                continue
            location_names.add(name)
            price = max(1, generate_variable(2))
            world.append('{name}: will buy 1000 kg of Anything for ${price}'.format(name=name, price=price))
            break
    suburbs = random_copy(suburb_list)
    for n in range(n_charging):
        while True:
            suburb = random.choice(suburbs)
            template = random.choice(electricity_location_templates)
            name = template.format(suburb=suburb)
            if name in location_names:
                continue
            location_names.add(name)
            price = max(1, generate_variable(4))
            world.append('{name}: will sell 100 L of Petrol for ${price}'.format(name=name, price=price))
            break
    buyers = random_copy(buyer_locations)
    suburbs = random_copy(suburb_list)
    rocks = random_copy(rock_list)[:n_fruit]
    n_fruit = min(len(rocks), n_fruit)
    mean_traders = max(1, round(n_bots/n_fruit))
    for rock in rocks:
        plural_fruit = fruit_plural(rock)
        if not buyers:
                break
        n_buyers = max(2, generate_variable(mean_traders))
        n_sellers = max(1, generate_variable(mean_traders))
        price = max(4, generate_variable(50) - 20)
        for b in range(n_buyers):
            if not buyers:
                break
            name = buyers.pop()
            world.append('{name}: will buy 1 Kg of {rock} for ${price}'.format(name=name, rock=plural_fruit, price=price))
        for b in range(n_sellers):
            while True:
                suburb = random.choice(suburbs)
                template = random.choice(seller_location_templates)
                name = template.format(rock=rock, suburb=suburb)
                if name not in location_names:
                    break
            location_names.add(name)
            world.append('{name}: will sell 1 Kg of {rock} for ${price}'.format(name=name, rock=plural_fruit, price=price))
    n_locations = len(world)
    # maximum_move = max(5, generate_variable(0.1*n_locations))
    maximum_move = generate_variable(-300000 / (n_locations + 1500) + 202)
    world.append('turns_left=60')
    world.append('maximum_move={}'.format(maximum_move))
    world.append('fuel_capacity={}'.format(generate_variable(4 * maximum_move)))
    world.append('bag_capacity={}'.format(generate_variable(20)))
    return '\n'.join(world)  + '\n'


anything_location_templates = """
{suburb} Rock Cruncher
{suburb} Metallic Waste
{suburb} Garbage
{suburb} Recycling
""".splitlines()

buyer_locations = """
AGSM LG06
Ainsworth 101
Ainsworth 102
Ainsworth 201
Ainsworth 202
Ainsworth G01
Ainsworth G02
Ainsworth G03
Blockhouse G13
Blockhouse G14
Blockhouse G15
Blockhouse G16
Blockhouse G6
Bongo Lab
Bugle Lab
Cello Lab
Central Lecture Block 1
Central Lecture Block 2
Central Lecture Block 3
Central Lecture Block 4
Central Lecture Block 5
Central Lecture Block 6
Central Lecture Block 7
Central Lecture Block 8
Chemical Sc M10
Chemical Sc M11
Chemical Sc M18
ChemicalSc M17
Chi Lab
Civil Engineering 101
Civil Engineering 102
Civil Engineering 109
Civil Engineering 701
Civil Engineering G1
Civil Engineering G6
Civil Engineering G8
Clancy Auditorium
Clavier Lab
Colombo LG01
Colombo LG02
Colombo Theatre A
Colombo Theatre B
Colombo Theatre C
Drum Lab
EE 418
EE G24
EE G25
Electrical Eng 418
Electrical Eng G24
Electrical Eng G25
Flute Lab
Goldstein G01
Goldstein G02
Goldstein G03
Goldstein G04
Goldstein G05
Goldstein G06
Goldstein G07
Goldstein G09
Horn Lab
J17 G01
J17 G02
J17 G03
J17-101
J17-102
J17-201
J17-202
John B Reid Theatre
John Goodsell LG19
John Goodsell LG21
K17 Basement
Keith Burrows Theatre
Kora Lab
Law Building 101
Law Building 162
Law Building 163
Law Building 201
Law Building 202
Law Building 203
Law Building 275
Law Building 276
Law Building 301
Law Building 302
Law Building 303
Law Building 388
Law Building 389
Law Library 111
Law Library G17
Law Theatre
Law Theatre G02
Law Theatre G04
Law Theatre G23
Macauley Theatre
Mathews 101
Mathews 102
Mathews 103
Mathews 104
Mathews 105
Mathews 106
Mathews 107
Mathews 108
Mathews 226
Mathews 227
Mathews 228
Mathews 230
Mathews 231
Mathews 232
Mathews 301
Mathews 302
Mathews 303
Mathews 306
Mathews 307
Mathews 308
Mathews 309
Mathews 310
Mathews 311
Mathews 312
Mathews 313
Mathews A
Mathews B
Mathews C
Mathews D
Morven Brown G3
Morven Brown G4
Morven Brown G5
Morven Brown G6
Morven Brown LG2
Morven Brown LG30
New South Global Theatre
Newton 306
Newton 307
Oboe Lab
Old Main Building 149
Old Main Building 150
Old Main Building 151
Old Main Building 229
Old Main Building 230
Old Main Building G31
Old Main Building G32
Organ Lab
Oud Lab
Physics Theatre
Piano Lab
Pioneer International Theatre
Quadrangle 1001
Quadrangle 1042
Quadrangle 1043
Quadrangle 1045
Quadrangle 1046
Quadrangle 1047
Quadrangle 1048
Quadrangle 1049
Quadrangle G025
Quadrangle G026
Quadrangle G027
Quadrangle G031
Quadrangle G032
Quadrangle G033
Quadrangle G034
Quadrangle G035
Quadrangle G040
Quadrangle G041
Quadrangle G042
Quadrangle G044
Quadrangle G045
Quadrangle G046
Quadrangle G047
Quadrangle G048
Quadrangle G052
Quadrangle G053
Quadrangle G054
Quadrangle G055
Red Centre Central Wing 1040
Red Centre Central Wing 1041
Red Centre Central Wing 1042
Red Centre Central Wing 1043
Red Centre Central Wing 2060
Red Centre Central Wing 2061
Red Centre Central Wing 2062
Red Centre Central Wing 2063
Red Centre Central Wing M032
Red Centre Theatre
Red Centre West 2035
Red Centre West 3037
Red Centre West 4034
Red Centre West 4037
Red Centre West M010
Rex Vowels Theatre
Ritchie Theatre
Science Theatre
Sitar Lab
Tabla Lab
Viola Lab
Webster 250
Webster 251
Webster 252
Webster 256
Webster 302
Webster Theatre A
Webster Theatre B
""".splitlines()

electricity_location_templates = """
{suburb} Ethanol
{suburb} Petroleum
{suburb} BP
{suburb} Fuel
Shell
""".splitlines()

suburb_list = """
Beaconsfield
Bondi
Botany
Bronte
Campus
Clovelly
Daceyville
Eastgardens
Kensington
Kingsford
Kogarah
La Perouse
Little Bay
Malabar
Maroubra
Mascot
Matraville
Paddington
Padstow
Penrith
Randwick
Rosebery
UNSW
Waverly
Wentworth
Zetland
""".splitlines()

seller_location_templates ="""
{suburb} {rock} Jeweler
Bondi {rock} Sellers
{suburb} {rock} Mine
{suburb} Rock
{suburb} {rock}
{rock} Brothers
{rock} Sisters
{rock}s R Us
Great {rock}
{suburb} Estate
{suburb} {rock} Centre
{suburb} {rock} Specialists
Lovely {rock}s
Shiny {rock}s
Heavy {rock}s
""".splitlines()

def fruit_plural(rock):
    # if rock.endswith('y'):
    #     return rock[:-1] + 'ies'
    # if rock.endswith('rock') or rock.endswith('arb'):
    #     return rock
    # if rock.endswith('h') :
    #     return rock + 'es'
    # if rock.endswith('ato'):
    #     return rock + 'es'
    # if rock.endswith('d'):
    #     return rock + 's'
    return rock

rock_list = """Diamond
Sapphire
Ruby
Emerald
Topaz
Opal
Jade
Amethyst
Quartz
Turquoise
Gold
Iron
Silver
Copper
Sandstone
Limestone
Granite
Platinum
Marble
Clay
Shale
Aquamarine""".splitlines()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
