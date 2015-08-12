
import csv
import argparse
from prettytable import PrettyTable

def show_positions(args):
    # Load symbols map
    symbolsmap_rdr = csv.DictReader(open(args.symbolmap))
    symbol_map = {}
    for symbol_idx, symbol in enumerate(symbolsmap_rdr):
        symbol_map[symbol['Stock symbol']] = symbol['Target symbol']

    # Load allocation targets
    targets_rdr = csv.DictReader(open(args.targets))
    targets = {}
    targets["Other"] = {"Name":"Other","Symbol":"Other","Target":0}
    for target_idx, target in enumerate(targets_rdr):
        if len(target) == 0: continue
        targets[target['Symbol']] = target

    # Load positions and group them by asset type
    positions_rdr = csv.DictReader(open(args.positions))
    positions = []
    allocations = { target_type['Symbol']: {} for target_type in targets.itervalues() }
    for pos_idx, pos in enumerate(positions_rdr):
        if len(pos) == 0: continue
        positions.append(pos)
        position_type = symbol_map[pos['EquitySymbol']]
        
        if position_type == '':
            print "WARNING. Position type for %s (%s) is an empty string!" % (pos['EquitySymbol'], pos['EquityDescription'])
            position_type = "Other"

        if not pos['EquitySymbol'] in allocations[position_type]:
            allocations[position_type][pos['EquitySymbol']] = [pos]
        else:
            allocations[position_type][pos['EquitySymbol']].append(pos)
    

    allocation_totals = []
    total_portfolio = 0
    for asset_type, assets in allocations.iteritems():
        asset_total = {'CAD':0, 'USD':0, 'total':0}
        for asset_symbol, asset_positions in assets.iteritems():
            for pos in asset_positions:
                asset_total[pos['CurrencyDisplay']] += float(pos['MarketValue'])
        
        asset_total['total'] = asset_total['CAD'] + asset_total['USD'] * args.xchrate
        total_portfolio += asset_total['total']

        allocation_totals.append({
            'type': asset_type,
            'totals': asset_total
        })

    
    print "Total portfolio value: %0.2f" % total_portfolio

    x = PrettyTable(["Asset","Target","Current", "Prop diff", "Market value", "Target value"])
    x.align["Market value"] = "r"
    x.align["Target value"] = "r"
    for asset_totals in allocation_totals:

        atarget = float(targets[asset_totals["type"]]['Target'])
        aprop   = asset_totals["totals"]['total'] / total_portfolio
        difference = aprop / atarget if atarget != 0 else 0

        x.add_row([targets[asset_totals["type"]]['Name'],
                "%0.2f" % atarget,
                "%0.3f" % aprop,
                "%0.2f" % difference,
                "%0.2f$" % asset_totals["totals"]['total'],
                "%0.2f$" % (atarget * total_portfolio)])

    print x

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Show current portfolio balancing')
    
    parser.add_argument('--targets', type=str, default="targets.csv",
                           help='targets csv file')
    parser.add_argument('--symbolmap', type=str, default="symbolmap.csv",
                           help='symbols map csv file')
    parser.add_argument('--positions', type=str,
                           help='positions csv file')
    parser.add_argument('--xchrate', type=float,
                           help='exchange rate (US to CAD)')

    args = parser.parse_args()

    show_positions(args)
