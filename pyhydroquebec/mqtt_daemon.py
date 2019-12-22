"""MQTT Daemon which collected Hydroquebec Data.

And send it to MQTT using Home-Assistant format.
"""
import asyncio
from datetime import datetime, timedelta
import json
import os
import uuid

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import mqtt_hass_base

from pyhydroquebec.__version__ import VERSION
from pyhydroquebec.client import HydroQuebecClient
from pyhydroquebec.consts import DAILY_MAP, CURRENT_MAP, HQ_TIMEZONE


def get_mac():
    """Get mac address."""
    mac_addr = (':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                for ele in range(0, 8 * 6, 8)][::-1]))
    return mac_addr


class MqttHydroQuebec(mqtt_hass_base.MqttDevice):
    """MQTT MqttHydroQuebec."""

    timeout = None
    frequency = None

    def __init__(self):
        """Create new MqttHydroQuebec Object."""
        mqtt_hass_base.MqttDevice.__init__(self, "mqtt-hydroquebec")

    def read_config(self):
        """Read config from yaml file."""
        with open(os.environ['CONFIG']) as fhc:
            self.config = load(fhc, Loader=Loader)
        self.timeout = self.config.get('timeout', 30)
        # 6 hours
        self.frequency = self.config.get('frequency', None)

    async def _init_main_loop(self):
        """Init before starting main loop."""

    def _publish_sensor(self, sensor_type, contract_id,
                        unit=None, device_class=None, icon=None):
        """Publish a Home-Assistant MQTT sensor."""
        mac_addr = get_mac()

        base_topic = ("{}/sensor/hydroquebec_{}".format(self.mqtt_root_topic,
                                                        contract_id))

        sensor_config = {}
        sensor_config["device"] = {"connections": [["mac", mac_addr]],
                                   "name": "hydroquebec_{}".format(contract_id),
                                   "identifiers": ['hydroquebec', contract_id],
                                   "manufacturer": "mqtt-hydroquebec",
                                   "sw_version": VERSION}

        sensor_state_config = "{}/{}/state".format(base_topic, sensor_type)
        sensor_config.update({
            "state_topic": sensor_state_config,
            "name": "hydroquebec_{}_{}".format(contract_id, sensor_type),
            "unique_id": "{}_{}".format(contract_id, sensor_type),
            "force_update": True,
            "expire_after": 0,
            })

        if device_class:
            sensor_config["device_class"] = device_class
        if unit:
            sensor_config["unit_of_measurement"] = unit
        if icon:
            sensor_config["icon"] = icon

        sensor_config_topic = "{}/{}/config".format(base_topic, sensor_type)

        self.mqtt_client.publish(topic=sensor_config_topic,
                                 retain=True,
                                 payload=json.dumps(sensor_config))

        return sensor_state_config

    async def _main_loop(self):
        """Run main loop."""
        self.logger.debug("Get Data")
        for account in self.config['accounts']:
            client = HydroQuebecClient(account['username'],
                                       account['password'],
                                       self.timeout,
                                       log_level=self._loglevel)
            await client.login()
            for contract_data in account['contracts']:
                # Get contract
                customer = None
                for client_customer in client.customers:
                    if str(client_customer.contract_id) == str(contract_data['id']):
                        customer = client_customer

                if customer is None:
                    self.logger.warning('Contract %s not found', contract_data['id'])
                    continue

                await customer.fetch_current_period()
                # await customer.fetch_annual_data()
                # await customer.fetch_monthly_data()
                yesterday = datetime.now(HQ_TIMEZONE) - timedelta(days=1)
                yesterday_str = yesterday.strftime("%Y-%m-%d")
                await customer.fetch_daily_data(yesterday_str, yesterday_str)
                if not customer.current_daily_data:
                    yesterday = yesterday - timedelta(days=1)
                    yesterday_str = yesterday.strftime("%Y-%m-%d")
                    await customer.fetch_daily_data(yesterday_str, yesterday_str)

                # Balance
                # Publish sensor
                balance_topic = self._publish_sensor('balance', customer.account_id,
                                                     unit="$", device_class=None,
                                                     icon="mdi:currency-usd")
                # Send sensor data
                self.mqtt_client.publish(
                        topic=balance_topic,
                        payload=customer.balance)

                # Current period
                for data_name, data in CURRENT_MAP.items():
                    # Publish sensor
                    sensor_topic = self._publish_sensor(data_name,
                                                        customer.contract_id,
                                                        unit=data['unit'],
                                                        icon=data['icon'],
                                                        device_class=data['device_class'])
                    # Send sensor data
                    self.mqtt_client.publish(
                            topic=sensor_topic,
                            payload=customer.current_period[data_name])

                # Yesterday data
                for data_name, data in DAILY_MAP.items():
                    # Publish sensor
                    sensor_topic = self._publish_sensor('yesterday_' + data_name,
                                                        customer.contract_id,
                                                        unit=data['unit'],
                                                        icon=data['icon'],
                                                        device_class=data['device_class'])
                    # Send sensor data
                    self.mqtt_client.publish(
                            topic=sensor_topic,
                            payload=customer.current_daily_data[yesterday_str][data_name])

            await client.close_session()

        if self.frequency is None:
            self.logger.info("Frequency is None, so it's a one shot run")
            self.must_run = False
            return

        self.logger.info("Waiting for %d seconds before the next check", self.frequency)
        i = 0
        while i < self.frequency and self.must_run:
            await asyncio.sleep(1)
            i += 1

    def _on_connect(self, client, userdata, flags, rc):
        """On connect callback method."""

    def _on_publish(self, client, userdata, mid):
        """MQTT on publish callback."""

    def _mqtt_subscribe(self, client, userdata, flags, rc):
        """Subscribe to all needed MQTT topic."""

    def _on_message(self, client, userdata, msg):
        """MQTT on message callback."""

    def _signal_handler(self, signal_, frame):
        """Handle SIGKILL."""

    async def _loop_stopped(self):
        """Run after the end of the main loop."""
