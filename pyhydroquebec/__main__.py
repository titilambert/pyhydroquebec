import argparse
import json
import sys

from pyhydroquebec import HydroQuebecClient, REQUESTS_TIMEOUT


def _format_output(account, data):
    """Format data to get a readable output"""
    data['account'] = account
    output = ("""Hydro Quebec data for account: {d[account]}

Period Info
===========
Period day number:         {d[period_length]:d}
Period total days:     {d[period_total_days]:d} days

Period current bill
===================
Total Bill: {d[period_total_bill]:.2f} $
Mean Daily Bill: {d[period_mean_daily_bill]:.2f} $

Total period consumption
========================
Lower price: {d[period_lower_price_consumption]:.2f} kWh
Higher price: {d[period_higher_price_consumption]:.2f} kWh
Total: {d[period_total_consumption]:.2f} kWh
Mean daily: {d[period_mean_daily_consumption]:.2f} kWh

Yesterday consumption
=====================
Lower price:  {d[yesterday_lower_price_consumption]:.2f} kWh
Higher price: {d[yesterday_higher_price_consumption]:.2f} kWh
Total:  {d[yesterday_total_consumption]:.2f} kWh
""")
    print(output.format(d=data))


def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        required=True, help='Hydro Quebec username')
    parser.add_argument('-p', '--password',
                        required=True, help='Password')
    parser.add_argument('-j', '--json', action='store_true',
                        default=False, help='Json output')
    parser.add_argument('-t', '--timeout',
                        default=REQUESTS_TIMEOUT, help='Request timeout')
    args = parser.parse_args()
    client = HydroQuebecClient(args.username, args.password, args.timeout)
    client.fetch_data()
    if not client.get_data():
        return
    if args.json:
        print(json.dumps(client.get_data()))
    else:
        _format_output(args.username, client.get_data())


if __name__ == '__main__':
    sys.exit(main())
