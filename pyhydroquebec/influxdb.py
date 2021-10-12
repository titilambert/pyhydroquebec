try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions

except ImportError:
    raise ImportError("Install influxdb to use this feature")

import pytz
import os, time
from datetime import datetime
from .consts import DAILY_MAP, CURRENT_MAP, ANNUAL_MAP

try:
    # Load parameters from environment variables
    if os.path.isfile("{}/.env".format(os.getcwd())):
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.getcwd(), ".env"))
except ImportError:
    print("You need to pip install python-dotenv to use your .env file")

class InfluxDB:
    """
    Connection to InfluxDB to write to DB
    """

    url = None
    port = 8086
    token = None
    org = None
    bucket = None
    tags_file = None
    username = None
    password = None
    client = None

    def __init__(self, params):
        # params should be a dict with name=InfluxDB and bucket=valid_bucket_to_use.
        # optional params : url, port, token and org may be provided
        # if they are not provided, we will try to get them from environment
        # variables that shoudl have been provided in a .env file.
        for k, v in params.items():
            setattr(self, k, v)
        if self.bucket is None:
            raise ValueError("Missing bucket name, please provide one in db_params")
        self.connect_to_db()

        self.write_api = self.client.write_api(
            write_options=WriteOptions(
                batch_size=getattr(self, "batch_size", 25),
                flush_interval=getattr(self, "flush_interval", 10_000),
                jitter_interval=getattr(self, "jitter_interval", 2_000),
                retry_interval=getattr(self, "retry_interval", 5_000),
                max_retries=getattr(self, "max_retries", 5),
                max_retry_delay=getattr(self, "max_retry_delay", 30_000),
                exponential_base=getattr(self, "exponential_base", 2),
            )
        )
        self.query_api = self.client.query_api()
        print(self.health)

    def connect_to_db(self):
        if self.url is None:
            # Will try environment variables
            self.client = InfluxDBClient.from_env_properties()
        else:
            _url = "{}:{}".format(self.url, self.port)
            if self.token:
                self.client = InfluxDBClient(url=_url, token=self.token)
            else:
                self.client = InfluxDBClient(
                    url=_url,
                    token="{}:{}".format(self.username, self.password),
                    bucket=self.bucket,
                    org="-",
                )
        try:
            self.health
        except:
            raise ConnectionError("Error connecting to InfluxDB")

    @property
    def health(self):
        return self.client.health()

    def write_data_to_db(self, customer, show_hourly=False):
        _data = []

        # account
        account_id = customer.account_id
        customer_id = customer.customer_id
        contract_id = customer.contract_id
        id_prefix = "{}|{}|{}".format(account_id, customer_id, contract_id)
        balance = customer.balance

        yesterday_date = list(customer.current_daily_data.keys())[0]
        data = {'date': yesterday_date}
        data.update(customer.current_daily_data[yesterday_date])

        # yesterday
        # (id, value, units, tag)
        _points = []
        for k, v in CURRENT_MAP.items():
            _id = "{}|{}".format(id_prefix, k)
            _point = (
                Point(_id)
                .field("value", customer.current_period[k])
                .tag("category", "current_period")
                .tag("account_id", account_id)
                .tag("customer_id", customer_id)
                .tag("contract_id", contract_id)
                .tag("unit", v['unit'])
                .tag('name', v['raw_name'])
                .time(datetime.fromisoformat(data['date']).astimezone(pytz.UTC))
            )
            _points.append(_point)

        # annual
        _id = "{}|{}".format(id_prefix, 'annual_kwh_price_cent')
        _point = (
            Point(_id)
            .field("annual_kwh_price_cent", customer.current_annual_data['annual_kwh_price_cent'])
            .field("annual_mean_daily_bill", customer.current_annual_data['annual_mean_daily_bill'])
            .field("annual_total_consumption", customer.current_annual_data['annual_mean_daily_bill'])
            .field("annual_mean_daily_consumption", customer.current_annual_data['annual_mean_daily_consumption'])
            .tag("category", "annual")
            .tag("unit", "")
            .tag("date_start", customer.current_annual_data['annual_date_start'])
            .tag("date_end", customer.current_annual_data['annual_date_end'])
            .tag('name', 'Annual_Stats')
            .tag("account_id", account_id)
            .tag("customer_id", customer_id)
            .tag("contract_id", contract_id)
            .time(datetime.fromisoformat(data['date']).astimezone(pytz.UTC))
        )
        _points.append(_point)

        if show_hourly:
            # hourly
            for hour, _data in customer.hourly_data[yesterday_date]["hours"].items():
                for k, v in DAILY_MAP.items():
                    _id = "{}|{}".format(id_prefix, k)
                    _point = (
                        Point(_id)
                        .field("value", _data[k])
                        .tag("category", "hourly")
                        .tag("unit", v['unit'])
                        .tag('name', v['raw_name'])
                        .tag("account_id", account_id)
                        .tag("customer_id", customer_id)
                        .tag("contract_id", contract_id)
                        .time(datetime.fromisoformat("{}T{:02d}:00".format(data['date'], hour)).astimezone(pytz.UTC))
                    )
                    _points.append(_point)
        self.write_api.write(self.bucket, self.org, _points)

        # Give time to the scheduler so it can write to InfluxDB
        for each in range(0,100):
            time.sleep(0.1)
class ConnectionError(Exception):
    pass
