import argparse
import json
import sys
import datetime
import asyncio

from dateutil import tz

from pyhydroquebec import HydroQuebecClient, REQUESTS_TIMEOUT, HQ_TIMEZONE


def _format_output(account, all_data, show_hourly=False):
    """Format data to get a readable output"""
    print("""
#################################
# Hydro Quebec data for account #
# {}
#################################""".format(account))
    for contract, data in all_data.items():
        data['contract'] = contract
        if data['period_total_bill'] is None:
            data['period_total_bill'] = 0.0
        if data['period_projection'] is None:
            data['period_projection'] = 0.0
        if data['period_mean_daily_bill'] is None:
            data['period_mean_daily_bill'] = 0.0
        output = ("""
----------------------------------------------------------------

Contract: {d[contract]}
===================

Balance: {d[balance]:.2f} $

Period Info
===========
Period day number:      {d[period_length]:d}
Period total days:      {d[period_total_days]:d} days

Period current bill
===================
Total Bill:             {d[period_total_bill]:.2f} $
Projection bill:        {d[period_projection]:.2f} $
Mean Daily Bill:        {d[period_mean_daily_bill]:.2f} $

Total period consumption
========================
Lower price:            {d[period_lower_price_consumption]:.2f} kWh
Higher price:           {d[period_higher_price_consumption]:.2f} kWh
Total:                  {d[period_total_consumption]:.2f} kWh
Mean daily:             {d[period_mean_daily_consumption]:.2f} kWh""")
        print(output.format(d=data))
        if data.get("period_average_temperature") is not None:
            output2 = ("""Temperature:            {d[period_average_temperature]:d} °C""")
            print(output2.format(d=data))
        if data.get("yesterday_average_temperature") is not None:
            output3 = ("""
Yesterday consumption
=====================
Temperature:            {d[yesterday_average_temperature]:d} °C
Lower price:            {d[yesterday_lower_price_consumption]:.2f} kWh
Higher price:           {d[yesterday_higher_price_consumption]:.2f} kWh
Total:                  {d[yesterday_total_consumption]:.2f} kWh""")
            print(output3.format(d=data))
        if show_hourly:
            msg = ("""
Yesterday consumption details
-----------------------------
   Hour  | Temperature | Lower price consumption | Higher price consumption | total comsumption
""")
            for hdata in data['yesterday_hourly_consumption']:
                msg += "{d[hour]} | {d[temp]:8d} °C | {d[lower]:19.2f} kWh | {d[high]:20.2f} kWh | {d[total]:.2f} kWh\n".format(d=hdata)
            print(msg)

        output3 = ("""
Annual Total
============

Start date:             {d[annual_date_start]}
End date:               {d[annual_date_end]}
Total bill:             {d[annual_total_bill]:.2f} $
Mean daily bill:        {d[annual_mean_daily_bill]:.2f} $
Total consumption:      {d[annual_total_consumption]:.2f} kWh
Mean dailyconsumption:  {d[annual_mean_daily_consumption]:.2f} kWh
kWh price:              {d[annual_kwh_price_cent]:0.2f} ¢
""")
        print(output3.format(d=data))


def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        required=True, help='Hydro Quebec username')
    parser.add_argument('-p', '--password',
                        required=True, help='Password')
    parser.add_argument('-j', '--json', action='store_true',
                        default=False, help='Json output')
    parser.add_argument('-c', '--contract',
                        default=None, help='Contract number')
    parser.add_argument('-l', '--list-contracts', action='store_true',
                        default=False, help='List all your contracts')
    parser.add_argument('-H', '--hourly', action='store_true',
                        default=False, help='Show yesterday hourly consumption')
    parser.add_argument('-t', '--timeout',
                        default=REQUESTS_TIMEOUT, help='Request timeout')
    raw_group = parser.add_argument_group('Detailled-energy raw download option')
    raw_group.add_argument('--detailled-energy', action='store_true',
                           default=False, help='Get raw json output download')
    raw_group.add_argument('--start-date',
                           default=None, help='Start date for detailled-output')
    raw_group.add_argument('--end-date',
                           default=datetime.datetime.now(HQ_TIMEZONE).strftime("%Y-%m-%d"),
                           help="End date for detailled-output")

    args = parser.parse_args()

    client = HydroQuebecClient(args.username, args.password, args.timeout)
    loop = asyncio.get_event_loop()

    if args.detailled_energy is False:
        async_func = client.fetch_data()
    else:
        async_func = client.fetch_data_detailled_energy_use(args.contract,
                                                            args.start_date,
                                                            args.end_date)
    try:
        fut = asyncio.wait([async_func])
        loop.run_until_complete(fut)
    except BaseException as exp:
        print(exp)
        return 1
    finally:
        close_fut = asyncio.wait([client.close_session()])
        loop.run_until_complete(close_fut)

    if not client.get_data():
        return 2

    if args.list_contracts:
        print("Contracts: {}".format(", ".join(client.get_contracts())))
    elif args.json or args.detailled_energy:
        print(json.dumps(client.get_data(args.contract)))
    else:
        _format_output(args.username, client.get_data(args.contract), args.hourly)


if __name__ == '__main__':
    sys.exit(main())
