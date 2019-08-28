"""PyHydroQuebec Entrypoint Module."""

import argparse
import sys
import datetime
import asyncio


from pyhydroquebec import HydroQuebecClient, REQUESTS_TIMEOUT, HQ_TIMEZONE
from pyhydroquebec.output import output_text, output_influx, output_json
from version import VERSION

def main():
    """Entrypoint function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        help='Hydro Quebec username')
    parser.add_argument('-p', '--password',
                        help='Password')
    parser.add_argument('-j', '--json', action='store_true',
                        default=False, help='Json output')
    parser.add_argument('-i', '--influxdb', action='store_true',
                        default=False, help='InfluxDb output')
    parser.add_argument('-c', '--contract',
                        default=None, help='Contract number')
    parser.add_argument('-l', '--list-contracts', action='store_true',
                        default=False, help='List all your contracts')
    parser.add_argument('-H', '--hourly', action='store_true',
                        default=False, help='Show yesterday hourly consumption')
    parser.add_argument('-t', '--timeout',
                        default=REQUESTS_TIMEOUT, help='Request timeout')
    parser.add_argument('-V', '--version', action='store_true',
                        default=False, help='Show version')
    raw_group = parser.add_argument_group('Detailled-energy raw download option')
    raw_group.add_argument('--detailled-energy', action='store_true',
                           default=False, help='Get raw json output download')
    raw_group.add_argument('--start-date',
                           default=(datetime.datetime.now(HQ_TIMEZONE) -
                                    datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                           help='Start date for detailled-output')
    raw_group.add_argument('--end-date',
                           default=datetime.datetime.now(HQ_TIMEZONE).strftime("%Y-%m-%d"),
                           help="End date for detailled-output")

    args = parser.parse_args()

    if args.version:
        print(VERSION)
        return 0

    if not args.username or not args.password:
        parser.print_usage()
        print("pyhydroquebec: error: the following arguments are required: "
              "-u/--username, -p/--password")
        return 3

    client = HydroQuebecClient(args.username, args.password, args.timeout)
    loop = asyncio.get_event_loop()

    if args.detailled_energy is False:
        async_func = client.fetch_data()
    else:
        start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
        async_func = client.fetch_data_detailled_energy_use(start_date,
                                                            end_date)
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
    elif args.influxdb:
        output_influx(client.get_data(args.contract))
    elif args.json or args.detailled_energy:
        output_json(client.get_data(args.contract))
    else:
        output_text(args.username, client.get_data(args.contract), args.hourly)
    return 0


if __name__ == '__main__':
    sys.exit(main())
