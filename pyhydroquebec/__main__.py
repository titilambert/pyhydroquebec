"""PyHydroQuebec Entrypoint Module."""

import argparse
import asyncio
from datetime import datetime, timedelta
from pprint import pprint
import sys
import os

from pyhydroquebec.client import HydroQuebecClient
from pyhydroquebec.consts import REQUESTS_TIMEOUT, HQ_TIMEZONE
from pyhydroquebec.outputter import output_text, output_influx, output_json
from pyhydroquebec.mqtt_daemon import MqttHydroQuebec
from pyhydroquebec.__version__ import VERSION


async def fetch_data(client, contract_id, fetch_hourly=False):
    """Fetch data for basic report."""
    await client.login()
    for customer in client.customers:
        if customer.contract_id != contract_id and contract_id is not None:
            continue
        if contract_id is None:
            client.logger.warn("Contract id not specified, using first available.")

        await customer.fetch_current_period()
        await customer.fetch_annual_data()
        await customer.fetch_monthly_data()
        yesterday = datetime.now(HQ_TIMEZONE) - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        await customer.fetch_daily_data(yesterday_str, yesterday_str)
        if not customer.current_daily_data:
            yesterday = yesterday - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            await customer.fetch_daily_data(yesterday_str, yesterday_str)
        if fetch_hourly:
            await customer.fetch_hourly_data(yesterday_str)
        return customer


async def dump_data(client, contract_id):
    """Fetch all data and dump them for debug and dev."""
    customer = await fetch_data(client, contract_id)
    await customer.fetch_daily_data()
    await customer.fetch_hourly_data()
    return customer


async def list_contracts(client):
    """Return the list of the contracts for a given account."""
    await client.login()
    return [{"account_id": c.account_id,
             "customer_id": c.customer_id,
             "contract_id": c.contract_id}
            for c in client.customers]


async def fetch_data_detailled_energy_use(client, start_date, end_date):
    """Fetch hourly data for a given period."""
    # TODO
    raise Exception("FIXME")


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
    parser.add_argument('-D', '--dump-data', action='store_true',
                        default=False, help='Show contract python object as dict')
    parser.add_argument('-t', '--timeout',
                        default=REQUESTS_TIMEOUT, help='Request timeout')
    parser.add_argument('-L', '--log-level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='WARNING', help='Log level')
    parser.add_argument('-V', '--version', action='store_true',
                        default=False, help='Show version')
    raw_group = parser.add_argument_group('Detailled-energy raw download option')
    raw_group.add_argument('--detailled-energy', action='store_true',
                           default=False, help='Get raw json output download')
    raw_group.add_argument('--start-date',
                           default=(datetime.now(HQ_TIMEZONE) -
                                    timedelta(days=1)).strftime("%Y-%m-%d"),
                           help='Start date for detailled-output')
    raw_group.add_argument('--end-date',
                           default=datetime.now(HQ_TIMEZONE).strftime("%Y-%m-%d"),
                           help="End date for detailled-output")

    args = parser.parse_args()

    if args.version:
        print(VERSION)
        return 0

    # Check input for Username, Password and Contract - CLI overwrite ENV variable

    # Check Env
    hydro_user = os.environ.get("PYHQ_USER")
    hydro_pass = os.environ.get("PYHQ_PASSWORD")
    hydro_contract = os.environ.get("PYHQ_CONTRACT")

    # Check Cli
    if args.username:
        hydro_user = args.username
    if args.password:
        hydro_pass = args.password
    if args.contract:
        hydro_contract = args.contract

    if not hydro_user or not hydro_pass:
        parser.print_usage()
        print("pyhydroquebec: error: the following arguments are required: "
              "-u/--username, -p/--password")
        return 3

    client = HydroQuebecClient(hydro_user, hydro_pass,
                               args.timeout, log_level=args.log_level)
    loop = asyncio.get_event_loop()

    # Get the async_func
    if args.list_contracts:
        async_func = list_contracts(client)
    elif args.dump_data:
        async_func = dump_data(client, hydro_contract)
    elif args.detailled_energy is False:
        async_func = fetch_data(client, hydro_contract, args.hourly)
    else:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        async_func = fetch_data_detailled_energy_use(client, start_date, end_date)

    # Fetch data
    try:
        results = loop.run_until_complete(asyncio.gather(async_func))
    except BaseException as exp:
        print(exp)
        return 1
    finally:
        close_fut = asyncio.wait([client.close_session()])
        loop.run_until_complete(close_fut)
        loop.close()

    # Output data
    if args.list_contracts:
        for customer in results[0]:
            print("Contract: {contract_id}\n\t"
                  "Account: {account_id}\n\t"
                  "Customer: {customer_id}".format(**customer))
    elif args.dump_data:
        pprint(results[0].__dict__)
    elif args.influxdb:
        output_influx(results[0])
    elif args.json or args.detailled_energy:
        output_json(results[0], args.hourly)
    else:
        output_text(results[0], args.hourly)
    return 0


def mqtt_daemon():
    """Entrypoint function."""
    dev = MqttHydroQuebec()
    asyncio.run(dev.async_run())


if __name__ == '__main__':
    sys.exit(main())
