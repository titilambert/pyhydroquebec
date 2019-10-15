import os
import asyncio

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import mqtt_hass_base

from pyhydroquebec import HydroQuebecClient, REQUESTS_TIMEOUT, HQ_TIMEZONE


class MqttHydroQuebec(mqtt_hass_base.MqttDevice):
    """MQTT MqttHydroQuebec."""

    def __init__(self):
        """Constructor."""
        mqtt_hass_base.MqttDevice.__init__(self, "mqtt-hydroquebec")

    def read_config(self):
        with open(os.environ['CONFIG']) as fhc:
            self.config = load(fhc, Loader=Loader)


    async def _init_main_loop(self):
        """Init before starting main loop."""

    async def _main_loop(self):
        """Run main loop."""
        self.logger.debug("Get Data")
        for account in self.config['accounts']:
            client = HydroQuebecClient(account['username'], account['password'], self.config['timeout'])
            await client.login()
            print(client.customer[0].balance())
        await asyncio.sleep(900)
        # TODO
