"""Tests for output module."""
import json
import re
import unittest

from pyhydroquebec.outputter import output_influx, output_json


@unittest.skip('Influx output broken.')
def test_influx_output(capsys):
    """Test influx output function."""

    data = {'310277835': {
               'annual_date_end': '2018-11-28',
               'annual_date_start': '2017-11-25',
               'annual_kwh_price_cent': 8.94,
               'annual_length': 369,
               'annual_mean_daily_bill': 5.05,
               'annual_mean_daily_consumption': 56.5,
               'annual_total_bill': 1863.19,
               'annual_total_consumption': 20835,
               'balance': 320.59,
               'period_average_temperature': 0,
               'period_higher_price_consumption': 0,
               'period_length': 2,
               'period_lower_price_consumption': 118,
               'period_mean_daily_bill': 5.33,
               'period_mean_daily_consumption': 59.0,
               'period_projection': 537.21,
               'period_total_bill': 10.65,
               'period_total_consumption': 118,
               'period_total_days': 65,
               'yesterday_average_temperature': -1,
               'yesterday_higher_price_consumption': 0,
               'yesterday_hourly_consumption': [{'high': 0,
                                                 'hour': '00:00:00',
                                                 'lower': 0.97,
                                                 'temp': 0,
                                                 'total': 0.97},
                                                {'high': 0,
                                                 'hour': '01:00:00',
                                                 'lower': 1.2,
                                                 'temp': 0,
                                                 'total': 1.2},
                                                {'high': 0,
                                                 'hour': '02:00:00',
                                                 'lower': 1.62,
                                                 'temp': 0,
                                                 'total': 1.62}],
               'yesterday_lower_price_consumption': 55.23,
               'yesterday_total_consumption': 55.23}}

    expected = (r'''pyhydroquebec,contract=310277835 annual_date_end="2018-11-28",'''
                r'''annual_date_start="2017-11-25",annual_kwh_price_cent=8.94,'''
                r'''annual_length=369,annual_mean_daily_bill=5.05,'''
                r'''annual_mean_daily_consumption=56.5,annual_total_bill=1863.19,'''
                r'''annual_total_consumption=20835,balance=320.59,period_average_temperature=0'''
                r''',period_higher_price_consumption=0,period_length=2,'''
                r'''period_lower_price_consumption=118,period_mean_daily_bill=5.33,'''
                r'''period_mean_daily_consumption=59.0,period_projection=537.21,'''
                r'''period_total_bill=10.65,period_total_consumption=118,period_total_days=65,'''
                r'''yesterday_average_temperature=-1,yesterday_higher_price_consumption=0,'''
                r'''yesterday_lower_price_consumption=55.23,yesterday_total_consumption=55.23'''
                r''' \d*\n'''
                r'''pyhydroquebec,contract=310277835 high=0,lower=0.97,temp=0,total=0.97'''
                r''' \d*\n'''
                r'''pyhydroquebec,contract=310277835 high=0,lower=1.2,temp=0,total=1.2'''
                r''' \d*\n'''
                r'''pyhydroquebec,contract=310277835 high=0,lower=1.62,temp=0,total=1.62'''
                r''' \d*\n''')
    output_influx(data)
    captured = capsys.readouterr()
    assert re.match(expected, captured.out)


def test_json_output(capsys):
    """Test json output function."""

    data = {
        "overview": {
            "contract_id": "foo_customer",
            "account_id": "foo_accoutn",
            "customer_id": "foo_id",
            "balance": "foo_balance"
        },
        "current_period": {
            "period_total_bill": "foobar_total_bill", "current_period_data": "current_period_data"
        },
        "current_annual_data": {
            "some_annual_data_key": "foobar_annual_data_value"
        },
        "yesterday_data": {
            "date": "some_date",
            "hour1": {
                "foobar": "some_data"
            }
        }
    }

    # \n because of trailing newline in readouterr
    expected = f'{json.dumps(data)}\n'

    class MockCustomer:  # pylint: disable=too-few-public-methods
        """Mock class for Customer."""
        contract_id = "foo_customer"
        account_id = "foo_accoutn"
        customer_id = "foo_id"
        balance = "foo_balance"
        current_period = {
            "period_total_bill": "foobar_total_bill", "current_period_data": "current_period_data"
        }
        current_annual_data = {"some_annual_data_key": "foobar_annual_data_value"}
        current_daily_data = {"some_date": {"hour1": {"foobar": "some_data"}}}

    mock_customer = MockCustomer()
    output_json(mock_customer)
    captured = capsys.readouterr()

    assert captured.out == expected
