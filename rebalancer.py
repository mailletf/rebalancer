
import os
import re
import csv
import requests
import argparse
from prettytable import PrettyTable

# Manage key names that changed in December 2015
def getPosKey(d, key):
    # pre dec 2015
    if "EquitySymbol" in d:
        return d[key]

    # post dec 2015
    if key == "EquitySymbol":
        return d["Equity Symbol"]
    if key == "EquityDescription":
        return d["Equity Description"]
    if key == "CurrencyDisplay":
        return d["Currency"]
    if key == "MarketValue":
        return d["Market Value"]

    raise Error("Unknown key: " % key)


def get_exchange_rate(args):
    # if we've passed the exchange rate on the cmd line, use it
    if args.xchrate:
        return args.xchrate

    # else try to use fixer.io
    fixerio_keyfile = "fixerio_apikey.txt"
    if os.path.exists(fixerio_keyfile):
        key = open(fixerio_keyfile).readlines()[0].strip()

    # we're assuming that the positions file has the date naming convention
    p = re.compile(".*([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])).*")
    m = p.match(args.positions)
    if not m:
        raise Exception("Exchange rate not provided on command line and unable to fetch from Fixer API")

    fixer_url = "http://data.fixer.io/api/%s?access_key=%s&symbols=USD,CAD&format=1" % (m.group(1), key)
    print ">> Calling Fixer API with: " + fixer_url

    response = requests.get(fixer_url)
    if response.status_code != 200:
        raise Exception("Status code %d on Fixer API call" % response.status_code)

    data = response.json()

    # free plan only gives us Euros to CAD/USD, so divide them together
    rate = data['rates']['CAD'] / data['rates']['USD']
    print "USD -> CAD exchange rate = %0.4f" % rate
    return rate

def show_positions(args):

    # resolve xchange rate
    xchrate = get_exchange_rate(args)

    # Load symbols map
    symbolsmap_rdr = csv.DictReader(open(args.symbolmap))
    symbol_map = {}
    for symbol_idx, symbol in enumerate(symbolsmap_rdr):
        symbol_map[symbol['Stock symbol']] = symbol['Target symbol']

    # Load allocation targets
    targets_rdr = csv.DictReader(open(args.targets))
    targets = {}
    targets["Other"] = {"Name":"Other","Symbol":"Other","Target":0}
    _total_target = 0
    for target_idx, target in enumerate(targets_rdr):
        if len(target) == 0: continue
        targets[target['Symbol']] = target
        _total_target += float(target["Target"])

    if _total_target != 1:
        raise Exception("Target allocation should sum to 1, not %0.2f" % _total_target)

    # Load positions and group them by asset type
    positions_rdr = csv.DictReader(open(args.positions))
    positions = []
    allocations = { target_type['Symbol']: {} for target_type in targets.itervalues() }
    for pos_idx, pos in enumerate(positions_rdr):
        if len(pos) == 0: continue
        positions.append(pos)
        position_type = symbol_map[getPosKey(pos, 'EquitySymbol')]

        if position_type == '':
            print "WARNING. Position type for %s (%s) is an empty string!" % (getPosKey(pos, 'EquitySymbol'), getPosKey(pos, 'EquityDescription'))
            position_type = "Other"

        if not getPosKey(pos, 'EquitySymbol') in allocations[position_type]:
            allocations[position_type][getPosKey(pos, 'EquitySymbol')] = [pos]
        else:
            allocations[position_type][getPosKey(pos, 'EquitySymbol')].append(pos)


    allocation_totals = []
    total_portfolio = 0
    for asset_type, assets in allocations.iteritems():
        asset_total = {'CAD':0, 'USD':0, 'total':0}
        for asset_symbol, asset_positions in assets.iteritems():
            for pos in asset_positions:
                asset_total[getPosKey(pos, 'CurrencyDisplay')] += float(getPosKey(pos, 'MarketValue'))

        asset_total['total'] = asset_total['CAD'] + asset_total['USD'] * xchrate
        total_portfolio += asset_total['total']

        allocation_totals.append({
            'type': asset_type,
            'totals': asset_total
        })

    # load cash file
    if args.cash:
        cash_total = {'CAD':0, 'USD':0, 'total':0}
        cash_rdr = csv.DictReader(open(args.cash))
        for line in cash_rdr:
            if line['currency'] not in ['USD', 'CAD']:
                raise Exception("wrong currency!!")

            cash_total[line['currency']] = float(line['total'])

        cash_total['total'] = cash_total['CAD'] + cash_total['USD'] * xchrate
        total_portfolio += cash_total['total']
        allocation_totals.append({
            'type': "Cash",
            'totals': cash_total
        })
        targets['Cash'] = {'Symbol': 'Cash', 'Name': 'Cash', 'Target': '0'}


    print "Total portfolio value: %0.2f" % total_portfolio

    x = PrettyTable(["Asset","Target","Current", "Prop diff", "Market value", "Target value", "+/- value"])
    x.align["Market value"] = "r"
    x.align["Target value"] = "r"
    x.align["+/- value"] = "r"
    for asset_totals in allocation_totals:

        atarget = float(targets[asset_totals["type"]]['Target'])

        # skip if target is 0 allocation and we have none
        if atarget==0 and asset_totals["totals"]['total']==0: continue

        aprop   = asset_totals["totals"]['total'] / total_portfolio
        difference = aprop / atarget if atarget != 0 else 0
        targetVal = (atarget * total_portfolio)

        x.add_row([targets[asset_totals["type"]]['Name'],
                "%0.2f" % atarget,
                "%0.3f" % aprop,
                "%0.2f" % difference,
                "%0.2f$" % asset_totals["totals"]['total'],
                "%0.2f$" % targetVal,
                "%0.2f$" % (asset_totals["totals"]['total']-targetVal)])

    print x

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Show current portfolio balancing')

    parser.add_argument('--targets', type=str, default="targets.csv",
                           help='targets csv file')
    parser.add_argument('--symbolmap', type=str, default="symbolmap.csv",
                           help='symbols map csv file')
    parser.add_argument('--positions', type=str,
                           help='positions csv file')
    parser.add_argument('--cash', type=str,
                           help='cash csv file')
    parser.add_argument('--xchrate', type=float,
                           help='exchange rate (US to CAD). If not specified, will attempt to fetch from Fixer API')

    args = parser.parse_args()

    show_positions(args)
