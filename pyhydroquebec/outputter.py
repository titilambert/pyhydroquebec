"""PyHydroQuebec Output Module.

This module defines the different output functions:
* text
* influxdb
* json
"""

from pyhydroquebec.consts import (OVERVIEW_TPL,
                                  CONSUMPTION_PROFILE_TPL,
                                  YESTERDAY_TPL, ANNUAL_TPL)


def output_text(customer, show_hourly=False):
    """Format data to get a readable output."""
    print(OVERVIEW_TPL.format(customer))
    print(CONSUMPTION_PROFILE_TPL.format(d=customer.current_period))
    print(ANNUAL_TPL.format(d=customer.current_annual_data))
    yesterday_date = list(customer.current_daily_data.keys())[0]
    data = {'date': yesterday_date}
    data.update(customer.current_daily_data[yesterday_date])
    print(YESTERDAY_TPL.format(d=data))
    # print(HOURLY_TPL)
    raise Exception("FIXME: missing HOURLY")


def output_influx(contract):
    """Print data using influxDB format."""
    raise Exception("FIXME")
#    # Pop yesterdays data
#    yesterday_data = contract]['yesterday_hourly_consumption']
#    del data[contract]['yesterday_hourly_consumption']
#
#    # Print general data
#    out = "pyhydroquebec,contract=" + contract + " "
#
#    for index, key in enumerate(data[contract]):
#        if index != 0:
#            out = out + ","
#        if key in ("annual_date_start", "annual_date_end"):
#            out += key + "=\"" + str(data[contract][key]) + "\""
#        else:
#            out += key + "=" + str(data[contract][key])
#
#    out += " " + str(int(datetime.datetime.now(HQ_TIMEZONE).timestamp() * 1000000000))
#    print(out)
#
#    # Print yesterday values
#    yesterday = datetime.datetime.now(HQ_TIMEZONE) - datetime.timedelta(days=1)
#    yesterday = yesterday.replace(minute=0, hour=0, second=0, microsecond=0)
#
#    for hour in yesterday_data:
#        msg = "pyhydroquebec,contract={} {} {}"
#
#        data = ",".join(["{}={}".format(key, value) for key, value in hour.items()
#                         if key != 'hour'])
#
#        datatime = datetime.datetime.strptime(hour['hour'], '%H:%M:%S')
#        yesterday = yesterday.replace(hour=datatime.hour)
#        yesterday_str = str(int(yesterday.timestamp() * 1000000000))
#
#        print(msg.format(contract, data, yesterday_str))


def output_json(data):
    """Print data as Json."""
    raise Exception("FIXME")
#    print(json.dumps(data))
