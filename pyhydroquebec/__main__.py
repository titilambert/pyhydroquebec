"""PyHydroQuebec Entrypoint Module."""

import argparse
import sys
import datetime
import asyncio

from pyhydroquebec import HydroQuebecClient, REQUESTS_TIMEOUT, HQ_TIMEZONE
from pyhydroquebec.outputter import output_text, output_influx, output_json
from pyhydroquebec.mqtt_daemon import MqttHydroQuebec
from version import VERSION


async def fetch_data(client, contract_id):
    await client.login()
    for customer in client.customers:
        if customer.contract_id != contract_id:
            continue
        await customer.fetch_current_period()
        return customer
        #await customer.fetch_hourly_data("2019-10-12")
        #await customer.fetch_annual_data()
        #await customer.fetch_daily_data()
        #await customer.fetch_monthly_data()
        #await customer.fetch_hourly_data()

async def list_contracts(client):
    await client.login()
    return [{"account_id": c.account_id, 
             "customer_id": c.customer_id,
             "contract_id": c.contract_id}
            for c in client.customers]


async def fetch_data_detailled_energy_use(client, start_date, end_date):
    pass
    # TODO

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

    if args.list_contracts:
        async_func = list_contracts(client)
    elif args.detailled_energy is False:
        async_func = fetch_data(client, args.contract)
    else:
        raise Exception("FIXME")
        start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
        async_func = fetch_data_detailled_energy_use(client, start_date, end_date)
    try:
        results = loop.run_until_complete(asyncio.gather(async_func))
    except BaseException as exp:
        print(exp)
        return 1
    finally:
        close_fut = asyncio.wait([client.close_session()])
        loop.run_until_complete(close_fut)

    if args.list_contracts:
        for customer in results[0]:
            print("Contract: {contract_id}\n\tAccount: {account_id}\n\tCustomer: {customer_id}".format(**customer)) 
    elif args.influxdb:
        output_influx(results[0])
    elif args.json or args.detailled_energy:
        output_json(results[0])
    else:
        output_text(results[0], args.hourly)
    return 0


def mqtt_daemon():
    """Entrypoint function."""
    dev = MqttHydroQuebec()
    asyncio.run(dev.async_run())


if __name__ == '__main__':
    sys.exit(main())
