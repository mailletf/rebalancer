# Portfolio rebalancing helper for Questrade portfolio

This project is a little portfolio rebalancing helper that I've been using to help rebalance a [Questrade](https://www.questrade.com) portfolio
where asset classes are distributed accross different accounts (unregistered, TFSA, RRSP). It supports CAD and USD.

## How to use

### Setup your target allocations

This file contains your target allocations. Create a file called `targets.csv` from the example `targets.csv.example` file.

```
Name,Symbol,Target
Bonds,Bonds,0.20
Stock,STOCK,0.80
```

### Setup symbol map file

This file maps indifidual stocks to an asset class. Create a file called `symbolmap.csv` from the example `symbolmap.csv.example` file.

```
Stock symbol,Target symbol
TSLA,STOCK
AAPL,STOCK
XBB,BONDS
```

### Download your current investment summary

[Download your investment summary in Excel format](http://help.questrade.com/how-to/portfolio-iq/custom-settings/exporting-data-to-excel#.W2X12FInbOQ)
from the Questrade website. I recommend creating a `positions` folder and saving the Excel file there by using the export date as the name.

If you wish to track cash as well, add a CSV file named with the same date and the `.cash` extension along with it. This is because Questrade
does not export the amounts of cash in your accounts.

The format of this file should be:

```
currency,total
CAD,100.00
USD,0.00
```

This will give you the following files:

```
rebalancer/positions/2018-08-04.xlsx
rebalancer/positions/2018-08-04.cash
```

### Run the script

Assuming we are using the files named with the date `2018-04-04`, and given a USD->CAD exchange rate of 1.3, run the following commands:

```
python xlsx2csv/xlsx2csv.py -a positions/2018-04-04.xlsx positions/2018-04-04
python rebalancer.py --position=../positions/2018-04-04/Positions.csv --cash=../positions/2018-04-04.cash --xchrate=1.3
```

This will give you an output like this:

```
Total portfolio value: 1000.00$
+---------------------------+--------+---------+-----------+--------------+--------------+------------+
|           Asset           | Target | Current | Prop diff | Market value | Target value |  +/- value |
+---------------------------+--------+---------+-----------+--------------+--------------+------------+
|            Bonds          |  0.20  |  0.500  |    2.5    |    500.00$   |      200.00$ |    300.00$ |
|            Stock          |  0.80  |  0.400  |    0.5    |    400.00$   |      800.00$ |   -400.00$ |
|            Cash           |  0.00  |  0.100  |           |    100.00$   |              |    100.00$ |
+---------------------------+--------+---------+-----------+--------------+--------------+------------+
```

### Fetching the exchange rate from Fixer.io API

To not have to specify the exchange rate manually, create a [Fixer.io](https://fixer.io) account with the Free tier and put your
API key in a file named `fixerio_apikey.txt`. The script will infer the date from the positions file and fetch the correct
exchange rate for the day of the positions export.

